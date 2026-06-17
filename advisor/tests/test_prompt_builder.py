from advisor.core.models import SearchResult
from advisor.core.session import SessionTurn
from advisor.prompts.prompt_builder import build_user_prompt, is_brief_question


def test_prompt_includes_history_context_and_citations_labels():
    result = SearchResult(
        chunk={
            "class_id": "brown_plant_hopper",
            "common_name": "Rầy nâu",
            "scientific_name": None,
            "section": "management_ipm",
            "source_org": "Extension",
            "source_relation": "exact",
            "source_url": "https://example.test",
            "text": "Theo dõi ruộng và xử lý rầy nâu theo IPM.",
        },
        embedding_score=0.8,
        rerank_score=0.9,
        rank=1,
    )
    history = [
        SessionTurn(
            question="Lá có đốm thì sao?",
            answer="Cần kiểm tra dạng vết bệnh.",
            created_at="2026-01-01T00:00:00+00:00",
        )
    ]

    prompt = build_user_prompt("Nên xử lý thế nào?", [result], history=history)

    assert "LỊCH SỬ HỘI THOẠI GẦN NHẤT" in prompt
    assert "Lá có đốm thì sao?" in prompt
    assert "[S1]" in prompt
    assert "Theo dõi ruộng và xử lý rầy nâu theo IPM." in prompt


def test_prompt_switches_to_brief_checklist_mode():
    prompt = build_user_prompt(
        "Nói ngắn gọn cho tôi checklist việc cần làm sáng mai ngoài ruộng.",
        [],
        history=[],
        profile={"class_id": "brown_plant_hopper", "disease": "rầy nâu"},
    )

    assert is_brief_question("Nói ngắn gọn checklist sáng mai")
    assert "CHẾ ĐỘ CHECKLIST NGẮN" in prompt
    assert "Trả lời tối đa 7 bullet" in prompt
    assert "QUY TẮC CHỐNG LAN MAN" in prompt


def test_prompt_uses_intent_following_mode_by_default():
    prompt = build_user_prompt(
        "Nếu phải dùng thuốc thì chú ý gì?",
        [],
        history=[],
        profile={"class_id": "brown_plant_hopper"},
    )

    assert "CHẾ ĐỘ TRẢ LỜI THEO Ý ĐỊNH" in prompt
    assert "Hỏi gì trả lời đúng ý đó" in prompt
    assert "Không trả lời theo template đầy đủ" in prompt
