import os
import sys

# Automatically configure sys.path for test discovery across the reorganized codebase
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))

paths_to_add = [
    PROJECT_ROOT,
    os.path.join(PROJECT_ROOT, "src"),
    os.path.join(PROJECT_ROOT, "src", "backend"),
    os.path.join(PROJECT_ROOT, "src", "governance"),
    os.path.join(PROJECT_ROOT, "src", "ingestion"),
    os.path.join(PROJECT_ROOT, "src", "evaluation"),
    os.path.join(PROJECT_ROOT, "studio"),
]

for p in paths_to_add:
    if p not in sys.path:
        sys.path.insert(0, p)
