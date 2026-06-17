from __future__ import annotations

import re

from crawler.models import ParsedDocument, PestProfile, PestTaxonomy
from crawler.utils import sha256_text

SECTION_KEYWORDS = {
    "chemical_control": [
        "chemical",
        "insecticide",
        "pesticide",
        "spray",
        "thuốc bảo vệ thực vật",
        "thuốc bvtv",
        "thuốc trừ sâu",
        "phun thuốc",
        "hoạt chất",
        "4 đúng",
    ],
    "identity": [
        "description",
        "identity",
        "taxonomy",
        "host",
        "đặc điểm",
        "đặc điểm hình thái",
        "nhận dạng",
        "nhận diện",
        "ký chủ",
    ],
    "damage_symptoms": [
        "damage",
        "symptom",
        "symptoms",
        "signs",
        "injury",
        "triệu chứng",
        "gây hại",
        "tác hại",
        "biểu hiện",
        "cháy rầy",
        "bông bạc",
        "dảnh héo",
        "lá bị cuốn",
    ],
    "life_cycle": ["life cycle", "biology", "development", "vòng đời", "sinh học", "phát dục"],
    "favorable_conditions": [
        "favorable",
        "conditions",
        "outbreak",
        "ecology",
        "điều kiện phát sinh",
        "phát sinh gây hại",
        "thời tiết",
        "mật độ",
        "cao điểm",
    ],
    "field_diagnosis": [
        "diagnosis",
        "field",
        "identification",
        "monitoring",
        "thăm đồng",
        "kiểm tra đồng ruộng",
        "điều tra",
        "theo dõi",
        "ngưỡng phòng trừ",
    ],
    "management_ipm": [
        "management",
        "control",
        "ipm",
        "prevention",
        "phòng trừ",
        "quản lý",
        "biện pháp",
        "khuyến cáo",
        "vệ sinh đồng ruộng",
        "bón phân cân đối",
    ],
}

CHEMICAL_TERMS = ["chemical", "insecticide", "pesticide", "spray", "thuốc", "phun", "hoạt chất"]
DAMAGE_INDICATOR_TERMS = [
    "damage",
    "injury",
    "feeding",
    "scar",
    "root pruning",
    "triệu chứng",
    "gây hại",
    "phá hại",
    "vết xước",
    "héo",
    "gãy gục",
    "còi cọc",
    "rễ lúa",
    "cháy rầy",
    "bông bạc",
    "dảnh héo",
    "lá bị cuốn",
]
MANAGEMENT_INDICATOR_TERMS = [
    "management",
    "control",
    "monitor",
    "ipm",
    "prevention",
    "phòng trừ",
    "biện pháp",
    "khuyến cáo",
    "vệ sinh đồng ruộng",
    "thăm đồng",
    "phun phòng trừ",
    "bón phân cân đối",
]
HEADING_RE = re.compile(r"^(#{1,6}\s+)?[A-Z][A-Za-z0-9 /(),:-]{2,80}$")
LABEL_TO_SECTION = [
    ("thuốc bảo vệ thực vật", "chemical_control"),
    ("thuốc bvtv", "chemical_control"),
    ("biện pháp hóa học", "chemical_control"),
    ("biện pháp hoá học", "chemical_control"),
    ("phun thuốc", "chemical_control"),
    ("description", "identity"),
    ("symptom of damage", "damage_symptoms"),
    ("nature of damage", "damage_symptoms"),
    ("damage", "damage_symptoms"),
    ("identification of pest", "identity"),
    ("identification", "identity"),
    ("life cycle", "life_cycle"),
    ("biology", "life_cycle"),
    ("favourable conditions", "favorable_conditions"),
    ("favorable conditions", "favorable_conditions"),
    ("management strategies", "management_ipm"),
    ("cultural methods", "management_ipm"),
    ("biological methods", "management_ipm"),
    ("management", "management_ipm"),
    ("chemical control", "chemical_control"),
    ("chemical methods", "chemical_control"),
    ("đặc điểm hình thái", "identity"),
    ("đặc điểm nhận dạng", "identity"),
    ("nhận dạng", "identity"),
    ("nhận diện", "identity"),
    ("triệu chứng gây hại", "damage_symptoms"),
    ("triệu chứng", "damage_symptoms"),
    ("tác hại", "damage_symptoms"),
    ("đặc điểm gây hại", "damage_symptoms"),
    ("vòng đời", "life_cycle"),
    ("đặc điểm sinh học", "life_cycle"),
    ("điều kiện phát sinh", "favorable_conditions"),
    ("phát sinh gây hại", "favorable_conditions"),
    ("biện pháp phòng trừ", "management_ipm"),
    ("biện pháp quản lý", "management_ipm"),
]

