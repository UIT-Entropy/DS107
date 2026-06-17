from __future__ import annotations

import argparse
from collections import Counter

import _bootstrap  # noqa: F401
from crawler.models import PestProfile
from crawler.profile_quality import assess_profile
from crawler.storage import load_models, write_jsonl
from crawler.taxonomy import load_crawler_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit pest profile advisory quality.")
    parser.add_argument("--input", help="Optional pest_profiles.jsonl path.")
    parser.add_argument("--output", default="data/logs/profile_quality.jsonl")
    parser.add_argument("--class-output", default="data/logs/class_quality.jsonl")
    args = parser.parse_args()

    output_config = load_crawler_config()["output"]
    input_path = args.input or output_config["pest_profiles_path"]
    profiles = load_models(input_path, PestProfile)
    assessments = [assess_profile(profile) for profile in profiles]
    write_jsonl(args.output, assessments)

    by_class: dict[str, list[dict]] = {}
    for row in assessments:
        by_class.setdefault(row["class_id"], []).append(row)
    class_assessments = []
    for class_id, rows in sorted(by_class.items()):
        ready_rows = [row for row in rows if row["advisory_ready"]]
        actionable_rows = [row for row in rows if row["actionable"]]
        best_candidates = ready_rows or actionable_rows or rows
        best_row = max(best_candidates, key=lambda row: row["score"])
        class_assessments.append(
            {
                "class_id": class_id,
                "advisory_ready": bool(ready_rows),
                "actionable": bool(actionable_rows),
                "best_grade": best_row["grade"],
                "best_score": best_row["score"],
                "ready_sources": [row["source_org"] for row in ready_rows],
                "related_sources": [row["source_org"] for row in actionable_rows if row["source_relation"] == "related"],
                "sources": [row["source_org"] for row in rows],
                "missing_core_sections": sorted({section for row in rows for section in row["missing_core_sections"]})
                if not actionable_rows
                else [],
            }
        )
    write_jsonl(args.class_output, class_assessments)

    grade_counts = Counter(row["grade"] for row in assessments)
    ready_classes = sorted(row["class_id"] for row in class_assessments if row["advisory_ready"])
    actionable_classes = sorted(row["class_id"] for row in class_assessments if row["actionable"])
    weak_classes = sorted(row["class_id"] for row in class_assessments if not row["actionable"])
    print(f"profiles={len(assessments)}")
    print(f"classes={len(class_assessments)}")
    print("grades=" + ", ".join(f"{grade}:{count}" for grade, count in sorted(grade_counts.items())))
    print("advisory_ready_classes=" + ",".join(ready_classes))
    print("actionable_classes=" + ",".join(actionable_classes))
    print("not_ready_classes=" + ",".join(weak_classes))


if __name__ == "__main__":
    main()
