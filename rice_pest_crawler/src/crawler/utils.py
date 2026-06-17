from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


def find_project_root(start: str | Path | None = None) -> Path:
    current = Path(start) if start is not None else Path(__file__)
    current = current.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "config" / "crawler.yaml").is_file() and (candidate / "src" / "crawler").is_dir():
            return candidate

    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = find_project_root()


def project_path(path: str | Path) -> Path:
    value = Path(path)
    if value.is_absolute():
        return value
    return PROJECT_ROOT / value


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    compact: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank:
                compact.append("")
            blank = True
            continue
        compact.append(" ".join(line.split()))
        blank = False
    return "\n".join(compact).strip()


def safe_filename(value: str, suffix: str) -> str:
    digest = sha256_text(value)[:16]
    return f"{digest}{suffix}"
