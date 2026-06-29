from retrieval.vector_store import cosine_similarity
from config import top_k, min_score_threshold


def find_relevant(query_embedding, doc_embeddings, k=None):
    limit = k or top_k
    scores = []

    for i, doc_emb in enumerate(doc_embeddings):
        score = cosine_similarity(query_embedding, doc_emb)
        if score >= min_score_threshold:
            scores.append((i, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:limit]
