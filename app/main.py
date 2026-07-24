import sys
import os
import sqlite3
import uuid
import threading
import importlib
import math
from datetime import datetime
import webview
import re
from dotenv import load_dotenv

# Load env vars from project root .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.document_loader import load_documents
from ingestion.text_splitter import split_documents
from ingestion.embedding_store import save_embeddings, load_embeddings
from llm.local_llm import initialize_foundry, load_embedding_model, load_chat_client
from ingestion.embedding_generator import generate_document_embeddings
from rag_pipeline import ask_question
from rag_streaming import stream_ask_question

DOCS_PATH = os.getenv("DOCS_PATH", "data")
EMBEDDINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../vector/embeddings.db")
CHATS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../vector/chats.db")

# Global streaming sessions storage
streaming_sessions = {}


class Api:
    # Bridge exposed to the frontend via pywebview (window.pywebview.api.*)

    def __init__(self):
        self.history = []
        self.chunks = None
        self.doc_embeddings = None
        self.embedding_client = None
        self.chat_client = None
        self.ready = False
        self.conn = sqlite3.connect(CHATS_DB_PATH, check_same_thread=False)
        self._create_tables_if_not_exist()
        self.current_chat_id = None
        self.new_chat()

    def _create_tables_if_not_exist(self):
        """
        Creates two tables in the database (if they don't already exist):
        - chats: which chats exist, when they were created
        - messages: individual messages inside each chat
        """
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                role TEXT,
                content TEXT,
                created_at TEXT
            )
        """)
        self.conn.commit()

    def new_chat(self):
        """
        Called when the user clicks the 'New Chat' button.
        Generates a new chat ID, saves it to the database,
        and resets the currently active conversation history.
        """
        new_chat_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO chats (chat_id, title, created_at) VALUES (?, ?, ?)",
            (new_chat_id, "New Chat", datetime.now().isoformat())
        )
        self.conn.commit()
        self.current_chat_id = new_chat_id
        self.history = []
        return {"chat_id": new_chat_id}

    def list_chats(self):
        """
        Returns the list of all past chats.
        Used to display them in a sidebar (e.g. 'Query History').
        """
        cursor = self.conn.execute(
            "SELECT chat_id, title, created_at FROM chats ORDER BY created_at DESC"
        )
        result = []
        for chat_id, title, created_at in cursor.fetchall():
            result.append({
                "chat_id": chat_id,
                "title": title,
                "created_at": created_at
            })
        return result

    def switch_chat(self, chat_id):
        """
        Called when the user clicks on an old chat in the sidebar.
        Loads all messages of that chat back from the database.
        """
        self.current_chat_id = chat_id
        cursor = self.conn.execute(
            "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id",
            (chat_id,)
        )
        messages = []
        for role, content in cursor.fetchall():
            messages.append({"role": role, "content": content})
        self.history = messages
        return {"messages": messages}

    def delete_chat(self, chat_id):
        """Permanently remove one chat and all of its saved messages."""
        if not chat_id:
            return {"success": False, "error": "missing_chat_id"}

        cursor = self.conn.execute(
            "SELECT 1 FROM chats WHERE chat_id=?", (chat_id,)
        )
        if cursor.fetchone() is None:
            return {"success": False, "error": "chat_not_found"}

        was_active = chat_id == self.current_chat_id
        with self.conn:
            self.conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
            self.conn.execute("DELETE FROM chats WHERE chat_id=?", (chat_id,))

        if was_active:
            self.current_chat_id = None
            self.history = []
            new_chat = self.new_chat()
            return {"success": True, "was_active": True, **new_chat}

        return {"success": True, "was_active": False}

    def _save_message(self, role, content):
        """
        Saves a single message (user or assistant) to the database.
        role: 'user' or 'assistant'
        """
        self.conn.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (self.current_chat_id, role, content, datetime.now().isoformat())
        )
        self.conn.commit()

    def _update_title_if_needed(self, first_message):
        """
        If the chat's title is still 'New Chat',
        sets the title to the first 40 characters of the first message.
        (So the sidebar shows a meaningful name instead of 'New Chat')
        """
        cursor = self.conn.execute(
            "SELECT title FROM chats WHERE chat_id=?", (self.current_chat_id,)
        )
        row = cursor.fetchone()
        if row and row[0] == "New Chat":
            new_title = first_message.strip()[:40]
            self.conn.execute(
                "UPDATE chats SET title=? WHERE chat_id=?",
                (new_title, self.current_chat_id)
            )
            self.conn.commit()

    def initialize(self):
        # Loads models + index once; no-op if already ready
        if self.ready:
            return {"status": "already initialized"}

        print("\nInitializing RAG system...\n", flush=True)
        manager = initialize_foundry()

        # Reuse cached embeddings if they exist, otherwise build from scratch
        self.chunks, self.doc_embeddings = load_embeddings(EMBEDDINGS_PATH)
        if self.chunks is None:
            documents = load_documents(DOCS_PATH)
            self.chunks = split_documents(documents)
            self.embedding_client = load_embedding_model(manager)
            self.doc_embeddings = generate_document_embeddings(self.chunks, self.embedding_client)
            save_embeddings(self.chunks, self.doc_embeddings, EMBEDDINGS_PATH)
        else:
            self.embedding_client = load_embedding_model(manager)

        self.chat_client = load_chat_client(manager)
        self.ready = True
        print("\nRAG system ready!\n", flush=True)
        return {"status": "ready"}

    def ask(self, query):
        # Non-streaming Q&A: run full pipeline, save and return the answer
        query = (query or "").strip()
        if not query:
            return {"answer": "", "error": "empty_query"}

        try:
            self._update_title_if_needed(query)
            self._save_message("user", query)
            answer, self.history = ask_question(
                query, self.chunks, self.doc_embeddings,
                self.embedding_client, self.chat_client, self.history
            )
            self._save_message("assistant", answer)
            return {"answer": answer, "error": None}
        except Exception as e:
            return {"answer": "", "error": str(e)}

    def start_streaming_session(self, query):
        """
        Starts a streaming session and returns session_id.
        Backend collects streaming events in a queue.
        """
        query = (query or "").strip()
        if not query:
            return {"error": "empty_query", "session_id": None}

        session_id = str(uuid.uuid4())
        streaming_sessions[session_id] = {
            "events": [],
            "completed": False,
            "query": query
        }

        # Start background thread to collect events
        thread = threading.Thread(
            target=self._collect_streaming_events,
            args=(session_id, query),
            daemon=True
        )
        thread.start()

        return {"session_id": session_id, "error": None}

    def _collect_streaming_events(self, session_id, query):
        """Background thread that collects streaming events."""
        try:
            self._update_title_if_needed(query)
            self._save_message("user", query)

            full_answer = ""
            sources = []

            for event in stream_ask_question(
                query, self.chunks, self.doc_embeddings,
                self.embedding_client, self.chat_client, self.history
            ):
                # Log sources to terminal
                if event["type"] == "retrieved":
                    print("\n" + "=" * 60)
                    print("RETRIEVED DOCUMENTS")
                    print("=" * 60)
                    for doc_info in event["data"]["documents"]:
                        print(f"Rank {doc_info['rank']}: {doc_info['source']}")
                        print(f"  Score: {doc_info['score']:.4f}")
                        print(f"  Path: {doc_info['full_path']}")
                    print("=" * 60 + "\n")

                # Accumulate LLM text for saving
                if event["type"] == "chunk":
                    full_answer += event["data"]["text"]

                # Save message and collect sources when complete
                elif event["type"] == "complete":
                    answer = event["data"]["answer"]
                    sources = event["data"]["sources"]

                    # Deduplicate sources while preserving order
                    sources = list(dict.fromkeys(sources))

                    if not answer:
                        answer = full_answer

                    self._save_message("assistant", answer)

                    # Log sources summary to terminal
                    print("\n" + "=" * 60)
                    print("SOURCES USED")
                    print("=" * 60)
                    for source in sources:
                        print(f"  • {source}")
                    print("=" * 60 + "\n")

                # Add event to session queue
                if session_id in streaming_sessions:
                    streaming_sessions[session_id]["events"].append(event)

            if session_id in streaming_sessions:
                streaming_sessions[session_id]["completed"] = True

        except Exception as e:
            # Surface pipeline errors as an "error" event
            if session_id in streaming_sessions:
                streaming_sessions[session_id]["events"].append({
                    "type": "error",
                    "data": {"error": str(e)}
                })
                streaming_sessions[session_id]["completed"] = True

    def get_streaming_event(self, session_id):
        """Gets next event from streaming session queue."""
        if session_id not in streaming_sessions:
            return {"event": None, "completed": True}

        session = streaming_sessions[session_id]
        if session["events"]:
            event = session["events"].pop(0)
            return {"event": event, "completed": False}

        if session["completed"]:
            return {"event": None, "completed": True}

        return {"event": None, "completed": False}

    def cancel_streaming_session(self, session_id):
        """Cancels a streaming session."""
        if session_id in streaming_sessions:
            del streaming_sessions[session_id]
        return {"success": True}

    def get_stats(self):
        # Counts indexed chunks per file extension for the dashboard
        chunks = self.chunks
        if not self.ready or not chunks:
            return {"total": 0, "pdfs": 0, "txts": 0, "docxs": 0, "mds": 0,
                     "pptxs": 0, "xlsx": 0, "jpgs": 0, "jpegs": 0, "pngs": 0, "ready": False}

        def source_of(c):
            if isinstance(c, dict):
                return str(c.get("source", "")).lower()
            return str(getattr(c, "source", "")).lower()

        pdfs = sum(1 for c in chunks if source_of(c).endswith(".pdf"))
        txts = sum(1 for c in chunks if source_of(c).endswith(".txt"))
        docxs = sum(1 for c in chunks if source_of(c).endswith(".docx"))
        mds = sum(1 for c in chunks if source_of(c).endswith(".md"))
        pptxs = sum(1 for c in chunks if source_of(c).endswith(".pptx"))
        xlsx = sum(1 for c in chunks if source_of(c).endswith(".xlsx"))
        jpgs = sum(1 for c in chunks if source_of(c).endswith(".jpg"))
        jpegs = sum(1 for c in chunks if source_of(c).endswith(".jpeg"))
        pngs = sum(1 for c in chunks if source_of(c).endswith(".png"))

        return {
            "total": len(chunks),
            "pdfs": pdfs, "txts": txts, "docxs": docxs, "mds": mds,
            "pptxs": pptxs, "xlsx": xlsx, "jpgs": jpgs, "jpegs": jpegs, "pngs": pngs,
            "ready": True
        }

    def resync_index(self):
        # Indexes only new files, appends to existing chunks/embeddings
        try:
            data_dir = DOCS_PATH

            if self.chunks:
                already_indexed_chunks = self.chunks
            else:
                already_indexed_chunks = []

            already_indexed_paths = set()
            for chunk in already_indexed_chunks:
                already_indexed_paths.add(chunk["source"])

            all_documents = load_documents(data_dir)
            new_documents = []
            for doc in all_documents:
                if doc["source"] not in already_indexed_paths:
                    new_documents.append(doc)

            if len(new_documents) == 0:
                return {
                    "status": "ok",
                    "total": len(already_indexed_chunks),
                    "added": 0
                }

            new_chunks = split_documents(new_documents)

            if self.embedding_client is None:
                manager = initialize_foundry()
                self.embedding_client = load_embedding_model(manager)

            new_embeddings = generate_document_embeddings(new_chunks, self.embedding_client)

            if self.doc_embeddings:
                existing_embeddings = self.doc_embeddings
            else:
                existing_embeddings = []

            self.chunks = already_indexed_chunks + new_chunks
            self.doc_embeddings = existing_embeddings + new_embeddings

            save_embeddings(self.chunks, self.doc_embeddings, EMBEDDINGS_PATH)

            return {
                "status": "ok",
                "total": len(self.chunks),
                "added": len(new_chunks),
                "new_files": len(new_documents)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_model_info(self):
        # Returns active model names + query count for the info view
        from config import chat_model_name, embedding_model_name, top_k

        total_queries = 0
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM messages WHERE role='user'")
            total_queries = cursor.fetchone()[0]
        except Exception:
            pass

        return {
            "llm_model": chat_model_name,
            "embedding_model": embedding_model_name,
            "runtime": "Microsoft Foundry Local",
            "total_queries": total_queries,
            "top_k": top_k
        }

    def get_settings(self):
        # Read from the loaded config module so saved values are shown immediately.
        settings = importlib.import_module("config")

        return {
            "top_k": settings.top_k,
            "retrieval_candidate_k": settings.retrieval_candidate_k,
            "min_score_threshold": settings.min_score_threshold,
            "min_confidence_score": settings.min_confidence_score,
            "relative_score_ratio": settings.relative_score_ratio,
            "enable_reranker": settings.enable_reranker,
            "bm25_weight": settings.bm25_weight,
            "semantic_weight": settings.semantic_weight
        }

    def save_settings(self, new_settings):
        """Validate, persist, and immediately apply retrieval settings."""
        try:
            integer_keys = {"top_k", "retrieval_candidate_k"}
            float_keys = {
                "min_score_threshold", "min_confidence_score", "relative_score_ratio",
                "bm25_weight", "semantic_weight"
            }
            allowed_keys = integer_keys | float_keys | {"enable_reranker"}
            if not isinstance(new_settings, dict) or set(new_settings) != allowed_keys:
                return {"success": False, "error": "Invalid settings payload."}

            parsed = {}
            for key in integer_keys:
                parsed[key] = int(new_settings[key])
                if parsed[key] < 1:
                    raise ValueError(f"{key} must be at least 1.")
            for key in float_keys:
                parsed[key] = float(new_settings[key])
                if not math.isfinite(parsed[key]) or not 0 <= parsed[key] <= 1:
                    raise ValueError(f"{key} must be between 0 and 1.")

            reranker_value = new_settings["enable_reranker"]
            if isinstance(reranker_value, bool):
                parsed["enable_reranker"] = reranker_value
            elif str(reranker_value).lower() in {"true", "false"}:
                parsed["enable_reranker"] = str(reranker_value).lower() == "true"
            else:
                raise ValueError("enable_reranker must be true or false.")

            if not math.isclose(
                parsed["bm25_weight"] + parsed["semantic_weight"], 1.0, abs_tol=0.001
            ):
                raise ValueError("BM25 and semantic weights must add up to 1.")

            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")
            with open(config_path, "r", encoding="utf-8") as file:
                content = file.read()
            for key, value in parsed.items():
                content = re.sub(
                    rf"^{key}\s*=\s*.+$", f"{key} = {value!r}", content, flags=re.MULTILINE
                )
            with open(config_path, "w", encoding="utf-8") as file:
                file.write(content)

            # Other modules imported these values directly, so update their copies too.
            config_module = importlib.import_module("config")
            for key, value in parsed.items():
                setattr(config_module, key, value)
            for module_name in ("retrieval.retriever", "rag_pipeline", "rag_streaming"):
                module = importlib.import_module(module_name)
                for key, value in parsed.items():
                    if hasattr(module, key):
                        setattr(module, key, value)

            return {"success": True, "settings": parsed}
        except (TypeError, ValueError) as error:
            return {"success": False, "error": str(error)}
        except OSError as error:
            return {"success": False, "error": f"Could not save settings: {error}"}

    def get_documents_summary(self):
        # Groups indexed chunks by source file for the Documents view
        if not self.chunks:
            return []

        from collections import Counter
        counts = Counter()
        for chunk in self.chunks:
            source = chunk["source"] if isinstance(chunk, dict) else getattr(chunk, "source", "unknown")
            counts[source] += 1

        return [
            {"file": os.path.basename(source), "chunk_count": count}
            for source, count in counts.items()
        ]

    def list_local_files(self):
        # Builds a folder -> files tree for the Local Files view
        print("DEBUG: list_local_files() called")
        data_dir = DOCS_PATH

        # Which paths are already indexed, so we can show a badge
        indexed_paths = set()
        if self.chunks:
            for chunk in self.chunks:
                source = chunk["source"] if isinstance(chunk, dict) else getattr(chunk, "source", None)
                if source:
                    indexed_paths.add(source)

        folders = {}
        for root, dirs, files in os.walk(data_dir):
            rel = os.path.relpath(root, data_dir)
            folder_name = "DERSLER" if rel == "." else rel.split(os.sep)[0]

            for fname in files:
                full_path = os.path.join(root, fname)
                try:
                    size = os.path.getsize(full_path)
                    modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M")
                except OSError:
                    size = 0
                    modified = ""

                folders.setdefault(folder_name, []).append({
                    "name": fname,
                    "path": full_path,
                    "size": size,
                    "modified": modified,
                    "indexed": full_path in indexed_paths
                })

        # Sort folders alphabetically, and files within each folder alphabetically
        result = []
        for folder_name in sorted(folders.keys()):
            files_in_folder = sorted(folders[folder_name], key=lambda f: f["name"].lower())
            result.append({"folder": folder_name, "files": files_in_folder})

        return {"folders": result}

    def open_file(self, file_path):
        """
        Opens the file with the system default application.
        """
        try:
            import subprocess
            if os.path.exists(file_path):
                subprocess.Popen(['open', file_path])
                return {"success": True, "message": f"Opened: {file_path}"}
            else:
                return {"success": False, "error": f"File not found: {file_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Entry point: opens the pywebview window and wires up the Api bridge
    api = Api()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_path = os.path.join(project_root, "frontend", "index.html")

    window = webview.create_window(
        "LocalRAG AI Assistant", frontend_path,
        js_api=api, width=1100, height=750, resizable=True
    )

    def on_loaded():
        try:
            print("on_loaded triggered", flush=True)
            result = api.initialize()
            print("INIT RESULT:", result, flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()

    window.events.loaded += on_loaded
    webview.start(debug=True)
