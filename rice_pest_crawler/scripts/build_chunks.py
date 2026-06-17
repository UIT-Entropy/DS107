from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from crawler.pipeline import build_rag_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Build RAG chunks from pest profiles.")
    parser.add_argument("--input", help="Optional input pest_profiles.jsonl path.")
    args = parser.parse_args()

    chunks = build_rag_chunks(args.input)
    print(f"saved_chunks={len(chunks)}")


if __name__ == "__main__":
    main()
