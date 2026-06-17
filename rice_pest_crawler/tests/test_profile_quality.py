from __future__ import annotations

from crawler.models import PestProfile
from crawler.profile_quality import assess_profile


def test_source_profile_with_damage_and_management_is_advisory_ready() -> None:
    profile = PestProfile(
        profile_id="brown_plant_hopper__fixture",
        class_id="brown_plant_hopper",
        common_name="brown planthopper",
        scientific_name="Nilaparvata lugens",
        source_org="TNAU",
        source_url="https://example.edu/bph",
        source_tier=2,
        identity="Brown planthopper is a rice pest.",
        damage_symptoms="Hopperburn and yellowing occur.",
        management_ipm="Use resistant varieties and conserve natural enemies.",
    )

    result = assess_profile(profile)

    assert result["advisory_ready"] is True
    assert result["grade"] == "strong"


def test_taxonomy_profile_is_not_advisory_ready() -> None:
    profile = PestProfile(
        profile_id="normal__taxonomy",
        class_id="normal",
        source_org="Taxonomy config",
        source_url="config/pest_taxonomy.yaml",
        identity="Healthy rice.",
    )

    result = assess_profile(profile)

    assert result["advisory_ready"] is False
    assert result["grade"] == "taxonomy_only"


def test_chemical_only_profile_is_weak() -> None:
    profile = PestProfile(
        profile_id="yellow_rice_borer__fixture",
        class_id="yellow_rice_borer",
        common_name="yellow stem borer",
        source_org="TNAU",
        source_url="https://example.edu/ysb",
        source_tier=2,
        chemical_control="Spray according to label.",
    )

    result = assess_profile(profile)

    assert result["advisory_ready"] is False
    assert result["chemical_only"] is True


def test_related_profile_is_actionable_but_requires_confirmation() -> None:
    profile = PestProfile(
        profile_id="asiatic_rice_borer__related",
        class_id="asiatic_rice_borer",
        common_name="Asiatic rice borer",
        source_org="TNAU",
        source_url="https://example.edu/stem-borer",
        source_tier=2,
        source_relation="related",
        relation_note="Related stem-borer group advisory.",
        identity="Stem borer larvae damage rice.",
        damage_symptoms="Dead hearts and white ears may occur.",
        management_ipm="Remove stubbles and use resistant varieties.",
    )

    result = assess_profile(profile)

    assert result["grade"] == "related_usable"
    assert result["actionable"] is True
    assert result["advisory_ready"] is False
    assert result["requires_identity_confirmation"] is True


def test_normal_crop_care_profile_does_not_require_damage_symptoms() -> None:
    profile = PestProfile(
        profile_id="normal__crop-care",
        class_id="normal",
        common_name="healthy rice",
        source_org="Trung tam Khuyen nong Quoc gia",
        source_url="https://example.edu/rice-care",
        source_tier=2,
        management_ipm="Monitor the field, manage water, and avoid pesticide use when no pest is confirmed.",
    )

    result = assess_profile(profile)

    assert result["advisory_ready"] is True
    assert result["actionable"] is True
    assert "damage_symptoms" not in result["missing_core_sections"]
