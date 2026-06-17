from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from crawler.chunker import split_long_text
from crawler.downloader import detect_source_type, fetch_url, save_raw_content
from crawler.models import ParsedDocument, RagChunk
from crawler.parsers import parse_html, parse_pdf
from crawler.storage import append_jsonl, load_models, write_jsonl
from crawler.taxonomy import load_crawler_config, load_sources_config, load_yaml, source_tier_for_domain
from crawler.utils import get_domain, sha256_bytes, sha256_text


class LocalContextSource(BaseModel):
    source_org: str
    url: str
    language: str = "vi"
    tags: list[str] = Field(default_factory=list)


LOCAL_CONTEXT_SECTIONS = {
    "vietnam_field_monitoring": [
        "thăm ruộng",
        "kiểm tra ruộng",
        "theo dõi",
        "phát hiện",
        "nhận diện",
        "giám sát",
        "bám đồng",
    ],
    "vietnam_pesticide_safety": [
        "4 đúng",
        "thuốc bảo vệ thực vật",
        "thuốc bvtv",
        "phun",
        "đúng thuốc",
        "đúng liều",
        "đúng lúc",
        "đúng cách",
    ],
    "vietnam_growth_stage_context": [
        "giai đoạn mạ",
        "mạ",
        "đẻ nhánh",
        "đẻ nhánh rộ",
        "đứng cái",
        "làm đòng",
        "phân hóa đòng",
        "trổ",
        "trỗ",
        "trước trổ",
        "sau trổ",
        "trổ bông",
        "ngậm sữa",
        "chắc xanh",
        "chín",
    ],
    "vietnam_abiotic_stress_context": [
        "thiếu nước",
        "khô hạn",
        "hạn hán",
        "hạn mặn",
        "xâm nhập mặn",
        "nước mặn",
        "phèn",
        "ngập sâu",
        "ngập úng",
        "mưa lớn",
        "lũ",
        "đổ ngã",
        "nắng nóng",
        "rét đậm",
        "rét hại",
        "gió lốc",
    ],
    "vietnam_severity_context": [
        "diện tích nhiễm",
        "tỷ lệ hại",
        "mật độ",
        "ngưỡng",
        "ngưỡng phòng trừ",
        "nhiễm nhẹ",
        "trung bình",
        "nhiễm nặng",
        "cục bộ",
        "lan rộng",
        "khoanh vùng",
        "ổ dịch",
    ],
    "vietnam_normal_crop_care": [
        "sinh trưởng phát triển tốt",
        "sinh trưởng tốt",
        "cây lúa khỏe",
        "chăm sóc lúa",
        "chăm sóc",
        "bón thúc",
        "điều tiết nước",
        "dặm tỉa",
        "làm cỏ",
        "giữ nước",
        "thoát nước",
    ],
    "vietnam_crop_management": [
        "quy trình kỹ thuật",
        "kỹ thuật canh tác",
        "lượng giống",
        "giống gieo sạ",
        "gieo sạ",
        "sạ thưa",
        "mật độ gieo sạ",
        "phân đạm",
        "bón phân",
        "bón phân cân đối",
        "quản lý nước",
        "rút nước",
        "ngập khô xen kẽ",
        "mực nước",
        "cơ giới hóa",
    ],
    "vietnam_straw_residue_management": [
        "rơm rạ",
        "rơm",
        "không đốt rơm",
        "đốt rơm",
        "thu gom rơm",
        "xử lý rơm",
        "vùi rơm",
        "quản lý rơm",
        "trichoderma",
        "phụ phẩm",
        "phế phụ phẩm",
        "tủ gốc",
    ],
    "vietnam_low_emission_rice": [
        "phát thải thấp",
        "giảm phát thải",
        "1 triệu hecta",
        "một triệu hecta",
        "đề án 1 triệu",
        "đề án",
        "đbscl",
        "đồng bằng sông cửu long",
        "chất lượng cao",
        "tăng trưởng xanh",
        "khí nhà kính",
        "carbon",
        "mrv",
        "co2",
        "ch4",
    ],
    "vietnam_cooperative_market_context": [
        "hợp tác xã",
        "htx",
        "tổ hợp tác",
        "liên kết",
        "liên kết tiêu thụ",
        "doanh nghiệp",
        "tiêu thụ",
        "cánh đồng lớn",
        "vùng nguyên liệu",
        "chuỗi sản xuất",
        "đầu ra",
        "mã vùng trồng",
    ],
    "vietnam_farmer_training": [
        "tập huấn",
        "nông dân tham dự",
        "nâng cao năng lực",
        "chuyển giao kỹ thuật",
        "hướng dẫn kỹ thuật",
        "tuyên truyền",
        "đào tạo",
        "khuyến nông cộng đồng",
        "cán bộ khuyến nông",
    ],
    "vietnam_farmer_qa_advisory": [
        "hỏi:",
        "câu hỏi:",
        "trả lời:",
        "xin chuyên gia",
        "chuyên gia tư vấn",
        "xử lý khi",
        "biện pháp phòng trừ",
        "biện pháp khắc phục",
        "khắc phục",
        "xin trân trọng cảm ơn",
        "nhờ chuyên gia",
    ],
    "vietnam_local_extension": [
        "cán bộ",
        "khuyến nông",
        "bảo vệ thực vật",
        "trạm trồng trọt",
        "ngành chuyên môn",
        "tập huấn",
    ],
    "vietnam_ipm_general": [
        "ipm",
        "quản lý dịch hại",
        "quản lý dịch hại tổng hợp",
        "vệ sinh đồng ruộng",
        "khoanh vùng",
        "canh tác hợp lý",
        "cây lúa khỏe",
        "giảm mật độ sâu",
        "ít sâu bệnh",
    ],
    "vietnam_seasonal_disease_context": [
        "vụ xuân",
        "vụ hè thu",
        "vụ đông xuân",
        "thời tiết",
        "biến đổi khí hậu",
        "đạo ôn",
        "khô vằn",
        "sâu cuốn lá",
        "sâu bệnh",
        "dịch hại",
    ],
}


