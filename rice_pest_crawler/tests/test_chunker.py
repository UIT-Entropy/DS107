from __future__ import annotations

from crawler.chunker import build_chunks, split_long_text
from crawler.models import PestProfile


def _profile() -> PestProfile:
    return PestProfile(
        profile_id="brown_plant_hopper__fixture",
        class_id="brown_plant_hopper",
        common_name="brown planthopper",
        scientific_name="Nilaparvata lugens",
        source_org="IRRI",
        source_url="https://www.knowledgebank.irri.org/example",
        source_tier=1,
        damage_symptoms="Damage symptoms are described here.",
        management_ipm="Monitor fields and conserve natural enemies.",
        chemical_control="Use insecticide only according to local labels.",
    )


def test_chunk_includes_source_url_and_section() -> None:
    chunks = build_chunks(_profile())
    assert chunks
    assert all(chunk.source_url for chunk in chunks)
    assert {chunk.section for chunk in chunks} >= {"damage_symptoms", "management_ipm", "chemical_control"}


def test_long_text_is_split() -> None:
    text = " ".join(f"word{i}" for i in range(1200))
    pieces = split_long_text(text, target_tokens=500, max_tokens=600, overlap_tokens=100)
    assert len(pieces) > 1
    assert all(piece for piece in pieces)


def test_chemical_control_is_not_merged_into_ipm() -> None:
    chunks = build_chunks(_profile())
    by_section = {chunk.section: chunk.text for chunk in chunks}
    assert "insecticide" in by_section["chemical_control"].lower()
    assert "insecticide" not in by_section["management_ipm"].lower()


def test_chunk_ids_include_profile_id_to_avoid_source_collisions() -> None:
    chunks = build_chunks(_profile())
    assert all(chunk.chunk_id.startswith("brown_plant_hopper__fixture__") for chunk in chunks)
