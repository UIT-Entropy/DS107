from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from crawler.pipeline import discover_candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Load and score manual source candidates.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--class-id")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()

    candidates = discover_candidates(None if args.all else args.class_id)
    for candidate in candidates:
        print(candidate.model_dump_json())


if __name__ == "__main__":
    main()
