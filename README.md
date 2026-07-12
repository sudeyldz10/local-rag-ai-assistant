# Local RAG AI Assistant

An offline Retrieval-Augmented Generation (RAG) assistant built with Python and Microsoft Foundry Local — runs fully without internet or cloud APIs. Includes a native desktop UI built with pywebview.

---

## Demo

![Local RAG AI Assistant Demo](assets/demo.gif)

---

## Features

- **Desktop UI** — native app window built with pywebview (chat, knowledge base dashboard, model info, settings)
- **Multi-format document loading** — supports `.txt`, `.pdf`, `.docx`, `.md`, `.pptx`, `.xlsx`, and image files (`.jpg`, `.jpeg`, `.png`)
- **Recursive folder scanning** — automatically scans all subfolders for documents
- **Text chunking and preprocessing** — smart splitting with configurable chunk size and overlap
- **Embedding generation** — semantic vector representations via Foundry Local SDK
- **Embedding persistence** — embeddings saved to SQLite database, no recalculation on restart
- **Semantic similarity search** — finds the most relevant chunks for each query
- **Smart retrieval pipeline** — candidate pre-filtering, relative score filtering (%75 rule), and source preference for follow-up queries
- **Retrieval-Augmented Generation (RAG)** — grounds LLM answers in your documents
- **Persistent multi-chat history** — every conversation is saved to its own SQLite record and can be reopened from the sidebar's Query History
- **Conversation history** — remembers previous questions within a chat; follow-up queries are automatically enriched with prior context
- **Confidence-based early exit** — if retrieved chunks fall below the confidence threshold, the LLM is skipped and a clear "not enough info" message is returned instead
- **Source filtering** — use `[foldername]` tag to search only within a specific folder
- **Source-cited answers** — every document-based answer references the exact source file used
- **Math rendering** — LaTeX-style expressions rendered as real formulas in the UI (via MathJax)
- **Diagram rendering** — on request, the assistant can generate simple network/flow diagrams (via Mermaid)
- **Environment-based config** — document path set via `.env`, no hardcoded paths
- **Local LLM integration** — via Microsoft Foundry Local SDK, no cloud required
- **`<think>` token suppression** — Qwen model internal reasoning is stripped from output
- **Modular project architecture** — clean separation of ingestion, retrieval, generation, and UI
- **Fully offline workflow** — your data never leaves your machine

---

## Technologies Used

| Tool | Purpose |
|------|---------|
| Python | Core language |
| pywebview | Native desktop UI shell |
| HTML / CSS / JavaScript | Frontend (chat, sidebar, dashboard) |
| MathJax | Rendering math expressions in chat |
| Mermaid.js | Rendering diagrams in chat |
| Microsoft Foundry Local SDK | Local LLM inference and embedding generation |
| SQLite | Local vector storage and chat history storage |
| PyMuPDF (fitz) | PDF parsing |
| python-docx | DOCX parsing |
| NumPy | Cosine similarity computation |
| python-dotenv | Environment variable management |

---

## Project Structure

```
local-rag-ai-assistant/
│
├── app/
│   ├── config.py                  # Central config (thresholds, chunk size, model names)
│   ├── main.py                    # Api class: pywebview window, RAG init, chat & history management
│   ├── rag_pipeline.py            # End-to-end RAG logic with smart filtering
│   │
│   ├── ingestion/
│   │   ├── document_loader.py     # TXT, PDF, DOCX, MD, PPTX, XLSX, image loading with folder recursion
│   │   ├── text_splitter.py       # Chunk splitting logic
│   │   ├── embedding_generator.py # Vector generation via Foundry Local
│   │   └── embedding_store.py     # Save/load embeddings to SQLite
│   │
│   ├── retrieval/
│   │   ├── vector_store.py        # Cosine similarity
│   │   └── retriever.py           # Top-k semantic search with score thresholding
│   │
│   ├── llm/
│   │   ├── local_llm.py           # Foundry Local initialization
│   │   └── prompt_templates.py    # System prompt builder with conversation history
│   │
│   └── utils/
│       └── helpers.py             # Answer cleaning, <think> suppression
│
├── frontend/
│   ├── index.html                 # Desktop UI: chat, sidebar, knowledge base, query history
│   └── main.css                   # App styling
│
├── data/                          # Default document folder
├── vector/
│   ├── embeddings.db              # Cached document embeddings (auto-generated)
│   └── chats.db                   # Persisted multi-chat history (auto-generated)
├── requirements.txt
├── .env                           # Set DOCS_PATH here
└── .env.example
```

---

## How It Works

