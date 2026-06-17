from __future__ import annotations

from crawler.models import CandidateUrl
from crawler.taxonomy import load_manual_sources, load_sources_config, source_tier_for_domain
from crawler.utils import get_domain


def candidates_from_manual_sources(class_id: str | None = None) -> list[CandidateUrl]:
    sources_config = load_sources_config()
    rows = load_manual_sources()
    candidates: list[CandidateUrl] = []
    for row in rows:
        if class_id and row.class_id != class_id:
            continue
        domain = get_domain(row.url)
        candidates.append(
            CandidateUrl(
                class_id=row.class_id,
                url=row.url,
                domain=domain,
                source_tier=source_tier_for_domain(domain, sources_config),
                discovery_method="manual",
                source_org=row.source_org,
                source_relation=row.source_relation,
                relation_note=row.relation_note,
                relevance_terms=row.relevance_terms,
            )
        )
    return candidates


def build_search_queries(search_terms: list[str], domains: list[str]) -> list[str]:
    queries = []
    for term in search_terms:
        for domain in domains:
            queries.append(f"{term} site:{domain}")
    queries.append("filetype:pdf rice pest")
    return queries
