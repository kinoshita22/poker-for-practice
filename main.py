"""Hold'em Practice entry point.

Run with ``python main.py``. Virtual chips only; no real-money gambling.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services.application import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run())
