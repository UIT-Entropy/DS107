from advisor.core.models import SearchResult
from advisor.reranker.domain_reranker import DomainReranker, infer_intents, tokenize


def make_result(section: str, text: str, embedding_score: float = 0.7) -> SearchResult:
    return SearchResult(
        chunk={
            "chunk_id": section,
            "class_id": "brown_plant_hopper",
            "common_name": "Rầy nâu",
            "section": section,
            "source_relation": "exact",
            "source_tier": 1,
            "source_url": f"https://example.test/{section}",
            "language": "vi",
            "text": text,
        },
        embedding_score=embedding_score,
    )


def test_tokenize_normalizes_vietnamese_accents():
    assert "ray" in tokenize("Rầy nâu gây hại lúa")
    assert "lua" in tokenize("Rầy nâu gây hại lúa")


def test_infer_intents_detects_management_and_chemical():
    intents = infer_intents(set(tokenize("Cách xử lý và phun thuốc rầy nâu?")))
    assert "management" in intents
    assert "chemical" in intents


def test_reranker_prefers_management_context_for_management_question():
    candidates = [
        make_result("identity", "Rầy nâu là một loài sâu hại."),
        make_result("management_ipm", "Cách xử lý rầy nâu theo IPM và thăm đồng."),
        make_result("chemical_control", "Chỉ phun thuốc khi xác định đúng tác nhân."),
    ]

    results = DomainReranker().rerank(
        "Cách xử lý rầy nâu trên lúa?",
        candidates,
        top_k=2,
    )

    assert results[0].chunk["section"] == "management_ipm"
    assert results[0].rank == 1

