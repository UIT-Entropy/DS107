from __future__ import annotations

import fitz
import trafilatura
from bs4 import BeautifulSoup

from crawler.models import ParsedText
from crawler.utils import normalize_text


def parse_html(content: bytes, url: str) -> ParsedText:
    html = content.decode("utf-8", errors="replace")
    extracted = trafilatura.extract(html, url=url, include_tables=True, include_comments=False)
    soup = BeautifulSoup(html, "html.parser")
    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    h1 = soup.find("h1")
    if not title and h1:
        title = h1.get_text(" ", strip=True)

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    soup_text = soup.get_text("\n", strip=True)

    if "agritech.tnau.ac.in" in url:
        extracted = soup_text
    elif not extracted:
        extracted = soup_text

    return ParsedText(title=title, text=normalize_text(extracted or ""))


def parse_pdf(content: bytes, url: str) -> ParsedText:
    doc = fitz.open(stream=content, filetype="pdf")
    pages: list[str] = []
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"[PAGE {index}]\n{text.strip()}")
    metadata_title = (doc.metadata or {}).get("title") or None
    return ParsedText(title=metadata_title, text=normalize_text("\n\n".join(pages)), page_count=doc.page_count)
