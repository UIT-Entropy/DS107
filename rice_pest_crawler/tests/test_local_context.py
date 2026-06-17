from __future__ import annotations

from crawler.local_context import _section_for_paragraph


def test_classifies_vietnam_pesticide_safety_context() -> None:
    paragraph = "Nông dân áp dụng nguyên tắc 4 đúng khi sử dụng thuốc bảo vệ thực vật và phun đúng thời điểm."
    assert _section_for_paragraph(paragraph) == "vietnam_pesticide_safety"


def test_classifies_vietnam_field_monitoring_context() -> None:
    paragraph = "Bà con cần thăm ruộng thường xuyên, theo dõi và phát hiện sớm sâu bệnh hại lúa."
    assert _section_for_paragraph(paragraph) == "vietnam_field_monitoring"


def test_classifies_vietnam_crop_management_context() -> None:
    paragraph = "Mô hình giảm lượng giống gieo sạ, bón phân đạm hợp lý và quản lý nước theo ngập khô xen kẽ."
    assert _section_for_paragraph(paragraph) == "vietnam_crop_management"


def test_classifies_vietnam_straw_context() -> None:
    paragraph = "Sau thu hoạch cần thu gom rơm rạ, hạn chế đốt rơm và xử lý phụ phẩm để cải thiện đất."
    assert _section_for_paragraph(paragraph) == "vietnam_straw_residue_management"


def test_classifies_vietnam_cooperative_context() -> None:
    paragraph = "Cánh đồng lớn giúp hợp tác xã liên kết tiêu thụ với doanh nghiệp và ổn định vùng nguyên liệu."
    assert _section_for_paragraph(paragraph) == "vietnam_cooperative_market_context"


def test_classifies_vietnam_growth_stage_context() -> None:
    paragraph = "Ruộng lúa đang làm đòng, chuẩn bị trổ bông nên cần chăm sóc khác với giai đoạn đẻ nhánh."
    assert _section_for_paragraph(paragraph) == "vietnam_growth_stage_context"


def test_classifies_vietnam_abiotic_stress_context() -> None:
    paragraph = "Khu vực này có nguy cơ thiếu nước, xâm nhập mặn và nắng nóng làm cây lúa sinh trưởng kém."
    assert _section_for_paragraph(paragraph) == "vietnam_abiotic_stress_context"


def test_classifies_vietnam_severity_context() -> None:
    paragraph = "Cần ghi nhận diện tích nhiễm, tỷ lệ hại, mật độ và ổ dịch cục bộ trước khi khuyến cáo xử lý."
    assert _section_for_paragraph(paragraph) == "vietnam_severity_context"


def test_classifies_vietnam_farmer_qa_context() -> None:
    paragraph = "Hỏi: Lúa có biểu hiện cháy lá, xin chuyên gia tư vấn biện pháp khắc phục và phòng trừ phù hợp."
    assert _section_for_paragraph(paragraph) == "vietnam_farmer_qa_advisory"
