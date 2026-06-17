from __future__ import annotations

import json
from pathlib import Path
from typing import Any


METADATA_SUFFIX = ".meta.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Loi JSON o {path}:{line_number}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def metadata_path(index_path: Path) -> Path:
    return index_path.with_suffix(index_path.suffix + METADATA_SUFFIX)


def load_chunks(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def load_index(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Chua co embedding index: {path}. Hay chay build-index truoc."
        )
    return read_jsonl(path)


def load_index_metadata(path: Path) -> dict[str, Any]:
    meta_path = metadata_path(path)
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


def save_index(
    path: Path,
    rows: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> None:
    write_jsonl(path, rows)
    if metadata is not None:
        meta_path = metadata_path(path)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
