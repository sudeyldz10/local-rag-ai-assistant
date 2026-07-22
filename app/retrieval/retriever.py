import os
import re
from rank_bm25 import BM25Okapi
from retrieval.vector_store import cosine_similarity_all
from config import top_k, min_score_threshold, bm25_weight, semantic_weight, enable_reranker, cross_encoder_model

# Cross-encoder is loaded lazily (only when first needed) to keep startup fast
try:
    from sentence_transformers import CrossEncoder
    _cross_encoder = None
    _cross_encoder_loaded = False
except ImportError:
    _cross_encoder = None
    _cross_encoder_loaded = False


def _get_cross_encoder():
    """Load the cross-encoder model once and cache it in memory."""
    global _cross_encoder, _cross_encoder_loaded

    if not enable_reranker:
        return None

    # Already attempted to load before, return cached instance (or None if it failed)
    if _cross_encoder_loaded:
        return _cross_encoder

    try:
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            _cross_encoder = CrossEncoder(cross_encoder_model, token=hf_token)
        else:
            _cross_encoder = CrossEncoder(cross_encoder_model)
        _cross_encoder_loaded = True
    except Exception as e:
        # Don't crash the app if the model can't be downloaded/loaded
        print(f"Warning: Failed to load cross-encoder: {e}")
        _cross_encoder = None
        _cross_encoder_loaded = True

    return _cross_encoder


def _tokenize(text: str):
    # Simple word tokenizer used for BM25 (lowercase, strip punctuation)
    return re.findall(r"\w+", (text or "").lower())


def _normalize(scores):
    # Min-max normalize scores to 0-1 range so BM25 and semantic scores are comparable
    if not scores:
        return []
    mn = min(scores)
    mx = max(scores)
    if mx == mn:
        return [1.0 for _ in scores]
    return [(s - mn) / (mx - mn) for s in scores]


def rerank_with_cross_encoder(query_text, docs, indices, scores):
    """Re-rank the top hybrid results using a cross-encoder for better precision."""
    cross_encoder = _get_cross_encoder()

    # If the model isn't available, just keep the original hybrid order
    if not cross_encoder or not indices:
        return [(idx, score) for idx, score in zip(indices, scores)]

    try:
        # Build (query, document) pairs for the cross-encoder to score
        pairs = []
        for idx in indices:
            doc_text = docs[idx]["text"] if isinstance(docs[idx], dict) else getattr(docs[idx], "text", "")
            pairs.append([query_text, doc_text])

        ce_scores = cross_encoder.predict(pairs)
        ce_scores_norm = _normalize(list(ce_scores))
        hybrid_norm = _normalize(scores)

        # Weighted average of cross-encoder score and hybrid (BM25+semantic) score
        combined = [0.7 * ce + 0.3 * hyb for ce, hyb in zip(ce_scores_norm, hybrid_norm)]

        result = list(zip(indices, combined))
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    except Exception as e:
        # Fall back to hybrid scores if re-ranking fails for any reason
        print(f"Warning: Cross-encoder re-ranking failed, using hybrid scores: {e}")
        return [(idx, score) for idx, score in zip(indices, scores)]


def find_relevant(query_text, query_embedding, docs, doc_embeddings, k=None, use_reranker=True):
    """
    Hybrid retrieval: combines BM25 and semantic cosine similarity.
    Optionally re-ranks with cross-encoder.

    - `query_text`: raw query string used for BM25
    - `query_embedding`: vector used for semantic search
    - `docs`: list of chunk dicts (with 'text')
    - `doc_embeddings`: list of vectors aligned with `docs`
    - `use_reranker`: whether to apply cross-encoder re-ranking

    Returns list of (index, combined_score) sorted descending.
    """
    limit = k or top_k
    texts = [d["text"] if isinstance(d, dict) else getattr(d, "text", "") for d in docs]
    tokenized = [_tokenize(t) for t in texts]

    # BM25 scores (keyword-based retrieval, good for exact term matches)
    try:
        bm25 = BM25Okapi(tokenized)
        bm25_scores = bm25.get_scores(_tokenize(query_text))
        bm25_scores = list(bm25_scores)
    except Exception:
        # If BM25 fails (e.g. empty corpus), fall back to zero scores
        bm25_scores = [0.0] * len(texts)

    # Semantic scores (embedding-based cosine similarity, good for meaning/paraphrase matches)
    sem_scores = cosine_similarity_all(query_embedding, doc_embeddings)

    # Guard against mismatched lengths between docs/embeddings/scores
    n = min(len(texts), len(sem_scores), len(bm25_scores))
    bm25_scores = bm25_scores[:n]
    sem_scores = sem_scores[:n]

    # Normalize both score types to 0-1, then blend using configured weights
    bm25_norm = _normalize(bm25_scores)
    sem_norm = _normalize(sem_scores)
    combined = [bm25_weight * b + semantic_weight * s for b, s in zip(bm25_norm, sem_norm)]

    # Keep only chunks above the minimum score threshold
    results = []
    for i, score in enumerate(combined):
        if score >= min_score_threshold:
            results.append((i, score))
    results.sort(key=lambda x: x[1], reverse=True)

    # Further filter by semantic score to avoid off-topic results
    filtered_results = []
    for idx, score in results:
        if sem_norm[idx] >= 0.4:  # Semantic score must be at least 0.4
            filtered_results.append((idx, score))
    results = filtered_results if filtered_results else results[:limit]

    # Apply cross-encoder re-ranking on the shortlist if enabled
    if use_reranker and enable_reranker:
        indices = [idx for idx, _ in results]
        scores = [score for _, score in results]
        results = rerank_with_cross_encoder(query_text, docs, indices, scores)

    return results[:limit]