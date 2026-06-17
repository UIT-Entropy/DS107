from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from crawler.storage import read_jsonl, write_jsonl
from crawler.taxonomy import load_crawler_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine pest and Vietnam local context chunks.")
    parser.parse_args()

    output = load_crawler_config()["output"]
    pest_chunks = read_jsonl(output["chunks_path"])
    local_chunks = read_jsonl(output["local_context_chunks_path"])
    combined = pest_chunks + local_chunks
    write_jsonl(output["all_chunks_path"], combined)
    print(f"saved_all_chunks={len(combined)}")
    print(f"pest_chunks={len(pest_chunks)}")
    print(f"local_context_chunks={len(local_chunks)}")


if __name__ == "__main__":
    main()
