from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any

from advisor.core.models import SearchResult


DIAGNOSIS_TERMS = {
    "benh",
    "dau",
    "hieu",
    "la",
    "than",
    "re",
    "trieu",
    "chung",
    "nhan",
    "dien",
    "phan",
    "biet",
    "vang",
    "dom",
    "chay",
    "xoan",
    "he",
    "lua",
}

MANAGEMENT_TERMS = {
    "xu",
    "ly",
    "tri",
    "phong",
    "ngua",
    "quan",
    "ly",
    "ipm",
    "giam",
    "hai",
    "lam",
    "sao",
    "cach",
}

CHEMICAL_TERMS = {
    "thuoc",
    "phun",
    "lieu",
    "hoat",
    "chat",
    "nong",
    "do",
    "pesticide",
    "chemical",
}

MONITORING_TERMS = {
    "theo",
    "doi",
    "kiem",
    "tra",
    "dong",
    "ruong",
    "nguong",
    "mat",
    "do",
}

BASE_SECTION_WEIGHTS = {
    "field_diagnosis": 0.12,
    "damage_symptoms": 0.11,
    "identity": 0.06,
    "management_ipm": 0.11,
    "chemical_control": 0.07,
    "warnings": 0.07,
    "vietnam_pesticide_safety": 0.08,
    "vietnam_ipm_general": 0.07,
    "vietnam_farmer_qa_advisory": 0.07,
    "vietnam_field_monitoring": 0.07,
    "favorable_conditions": 0.05,
    "life_cycle": 0.04,
}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.lower()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", normalize_text(text))


def lexical_overlap(question_tokens: set[str], chunk: dict[str, Any]) -> float:
    fields = [
        str(chunk.get("class_id") or ""),
        str(chunk.get("common_name") or ""),
        str(chunk.get("scientific_name") or ""),
        str(chunk.get("section") or ""),
        str(chunk.get("source_org") or ""),
        str(chunk.get("text") or ""),
    ]
    chunk_tokens = set(tokenize(" ".join(fields)))
    if not question_tokens or not chunk_tokens:
        return 0.0
    overlap = question_tokens & chunk_tokens
    return min(len(overlap) / max(len(question_tokens), 1), 1.0)


def source_quality_score(chunk: dict[str, Any]) -> float:
    score = 0.0
    relation = str(chunk.get("source_relation") or "").lower()
    if relation == "exact":
        score += 0.06
    elif relation == "related":
        score += 0.015

    tier = chunk.get("source_tier")
    if isinstance(tier, int):
        score += max(0.0, (4 - tier) * 0.02)

    if chunk.get("source_url"):
        score += 0.015
    if str(chunk.get("language") or "").lower() == "vi":
        score += 0.01
    return score


def infer_intents(question_tokens: set[str]) -> set[str]:
    intents: set[str] = set()
    if question_tokens & DIAGNOSIS_TERMS:
        intents.add("diagnosis")
    if question_tokens & MANAGEMENT_TERMS:
        intents.add("management")
    if question_tokens & CHEMICAL_TERMS:
        intents.add("chemical")
    if question_tokens & MONITORING_TERMS:
        intents.add("monitoring")
    if not intents:
        intents.add("general")
    return intents


def section_score(section: str, intents: set[str]) -> float:
    score = BASE_SECTION_WEIGHTS.get(section, 0.02)

    if "diagnosis" in intents and section in {
        "field_diagnosis",
        "damage_symptoms",
        "identity",
        "favorable_conditions",
    }:
        score += 0.08

    if "management" in intents and section in {
        "management_ipm",
        "vietnam_ipm_general",
        "vietnam_farmer_qa_advisory",
        "warnings",
    }:
        score += 0.09

    if "chemical" in intents and section in {
        "chemical_control",
        "vietnam_pesticide_safety",
        "warnings",
    }:
        score += 0.10

    if "monitoring" in intents and section in {
        "field_diagnosis",
        "vietnam_field_monitoring",
        "vietnam_severity_context",
    }:
        score += 0.08

    return score


def diversity_penalty(result: SearchResult, source_counts: Counter[str]) -> float:
    source_url = str(result.chunk.get("source_url") or "")
    if not source_url:
        return 0.0
    return min(source_counts[source_url] * 0.025, 0.075)


class DomainReranker:
    def rerank(
        self,
        question: str,
        candidates: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        question_tokens = set(tokenize(question))
        intents = infer_intents(question_tokens)

        scored: list[SearchResult] = []
        source_counts: Counter[str] = Counter()

        for candidate in candidates:
            chunk = candidate.chunk
            section = str(chunk.get("section") or "")
            lexical = lexical_overlap(question_tokens, chunk)
            metadata = source_quality_score(chunk)
            section_boost = section_score(section, intents)

            score = (
                0.72 * candidate.embedding_score
                + 0.14 * lexical
                + metadata
                + section_boost
            )
            score -= diversity_penalty(candidate, source_counts)
            source_counts[str(chunk.get("source_url") or "")] += 1

            candidate.rerank_score = score
            candidate.reasons = [
                f"embedding={candidate.embedding_score:.3f}",
                f"lexical={lexical:.3f}",
                f"section={section}",
                f"intents={','.join(sorted(intents))}",
            ]
            scored.append(candidate)

        reranked = sorted(scored, key=lambda result: result.rerank_score, reverse=True)
        for rank, result in enumerate(reranked[:top_k], start=1):
            result.rank = rank
        return reranked[:top_k]

