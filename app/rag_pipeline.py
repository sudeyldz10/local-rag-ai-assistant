import re
from app.ingestion.embedding_generator import generate_document_embeddings, generate_query_embedding
from app.retrieval.retriever import find_relevant
from app.llm.prompt_templates import built_rag_prompt as build_rag_prompt
from app.utils.helpers import clean_answer


def ask_question(query, docs, doc_embeddings, embedding_client, chat_client):
    
    query_embedding = generate_query_embedding(query, embedding_client)
    results = find_relevant(query_embedding, doc_embeddings)

    print("\nRetrieved documents: ")
    
    for i, score in results:
        print(f"Score: {score:.4f} | {docs[i]}")
            
    context = "\n".join(f"- {docs[i]}" for i, _ in results)

    messages = [
        {
            "role": "system",
            "content": build_rag_prompt(context)
        },
        {
            "role": "user", "content": query
        },
    
    ]
    full_answer = ""
    inside_think=False


    for chunk in chat_client.complete_streaming_chat(messages):
        if not chunk.choices:
            continue
                
        content = chunk.choices[0].delta.content
                
        if content:
            full_answer += content

            if "<think>" in full_answer:
                inside_think = True

            if "</think>" in full_answer:
                inside_think = False

                full_answer = re.sub(r"<think>.*?</think>", "", full_answer, flags=re.DOTALL)


    return full_answer.strip()


            
    



