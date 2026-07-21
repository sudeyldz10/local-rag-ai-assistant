"""Tests for rag_pipeline.py: repetition, follow-up detection, ask_question."""

from unittest.mock import patch

from _common import run, doc, FakeChatClient, FakeEmbeddingClient
import rag_pipeline as p


def test_short_text_not_repeating():
    assert p._is_repeating("short answer") is False


def test_below_threshold_not_repeating():
    # window=30, min_repeats=5 by default -> needs 150 chars of exact repeats
    assert p._is_repeating("x" * 30 * 4) is False  # only 4 repeats, below 5


def test_at_threshold_is_repeating():
    assert p._is_repeating("x" * 30 * 5) is True


def test_vague_short_query():
    assert p._is_vague_followup("what about this?") is True


def test_long_query_not_vague():
    # MAX_WORDS_FOR_FOLLOWUP=12 -> needs 13+ words to not be vague
    long_query = "what about this whole system in general terms today and how does it apply here"
    assert len(long_query.split()) > 12
    assert p._is_vague_followup(long_query) is False


def test_turkish_word_is_matched():
    # Turkish words were added directly into rag_pipeline's own regex.
    assert p._is_vague_followup("bu ne demek") is True


def test_extract_last_source():
    history = [
        {"role": "user", "content": "what is X"},
        {"role": "assistant", "content": "Answer.\n\nSource: Chapter1.PDF"},
    ]
    assert p._extract_last_source(history) == "chapter1.pdf"


def test_extract_last_source_none_without_history():
    assert p._extract_last_source([]) is None


def test_enriched_query_includes_prev_question_only():
    # _build_enriched_query only prepends the previous question, not the
    # previous answer.
    history = [
        {"role": "user", "content": "what is a linked list"},
        {"role": "assistant", "content": "A linked list is a data structure."},
    ]
    enriched = p._build_enriched_query("tell me more about this", history)
    assert "what is a linked list" in enriched
    assert "tell me more about this" in enriched
    assert "A linked list is a data structure." not in enriched


def test_relative_score_filter_drops_low_scores():
    results = [(0, 1.0), (1, 0.95), (2, 0.5)]
    filtered = p._apply_relative_score_filter(results)
    assert [i for i, _ in filtered] == [0, 1]


def test_ask_question_no_results_returns_fallback():
    docs = [doc("Chapter about trees.", "/data/DataStructures.pdf")]
    with patch.object(p, "generate_query_embedding", return_value=[0, 0, 0]), \
         patch.object(p, "find_relevant", return_value=[]):
        answer, _ = p.ask_question(
            "what is a tree", docs, [[0, 0, 0]], FakeEmbeddingClient(), FakeChatClient([])
        )
    assert "does not contain enough information" in answer


def test_ask_question_strips_think_block():
    docs = [doc("Chapter about trees.", "/data/DataStructures.pdf")]
    pieces = ["<think>reasoning</think>", "A tree is a data structure."]
    with patch.object(p, "generate_query_embedding", return_value=[0, 0, 0]), \
         patch.object(p, "find_relevant", return_value=[(0, 0.9)]):
        answer, _ = p.ask_question(
            "what is a tree", docs, [[0, 0, 0]], FakeEmbeddingClient(), FakeChatClient(pieces)
        )
    assert "<think>" not in answer
    assert "A tree is a data structure." in answer


def test_ask_question_flags_repetition():
    docs = [doc("Chapter about trees.", "/data/DataStructures.pdf")]
    pieces = ["x" * 30] * 5  # 5 repeats of a 30-char block -> hits the threshold
    with patch.object(p, "generate_query_embedding", return_value=[0, 0, 0]), \
         patch.object(p, "find_relevant", return_value=[(0, 0.9)]):
        answer, _ = p.ask_question(
            "what is a tree", docs, [[0, 0, 0]], FakeEmbeddingClient(), FakeChatClient(pieces)
        )
    assert "cut short" in answer.lower()


if __name__ == "__main__":
    run({
        "short text is never flagged as repeating": test_short_text_not_repeating,
        "below-threshold repeats pass": test_below_threshold_not_repeating,
        "at-threshold repeats are flagged": test_at_threshold_is_repeating,
        "short vague query is detected": test_vague_short_query,
        "long query (13+ words) is not vague": test_long_query_not_vague,
        "Turkish word is matched (fixed in rag_pipeline's regex)": test_turkish_word_is_matched,
        "last source extracted from history": test_extract_last_source,
        "no history -> no last source": test_extract_last_source_none_without_history,
        "enriched query includes prev question only (not prev answer)": test_enriched_query_includes_prev_question_only,
        "relative score filter drops weak results": test_relative_score_filter_drops_low_scores,
        "no results -> fallback answer": test_ask_question_no_results_returns_fallback,
        "<think> block stripped from final answer": test_ask_question_strips_think_block,
        "repetition adds cutoff note": test_ask_question_flags_repetition,
    })
