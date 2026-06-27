import re
from ingestion.embedding_generator import generate_document_embeddings, generate_query_embedding
from retrieval.retriever import find_relevant
from llm.prompt_templates import built_rag_prompt as build_rag_prompt
from utils.helpers import clean_answer


def ask_question(query, docs, doc_embeddings, embedding_client, chat_client, history=[]):
    
    source_filter=None
    if query.startswith("[") and "]" in query:
        tag_end=query.index("]")
        source_filter=query[1:tag_end].lower()
        query=query[tag_end+1:].strip()


    if history:
        last_question=history[-2]["content"]
        enriched_query= last_question + " " + query
    else:
        enriched_query=query

    query_embedding= generate_query_embedding(enriched_query, embedding_client)
    results = find_relevant(query_embedding, doc_embeddings)

    if source_filter:
        filtered=[]
        for i, score in results:
            if source_filter in docs[i]["source"].lower():
                filtered.append((i,score))
        results= filtered       

    print("\nRetrieved documents: ")
    
    for i, score in results:
        doc = docs[i]
        print(f"Score: {score:.4f} | {doc['source']}")

    context = ""
    for i, _ in results:
        doc = docs[i]
        context += f"- {doc['text']}\n"

    messages = [
        {
            "role": "system",
            "content": build_rag_prompt(context)
        }
    ]

    for h in history:
        messages.append(h)
    
    messages.append({"role": "user", "content": query})


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

    answer=full_answer.strip()

    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})
    
    
    return answer, history 


            
    



