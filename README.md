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
- Hybrid retrieval: custom NumPy BM25 (lexical) combined with dense semantic search
- Cross-encoder re-ranking (`sentence-transformers`, `cross-encoder/ms-marco-MiniLM-L-6-v2`) for higher-precision result ordering
- Reliable source attribution via word-overlap matching, instead of relying on the LLM to self-report sources
- Streaming responses pushed live to the UI via `window.evaluate_js()`
- Turkish language support: pronoun/topic-word detection for vague follow-up questions
- Sentence-aware chunking (splits on sentence boundaries instead of fixed character windows)
- Vectorized cosine similarity with NumPy (~480x speedup over the naive loop-based version)
- Multi-chat with SQLite-backed persistence (multiple conversations, full session recall)
- Desktop UI built with pywebview, pink/orchid theme
- Four sidebar panels: Model Information, Local Files, Documents, and Settings
- Test suite (`tests/` directory, `unittest.mock`) covering ingestion, retrieval, embedding persistence, and regression cases for previously fixed bugs

---

## Technologies Used

- Python
- Sentence Transformers
- ChromaDB / FAISS
- Foundry Local SDK
- Local Language Models
- NumPy
- PyTorch
- pywebview (desktop UI)
- SQLite (embedding storage + chat history persistence)
- unittest / unittest.mock (test suite)

---

## Project Structure

```
app/
│
├── ingestion/
│   ├── document_loader.py
│   ├── embedding_generator.py
│   └── text_splitter.py
│
├── retrieval/
│   ├── retriever.py
│   └── vector_store.py
│
├── generation/
│   └── llm_handler.py
│
├── utils/
│   └── helpers.py
│
└── main.py

tests/
│   └── (unittest.mock-based test suite covering all modules and regression cases)
```

---

## How It Works

1. Documents are loaded into the system
2. Text is split into smaller chunks
3. Embeddings are generated for each chunk
4. Embeddings are stored in a vector database
5. User queries are converted into embeddings
6. Relevant chunks are retrieved using semantic similarity
7. Retrieved context is passed to the local LLM
8. The assistant generates a contextual response
9. Retrieval is hybrid: BM25 (lexical) and semantic similarity scores are combined, then top candidates are re-ranked with a cross-encoder before being passed to the LLM
10. The response is streamed token-by-token into the desktop UI instead of being returned all at once
11. Sources cited in the answer are verified against the retrieved chunks via word-overlap matching, so attribution doesn't depend on the LLM self-reporting correctly

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

- PDF and DOCX support
- Conversation memory
- Desktop GUI interface
- Multi-document indexing
- Streaming responses
- Better ranking and retrieval optimization
- Standalone installer packaging
- Broader language support beyond Turkish/English

---

## Installation

```
git clone <your-repository-link>
cd local-rag-ai-assistant
pip install -r requirements.txt
```

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
python -m unittest discover tests
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