# Local RAG AI Assistant

An offline Retrieval-Augmented Generation (RAG) assistant built with Python and local language models.

This project focuses on document retrieval, semantic search, and local AI inference without relying on cloud-based APIs.

---

## Features

- Local document processing
- Text chunking and preprocessing
- Embedding generation
- Semantic similarity search
- Retrieval-Augmented Generation (RAG)
- Local LLM integration
- Modular project architecture
- Offline AI workflow
- Hybrid retrieval: BM25 (`rank-bm25`, lexical) combined with dense semantic search
- Cross-encoder re-ranking (`sentence-transformers`, `cross-encoder/qnli-distilroberta-base`) for higher-precision result ordering, blended 70/30 with the hybrid score
- Reliable source attribution via word-overlap matching, instead of relying on the LLM to self-report sources
- Streaming responses via a session-based polling architecture (`start_streaming_session` / `get_streaming_event` / `cancel_streaming_session`), so the UI pulls tokens as they're generated instead of waiting for a full response
- Turkish language support: pronoun/topic-word detection for vague follow-up questions
- Sentence-aware chunking (splits on sentence boundaries instead of fixed character windows), with hard character-based splitting as a fallback for oversized sentences
- Vectorized cosine similarity with NumPy (~480x speedup over the naive loop-based version)
- Multi-chat with SQLite-backed persistence, full session recall, and per-chat deletion from Query History
- Desktop UI built with pywebview, pink/orchid theme
- Six sidebar views: Dashboard, Model Management, Query History, Local Files, Documents, and Settings — in addition to the main Chat view
- Live-tunable retrieval settings from the Settings panel: `top_k`, candidate `k`, minimum score threshold, minimum confidence, relative score ratio, reranker on/off, and BM25/semantic weight split — no restart needed
- Document ingestion beyond TXT/PDF/DOCX: also supports Markdown, PPTX (slide text extraction), XLSX (cell-by-cell text extraction), and PNG/JPG/JPEG via Tesseract OCR
- `[filename] question` query syntax to restrict retrieval to a single source document
- Mermaid diagram generation and LaTeX math rendering (`$...$` / `$$...$$`, via MathJax) built into the assistant's answers
- Multiple generation safety nets: repetition-loop detection (stops the model if it starts looping), a hard 4000-character cap on streamed answers, and relative/absolute confidence filtering so weak or off-topic retrieval results get dropped instead of answered from
- `resync_index` action to re-index the documents folder from the UI without restarting the app
- Test suite (`app/tests/`, `unittest.mock`) covering retrieval, RAG pipeline, streaming, helper functions, and the local-files API, with a `run_all.py` runner

---

## Technologies Used

- Python
- Sentence Transformers (cross-encoder re-ranking)
- Foundry Local SDK (Qwen3 embedding + chat models, served fully locally)
- `rank-bm25` (lexical retrieval)
- NumPy (vectorized similarity search)
- PyMuPDF / `python-docx` / `python-pptx` / `openpyxl` (document ingestion)
- Tesseract OCR / `pytesseract` / Pillow (PNG, JPG, and JPEG ingestion)
- pywebview (desktop UI)
- SQLite (embedding storage + chat history persistence)
- python-dotenv (`.env` config, e.g. `DOCS_PATH`)
- MathJax (in-app LaTeX rendering)
- unittest / unittest.mock (test suite)

> Note: `ChromaDB` / `FAISS` and a standalone `PyTorch` dependency, previously listed here, aren't actually used — embeddings are stored in SQLite and similarity search is a custom NumPy implementation, not a vector-database library.

---

## Project Structure

```
app/
│
├── ingestion/
│   ├── document_loader.py       # TXT / PDF / DOCX / MD / PPTX / XLSX / image-OCR loaders
│   ├── embedding_generator.py
│   ├── embedding_store.py       # SQLite persistence for embeddings
│   └── text_splitter.py
│
├── retrieval/
│   ├── retriever.py             # hybrid BM25 + semantic search, cross-encoder re-ranking
│   └── vector_store.py          # NumPy-vectorized cosine similarity
│
├── llm/
│   ├── local_llm.py             # Foundry Local client setup (embedding + chat models)
│   └── prompt_templates.py      # RAG system prompt (incl. Mermaid/LaTeX instructions)
│
├── utils/
│   └── helpers.py               # clean_answer() - strips <think> blocks, etc.
│
├── tests/
│   ├── _common.py
│   ├── run_all.py
│   ├── test_api_list_local_files.py
│   ├── test_helpers.py
│   ├── test_rag_pipeline.py
│   ├── test_rag_streaming.py
│   └── test_retriever.py
│
├── config.py                    # model names + all retrieval/reranker settings
├── rag_pipeline.py               # non-streaming RAG turn (ask_question)
├── rag_streaming.py               # streaming RAG turn (stream_ask_question)
├── main.py                       # pywebview Api class: chats, streaming sessions, settings, files
└── test.py

frontend/
├── index.html                   # pywebview UI (chat, dashboard, model mgmt, query history, local files, documents, settings)
└── main.css                     # pink/orchid theme

vector/
└── embeddings.db                 # SQLite embedding cache

data/                              # documents to be ingested (path configurable via DOCS_PATH)
docs/
```

