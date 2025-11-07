from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    sys.path.insert(0, str(src))