VIETNAMESE_MARKERS = [
    "lúa",
    "sâu",
    "rầy",
    "phòng trừ",
    "gây hại",
    "thuốc bảo vệ thực vật",
    "đồng ruộng",
]


def _pick_first_present(text: str, terms: list[str]) -> str | None:
    lowered = text.lower()
    for term in terms:
        if term.lower() in lowered:
            return term
    return None


def _detect_language(text: str) -> str:
    lowered = text.lower()
    return "vi" if any(marker in lowered for marker in VIETNAMESE_MARKERS) else "en"


def _sentences_with_terms(text: str, terms: list[str], max_sentences: int = 6) -> str | None:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?。])\s+|\n+", text) if sentence.strip()]
    matches = [sentence for sentence in sentences if any(term in sentence.lower() for term in terms)]
    if not matches:
        return None
    return "\n".join(matches[:max_sentences])


def _taxonomy_terms(taxonomy: PestTaxonomy) -> list[str]:
    return [term.lower() for term in taxonomy.common_names_en + taxonomy.common_names_vi + taxonomy.scientific_names if term]


def _focus_text_on_taxonomy(text: str, taxonomy: PestTaxonomy, max_paragraphs: int = 18) -> str:
    if len(text) <= 12_000:
        return text

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) <= max_paragraphs:
        return text

    terms = _taxonomy_terms(taxonomy)
    matched_indexes = [
        index
        for index, paragraph in enumerate(paragraphs)
        if any(term in paragraph.lower() for term in terms)
    ]
    if not matched_indexes:
        return text

    selected: set[int] = set()
    for index in matched_indexes:
        selected.update(range(max(0, index - 1), min(len(paragraphs), index + 2)))

    focused = [paragraphs[index] for index in sorted(selected)[:max_paragraphs]]
    return "\n\n".join(focused)


def _split_by_inline_labels(text: str) -> dict[str, str]:
    label_patterns = [(label, section, re.compile(rf"\b{re.escape(label)}\b\s*:?", re.IGNORECASE)) for label, section in LABEL_TO_SECTION]
    matches: list[tuple[int, int, str]] = []
    for _label, section, pattern in label_patterns:
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), section))
    if len(matches) < 2:
        return {}

    matches.sort()
    sections: dict[str, list[str]] = {}
    for index, (_start, end, section) in enumerate(matches):
        next_start = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        content = text[end:next_start].strip(" :|-\n\t")
        if len(content.split()) >= 4:
            sections.setdefault(section, []).append(content)
    return {section: "\n\n".join(parts).strip() for section, parts in sections.items()}


def _section_for_heading(heading: str) -> str | None:
    lowered = heading.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return section
    return None


