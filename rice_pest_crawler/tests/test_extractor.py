from __future__ import annotations

from crawler.extractor import extract_profile
from crawler.models import ParsedDocument
from crawler.taxonomy import load_taxonomy


def test_extracts_damage_and_management_sections() -> None:
    text = """
Description
The brown planthopper Nilaparvata lugens feeds on rice.

Damage
Plants turn yellow and hopperburn can occur.

Management
Monitor fields and conserve natural enemies.

Chemical control
Use pesticide only when thresholds and local labels allow it.
"""
    document = ParsedDocument(
        document_id="fixture",
        class_id="brown_plant_hopper",
        url="https://www.knowledgebank.irri.org/example",
        domain="www.knowledgebank.irri.org",
        source_tier=1,
        source_type="html",
        title="Brown planthopper",
        text=text,
        raw_path=None,
        text_hash="hash",
        fetched_at="2026-06-15T00:00:00Z",
        source_org="IRRI",
    )
    profile = extract_profile(document, load_taxonomy()["brown_plant_hopper"])
    assert profile.damage_symptoms and "hopperburn" in profile.damage_symptoms
    assert profile.management_ipm and "Monitor" in profile.management_ipm
    assert profile.chemical_control and "pesticide" in profile.chemical_control
    assert profile.warnings


def test_extracts_vietnamese_advisory_sections() -> None:
    text = """
Đặc điểm nhận dạng
Rầy nâu Nilaparvata lugens thường sống ở gốc lúa.

Triệu chứng gây hại
Cây lúa bị vàng, cháy rầy và có thể bị lùn xoắn lá khi mật độ rầy cao.

Biện pháp phòng trừ
Thăm đồng thường xuyên, gieo sạ mật độ hợp lý, bón phân cân đối và bảo vệ thiên địch.

Thuốc bảo vệ thực vật
Chỉ phun thuốc khi vượt ngưỡng phòng trừ và phải tuân thủ nguyên tắc 4 đúng.
"""
    document = ParsedDocument(
        document_id="fixture-vi",
        class_id="brown_plant_hopper",
        url="https://khuyennongvn.gov.vn/example",
        domain="khuyennongvn.gov.vn",
        source_tier=2,
        source_type="html",
        title="Rầy nâu hại lúa",
        text=text,
        raw_path=None,
        text_hash="hash-vi",
        fetched_at="2026-06-15T00:00:00Z",
        source_org="Trung tam Khuyen nong Quoc gia",
    )
    profile = extract_profile(document, load_taxonomy()["brown_plant_hopper"])
    assert profile.language == "vi"
    assert profile.identity and "Nilaparvata lugens" in profile.identity
    assert profile.damage_symptoms and "cháy rầy" in profile.damage_symptoms
    assert profile.management_ipm and "Thăm đồng" in profile.management_ipm
    assert profile.chemical_control and "4 đúng" in profile.chemical_control
