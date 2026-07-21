"""Tests for utils.helpers.clean_answer (<think> tag stripping)."""

from _common import run
from utils.helpers import clean_answer


def test_closed_think_block():
    assert clean_answer("<think>reasoning</think>Real answer.") == "Real answer."


def test_closed_thinking_block():
    assert clean_answer("<thinking>steps</thinking>Answer.") == "Answer."


def test_unclosed_block_leaves_nothing():
    assert clean_answer("<think>never finished") == ""


def test_case_insensitive():
    assert clean_answer("<THINK>x</THINK>Answer") == "Answer"


def test_no_tags_untouched():
    assert clean_answer("Just a normal answer.") == "Just a normal answer."


def test_multiline_block():
    assert clean_answer("<think>\nline1\nline2\n</think>\nAnswer.") == "Answer."


if __name__ == "__main__":
    run({
        "closed think block is stripped": test_closed_think_block,
        "closed thinking block is stripped": test_closed_thinking_block,
        "unclosed block leaves empty answer": test_unclosed_block_leaves_nothing,
        "tag matching is case-insensitive": test_case_insensitive,
        "no tags leaves text untouched": test_no_tags_untouched,
        "multiline block is stripped": test_multiline_block,
    })