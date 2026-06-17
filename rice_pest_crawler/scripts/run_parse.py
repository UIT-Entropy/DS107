from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from crawler.parsers import parse_html, parse_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse one local HTML or PDF file for inspection.")
    parser.add_argument("path")
    parser.add_argument("--url", default="local://fixture")
    args = parser.parse_args()

    path = Path(args.path)
    content = path.read_bytes()
    parsed = parse_pdf(content, args.url) if path.suffix.lower() == ".pdf" else parse_html(content, args.url)
    print(parsed.model_dump_json())


if __name__ == "__main__":
    main()
