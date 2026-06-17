from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from crawler.pipeline import extract_profiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract structured pest profiles from parsed documents.")
    parser.add_argument("--all", action="store_true", help="Process all parsed documents.")
    parser.add_argument("--input", help="Optional input documents.jsonl path.")
    args = parser.parse_args()
    if not args.all and not args.input:
        parser.error("provide --all or --input")

    profiles = extract_profiles(args.input)
    print(f"saved_profiles={len(profiles)}")


if __name__ == "__main__":
    main()
