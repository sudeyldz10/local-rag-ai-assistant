import re
import os

from ingestion.embedding_generator import generate_query_embedding
from retrieval.retriever import find_relevant
from llm.prompt_templates import built_rag_prompt as build_rag_prompt
from utils.helpers import clean_answer
from config import top_k, retrieval_candidate_k, min_confidence_score, relative_score_ratio, min_score_threshold

# Words that flag a vague follow-up question ("that", "bu", "yukarıdaki"...)
VAGUE_FOLLOWUP = re.compile(
    r"\b(this|that|it|these|those|them|structure|above|previous|"
    r"bu|şu|o|bunu|şunu|onu|bunun|şunun|onun|bunlar|şunlar|onlar|"
    r"bununla|şununla|onunla|konu|konuyla|yukarıda|önceki|yukarıdaki|"
    r"örnek|misal)\b",
    re.IGNORECASE,
)
MAX_WORDS_FOR_FOLLOWUP = 12


def _is_repeating(text, window=30, min_repeats=5):
    # Detects the model looping the same text over and over
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


def _is_vague_followup(query):
    # Short query + referential word = treat as a vague follow-up
    word_count = len(query.split())
    return word_count <= MAX_WORDS_FOR_FOLLOWUP and bool(VAGUE_FOLLOWUP.search(query))


def _extract_last_source(history):
    # Reads back the "Source: ..." line from the previous answer
    if not history or history[-1]["role"] != "assistant":
        return None
    match = re.search(r"Source:\s*(.+)$", history[-1]["content"], re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().lower()


def _build_enriched_query(query, history):
    # Prepends previous question to vague follow-ups for better retrieval
    if not history or not _is_vague_followup(query):
        return query
    previous_question = history[-2]["content"]
    return f"{previous_question} {query}"


def _apply_relative_score_filter(results):
    # Drops results far weaker than the top score
    if len(results) <= 1:
        return results
    top_score = results[0][1]
    cutoff = top_score * relative_score_ratio
    return [(index, score) for index, score in results if score >= cutoff]


def _apply_source_preference(results, docs, preferred_source):
    # Puts chunks from the preferred source first, then fills with the rest
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


def ask_question(query, docs, doc_embeddings, embedding_client, chat_client, history=None):
    # Full non-streaming RAG turn: retrieve, build prompt, generate answer
    if history is None:
        history = []

    # Optional "[filename] question" syntax restricts retrieval to one file
    source_filter = None
    if query.startswith("[") and "]" in query:
        tag_end = query.index("]")
        source_filter = query[1:tag_end].lower()
        query = query[tag_end + 1:].strip()

    enriched_query = _build_enriched_query(query, history)
    query_embedding = generate_query_embedding(enriched_query, embedding_client)
    results = find_relevant(enriched_query, query_embedding, docs, doc_embeddings, k=retrieval_candidate_k)

    # Drop weak matches so unrelated documents don't get pulled in just to fill top_k
    results = [(idx, score) for idx, score in results if score >= min_score_threshold]
    results = _apply_relative_score_filter(results)

    # For follow-ups, bias toward the previous answer's source; otherwise take top_k
    if history and _is_vague_followup(query):
        preferred_source = _extract_last_source(history)
        results = _apply_source_preference(results, docs, preferred_source)
    else:
        results = results[:top_k]

    # Apply the "[filename]" filter, if given
    if source_filter:
        filtered = []
        for i, score in results:
            if source_filter in docs[i]["source"].lower():
                filtered.append((i, score))
        results = filtered

    # No matches left -> bail out instead of guessing
    if not results:
        answer = (
            "The provided context does not contain enough information. "
            "Please ask a more specific question."
        )
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        return answer, history

    # Low-confidence vague follow-up with no history -> bail out too
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

    # Build the context block fed to the model
    context = ""
    for chunk_number, (index, score) in enumerate(results, start=1):
        doc = docs[index]
        context += (
            f"[Chunk {chunk_number}]\n"
            f"Source: {doc['source']}\n"
            f"{doc['text']}\n\n"
        )

    # System prompt + history + current question
    messages = [
        {
            "role": "system",
            "content": build_rag_prompt(context)
        }
    ]
    for h in history:
        messages.append(h)
    messages.append({"role": "user", "content": query})

    # Stream the answer, stopping early if the model starts repeating
    full_answer = ""
    stopped_early = False
    for chunk in chat_client.complete_streaming_chat(messages):
        if not chunk.choices:
            continue
        content = chunk.choices[0].delta.content
        if content:
            full_answer += content
            if _is_repeating(full_answer):
                print("Repetition detected in model output - stopping generation early.")
                stopped_early = True
                break

    answer = clean_answer(full_answer)
    if not answer:
        answer = (
            "The model got stuck generating a response. "
            "Please try rephrasing your question or asking again."
        )
    elif stopped_early:
        answer += "\n\n_(Response was cut short - the model started repeating itself.)_"

    # Attribute the answer to whichever chunk shares the most words with it
    if results:
        answer_words = answer.lower().split()
        best_index = results[0][0]
        best_count = -1
        for index, score in results:
            chunk_text = docs[index]["text"].lower()
            count = sum(1 for word in answer_words if len(word) > 3 and word in chunk_text)
            if count > best_count:
                best_count = count
                best_index = index

        if best_count >= 3:
            source_name = os.path.basename(docs[best_index]["source"])
            answer += "\n\nSource: " + source_name

    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})

    return answer, history