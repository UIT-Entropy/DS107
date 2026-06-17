from __future__ import annotations

from crawler.models import PestProfile

ADVISORY_SECTIONS = [
    "identity",
    "damage_symptoms",
    "life_cycle",
    "favorable_conditions",
    "field_diagnosis",
    "management_ipm",
    "chemical_control",
]

CORE_SECTIONS = ["damage_symptoms", "management_ipm"]


def assess_profile(profile: PestProfile) -> dict:
    present_sections = [section for section in ADVISORY_SECTIONS if getattr(profile, section)]
    is_normal = profile.class_id == "normal"
    required_core_sections = ["management_ipm"] if is_normal else CORE_SECTIONS
    missing_core_sections = [section for section in required_core_sections if not getattr(profile, section)]
    has_management = bool(profile.management_ipm)
    has_chemical_only = bool(profile.chemical_control and not profile.management_ipm)
    is_taxonomy_only = profile.source_org == "Taxonomy config"
    is_related = profile.source_relation == "related"
    has_identity = bool(profile.identity or profile.common_name or profile.scientific_name or (is_normal and not is_taxonomy_only))

    score = 0
    if profile.source_tier == 1:
        score += 3
    elif profile.source_tier == 2:
        score += 2
    if has_identity:
        score += 1
    if profile.damage_symptoms:
        score += 2
    if profile.field_diagnosis:
        score += 1
    if profile.life_cycle:
        score += 1
    if has_management:
        score += 3
    if profile.chemical_control:
        score += 1
    if is_taxonomy_only:
        score = min(score, 1)
    if has_chemical_only:
        score = max(0, score - 2)

    pest_core_ready = (
        not is_taxonomy_only
        and profile.source_tier in {1, 2}
        and has_identity
        and bool(profile.damage_symptoms)
        and has_management
    )
    normal_core_ready = (
        is_normal
        and not is_taxonomy_only
        and profile.source_tier in {1, 2}
        and has_identity
        and bool(profile.management_ipm or profile.field_diagnosis or profile.favorable_conditions)
    )
    core_ready = normal_core_ready if is_normal else pest_core_ready
    advisory_ready = core_ready and not is_related
    actionable = core_ready

    if advisory_ready and score >= 8:
        grade = "strong"
    elif advisory_ready:
        grade = "usable"
    elif core_ready and is_related:
        grade = "related_usable"
    elif is_taxonomy_only:
        grade = "taxonomy_only"
    else:
        grade = "weak"

    return {
        "profile_id": profile.profile_id,
        "class_id": profile.class_id,
        "source_org": profile.source_org,
        "source_url": profile.source_url,
        "source_tier": profile.source_tier,
        "grade": grade,
        "score": score,
        "advisory_ready": advisory_ready,
        "actionable": actionable,
        "requires_identity_confirmation": is_related,
        "source_relation": profile.source_relation,
        "relation_note": profile.relation_note,
        "present_sections": present_sections,
        "missing_core_sections": missing_core_sections,
        "chemical_only": has_chemical_only,
        "taxonomy_only": is_taxonomy_only,
    }
