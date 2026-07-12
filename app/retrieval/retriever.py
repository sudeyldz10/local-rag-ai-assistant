from retrieval.vector_store import cosine_similarity_all
from config import top_k, min_score_threshold


def find_relevant(query_embedding, doc_embeddings, k=None):
    limit = k or top_k

    all_scores = cosine_similarity_all(query_embedding, doc_embeddings)

    scores = []
    for i, score in enumerate(all_scores):
        if score >= min_score_threshold:
            scores.append((i, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:limit]
