from __future__ import annotations

from typing import Any


def chunk_title(chunk: dict[str, Any]) -> str:
    title_parts = [
        chunk.get("common_name"),
        chunk.get("scientific_name"),
        chunk.get("class_id"),
        chunk.get("section"),
        chunk.get("source_org"),
    ]
    return " - ".join(str(part) for part in title_parts if part) or "none"


def format_document_for_embedding(chunk: dict[str, Any]) -> str:
    return f"title: {chunk_title(chunk)} | text: {chunk.get('text', '')}"


def format_query_for_embedding(question: str) -> str:
    return f"task: question answering | query: {question}"

