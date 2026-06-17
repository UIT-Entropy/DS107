# Rice Pest Crawler

Curated crawler for rice pest advisory RAG data. The MVP uses manual seed URLs, trusted allowlisted sources, rule-based extraction, and JSONL outputs.

## Setup

```bash
cd rice_pest_crawler
python -m pip install -r requirements.txt
```

## Usage

```bash
python scripts/run_discovery.py --all
python scripts/run_crawl.py --class-id brown_plant_hopper
python scripts/run_crawl.py --all
python scripts/run_extract.py --all
python scripts/build_chunks.py
python scripts/audit_quality.py
python scripts/run_local_context.py
python scripts/build_all_chunks.py
python scripts/audit_sources.py
```

Outputs:

- `data/parsed/documents.jsonl`
- `data/parsed/pest_profiles.jsonl`
- `data/rag/chunks.jsonl`
- `data/rag/local_context_chunks.jsonl`
- `data/rag/all_chunks.jsonl`
- `data/logs/crawl_errors.jsonl`
- `data/logs/rejected_urls.jsonl`
- `data/logs/profile_quality.jsonl`
- `data/logs/class_quality.jsonl`
- `data/logs/source_inventory.md`

## Advisory Readiness

Use `audit_quality.py` after every crawl. A profile is considered advisory-ready only when it comes from an exact trusted source and has at least identity, damage/symptoms, and IPM management content. Related/group sources can be actionable but require identity confirmation in the final answer. Taxonomy-only fallback profiles are kept in `pest_profiles.jsonl` for class coverage, but they are not emitted as RAG chunks.

For final Q&A, treat `profile_quality.jsonl` as a guardrail:

- `strong` / `usable`: Qwen can answer with citations and local-label pesticide cautions.
- `related_usable`: Qwen can give group-level steps, but must say the source is for a related pest group and field confirmation is needed.
- `weak`: Qwen should say the crawler has incomplete advisory detail and avoid full treatment workflows.
- `taxonomy_only`: Qwen should identify the class only and ask for more field evidence or curated sources.

## Notes

- This is a curated crawler, not a broad web crawler.
- It does not bypass CAPTCHA, login pages, or paywalls.
- Chemical control text is stored separately from general IPM advice.
- Exact pesticide dosage should not be surfaced unless present in an official local source.

## Tests

```bash
python -m pytest
```
