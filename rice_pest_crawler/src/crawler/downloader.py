from __future__ import annotations

import time
from pathlib import Path

import requests

from crawler.models import FetchResult
from crawler.storage import ensure_parent
from crawler.utils import get_domain, project_path, safe_filename, sha256_bytes, utc_now_iso

_LAST_FETCH_BY_DOMAIN: dict[str, float] = {}
_SEEN_HASHES: set[str] = set()


def fetch_url(url: str, user_agent: str, timeout_seconds: int, delay_seconds_per_domain: float) -> FetchResult:
    domain = get_domain(url)
    last_fetch = _LAST_FETCH_BY_DOMAIN.get(domain)
    if last_fetch is not None:
        wait_for = delay_seconds_per_domain - (time.monotonic() - last_fetch)
        if wait_for > 0:
            time.sleep(wait_for)

    response = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=timeout_seconds,
        allow_redirects=True,
    )
    _LAST_FETCH_BY_DOMAIN[domain] = time.monotonic()
    return FetchResult(
        url=url,
        final_url=response.url,
        status_code=response.status_code,
        content_type=response.headers.get("content-type", ""),
        content=response.content,
        fetched_at=utc_now_iso(),
    )


def detect_source_type(fetch_result: FetchResult) -> str:
    content_type = fetch_result.content_type.lower()
    final_url = fetch_result.final_url.lower()
    if "pdf" in content_type or final_url.endswith(".pdf"):
        return "pdf"
    return "html"


def save_raw_content(fetch_result: FetchResult, raw_html_dir: str, raw_pdf_dir: str) -> str | None:
    content_hash = sha256_bytes(fetch_result.content)
    if content_hash in _SEEN_HASHES:
        return None
    _SEEN_HASHES.add(content_hash)

    source_type = detect_source_type(fetch_result)
    suffix = ".pdf" if source_type == "pdf" else ".html"
    base_dir = raw_pdf_dir if source_type == "pdf" else raw_html_dir
    output_path = project_path(base_dir) / safe_filename(fetch_result.final_url, suffix)
    ensure_parent(output_path)
    output_path.write_bytes(fetch_result.content)
    return str(Path(base_dir) / output_path.name)
