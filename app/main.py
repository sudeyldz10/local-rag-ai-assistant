import sys
import os
import sqlite3
import uuid
from datetime import datetime
import webview
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.document_loader import load_documents
from ingestion.text_splitter import split_documents
from ingestion.embedding_store import save_embeddings, load_embeddings
from llm.local_llm import initialize_foundry, load_embedding_model, load_chat_client
from ingestion.embedding_generator import generate_document_embeddings
from rag_pipeline import ask_question

DOCS_PATH = os.getenv("DOCS_PATH", "data")
EMBEDDINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../vector/embeddings.db")


CHATS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../vector/chats.db")


class Api:
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
        if self.ready:
            return {"status": "already initialized"}

        print("\nInitializing RAG system...\n")
        manager = initialize_foundry()

        self.chunks, self.doc_embeddings = load_embeddings(EMBEDDINGS_PATH)

        if self.chunks is None:
            documents = load_documents("/Users/sudeyildiz1012/Desktop/DERSLER")
            self.chunks = split_documents(documents)
            self.embedding_client = load_embedding_model(manager)
            self.doc_embeddings = generate_document_embeddings(self.chunks, self.embedding_client)
            save_embeddings(self.chunks, self.doc_embeddings, EMBEDDINGS_PATH)
        else:
            self.embedding_client = load_embedding_model(manager)

        self.chat_client = load_chat_client(manager)
        self.ready = True

        print("\nRAG system ready!\n")
        return {"status": "ready"}


    def ask(self, query):
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


    
    def get_stats(self):
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
        try:
            data_dir = "/Users/sudeyildiz1012/Desktop/DERSLER"

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


if __name__ == "__main__":
    api = Api()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_path = os.path.join(project_root, "frontend", "index.html")

    window = webview.create_window(
        "LocalRAG AI Assistant", frontend_path,
        js_api=api, width=1100, height=750, resizable=True
    )

    def on_loaded():
        api.initialize()

    window.events.loaded += on_loaded

    webview.start()