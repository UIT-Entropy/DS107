from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from crawler.local_context import build_local_context_chunks, crawl_local_context, run_local_context_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl and chunk Vietnam local advisory context.")
    parser.add_argument("--crawl-only", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()

    if args.crawl_only and args.build_only:
        parser.error("choose only one of --crawl-only or --build-only")
    if args.crawl_only:
        documents = crawl_local_context()
        print(f"saved_local_context_documents={len(documents)}")
    elif args.build_only:
        chunks = build_local_context_chunks()
        print(f"saved_local_context_chunks={len(chunks)}")
    else:
        result = run_local_context_pipeline()
        print(f"saved_local_context_documents={result['documents']}")
        print(f"saved_local_context_chunks={result['chunks']}")


if __name__ == "__main__":
    main()
