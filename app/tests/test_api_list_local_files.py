"""Tests for api.py -> Api.list_local_files() output format.

api.py isn't imported directly (webview/sqlite side effects + a
hardcoded path); the same folder-walking logic is reproduced below
and run against a temp directory instead.
"""

import os
import shutil
import tempfile
from datetime import datetime

from _common import run


def list_local_files(data_dir, indexed_paths=frozenset()):
    folders = {}
    for root, _, files in os.walk(data_dir):
        rel = os.path.relpath(root, data_dir)
        folder_name = os.path.basename(data_dir) if rel == "." else rel.split(os.sep)[0]
        for fname in files:
            full_path = os.path.join(root, fname)
            folders.setdefault(folder_name, []).append({
                "name": fname,
                "path": full_path,
                "size": os.path.getsize(full_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M"),
                "indexed": full_path in indexed_paths,
            })
    return {
        "folders": [
            {"folder": name, "files": sorted(folders[name], key=lambda f: f["name"].lower())}
            for name in sorted(folders)
        ]
    }


def make_test_tree():
    tmpdir = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmpdir, "Math"))
    os.makedirs(os.path.join(tmpdir, "Physics"))
    open(os.path.join(tmpdir, "Math", "algebra.pdf"), "w").close()
    open(os.path.join(tmpdir, "Math", "Basics.pdf"), "w").close()
    open(os.path.join(tmpdir, "Physics", "mechanics.txt"), "w").close()
    return tmpdir


TMPDIR = make_test_tree()
OUT = list_local_files(TMPDIR)


def test_has_folders_key():
    assert "folders" in OUT


def test_folders_sorted():
    names = [f["folder"] for f in OUT["folders"]]
    assert names == sorted(names)


def test_files_sorted_case_insensitive():
    math = next(f for f in OUT["folders"] if f["folder"] == "Math")
    names = [f["name"] for f in math["files"]]
    assert names == sorted(names, key=str.lower)


def test_file_entry_has_all_fields():
    math = next(f for f in OUT["folders"] if f["folder"] == "Math")
    entry = math["files"][0]
    assert set(entry.keys()) == {"name", "path", "size", "modified", "indexed"}


def test_indexed_flag_true():
    target = os.path.join(TMPDIR, "Physics", "mechanics.txt")
    out = list_local_files(TMPDIR, indexed_paths={target})
    physics = next(f for f in out["folders"] if f["folder"] == "Physics")
    assert physics["files"][0]["indexed"] is True


def test_indexed_flag_false_by_default():
    math = next(f for f in OUT["folders"] if f["folder"] == "Math")
    assert all(f["indexed"] is False for f in math["files"])


if __name__ == "__main__":
    try:
        run({
            "output has a 'folders' key": test_has_folders_key,
            "folders sorted alphabetically": test_folders_sorted,
            "files sorted case-insensitively": test_files_sorted_case_insensitive,
            "file entry has all expected fields": test_file_entry_has_all_fields,
            "indexed=True flagged correctly": test_indexed_flag_true,
            "non-indexed files flagged False": test_indexed_flag_false_by_default,
        })
    finally:
        shutil.rmtree(TMPDIR, ignore_errors=True)