---

## How It Works

1. Documents are loaded into the system
2. Text is split into smaller chunks
3. Embeddings are generated for each chunk
4. Embeddings are cached in a local SQLite database (no vector-database library involved), so they aren't regenerated on the next launch
5. User queries are converted into embeddings
6. Relevant chunks are retrieved using semantic similarity
7. Retrieved context is passed to the local LLM
8. The assistant generates a contextual response
9. Retrieval is hybrid: BM25 (lexical) and semantic similarity scores are combined (default 50/50), then the top candidates are re-ranked with a cross-encoder (weighted 70/30 against the hybrid score) before being passed to the LLM
10. Results below the minimum score threshold, or far weaker than the top result, are dropped; a vague follow-up with no prior history and low confidence gets a “not enough information” answer instead of a guess
11. An optional `[filename] question` syntax restricts retrieval to a single source document
12. The response is streamed into the desktop UI via a session-based polling loop, with `<think>` blocks buffered and stripped before anything reaches the screen, and generation stopped early if the model starts repeating itself or exceeds a hard character cap
13. Sources cited in the answer are verified against the retrieved chunks via word-overlap matching, so attribution doesn't depend on the LLM self-reporting correctly

---

## What I Learned

While building this project, I gained hands-on experience in:

- Understanding Retrieval-Augmented Generation (RAG) architectures
- Working with vector embeddings and semantic search
- Implementing cosine similarity-based retrieval systems
- Integrating local language models into Python applications
- Designing modular and scalable Python project structures
- Processing and chunking large text documents
- Managing vector databases and retrieval pipelines
- Debugging dependency and environment issues
- Building offline AI systems without external APIs
- Improving code organization and maintainability
- Designing a hybrid retrieval pipeline (lexical + dense) instead of relying on semantic search alone
- Why LLM self-reported source attribution is unreliable, and how to replace it with a deterministic matching approach
- Streaming LLM output into a desktop UI without blocking the main thread
- Vectorizing similarity computations with NumPy for large speedups over naive loops
- Handling Turkish-specific NLP quirks (pronoun/topic detection) not covered by most RAG tutorials
- Debugging silent failures: swallowed exceptions, JS errors halting entire scripts, embeddings regenerating on every launch
- Writing a regression-focused test suite that locks in fixes for previously encountered bugs

---

## Challenges I Faced

- Managing embedding model compatibility
- Structuring a scalable project architecture
- Handling local model initialization and configuration
- Improving retrieval accuracy
- Organizing document preprocessing pipelines
- Getting re-ranking and hybrid retrieval to actually improve answer quality, not just add latency
- Keeping the pywebview JS bridge stable under streaming (a single JS error could previously halt the whole script)
- Making source attribution trustworthy without depending on the LLM's own claims
- Supporting Turkish follow-up questions without a dedicated NLP library
- Avoiding embedding regeneration on every app launch while keeping the cache consistent with `DOCS_PATH`

---

## Future Improvements

- Multi-document indexing UI improvements (tagging, collections)
- Better ranking and retrieval optimization
- Standalone installer packaging
- Broader language support beyond Turkish/English

> The following were previously listed here as future work but are already implemented: PDF/DOCX support, conversation memory (multi-chat + history), the desktop GUI, and streaming responses.

---

## Installation

```
git clone https://github.com/sudeyldz10/local-rag-ai-assistant.git
cd local-rag-ai-assistant
pip install -r requirements.txt
```

For PNG/JPG/JPEG ingestion, install the Tesseract system application as well. `pytesseract` is only the Python bridge; it does not include the OCR engine or language data.

Set your documents folder in `.env`:

```
DOCS_PATH=/path/to/your/documents
```

Run the assistant:

```
python app/main.py
```

Run the test suite:

```
python app/tests/run_all.py
```

---

## Example Use Cases

- Offline AI assistant
- Research assistance
- Document question-answering
- Privacy-focused AI workflows
- Local knowledge retrieval systems

---

## License

This project is currently under active development and is shared for evaluation and educational purposes only.
