# Rice Pest Crawler

`rice_pest_crawler/` builds the textual knowledge base used by the advisor. It discovers candidate URLs, downloads source pages/PDFs, extracts pest profiles, builds RAG chunks, adds Vietnamese local-context chunks, and audits source quality.

The crawler does not call Gemini and does not generate final answers. Generation is handled by `advisor/`.

## Setup

Run from the repository root:

```powershell
python -m pip install -r rice_pest_crawler\requirements.txt
```

## Configuration

Main config files:

```text
rice_pest_crawler\config\crawler.yaml
rice_pest_crawler\config\manual_sources.yaml
rice_pest_crawler\config\local_context_sources.yaml
rice_pest_crawler\config\pest_taxonomy.yaml
```

The pest taxonomy should stay aligned with the YOLO/advisor class ids:

```text
asiatic_rice_borer
brown_plant_hopper
paddy_stem_maggot
rice_gall_midge
rice_leaf_caterpillar
rice_leaf_hopper
rice_leaf_roller
rice_water_weevil
small_brown_plant_hopper
yellow_rice_borer
```

## Full Pipeline

```powershell
python rice_pest_crawler\scripts\run_discovery.py --all
python rice_pest_crawler\scripts\run_crawl.py --all
python rice_pest_crawler\scripts\run_extract.py --all
python rice_pest_crawler\scripts\build_chunks.py
python rice_pest_crawler\scripts\run_local_context.py
python rice_pest_crawler\scripts\build_all_chunks.py
python rice_pest_crawler\scripts\audit_sources.py
python rice_pest_crawler\scripts\audit_quality.py
```

Run one class only:

```powershell
python rice_pest_crawler\scripts\run_crawl.py --class-id brown_plant_hopper
python rice_pest_crawler\scripts\run_extract.py --class-id brown_plant_hopper
```

## Outputs

Important generated files:

```text
rice_pest_crawler\data\parsed\documents.jsonl
rice_pest_crawler\data\parsed\local_context_documents.jsonl
rice_pest_crawler\data\parsed\pest_profiles.jsonl
rice_pest_crawler\data\rag\chunks.jsonl
rice_pest_crawler\data\rag\local_context_chunks.jsonl
rice_pest_crawler\data\rag\all_chunks.jsonl
rice_pest_crawler\data\logs\source_inventory.md
```

`all_chunks.jsonl` is the final chunk file consumed by `advisor/gemini_rag.py build-index`.

## Current Knowledge Base Summary

The paper reports:

- 62 accepted document rows from 52 unique URLs.
- Main accepted sources: Vietnamese National Agricultural Extension Center and TNAU.
- Additional targeted pages from UC IPM and LSU AgCenter for specific pests.
- 278 final chunks:
  - 134 pest-specific chunks
  - 144 Vietnamese local-context chunks

## Source Quality Guardrails

Run audits after changing sources or extraction rules:

```powershell
python rice_pest_crawler\scripts\audit_quality.py
python rice_pest_crawler\scripts\audit_sources.py
```

Quality labels used in logs:

```text
strong / usable   good source for RAG
related_usable    related source; field confirmation recommended
weak              limited detail; avoid overconfident answers
taxonomy_only     useful for class identity, insufficient for management advice
```

## Chunking

The advisor paper describes structured sections such as:

```text
identity
damage_symptoms
field_diagnosis
management_ipm
chemical_control
warnings
```

Long sections are chunked for retrieval. Keep section names stable because the advisory benchmark computes Section Hit@5 using these labels.

## Tests

```powershell
python -m pytest rice_pest_crawler\tests
```
