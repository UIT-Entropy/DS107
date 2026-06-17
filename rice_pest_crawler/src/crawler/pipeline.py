from __future__ import annotations

from crawler.downloader import detect_source_type, fetch_url, save_raw_content
from crawler.extractor import build_taxonomy_profile, extract_profile
from crawler.models import CandidateUrl, ParsedDocument, PestProfile, RagChunk
from crawler.parsers import parse_html, parse_pdf
from crawler.quality import quality_rejection_reason
from crawler.source_discovery import candidates_from_manual_sources
from crawler.storage import append_jsonl, load_models, write_jsonl
from crawler.taxonomy import load_crawler_config, load_sources_config, load_taxonomy
from crawler.url_scorer import is_accepted, score_candidate_url
from crawler.utils import get_domain, sha256_bytes, sha256_text


def discover_candidates(class_id: str | None = None) -> list[CandidateUrl]:
    taxonomy = load_taxonomy()
    sources_config = load_sources_config()
    candidates = []
    for candidate in candidates_from_manual_sources(class_id):
        pest = taxonomy.get(candidate.class_id)
        if not pest:
            continue
        candidates.append(score_candidate_url(candidate, pest, sources_config))
    return candidates


def crawl(class_id: str | None = None) -> list[ParsedDocument]:
    taxonomy = load_taxonomy()
    sources_config = load_sources_config()
    crawler_config = load_crawler_config()
    settings = crawler_config["crawler"]
    output = crawler_config["output"]
    min_score = int(settings["min_url_score"])
    max_urls = int(settings["max_urls_per_class"])
    write_jsonl(output["error_log_path"], [])
    write_jsonl(output["rejected_urls_path"], [])

    candidates = discover_candidates(class_id)
    accepted_by_class: dict[str, int] = {}
    documents: list[ParsedDocument] = []

    for candidate in candidates:
        if not is_accepted(candidate, min_score):
            append_jsonl(output["rejected_urls_path"], candidate.model_dump(mode="json") | {"reason_text": "low score"})
            continue
        if accepted_by_class.get(candidate.class_id, 0) >= max_urls:
            append_jsonl(output["rejected_urls_path"], candidate.model_dump(mode="json") | {"reason_text": "class URL limit"})
            continue

        pest = taxonomy[candidate.class_id]
        try:
            fetched = fetch_url(
                candidate.url,
                user_agent=settings["user_agent"],
                timeout_seconds=int(settings["request_timeout_seconds"]),
                delay_seconds_per_domain=float(settings["delay_seconds_per_domain"]),
            )
            if fetched.status_code >= 400:
                append_jsonl(
                    output["error_log_path"],
                    {"class_id": candidate.class_id, "url": candidate.url, "status_code": fetched.status_code},
                )
                continue

            raw_path = save_raw_content(fetched, output["raw_html_dir"], output["raw_pdf_dir"])
            source_type = detect_source_type(fetched)
            parsed = parse_pdf(fetched.content, fetched.final_url) if source_type == "pdf" else parse_html(fetched.content, fetched.final_url)

            rejection = quality_rejection_reason(
                parsed.text,
                pest,
                int(settings["min_text_chars"]),
                extra_relevance_terms=candidate.relevance_terms,
            )
            if rejection:
                append_jsonl(output["rejected_urls_path"], {"class_id": candidate.class_id, "url": candidate.url, "reason": rejection})
                continue

            document = ParsedDocument(
                document_id=sha256_bytes(fetched.content),
                class_id=candidate.class_id,
                url=fetched.final_url,
                domain=get_domain(fetched.final_url),
                source_tier=candidate.source_tier,
                source_type=source_type,
                title=parsed.title,
                text=parsed.text,
                raw_path=raw_path,
                text_hash=sha256_text(parsed.text),
                fetched_at=fetched.fetched_at,
                source_org=candidate.source_org,
                source_relation=candidate.source_relation,
                relation_note=candidate.relation_note,
            )
            documents.append(document)
            accepted_by_class[candidate.class_id] = accepted_by_class.get(candidate.class_id, 0) + 1
        except Exception as exc:  # noqa: BLE001 - CLI logs and continues per URL.
            append_jsonl(output["error_log_path"], {"class_id": candidate.class_id, "url": candidate.url, "error": str(exc)})

    write_jsonl(output["parsed_documents_path"], documents)
    return documents


def extract_profiles(input_path: str | None = None) -> list[PestProfile]:
    taxonomy = load_taxonomy()
    output = load_crawler_config()["output"]
    documents_path = input_path or output["parsed_documents_path"]
    documents = load_models(documents_path, ParsedDocument)
    profiles = [extract_profile(document, taxonomy[document.class_id]) for document in documents if document.class_id in taxonomy]
    covered_class_ids = {profile.class_id for profile in profiles}
    for class_id, pest_taxonomy in taxonomy.items():
        if class_id not in covered_class_ids:
            profiles.append(build_taxonomy_profile(class_id, pest_taxonomy))
    write_jsonl(output["pest_profiles_path"], profiles)
    return profiles


def build_rag_chunks(input_path: str | None = None) -> list[RagChunk]:
    from crawler.chunker import build_chunks

    output = load_crawler_config()["output"]
    profiles_path = input_path or output["pest_profiles_path"]
    profiles = load_models(profiles_path, PestProfile)
    chunks: list[RagChunk] = []
    for profile in profiles:
        chunks.extend(build_chunks(profile))
    write_jsonl(output["chunks_path"], chunks)
    return chunks