def _split_by_headings(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_section: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped and HEADING_RE.match(stripped):
            section = _section_for_heading(stripped)
            if section:
                if current_section and current_lines:
                    sections.setdefault(current_section, []).append("\n".join(current_lines).strip())
                current_section = section
                current_lines = []
                continue
        if current_section:
            current_lines.append(line)

    if current_section and current_lines:
        sections.setdefault(current_section, []).append("\n".join(current_lines).strip())

    return {section: "\n\n".join(parts).strip() for section, parts in sections.items() if any(parts)}


def _paragraph_keyword_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for paragraph in paragraphs:
        lowered = paragraph.lower()
        best_section = None
        best_score = 0
        for section, keywords in SECTION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in lowered)
            if score > best_score:
                best_section = section
                best_score = score
        if best_section:
            sections.setdefault(best_section, []).append(paragraph)
        elif len(paragraph) < 500:
            continue
    return {section: "\n\n".join(parts).strip() for section, parts in sections.items()}


def extract_profile(document: ParsedDocument, taxonomy: PestTaxonomy) -> PestProfile:
    source_text = _focus_text_on_taxonomy(document.text, taxonomy)
    sections = _split_by_inline_labels(source_text)
    if not sections:
        sections = _split_by_headings(source_text)
    if not sections:
        sections = _paragraph_keyword_sections(source_text)
    else:
        for section, content in _paragraph_keyword_sections(source_text).items():
            sections.setdefault(section, content)
    sections.setdefault("damage_symptoms", _sentences_with_terms(source_text, DAMAGE_INDICATOR_TERMS))
    sections.setdefault("management_ipm", _sentences_with_terms(source_text, MANAGEMENT_INDICATOR_TERMS))

    warnings = None
    warning_parts: list[str] = []
    if document.source_relation == "related":
        warning_parts.append(
            "Related/group advisory source; confirm field symptoms and pest identity before applying recommendations."
        )
    if any(term in source_text.lower() for term in CHEMICAL_TERMS):
        warning_parts.append("Chemical or pesticide terms detected; verify local registration and labels before use.")
    warnings = " ".join(warning_parts) if warning_parts else None

    return PestProfile(
        profile_id=f"{document.class_id}__{sha256_text(document.url)[:16]}",
        class_id=document.class_id,
        common_name=_pick_first_present(source_text, taxonomy.common_names_en + taxonomy.common_names_vi),
        scientific_name=_pick_first_present(source_text, taxonomy.scientific_names),
        source_org=document.source_org,
        source_url=document.url,
        source_tier=document.source_tier,
        source_relation=document.source_relation,
        relation_note=document.relation_note,
        language=_detect_language(source_text),
        identity=sections.get("identity"),
        damage_symptoms=sections.get("damage_symptoms"),
        life_cycle=sections.get("life_cycle"),
        favorable_conditions=sections.get("favorable_conditions"),
        field_diagnosis=sections.get("field_diagnosis"),
        management_ipm=sections.get("management_ipm"),
        chemical_control=sections.get("chemical_control"),
        warnings=warnings,
    )


def build_taxonomy_profile(class_id: str, taxonomy: PestTaxonomy) -> PestProfile:
    common_name = taxonomy.common_names_en[0] if taxonomy.common_names_en else None
    scientific_name = taxonomy.scientific_names[0] if taxonomy.scientific_names else None
    identity_parts = []
    if common_name:
        identity_parts.append(f"Common name: {common_name}.")
    if scientific_name:
        identity_parts.append(f"Scientific name: {scientific_name}.")
    if taxonomy.common_names_en:
        identity_parts.append(f"English aliases: {', '.join(taxonomy.common_names_en)}.")
    if taxonomy.scientific_names:
        identity_parts.append(f"Candidate scientific names: {', '.join(taxonomy.scientific_names)}.")

    return PestProfile(
        profile_id=f"{class_id}__taxonomy",
        class_id=class_id,
        common_name=common_name,
        scientific_name=scientific_name,
        source_org="Taxonomy config",
        source_url="config/pest_taxonomy.yaml",
        source_tier=None,
        source_relation="taxonomy",
        identity=" ".join(identity_parts) if identity_parts else None,
        warnings="Fallback taxonomy-only profile; advisory details were not extracted from a trusted source yet.",
    )
