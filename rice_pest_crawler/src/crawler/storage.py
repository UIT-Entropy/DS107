from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, TypeVar

from pydantic import BaseModel

from crawler.utils import project_path

T = TypeVar("T", bound=BaseModel)


def ensure_parent(path: str | Path) -> Path:
    resolved = project_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def write_jsonl(path: str | Path, records: Iterable[BaseModel | dict], append: bool = False) -> None:
    resolved = ensure_parent(path)
    mode = "a" if append else "w"
    with resolved.open(mode, encoding="utf-8") as handle:
        for record in records:
            if isinstance(record, BaseModel):
                data = record.model_dump(mode="json")
            else:
                data = record
            handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def append_jsonl(path: str | Path, record: BaseModel | dict) -> None:
    write_jsonl(path, [record], append=True)


def read_jsonl(path: str | Path) -> list[dict]:
    resolved = project_path(path)
    if not resolved.exists():
        return []
    rows: list[dict] = []
    with resolved.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_models(path: str | Path, model_type: type[T]) -> list[T]:
    return [model_type.model_validate(row) for row in read_jsonl(path)]
