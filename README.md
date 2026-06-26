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

---

## Technologies Used

- Python
- Sentence Transformers
- ChromaDB / FAISS
- Foundry Local SDK
- Local Language Models
- NumPy
- PyTorch

---

## Project Structure

```bash
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

---

## Challenges I Faced

- Managing embedding model compatibility
- Structuring a scalable project architecture
- Handling local model initialization and configuration
- Improving retrieval accuracy
- Organizing document preprocessing pipelines

---

## Future Improvements

- PDF and DOCX support
- Conversation memory
- Desktop GUI interface
- Multi-document indexing
- Streaming responses
- Better ranking and retrieval optimization

---

## Installation

```bash
git clone <your-repository-link>
cd local-rag-ai-assistant
pip install -r requirements.txt
```

Run the assistant:

```bash
python app/main.py
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
