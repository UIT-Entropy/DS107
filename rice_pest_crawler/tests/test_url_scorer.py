from __future__ import annotations

from crawler.models import CandidateUrl
from crawler.taxonomy import load_sources_config, load_taxonomy
from crawler.url_scorer import score_candidate_url


def _candidate(url: str) -> CandidateUrl:
    domain = url.split("/")[2].lower()
    return CandidateUrl(class_id="brown_plant_hopper", url=url, domain=domain, discovery_method="test")


def test_tier_1_url_gets_positive_score() -> None:
    taxonomy = load_taxonomy()["brown_plant_hopper"]
    config = load_sources_config()
    scored = score_candidate_url(_candidate("https://www.knowledgebank.irri.org/brown-planthopper-management"), taxonomy, config)
    assert scored.source_tier == 1
    assert scored.score >= 6


def test_shop_url_is_penalized() -> None:
    taxonomy = load_taxonomy()["brown_plant_hopper"]
    config = load_sources_config()
    scored = score_candidate_url(_candidate("https://shopee.vn/brown-planthopper-pesticide-sale"), taxonomy, config)
    assert scored.score < 0
    assert any("blocked" in reason for reason in scored.reason)


def test_scientific_name_gets_boosted() -> None:
    taxonomy = load_taxonomy()["brown_plant_hopper"]
    config = load_sources_config()
    scored = score_candidate_url(
        _candidate("https://www.fao.org/Nilaparvata-lugens-rice-ipm.pdf"),
        taxonomy,
        config,
    )
    assert any("scientific_name" in reason for reason in scored.reason)
    assert scored.score >= 10


def test_unknown_domain_gets_low_score() -> None:
    taxonomy = load_taxonomy()["brown_plant_hopper"]
    config = load_sources_config()
    scored = score_candidate_url(_candidate("https://example.com/random-rice-page"), taxonomy, config)
    assert scored.source_tier is None
    assert scored.score < 6
