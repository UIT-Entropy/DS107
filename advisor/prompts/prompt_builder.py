from __future__ import annotations

from pathlib import Path
from typing import Any

from advisor.core.models import SearchResult
from advisor.core.session import SessionTurn


BRIEF_QUESTION_MARKERS = (
    "checklist",
    "ngan gon",
    "ngắn gọn",
    "tom tat",
    "tóm tắt",
    "sang mai",
    "sáng mai",
    "viec can lam",
    "việc cần làm",
    "lam gi truoc",
    "làm gì trước",
)


def load_system_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def context_block(result: SearchResult) -> str:
    chunk = result.chunk
    text = str(chunk.get("text") or "")
    if len(text) > 1400:
        text = text[:1400].rstrip() + "..."

    lines = [
        f"[{result.source_label}]",
        f"rerank_score: {result.rerank_score:.4f}",
        f"embedding_score: {result.embedding_score:.4f}",
        f"class_id: {chunk.get('class_id')}",
        f"common_name: {chunk.get('common_name')}",
        f"scientific_name: {chunk.get('scientific_name')}",
        f"section: {chunk.get('section')}",
        f"source_org: {chunk.get('source_org')}",
        f"source_relation: {chunk.get('source_relation')}",
        f"source_url: {chunk.get('source_url')}",
        f"text: {text}",
    ]
    return "\n".join(lines)


def history_block(history: list[SessionTurn]) -> str:
    if not history:
        return "Không có lịch sử hội thoại trước đó."

    blocks = []
    for index, turn in enumerate(history, start=1):
        answer_summary = turn.answer.replace("\n", " ")[:300]
        blocks.append(
            "\n".join(
                [
                    f"Lượt {index}:",
                    f"Hỏi: {turn.question}",
                    f"Đáp tóm tắt trước đó: {answer_summary}",
                ]
            )
        )
    return "\n\n".join(blocks)


def profile_block(profile: dict[str, Any]) -> str:
    if not profile:
        return "Chưa có thông tin khởi tạo từ YOLO/session."

    labels = {
        "source": "Nguồn phát hiện",
        "disease": "Bệnh/sâu YOLO phát hiện",
        "class_id": "Class ID",
        "confidence": "Độ tin cậy YOLO",
        "image_path": "Ảnh đầu vào",
        "crop_stage": "Giai đoạn lúa",
        "location": "Địa điểm",
        "notes": "Ghi chú ban đầu",
        "created_at": "Tạo lúc",
    }
    lines = []
    for key, value in profile.items():
        label = labels.get(key, key)
        lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def is_brief_question(question: str) -> bool:
    normalized = question.lower()
    return any(marker in normalized for marker in BRIEF_QUESTION_MARKERS)


def answer_style_block(question: str) -> str:
    if is_brief_question(question):
        return """CHẾ ĐỘ CHECKLIST NGẮN:
- Trả lời tối đa 7 bullet.
- Mỗi bullet tối đa 1 câu ngắn.
- Tập trung vào việc cần làm ngay ngoài đồng.
- Không viết các mục dài như "Nhận định nhanh", "Căn cứ từ dữ liệu" hay giải thích lan man.
- Vẫn gắn citation [S1] nếu ý đó lấy từ context.
- Nếu cần hỏi thêm, chỉ hỏi 1 câu cuối cùng."""

    return """CHẾ ĐỘ TRẢ LỜI THEO Ý ĐỊNH:
- Hỏi gì trả lời đúng ý đó, không tự thêm đủ mọi mục.
- Mặc định 3-6 bullet hoặc 1-3 đoạn ngắn.
- Chỉ thêm phần thuốc, chẩn đoán, căn cứ, câu hỏi thêm nếu thật sự liên quan tới QUESTION.
- Ưu tiên hành động thực tế và citation."""


def build_user_prompt(
    question: str,
    retrieved: list[SearchResult],
    history: list[SessionTurn] | None = None,
    profile: dict[str, Any] | None = None,
) -> str:
    history = history or []
    profile = profile or {}
    context = "\n\n".join(context_block(result) for result in retrieved)
    return f"""Nhiệm vụ: Tư vấn cá nhân về sâu bệnh lúa dựa trên RAG context.

CHẾ ĐỘ TRẢ LỜI:
{answer_style_block(question)}

QUY TẮC CHỐNG LAN MAN:
- Không trả lời theo template đầy đủ nếu người dùng chỉ hỏi một việc nhỏ.
- Không tự thêm "thuốc BVTV" nếu người dùng không hỏi xử lý/phun/thuốc và context không bắt buộc cảnh báo.
- Không tự thêm "cần hỏi thêm" nếu câu trả lời đã đủ dùng.
- Không lặp lại toàn bộ bệnh học nếu session đã có bệnh YOLO.
- Với câu "tôi nên xử lý thế nào", đưa các bước ưu tiên theo thứ tự, không viết báo cáo dài.

LỊCH SỬ HỘI THOẠI GẦN NHẤT:
{history_block(history)}

THÔNG TIN KHỞI TẠO TỪ YOLO/SESSION:
{profile_block(profile)}

QUESTION:
{question}

CONTEXT:
{context}
"""