```
Your Documents (TXT / PDF / DOCX / MD / PPTX / XLSX / Images)
        │
        ▼
  [ Document Loader ]  →  recursive folder scan
        │
        ▼
  [ Text Splitter ]  →  overlapping chunks
        │
        ▼
  [ Embedding Generator ]  →  vectors via Foundry Local
        │
        ▼
  [ Embedding Store ]  →  saved to vector/embeddings.db (SQLite)
        │
   User Query (via desktop UI)
        │
        ▼
  [ Query Enrichment ]  →  follow-up queries enriched with conversation history
        │
        ▼
  [ Retriever ]  →  top-k candidates (with optional source filter)
        │
        ▼
  [ Score Filtering ]
    ├─ Absolute threshold  (min_score_threshold = 0.45)
    └─ Relative filter     (%75 rule — drops chunks far below best score)
        │
        ▼
  [ Confidence Check ]  →  if score < 0.60, skip LLM and return early message
        │
        ▼
  [ LLM (Foundry Local) ]
        │
        ▼
  [ <think> suppression ]  →  strips internal reasoning from Qwen output
        │
        ▼
  [ Math / Diagram Rendering ]  →  MathJax and Mermaid render formulas and diagrams in the UI
        │
        ▼
     Answer + Source Citation  →  saved to vector/chats.db ✓
```

---

## Configuration (`app/config.py`)

| Parameter | Value | Description |
|---|---|---|
| `retrieval_candidate_k` | `10` | Initial candidate pool size before filtering |
| `min_score_threshold` | `0.45` | Absolute minimum — chunks below this are discarded |
| `min_confidence_score` | `0.60` | If top score is below this on ambiguous queries, LLM is not called |

---

## Installation

```bash
git clone https://github.com/sudeyldz10/local-rag-ai-assistant.git
cd local-rag-ai-assistant
pip install -r requirements.txt
```

Set your documents folder in `.env`:
```
DOCS_PATH=/path/to/your/documents
```

Run the assistant:
```bash
python app/main.py
```

The desktop app window will open automatically. On first launch, your documents will be loaded, chunked, and embedded — this may take a moment depending on how many files you have.

---

## Usage

Type your question directly into the chat input in the desktop app.

**Basic question:**
```
What is the Mean Value Theorem?
```

**Filter by folder:**
```
[math210] implicit function theorem nedir?
```

Only documents inside the `math210` folder will be searched.

**New chat:**
Click **+ New Chat** in the sidebar to start a fresh conversation. Previous chats remain saved and can be reopened from **Query History**.

**Diagrams:**
Ask the assistant to "draw" or "show a diagram" for topics like network topologies to get a rendered diagram instead of plain text.

---

## What I Learned

Building this project gave me hands-on experience with:

- RAG architecture and how retrieval improves LLM accuracy
- Working with vector embeddings and cosine similarity search
- Parsing multiple document formats (TXT, PDF, DOCX, MD, PPTX, XLSX, images) in Python
- Integrating a local LLM through the Microsoft Foundry Local SDK
- Designing a modular, layered Python project from scratch
- Building a native desktop UI with pywebview, connecting a Python backend to an HTML/CSS/JS frontend
- Debugging import errors, module structure issues, and model initialization
- Building a fully offline AI system with zero external API calls
- Storing and querying structured data with SQLite, including multi-chat history persistence
- Tuning retrieval quality with score thresholds and relative filtering strategies
- Making follow-up queries work correctly by enriching them with prior context
- Prompt engineering for small local models: keeping instructions concise to avoid repetition and formatting drift
- Rendering math and diagrams in a chat UI with MathJax and Mermaid

---

## Challenges I Faced

- Handling different document encodings and formats consistently
- Getting the Foundry Local SDK initialized correctly (`alias` vs `name` attribute)
- Tuning chunk size and overlap for better retrieval quality
- Structuring the project so each module stays independent and testable
- Suppressing `<think>` reasoning tokens from Qwen model output using regex
- Scanned PDFs returning only `\n` characters — solved with a minimum content length filter
- Unrelated documents scoring high in retrieval — solved with source filtering and relative score filter
- Large embedding models (8b) being too slow for local use — reverted to `qwen3-embedding-0.6b`
- Preventing hallucination on vague queries — solved with confidence-based early exit before LLM call
- Follow-up queries losing context — solved by enriching queries with conversation history
- Small local models breaking down into repetitive output when given overly long, detailed prompts — solved by simplifying the system prompt
- Race conditions between UI polling and backend initialization causing crashes — solved with defensive checks in the stats endpoint
- Rendering LaTeX and diagram syntax cleanly in a lightweight desktop UI without a heavy frontend framework

---

## Future Improvements

- Streaming responses in real time
- Better retrieval ranking (hybrid search: BM25 + semantic)
- Re-ranking with a cross-encoder model
- Support for more formats (CSV, HTML)
- Full offline bundling of MathJax/Mermaid assets (currently loaded from CDN)

---

## Example Use Cases

- Ask questions about your lecture notes and textbooks
- Build a private, offline knowledge base from your own documents
- Summarize long documents without sending data to the cloud
- Filter searches by subject folder for more precise answers
- Keep separate, persistent chat threads for different courses or topics

---

## License

This project is currently under active development and is shared for evaluation and educational purposes only.