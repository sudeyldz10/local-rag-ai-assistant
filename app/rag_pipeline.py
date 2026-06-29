import re
import os
from ingestion.embedding_generator import generate_query_embedding
from retrieval.retriever import find_relevant
from llm.prompt_templates import built_rag_prompt as build_rag_prompt
from utils.helpers import clean_answer
from config import top_k, retrieval_candidate_k, min_confidence_score, relative_score_ratio

VAGUE_FOLLOWUP = re.compile(
    r"\b(this|that|it|these|those|them|structure|above|previous)\b",
    re.IGNORECASE,
)


def _is_vague_followup(query):
    return bool(VAGUE_FOLLOWUP.search(query))


def _extract_last_source(history):
    if not history or history[-1]["role"] != "assistant":
        return None

    match = re.search(r"Source:\s*(.+)$", history[-1]["content"], re.MULTILINE)
    if not match:
        return None

    return match.group(1).strip().lower()


def _build_enriched_query(query, history):
    if not history or not _is_vague_followup(query):
        return query

    previous_question = history[-2]["content"]
    previous_answer = history[-1]["content"]
    return f"{previous_question} {query} {previous_answer}"


def _apply_relative_score_filter(results):
    if len(results) <= 1:
        return results

    top_score = results[0][1]
    cutoff = top_score * relative_score_ratio
    return [(index, score) for index, score in results if score >= cutoff]


def _apply_source_preference(results, docs, preferred_source):
    if not preferred_source:
        return results[:top_k]

    preferred = [
        (index, score)
        for index, score in results
        if preferred_source in os.path.basename(docs[index]["source"]).lower()
        or preferred_source in docs[index]["source"].lower()
    ]
    others = [
        (index, score)
        for index, score in results
        if preferred_source not in os.path.basename(docs[index]["source"]).lower()
        and preferred_source not in docs[index]["source"].lower()
    ]

    return (preferred + others)[:top_k]


def ask_question(query, docs, doc_embeddings, embedding_client, chat_client, history=[]):
    
    source_filter=None
    if query.startswith("[") and "]" in query:
        tag_end=query.index("]")
        source_filter=query[1:tag_end].lower()
        query=query[tag_end+1:].strip()

    enriched_query = _build_enriched_query(query, history)

    query_embedding= generate_query_embedding(enriched_query, embedding_client)
    results = find_relevant(query_embedding, doc_embeddings, k=retrieval_candidate_k)
    results = _apply_relative_score_filter(results)

    if history and _is_vague_followup(query):
        preferred_source = _extract_last_source(history)
        results = _apply_source_preference(results, docs, preferred_source)
    else:
        results = results[:top_k]
    
    if source_filter:
        filtered=[]
        for i, score in results:
            if source_filter in docs[i]["source"].lower():
                filtered.append((i,score))
        results= filtered

    if not results:
        answer = (
            "The provided context does not contain enough information. "
            "Please ask a more specific question."
        )
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        return answer, history

    if not history and _is_vague_followup(query) and results[0][1] < min_confidence_score:
        answer = (
            "The provided context does not contain enough information. "
            "Please ask a more specific question."
        )
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        return answer, history

    print("\nRetrieved documents: ")
    
    for i, score in results:
        doc = docs[i]
        print(f"Score: {score:.4f} | {doc['source']}")


    context = ""
    for chunk_number, (index, score) in enumerate(results, start=1):
        doc = docs[index]

        context += (
            f"[Chunk {chunk_number}]\n"
            f"Source: {doc['source']}\n"
            f"{doc['text']}\n\n"
        )


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


    for chunk in chat_client.complete_streaming_chat(messages):
        if not chunk.choices:
            continue
                
        content = chunk.choices[0].delta.content
                
        if content:
            full_answer += content
    
    answer = clean_answer(full_answer)



    used_chunk_match= re.search(
        r"USED_CHUNK:\s*(\d+)", 
        answer
    )   
    if used_chunk_match:
        used_chunk_number= int(
            used_chunk_match.group(1)
        )
        real_doc_index= results[used_chunk_number -1][0]

        source_name= os.path.basename(
            docs[real_doc_index]["source"]
        )

        answer=re.sub(
            r"USED_CHUNK:\s*\d+",
            "",
            answer
        ).strip()

        answer+= "\n\nSource: " + source_name

    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})


    return answer, history 
