import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.document_loader import load_documents
from llm.local_llm import initialize_foundry, load_embedding_model, load_chat_client
from ingestion.embedding_generator import generate_document_embeddings
from rag_pipeline import ask_question



def main():
        print("\nInitializing RAG system...\n")

        manager = initialize_foundry()

        documents = load_documents()

        embedding_client =load_embedding_model(manager)
       
        doc_embeddings = generate_document_embeddings(documents, embedding_client)
     
        chat_client = load_chat_client(manager)

        print("\nRAG system ready!")

        print("Type 'quit' to exit.\n")

        while True:

            query = input("Question > ").strip()
            if not query or query.lower() == "quit":
                break


            answer = ask_question(query, documents, doc_embeddings, embedding_client, chat_client)

            print("\nAnswer: ", answer)
            


if __name__ == "__main__":
    docs= load_documents("data")
    for doc in docs:
        print(f"\nFile: {doc['source']}")
        print(f"first 200 character: {doc['text'][:200]}")

