# Local RAG AI Assistant

An offline Retrieval-Augmented Generation (RAG) assistant built with Python and Microsoft Foundry Local — runs fully without internet or cloud APIs.

---

## Demo

![Local RAG AI Assistant Demo](/Users/sudeyildiz1012/Downloads/demo.gif)

---

## Features

- **Multi-format document loading** — supports `.txt`, `.pdf`, and `.docx` files
- **Text chunking and preprocessing** — smart splitting for optimal retrieval
- **Embedding generation** — semantic vector representations of document content
- **Semantic similarity search** — finds the most relevant chunks for each query
- **Retrieval-Augmented Generation (RAG)** — grounds LLM answers in your documents
- **Local LLM integration** — via Microsoft Foundry Local SDK, no cloud required
- **Modular project architecture** — clean separation of ingestion, retrieval, and generation
- **Fully offline workflow** — your data never leaves your machine

---

## Technologies Used

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Microsoft Foundry Local SDK | Local LLM inference |
| Sentence Transformers | Embedding generation |
| ChromaDB / FAISS | Vector storage and retrieval |
| PyMuPDF / python-docx | PDF and DOCX parsing |
| NumPy / PyTorch | Numerical backend |

---

## Project Structure

```
local-rag-ai-assistant/
│
├── app/
│   ├── ingestion/
│   │   ├── document_loader.py    # TXT, PDF, DOCX loading
│   │   ├── text_splitter.py      # Chunk splitting logic
│   │   └── embedding_generator.py
│   │
│   ├── retrieval/
│   │   ├── vector_store.py       # ChromaDB / FAISS interface
│   │   └── retriever.py          # Semantic search
│   │
│   ├── generation/
│   │   └── llm_handler.py        # Foundry Local integration
│   │
│   ├── utils/
│   │   └── helpers.py
│   │
│   └── main.py                   # Entry point
│
├── data/                         # Place your documents here
├── docs/
├── requirements.txt
└── .env
```

---

## How It Works

```
Your Document (TXT / PDF / DOCX)
        │
        ▼
  [ Document Loader ]
        │
        ▼
  [ Text Splitter ]  →  chunks
        │
        ▼
  [ Embedding Generator ]  →  vectors
        │
        ▼
  [ Vector Store (ChromaDB/FAISS) ]
        │
   User Query
        │
        ▼
  [ Retriever ]  →  top-k relevant chunks
        │
        ▼
  [ LLM Handler (Foundry Local) ]
        │
        ▼
     Answer ✓
```

1. Documents are loaded and parsed by format (TXT / PDF / DOCX)
2. Text is split into overlapping chunks for better context coverage
3. Each chunk is converted to a vector embedding
4. Embeddings are stored in a local vector database
5. User queries are embedded and matched against stored vectors
6. The most relevant chunks are retrieved and passed to the local LLM
7. The LLM generates a grounded, context-aware response

---

## Installation

```bash
git clone https://github.com/sudeyldz10/local-rag-ai-assistant.git
cd local-rag-ai-assistant
pip install -r requirements.txt
```

Run the assistant:

```bash
python app/main.py
```

---

## What I Learned

Building this project gave me hands-on experience with:

- RAG architecture and how retrieval improves LLM accuracy
- Working with vector embeddings and cosine similarity search
- Parsing multiple document formats (TXT, PDF, DOCX) in Python
- Integrating a local LLM through the Microsoft Foundry Local SDK
- Designing a modular, layered Python project from scratch
- Debugging import errors, module structure issues, and model initialization
- Managing vector databases and retrieval pipelines
- Building a fully offline AI system with zero external API calls

---

## Challenges I Faced

- Handling different document encodings and formats consistently
- Getting the Foundry Local SDK initialized correctly
- Tuning chunk size and overlap for better retrieval quality
- Structuring the project so each module stays independent and testable
- Suppressing unwanted model output (e.g. `<think>` reasoning tokens)

---

## Future Improvements

- Conversation memory across turns
- Streaming responses in real time
- Desktop GUI interface
- Multi-document indexing and switching
- Better retrieval ranking (hybrid search: BM25 + semantic)
- Support for more formats (Markdown, HTML, CSV)

---

## Example Use Cases

- Ask questions about a research paper or report
- Build a private, offline knowledge base from your own documents
- Summarize long documents without sending data to the cloud
- Experiment with RAG pipelines and local LLM inference

---

## License

This project is currently under active development and is shared for evaluation and educational purposes only.
