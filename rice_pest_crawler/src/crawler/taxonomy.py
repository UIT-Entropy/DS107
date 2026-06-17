from __future__ import annotations

from pathlib import Path

import yaml

from crawler.models import ManualSource, PestTaxonomy
from crawler.utils import get_domain, project_path


def load_yaml(path: str | Path) -> dict:
    with project_path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_taxonomy(path: str | Path = "config/pest_taxonomy.yaml") -> dict[str, PestTaxonomy]:
    data = load_yaml(path)
    pests = data.get("pests", {})
    return {class_id: PestTaxonomy.model_validate(value) for class_id, value in pests.items()}


def load_sources_config(path: str | Path = "config/sources.yaml") -> dict:
    return load_yaml(path)


def load_crawler_config(path: str | Path = "config/crawler.yaml") -> dict:
    return load_yaml(path)


def load_manual_sources(path: str | Path = "config/manual_sources.yaml") -> list[ManualSource]:
    data = load_yaml(path)
    sources: list[ManualSource] = []
    for class_id, rows in (data.get("sources") or {}).items():
        for row in rows or []:
            sources.append(
                ManualSource(
                    class_id=class_id,
                    source_org=row.get("source_org"),
                    url=row["url"],
                    source_relation=row.get("source_relation", "exact"),
                    relation_note=row.get("relation_note"),
                    relevance_terms=row.get("relevance_terms", []),
                )
            )
    return sources


def source_tier_for_domain(domain: str, sources_config: dict) -> int | None:
    tiers = sources_config.get("allowlist_domains", {})
    if domain in set(tiers.get("tier_1", [])):
        return 1
    if domain in set(tiers.get("tier_2", [])):
        return 2
    return None


def is_allowlisted(url: str, sources_config: dict) -> bool:
    return source_tier_for_domain(get_domain(url), sources_config) is not None
