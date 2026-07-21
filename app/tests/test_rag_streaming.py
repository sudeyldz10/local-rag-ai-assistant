"""Tests for rag_streaming.py: think-block streaming, follow-up detection,
and min_score_threshold filtering."""

from unittest.mock import patch

from _common import run, doc, FakeChatClient, FakeEmbeddingClient
import config
import rag_pipeline
import rag_streaming as s

DOCS = [doc("Content about oceans.", "/data/Oceans.pdf")]


def stream(pieces, results=[(0, 0.9)]):
    with patch.object(s, "generate_query_embedding", return_value=[0, 0, 0]), \
         patch.object(s, "find_relevant", return_value=results):
        return list(s.stream_ask_question(
            "tell me about oceans", DOCS, [[0, 0, 0]], FakeEmbeddingClient(), FakeChatClient(pieces)
        ))


def test_repeating_text_is_flagged():
    # Use explicit window/min_repeats so this doesn't depend on whatever
    # defaults rag_streaming.py currently has for its own _is_repeating.
    assert s._is_repeating("z" * 20 * 6, window=20, min_repeats=6) is True


def test_short_text_not_flagged():
    assert s._is_repeating("short text") is False


def test_turkish_followup_now_detected():
    # rag_streaming imports _is_vague_followup straight from rag_pipeline.
    # Since Turkish words were added into rag_pipeline's own regex, this is
    # now correctly detected at runtime (previously this was a bug).
    assert s._is_vague_followup is rag_pipeline._is_vague_followup
    assert s._is_vague_followup("bu ne demek") is True


def test_think_block_split_across_chunks_stays_hidden():
    events = stream(["<thi", "nk>reasoning", " more</thi", "nk>Visible answer."])
    chunk_text = "".join(e["data"]["text"] for e in events if e["type"] == "chunk")
    assert "reasoning" not in chunk_text
    complete = next(e for e in events if e["type"] == "complete")
    assert "<think>" not in complete["data"]["answer"]


def test_no_think_block_streams_as_is():
    events = stream(["Hello ", "world."])
    chunk_text = "".join(e["data"]["text"] for e in events if e["type"] == "chunk")
    assert chunk_text == "Hello world."


def test_no_results_returns_empty_sources():
    events = stream([], results=[])
    assert [e["type"] for e in events] == ["retrieving", "complete"]
    assert events[-1]["data"]["sources"] == []


def test_below_threshold_score_is_dropped():
    events = stream([], results=[(0, config.min_score_threshold - 0.01)])
    assert events[-1]["data"]["sources"] == []


def test_repetition_adds_cutoff_note():
    events = stream(["y" * 60] * 4)  # plenty long enough for any reasonable default
    complete = next(e for e in events if e["type"] == "complete")
    assert "cut short" in complete["data"]["answer"].lower()


if __name__ == "__main__":
    run({
        "repeating text is flagged (explicit params)": test_repeating_text_is_flagged,
        "short text is never flagged": test_short_text_not_flagged,
        "Turkish follow-up now detected (bug fixed upstream)": test_turkish_followup_now_detected,
        "think block split across chunks stays hidden": test_think_block_split_across_chunks_stays_hidden,
        "no think block streams text as-is": test_no_think_block_streams_as_is,
        "no results -> empty sources": test_no_results_returns_empty_sources,
        "below-threshold score is dropped": test_below_threshold_score_is_dropped,
        "repetition adds cutoff note": test_repetition_adds_cutoff_note,
    })
