import sys
import os
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
EMBEDDINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../vector/embeddings.json")


def main():
        print("\nInitializing RAG system...\n")

        manager = initialize_foundry()

        chunks, doc_embeddings=load_embeddings(EMBEDDINGS_PATH)

        if chunks is None:
            documents = load_documents("/Users/sudeyildiz1012/Desktop/DERSLER")
            chunks= split_documents(documents)
            embedding_client =load_embedding_model(manager)
            doc_embeddings = generate_document_embeddings(chunks, embedding_client)
            save_embeddings(chunks, doc_embeddings, EMBEDDINGS_PATH)

        else: 
            embedding_client = load_embedding_model(manager)
 
        chat_client = load_chat_client(manager)

        print("\nRAG system ready!")

        print("Type 'quit' to exit.\n")

        while True:

            query = input("Question > ").strip()
            if not query or query.lower() == "quit":
                break


            answer = ask_question(query, chunks, doc_embeddings, embedding_client, chat_client)

            print("\nAnswer: ", answer)
            


if __name__ == "__main__":
    main()

