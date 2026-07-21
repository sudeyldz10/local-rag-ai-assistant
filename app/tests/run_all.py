"""Runs every test file in this folder. Usage: python3 tests/run_all.py"""

import os
import subprocess
import sys

FILES = [
    "test_helpers.py",
    "test_rag_pipeline.py",
    "test_rag_streaming.py",
    "test_retriever.py",
    "test_api_list_local_files.py",
]

here = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(here)
env = {**os.environ, "PYTHONPATH": project_root}

ok = True
for fname in FILES:
    print(f"\n== {fname} ==")
    result = subprocess.run([sys.executable, os.path.join(here, fname)], cwd=here, env=env)
    ok = ok and result.returncode == 0

print("\nALL PASSED" if ok else "\nSOME FAILED")
sys.exit(0 if ok else 1)