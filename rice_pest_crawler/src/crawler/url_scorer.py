from __future__ import annotations

from crawler.models import CandidateUrl, PestTaxonomy

CONTENT_KEYWORDS = ["symptom", "damage", "management", "ipm", "life cycle", "control", "biology"]


def _searchable(value: str) -> str:
    lowered = value.lower()
    normalized = "".join(char if char.isalnum() else " " for char in lowered)
    return " ".join(normalized.split())


def score_candidate_url(
    candidate: CandidateUrl,
    taxonomy: PestTaxonomy,
    sources_config: dict,
    text: str | None = None,
) -> CandidateUrl:
    score = 0
    reasons: list[str] = []
    text_or_url = _searchable(f"{candidate.url} {text or ''}")
    domain = candidate.domain.lower()
    tiers = sources_config.get("allowlist_domains", {})

    if domain in set(tiers.get("tier_1", [])):
        score += 5
        reasons.append("tier_1_source:+5")
        candidate.source_tier = 1
    elif domain in set(tiers.get("tier_2", [])):
        score += 3
        reasons.append("tier_2_source:+3")
        candidate.source_tier = 2

    if candidate.discovery_method == "manual":
        score += 3
        reasons.append("manual_seed:+3")

    for scientific_name in taxonomy.scientific_names:
        if _searchable(scientific_name) in text_or_url:
            score += 4
            reasons.append(f"scientific_name:{scientific_name}:+4")

    for common_name in taxonomy.common_names_en + taxonomy.common_names_vi:
        if _searchable(common_name) in text_or_url:
            score += 3
            reasons.append(f"common_name:{common_name}:+3")

    class_phrase = _searchable(candidate.class_id.replace("_", " "))
    if class_phrase in text_or_url:
        score += 2
        reasons.append("class_phrase:+2")

    for keyword in CONTENT_KEYWORDS:
        if keyword in text_or_url:
            score += 1
            reasons.append(f"content_keyword:{keyword}:+1")

    if candidate.url.lower().endswith(".pdf"):
        score += 1
        reasons.append("pdf:+1")

    if domain in set(sources_config.get("blocked_domains", [])):
        score -= 10
        reasons.append("blocked_domain:-10")

    for bad in sources_config.get("blocked_url_keywords", []):
        if bad in candidate.url.lower():
            score -= 5
            reasons.append(f"blocked_keyword:{bad}:-5")

    candidate.score = score
    candidate.reason = reasons
    return candidate


def is_accepted(candidate: CandidateUrl, min_score: int) -> bool:
    return candidate.source_tier is not None and candidate.score >= min_score
