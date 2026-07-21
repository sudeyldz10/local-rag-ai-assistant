"""Tests for retrieval/retriever.py: score filtering and reranker fallback."""

from unittest.mock import patch, MagicMock

from _common import run, doc
import retrieval.retriever as r

DOCS = [
    doc("python programming language basics", "/data/a.txt"),
    doc("pasta recipe", "/data/b.txt"),
    doc("more python programming content", "/data/c.txt"),
]


def test_low_semantic_score_is_dropped():
    with patch.object(r, "cosine_similarity_all", return_value=[0.9, 0.05, 0.85]):
        results = r.find_relevant("python", [0, 0, 0], DOCS, [[0, 0, 0]] * 3, k=5, use_reranker=False)
    assert 1 not in {i for i, _ in results}


def test_k_limit_is_respected():
    with patch.object(r, "cosine_similarity_all", return_value=[0.9, 0.8, 0.85]):
        results = r.find_relevant("python", [0, 0, 0], DOCS, [[0, 0, 0]] * 3, k=1, use_reranker=False)
    assert len(results) == 1


def test_no_cross_encoder_returns_original_scores():
    with patch.object(r, "_get_cross_encoder", return_value=None):
        out = r.rerank_with_cross_encoder("q", DOCS, [0, 1], [0.8, 0.3])
    assert out == [(0, 0.8), (1, 0.3)]


def test_cross_encoder_failure_falls_back():
    broken = MagicMock(predict=MagicMock(side_effect=RuntimeError("boom")))
    with patch.object(r, "_get_cross_encoder", return_value=broken):
        out = r.rerank_with_cross_encoder("q", DOCS, [0, 1], [0.8, 0.3])
    assert out == [(0, 0.8), (1, 0.3)]


def test_normalize_range():
    assert r._normalize([0, 5, 10]) == [0.0, 0.5, 1.0]


def test_normalize_all_equal():
    assert r._normalize([5, 5, 5]) == [1.0, 1.0, 1.0]


if __name__ == "__main__":
    run({
        "low semantic-score doc is dropped": test_low_semantic_score_is_dropped,
        "k limit is respected": test_k_limit_is_respected,
        "no cross-encoder -> original scores": test_no_cross_encoder_returns_original_scores,
        "cross-encoder failure -> fallback to hybrid scores": test_cross_encoder_failure_falls_back,
        "_normalize scales into 0-1": test_normalize_range,
        "_normalize handles all-equal scores": test_normalize_all_equal,
    })