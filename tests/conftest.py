import sys
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
TESTS_DIR = Path(__file__).resolve().parent

for directory in (MODEL_DIR, TESTS_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
