from __future__ import annotations

from crawler.models import PestProfile, RagChunk

SECTIONS = [
    "identity",
    "damage_symptoms",
    "life_cycle",
    "favorable_conditions",
    "field_diagnosis",
    "management_ipm",
    "chemical_control",
    "warnings",
]


def _tokenize(text: str) -> list[str]:
    return text.split()


def split_long_text(text: str, target_tokens: int = 750, max_tokens: int = 900, overlap_tokens: int = 100) -> list[str]:
    tokens = _tokenize(text)
    if len(tokens) <= max_tokens:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + target_tokens, len(tokens))
        chunks.append(" ".join(tokens[start:end]).strip())
        if end == len(tokens):
            break
        start = max(0, end - overlap_tokens)
    return chunks


def build_chunks(profile: PestProfile) -> list[RagChunk]:
    if profile.source_org == "Taxonomy config":
        return []

    chunks: list[RagChunk] = []
    for section in SECTIONS:
        text = getattr(profile, section)
        if not text:
            continue
        for index, piece in enumerate(split_long_text(text)):
            chunks.append(
                RagChunk(
                    chunk_id=f"{profile.profile_id}__{section}__{index:03d}",
                    class_id=profile.class_id,
                    scientific_name=profile.scientific_name,
                    common_name=profile.common_name,
                    section=section,
                    source_org=profile.source_org,
                    source_url=profile.source_url,
                    source_tier=profile.source_tier,
                    source_relation=profile.source_relation,
                    relation_note=profile.relation_note,
                    language=profile.language,
                    text=piece,
                )
            )
    return chunks
