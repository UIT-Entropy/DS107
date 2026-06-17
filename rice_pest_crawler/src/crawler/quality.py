from __future__ import annotations

import re

from crawler.models import PestTaxonomy

BLOCKED_PAGE_KEYWORDS = ["login", "signup", "cart", "add to cart", "buy now"]
ADVISORY_KEYWORDS = [
    "damage",
    "symptom",
    "management",
    "control",
    "ipm",
    "biology",
    "life cycle",
    "monitoring",
    "triệu chứng",
    "gây hại",
    "phòng trừ",
    "quản lý",
    "biện pháp",
    "thuốc bảo vệ thực vật",
    "thăm đồng",
    "kiểm tra đồng ruộng",
]
SALES_KEYWORDS = ["price", "checkout", "shipping", "product details"]
ECOMMERCE_CONTEXT = ["cart", "checkout", "shipping", "add to cart", "buy now", "product details"]


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def is_relevant_to_pest(text: str, taxonomy: PestTaxonomy, extra_terms: list[str] | None = None) -> bool:
    combined = text.lower()
    terms = taxonomy.common_names_en + taxonomy.common_names_vi + taxonomy.scientific_names + (extra_terms or [])
    return any(term.lower() in combined for term in terms)


def quality_rejection_reason(
    text: str,
    taxonomy: PestTaxonomy,
    min_text_chars: int,
    extra_relevance_terms: list[str] | None = None,
) -> str | None:
    lowered = text.lower()
    if len(text.strip()) < min_text_chars:
        return "text too short"
    if any(_contains_term(lowered, keyword) for keyword in BLOCKED_PAGE_KEYWORDS):
        return "blocked page keyword"
    if any(_contains_term(lowered, keyword) for keyword in ECOMMERCE_CONTEXT):
        return "sales/product page"
    if _contains_term(lowered, "price") and any(_contains_term(lowered, keyword) for keyword in ["product", "shop", "buy", "cart"]):
        return "sales/product page"
    if not is_relevant_to_pest(text, taxonomy, extra_relevance_terms):
        return "not related to target pest"
    if "references" in lowered and not any(keyword in lowered for keyword in ADVISORY_KEYWORDS):
        return "mostly references without advisory content"
    return None
