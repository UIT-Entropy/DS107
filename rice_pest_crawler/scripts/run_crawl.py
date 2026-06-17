from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from crawler.pipeline import crawl


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl allowlisted manual seed URLs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--class-id")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()

    documents = crawl(None if args.all else args.class_id)
    print(f"saved_documents={len(documents)}")


if __name__ == "__main__":
    main()