def load_local_context_sources(path: str | Path = "config/local_context_sources.yaml") -> list[LocalContextSource]:
    data = load_yaml(path)
    return [LocalContextSource.model_validate(row) for row in data.get("sources", [])]


def crawl_local_context() -> list[ParsedDocument]:
    crawler_config = load_crawler_config()
    sources_config = load_sources_config()
    settings = crawler_config["crawler"]
    output = crawler_config["output"]
    documents: list[ParsedDocument] = []

    for source in load_local_context_sources():
        domain = get_domain(source.url)
        source_tier = source_tier_for_domain(domain, sources_config)
        if source_tier is None:
            append_jsonl(
                output["rejected_urls_path"],
                {"class_id": "local_context", "url": source.url, "reason": "domain not allowlisted"},
            )
            continue

        try:
            fetched = fetch_url(
                source.url,
                user_agent=settings["user_agent"],
                timeout_seconds=int(settings["request_timeout_seconds"]),
                delay_seconds_per_domain=float(settings["delay_seconds_per_domain"]),
            )
            if fetched.status_code >= 400:
                append_jsonl(
                    output["error_log_path"],
                    {"class_id": "local_context", "url": source.url, "status_code": fetched.status_code},
                )
                continue

            source_type = detect_source_type(fetched)
            raw_path = save_raw_content(fetched, output["raw_html_dir"], output["raw_pdf_dir"])
            parsed = parse_pdf(fetched.content, fetched.final_url) if source_type == "pdf" else parse_html(fetched.content, fetched.final_url)

            if len(parsed.text.strip()) < int(settings["min_text_chars"]):
                append_jsonl(
                    output["rejected_urls_path"],
                    {"class_id": "local_context", "url": source.url, "reason": "text too short"},
                )
                continue

            documents.append(
                ParsedDocument(
                    document_id=sha256_bytes(fetched.content),
                    class_id="local_context",
                    url=fetched.final_url,
                    domain=get_domain(fetched.final_url),
                    source_tier=source_tier,
                    source_type=source_type,
                    title=parsed.title,
                    text=parsed.text,
                    raw_path=raw_path,
                    text_hash=sha256_text(parsed.text),
                    fetched_at=fetched.fetched_at,
                    source_org=source.source_org,
                    source_relation="exact",
                    relation_note="Vietnam local agricultural context for final advisory answers.",
                )
            )
        except Exception as exc:  # noqa: BLE001 - CLI logs and continues per URL.
            append_jsonl(output["error_log_path"], {"class_id": "local_context", "url": source.url, "error": str(exc)})

    write_jsonl(output["local_context_documents_path"], documents)
    return documents


def _paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in text.split("\n") if len(paragraph.strip()) >= 80]


def _section_for_paragraph(paragraph: str) -> str | None:
    lowered = paragraph.lower()
    best_section = None
    best_score = 0
    for section, keywords in LOCAL_CONTEXT_SECTIONS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_section = section
            best_score = score
    return best_section


def build_local_context_chunks(input_path: str | None = None) -> list[RagChunk]:
    output = load_crawler_config()["output"]
    documents_path = input_path or output["local_context_documents_path"]
    documents = load_models(documents_path, ParsedDocument)
    chunks: list[RagChunk] = []

    for document in documents:
        sections: dict[str, list[str]] = {}
        for paragraph in _paragraphs(document.text):
            section = _section_for_paragraph(paragraph)
            if section:
                sections.setdefault(section, []).append(paragraph)

        for section, paragraphs in sections.items():
            text = "\n\n".join(paragraphs)
            for index, piece in enumerate(split_long_text(text, target_tokens=450, max_tokens=650, overlap_tokens=80)):
                chunks.append(
                    RagChunk(
                        chunk_id=f"local_context__{section}__{sha256_text(document.url)[:8]}__{index:03d}",
                        class_id="local_context",
                        section=section,
                        source_org=document.source_org,
                        source_url=document.url,
                        source_tier=document.source_tier,
                        source_relation="exact",
                        relation_note=document.relation_note,
                        language="vi",
                        text=piece,
                    )
                )

    write_jsonl(output["local_context_chunks_path"], chunks)
    return chunks


def run_local_context_pipeline() -> dict[str, Any]:
    documents = crawl_local_context()
    chunks = build_local_context_chunks()
    return {"documents": len(documents), "chunks": len(chunks)}
