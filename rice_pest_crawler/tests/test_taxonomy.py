from __future__ import annotations

from crawler.taxonomy import load_taxonomy


def test_loads_all_classifier_classes() -> None:
    taxonomy = load_taxonomy()
    assert len(taxonomy) == 11
    assert "normal" in taxonomy
    assert "brown_plant_hopper" in taxonomy
    assert "paddy_stem_maggot" in taxonomy


def test_each_pest_has_required_terms() -> None:
    taxonomy = load_taxonomy()
    for pest in taxonomy.values():
        assert pest.common_names_en
        assert pest.scientific_names
        assert pest.search_terms


def test_paddy_stem_maggot_preserves_ambiguity() -> None:
    pest = load_taxonomy()["paddy_stem_maggot"]
    assert "Hydrellia sasakii" in pest.scientific_names
    assert "Chlorops oryzae" in pest.scientific_names
