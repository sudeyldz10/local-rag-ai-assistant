"""Shared helpers for the test files in this folder."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run(tests):
    """Runs a dict of {name: function}, printing OK/FAIL for each."""
    failed = 0
    for name, fn in tests.items():
        try:
            fn()
            print(f"  OK   {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {name}  ({e})")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    if failed:
        sys.exit(1)


def doc(text, source):
    return {"text": text, "source": source}


class FakeChatClient:
    """Fake chat_client that yields given text pieces as streaming chunks."""

    class _Chunk:
        def __init__(self, text):
            self.choices = [self]
            self.delta = self
            self.content = text

    def __init__(self, pieces):
        self.pieces = pieces

    def complete_streaming_chat(self, messages):
        for piece in self.pieces:
            yield self._Chunk(piece)


class FakeEmbeddingClient:
    def embed(self, text):
        return [0.0, 0.0, 0.0]