from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from urllib.parse import urlparse

import _bootstrap  # noqa: F401
from crawler.storage import read_jsonl
from crawler.taxonomy import load_crawler_config, load_manual_sources, load_yaml
from crawler.utils import project_path, utc_now_iso


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _short(value: object, limit: int = 90) -> str:
    text = _cell(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    return lines


def _chunk_counts() -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in read_jsonl("data/rag/chunks.jsonl"):
        counts[(row.get("class_id", ""), row.get("source_url", ""))] += 1
    for row in read_jsonl("data/rag/local_context_chunks.jsonl"):
        counts[("local_context", row.get("source_url", ""))] += 1
    return counts


def _configured_seed_rows(accepted_keys: set[tuple[str, str]], accepted_urls: set[str]) -> list[list[object]]:
    error_rows = read_jsonl("data/logs/crawl_errors.jsonl")
    rejected_rows = read_jsonl("data/logs/rejected_urls.jsonl")
    errors_by_url = defaultdict(list)
    rejected_by_url = defaultdict(list)
    for row in error_rows:
        errors_by_url[row.get("url", "")].append(row)
    for row in rejected_rows:
        rejected_by_url[row.get("url", "")].append(row)

    rows: list[list[object]] = []
    for source in load_manual_sources():
        key = (source.class_id, source.url)
        if key in accepted_keys:
            status = "accepted"
        elif source.url in accepted_urls:
            status = "accepted_for_other_class"
        elif source.url in errors_by_url:
            status = "error"
        elif source.url in rejected_by_url:
            status = "rejected"
        else:
            status = "configured_only"
        reason = ""
        if source.url in errors_by_url:
            reason = _short(errors_by_url[source.url][-1].get("error") or errors_by_url[source.url][-1].get("status_code"), 80)
        elif source.url in rejected_by_url:
            reason = _short(rejected_by_url[source.url][-1].get("reason") or rejected_by_url[source.url][-1].get("reason_text"), 80)
        rows.append(
            [
                "manual_pest",
                source.class_id,
                source.source_org,
                source.source_relation,
                status,
                reason,
                source.url,
            ]
        )

    for source in load_yaml("config/local_context_sources.yaml").get("sources", []):
        url = source["url"]
        status = "accepted" if url in accepted_urls else "configured_only"
        if url in errors_by_url:
            status = "error"
        elif url in rejected_by_url:
            status = "rejected"
        reason = ""
        if url in errors_by_url:
            reason = _short(errors_by_url[url][-1].get("error") or errors_by_url[url][-1].get("status_code"), 80)
        elif url in rejected_by_url:
            reason = _short(rejected_by_url[url][-1].get("reason") or rejected_by_url[url][-1].get("reason_text"), 80)
        rows.append(["local_context", ",".join(source.get("tags", [])), source.get("source_org"), "exact", status, reason, url])

    return rows


def build_source_inventory() -> str:
    output = load_crawler_config()["output"]
    pest_documents = read_jsonl(output["parsed_documents_path"])
    local_documents = read_jsonl(output["local_context_documents_path"])
    pest_chunks = read_jsonl(output["chunks_path"])
    local_chunks = read_jsonl(output["local_context_chunks_path"])
    all_chunks = read_jsonl(output["all_chunks_path"])
    profile_quality = read_jsonl("data/logs/profile_quality.jsonl")
    class_quality = read_jsonl("data/logs/class_quality.jsonl")
    errors = read_jsonl(output["error_log_path"])
    rejected = read_jsonl(output["rejected_urls_path"])

    chunk_counts = _chunk_counts()
    accepted_keys = {(row.get("class_id", ""), row.get("url", "")) for row in pest_documents}
    accepted_urls = {row.get("url", "") for row in pest_documents + local_documents}
    accepted_documents = pest_documents + [row | {"class_id": "local_context"} for row in local_documents]

    domains = Counter(_domain(row.get("url", "")) for row in accepted_documents)
    source_orgs = Counter(row.get("source_org") or "unknown" for row in accepted_documents)
    pest_chunks_by_class = Counter(row.get("class_id", "") for row in pest_chunks)
    local_chunks_by_section = Counter(row.get("section", "") for row in local_chunks)
    profile_grades = Counter(row.get("grade", "") for row in profile_quality)

    lines: list[str] = [
        "# Rice Pest Crawler Source Inventory",
        "",
        f"Generated at: `{utc_now_iso()}`",
        "",
        "## Summary",
        "",
    ]
    summary_rows = [
        ["pest_documents", len(pest_documents)],
        ["local_context_documents", len(local_documents)],
        ["accepted_document_rows", len(accepted_documents)],
        ["unique_accepted_urls", len(accepted_urls)],
        ["pest_chunks", len(pest_chunks)],
        ["local_context_chunks", len(local_chunks)],
        ["all_chunks", len(all_chunks)],
        ["profile_quality_rows", len(profile_quality)],
        ["class_quality_rows", len(class_quality)],
        ["crawl_errors", len(errors)],
        ["rejected_urls", len(rejected)],
    ]
    lines.extend(_table(["metric", "value"], summary_rows))
    lines.extend(["", "## Profile Grades", ""])
    lines.extend(_table(["grade", "count"], [[grade, count] for grade, count in sorted(profile_grades.items())]))
    lines.extend(["", "## Class Readiness", ""])
    lines.extend(
        _table(
            ["class_id", "advisory_ready", "actionable", "best_grade", "sources"],
            [
                [
                    row.get("class_id"),
                    row.get("advisory_ready"),
                    row.get("actionable"),
                    row.get("best_grade"),
                    len(row.get("sources", [])),
                ]
                for row in class_quality
            ],
        )
    )
    lines.extend(["", "## Accepted Source Organizations", ""])
    lines.extend(_table(["source_org", "documents"], [[org, count] for org, count in sorted(source_orgs.items())]))
    lines.extend(["", "## Accepted Source Domains", ""])
    lines.extend(_table(["domain", "documents"], [[domain, count] for domain, count in sorted(domains.items())]))
    lines.extend(["", "## Pest Chunks By Class", ""])
    lines.extend(_table(["class_id", "chunks"], [[class_id, count] for class_id, count in sorted(pest_chunks_by_class.items())]))
    lines.extend(["", "## Local Context Chunks By Section", ""])
    lines.extend(_table(["section", "chunks"], [[section, count] for section, count in sorted(local_chunks_by_section.items())]))

    accepted_rows = []
    for index, row in enumerate(sorted(accepted_documents, key=lambda item: (item.get("class_id", ""), item.get("url", ""))), start=1):
        class_id = row.get("class_id", "")
        url = row.get("url", "")
        accepted_rows.append(
            [
                index,
                class_id,
                row.get("source_org"),
                row.get("source_tier"),
                row.get("source_relation"),
                chunk_counts[(class_id, url)],
                _short(row.get("title"), 80),
                url,
            ]
        )
    lines.extend(["", "## Accepted Document Sources", ""])
    lines.extend(_table(["#", "scope/class", "source_org", "tier", "relation", "chunks", "title", "url"], accepted_rows))

    configured_rows = _configured_seed_rows(accepted_keys, accepted_urls)
    lines.extend(["", "## Configured Seeds And Crawl Status", ""])
    lines.extend(_table(["scope", "class_or_tags", "source_org", "relation", "status", "reason", "url"], configured_rows))

    issue_rows = []
    for row in errors:
        issue_rows.append(["error", row.get("class_id"), _short(row.get("error") or row.get("status_code"), 120), row.get("url")])
    for row in rejected:
        issue_rows.append(["rejected", row.get("class_id"), _short(row.get("reason") or row.get("reason_text"), 120), row.get("url")])
    lines.extend(["", "## Crawl Issues", ""])
    if issue_rows:
        lines.extend(_table(["type", "class_id", "reason", "url"], issue_rows))
    else:
        lines.append("No crawl errors or rejected URLs recorded.")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a Markdown inventory of all configured and accepted crawler sources.")
    parser.add_argument("--output", default="data/logs/source_inventory.md")
    args = parser.parse_args()

    output_path = project_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_source_inventory(), encoding="utf-8")
    print(f"saved_source_inventory={args.output}")


if __name__ == "__main__":
    main()
