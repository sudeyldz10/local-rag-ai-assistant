"""
Streaming support for RAG pipeline - simplified version.
Streams retrieval results and LLM response chunks in real-time.
"""
import re
import os
from ingestion.embedding_generator import generate_query_embedding
from retrieval.retriever import find_relevant
from llm.prompt_templates import built_rag_prompt as build_rag_prompt
from utils.helpers import clean_answer
from config import top_k, retrieval_candidate_k, min_score_threshold
from rag_pipeline import _is_vague_followup, _build_enriched_query
from rag_pipeline import _is_vague_followup, _build_enriched_query, _extract_last_source, _apply_source_preference

VAGUE_FOLLOWUP = re.compile(
    r"\b(this|that|it|these|those|them|structure|above|previous|"
    r"bu|şu|o|bunu|şunu|onu|bunun|şunun|onun|bunlar|şunlar|onlar|"
    r"bununla|şununla|onunla|konu|konuyla|yukarıda|önceki|yukarıdaki|"
    r"örnek|misal)\b",
    re.IGNORECASE,
)

MAX_WORDS_FOR_FOLLOWUP = 12


def _is_repeating(text, window=60, min_repeats=4):
    needed_length = window * min_repeats
    if len(text) < needed_length:
        return False

    tail = text[-needed_length:]
    pattern = tail[:window]

    repeats = 0
    position = 0
    while tail[position:position + window] == pattern:
        repeats += 1
        position += window
        if repeats >= min_repeats:
            return True

    return False

def stream_ask_question(query, docs, doc_embeddings, embedding_client, chat_client, history=None):
    """
    Simplified streaming version of ask_question.

    Yields dict events with:
    - "type": "retrieving" | "retrieved" | "generating" | "chunk" | "complete" | "error"
    - "data": relevant data for each event type
    """
    if history is None:
        history = []

    try:
        
        enriched_query = _build_enriched_query(query, history)

        query_embedding = generate_query_embedding(enriched_query, embedding_client)

        yield {"type": "retrieving", "data": {"query": query}}

        # Get relevant documents
        results = find_relevant(
            enriched_query, query_embedding, docs, doc_embeddings,
            k=retrieval_candidate_k, use_reranker=True
        )

        # Drop weak matches so unrelated documents don't get pulled in just to fill top_k
        results = [(idx, score) for idx, score in results if score >= min_score_threshold]
        if history and _is_vague_followup(query):
            preferred_source = _extract_last_source(history)
            print(f"DEBUG preferred_source: {preferred_source}")

            if preferred_source:
                print(f"DEBUG history length: {len(history)}")
                print(f"DEBUG last history item: {history[-1] if history else None}")
                print(f"DEBUG preferred_source: {preferred_source}")
                # Make sure last turn's document is always considered, even if
                # this turn's raw retrieval score for it is too low to make
                # the candidate cut on its own.
                already_in_results = {idx for idx, _ in results}
                for idx, doc in enumerate(docs):
                    source_name = os.path.basename(doc["source"]).lower()
                    if preferred_source in source_name or preferred_source in doc["source"].lower():
                        if idx not in already_in_results:
                            results.append((idx, min_score_threshold))

            results = _apply_source_preference(results, docs, preferred_source)
        else:
            results = results[:top_k]

        # Check if we have results
        if not results:
            yield {
                "type": "complete",
                "data": {
                    "answer": "The provided context does not contain enough information. Please ask a more specific question.",
                    "sources": []
                }
            }
            return

        # Collect retrieved documents for terminal logging only
        retrieved_info = []
        for rank, (idx, score) in enumerate(results, start=1):
            doc = docs[idx]
            source_name = os.path.basename(doc["source"])
            retrieved_info.append({
                "rank": rank,
                "score": float(score),
                "source": source_name,
                "full_path": doc["source"]
            })

        yield {"type": "retrieved", "data": {"documents": retrieved_info}}

        # Build context from retrieved documents
        context = ""
        for chunk_number, (index, score) in enumerate(results, start=1):
            doc = docs[index]
            context += f"[Chunk {chunk_number}]\nSource: {doc['source']}\n{doc['text']}\n\n"


        # Prepare messages for LLM
        messages = [{"role": "system", "content": build_rag_prompt(context)}]
        for h in history:
            messages.append(h)
        messages.append({"role": "user", "content": query})

        # Yield generating event
        yield {"type": "generating", "data": {"context_chunks": len(results)}}

        # Stream LLM response, holding back any <think> block until it's done
        # Stream LLM response, holding back any <think> block until it's done
        full_answer = ""
        think_buffer = ""
        thinking_done = False
        stopped_early = False

        MAX_ANSWER_CHARS = 4000  # hard safety cap - answer stops no matter what past this

        for chunk in chat_client.complete_streaming_chat(messages):
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if not content:
                continue

            full_answer += content

            # Stop if the model starts repeating itself endlessly
            if _is_repeating(full_answer):
                stopped_early = True
                break

            # Absolute safety net: no matter what, never let generation run forever
            if len(full_answer) > MAX_ANSWER_CHARS:
                stopped_early = True
                break

            if not thinking_done:
                think_buffer += content
                if "</think>" in think_buffer.lower() or "</thinking>" in think_buffer.lower():
                    thinking_done = True
                    visible_text = clean_answer(think_buffer)
                    if visible_text:
                        yield {"type": "chunk", "data": {"text": visible_text}}
                continue

            yield {"type": "chunk", "data": {"text": content}}

        if not thinking_done and think_buffer:
            visible_text = clean_answer(think_buffer)
            if visible_text:
                yield {"type": "chunk", "data": {"text": visible_text}}

        answer = clean_answer(full_answer)
        if not answer:
            answer = "The model got stuck. Please try rephrasing your question."
        elif stopped_early:
            answer += "\n\n_(Response was cut short - the model started repeating itself.)_"

        sources = [os.path.basename(docs[idx]["source"]) for idx, _ in results]  


        yield {
            "type": "complete",
            "data": {
                "answer": answer,
                "sources": sources
            }
        }

        history_answer = answer
        if sources:
            history_answer += "\n\nSource: " + sources[0]

        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": history_answer})

    except Exception as e:
        yield {"type": "error", "data": {"error": str(e)}}