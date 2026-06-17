from __future__ import annotations

import sys
from pathlib import Path


def find_project_root(start: str | Path | None = None) -> Path:
    current = Path(start) if start is not None else Path(__file__)
    current = current.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "config" / "crawler.yaml").is_file() and (candidate / "src" / "crawler").is_dir():
            return candidate

    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = find_project_root()
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
