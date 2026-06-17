from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from advisor.config import CONFIG, YOLO_CLASS_LABELS, AdvisorConfig, load_config
from advisor.core.advisor import RicePestAdvisor
from advisor.core.models import AdvisorAnswer, SearchResult
from advisor.core.session import (
    clear_sessions,
    delete_session,
    list_sessions,
    load_session,
    session_to_dict,
    start_session,
)
from advisor.embedding.index_store import load_index, load_index_metadata, metadata_path


def add_shared_args(parser: argparse.ArgumentParser, config: AdvisorConfig = CONFIG) -> None:
    parser.add_argument("--chunks", type=Path, default=config.paths.chunks_path)
    parser.add_argument("--index", type=Path, default=config.paths.index_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rice pest RAG advisor: build embeddings, rerank context, and ask Gemini."
    )
    add_shared_args(parser)

    # Backward-compatible flags from the first script version.
    parser.add_argument("--build-index", action="store_true")
    parser.add_argument("--ask", type=str, default="")
    parser.add_argument("--top-k", type=int, default=CONFIG.top_k)
    parser.add_argument("--candidate-k", type=int, default=CONFIG.candidate_k)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Gioi han so chunk khi build index de test nhanh.",
    )
    parser.add_argument("--delay", type=float, default=None)
    parser.add_argument("--session", type=str, default="")
    parser.add_argument(
        "--show-sources",
        action="store_true",
        help="In them danh sach context da dung sau cau tra loi.",
    )
    parser.add_argument("--json", action="store_true", help="In output dang JSON.")

    subparsers = parser.add_subparsers(dest="command")

    build_index = subparsers.add_parser("build-index", help="Tao embedding index.")
    add_shared_args(build_index)
    build_index.add_argument("--limit", type=int, default=None)
    build_index.add_argument("--delay", type=float, default=None)
    build_index.add_argument("--json", action="store_true")

    ask = subparsers.add_parser("ask", help="Hoi advisor bang RAG va Gemini.")
    add_shared_args(ask)
    ask.add_argument("question", type=str)
    ask.add_argument("--top-k", type=int, default=CONFIG.top_k)
    ask.add_argument("--candidate-k", type=int, default=CONFIG.candidate_k)
    ask.add_argument("--session", type=str, default="")
    ask.add_argument("--show-sources", action="store_true")
    ask.add_argument("--json", action="store_true")

    retrieve = subparsers.add_parser(
        "retrieve",
        help="Chi lay va rerank context, khong goi Gemini generation.",
    )
    add_shared_args(retrieve)
    retrieve.add_argument("question", type=str)
    retrieve.add_argument("--top-k", type=int, default=CONFIG.top_k)
    retrieve.add_argument("--candidate-k", type=int, default=CONFIG.candidate_k)
    retrieve.add_argument("--json", action="store_true")

    index_info = subparsers.add_parser("index-info", help="Xem metadata cua embedding index.")
    add_shared_args(index_info)
    index_info.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser("doctor", help="Kiem tra config/path/API key.")
    add_shared_args(doctor)
    doctor.add_argument("--json", action="store_true")

    sessions = subparsers.add_parser("sessions", help="Quan ly session hoi thoai.")
    add_shared_args(sessions)
    session_subparsers = sessions.add_subparsers(dest="session_command")

    sessions_start = session_subparsers.add_parser(
        "start",
        help="Tao/mo session tu ket qua YOLO.",
    )
    sessions_start.add_argument("session_id", type=str)
    sessions_start.add_argument("--class-id", type=str, required=True)
    sessions_start.add_argument("--disease", type=str, default="")
    sessions_start.add_argument("--confidence", type=float, default=None)
    sessions_start.add_argument("--image", type=str, default="")
    sessions_start.add_argument("--crop-stage", type=str, default="")
    sessions_start.add_argument("--location", type=str, default="")
    sessions_start.add_argument("--notes", type=str, default="")
    sessions_start.add_argument("--source", type=str, default="yolo")
    sessions_start.add_argument("--overwrite", action="store_true")
    sessions_start.add_argument("--json", action="store_true")

    sessions_list = session_subparsers.add_parser("list", help="Liet ke session.")
    sessions_list.add_argument("--json", action="store_true")

    sessions_show = session_subparsers.add_parser("show", help="Xem noi dung session.")
    sessions_show.add_argument("session_id", type=str)
    sessions_show.add_argument("--json", action="store_true")

    sessions_delete = session_subparsers.add_parser("delete", help="Xoa mot session.")
    sessions_delete.add_argument("session_id", type=str)

    session_subparsers.add_parser("clear", help="Xoa tat ca session.")
    return parser


def parse_args() -> argparse.Namespace:
    return build_parser().parse_args()


def print_sources(answer: AdvisorAnswer) -> None:
    print("\nNguồn đã dùng:")
    for result in answer.sources:
        print_result(result)


def print_result(result: SearchResult, include_text: bool = False) -> None:
    chunk = result.chunk
    print(
        f"[{result.source_label}] rerank={result.rerank_score:.4f} "
        f"embed={result.embedding_score:.4f} section={chunk.get('section')} "
        f"source={chunk.get('source_org')}"
    )
    print(f"    url: {chunk.get('source_url')}")
    print(f"    reasons: {', '.join(result.reasons)}")
    if include_text:
        text = str(chunk.get("text") or "").replace("\n", " ")
        print(f"    text: {text[:700]}")


def print_retrieved(results: list[SearchResult]) -> None:
    for result in results:
        print_result(result, include_text=True)


def run_index_info(args: argparse.Namespace) -> None:
    meta = load_index_metadata(args.index)
    row_count = len(load_index(args.index)) if args.index.exists() else 0
    info = {
        "index_path": str(args.index),
        "metadata_path": str(metadata_path(args.index)),
        "row_count": row_count,
        "metadata": meta,
    }
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    print(f"Index: {info['index_path']}")
    print(f"Metadata: {info['metadata_path']}")
    print(f"Rows: {row_count}")
    if meta:
        for key, value in meta.items():
            print(f"{key}: {value}")


def run_doctor(args: argparse.Namespace, config: AdvisorConfig) -> None:
    info = {
        "api_key_loaded": bool(config.api_key),
        "api_key_location": str(config.paths.advisor_root / "api_key.py"),
        "chunks_exists": config.paths.chunks_path.exists(),
        "chunks_path": str(config.paths.chunks_path),
        "index_exists": config.paths.index_path.exists(),
        "index_path": str(config.paths.index_path),
        "prompt_exists": config.paths.system_prompt_path.exists(),
        "prompt_path": str(config.paths.system_prompt_path),
        "model_profile": config.model_profile,
        "embedding_model": config.embedding_model,
        "generation_model": config.generation_model,
        "generation_fallback_models": list(config.generation_fallback_models),
        "top_k": config.top_k,
        "candidate_k": config.candidate_k,
        "max_output_tokens": config.max_output_tokens,
        "embedding_delay_seconds": config.embedding_delay_seconds,
        "api_retry_attempts": config.api_retry_attempts,
        "api_retry_delay_seconds": config.api_retry_delay_seconds,
    }
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    print(f"API key loaded: {'yes' if info['api_key_loaded'] else 'no'}")
    print(f"API key file: {info['api_key_location']}")
    print(f"Chunks exists: {'yes' if info['chunks_exists'] else 'no'}")
    print(f"Chunks path: {info['chunks_path']}")
    print(f"Index exists: {'yes' if info['index_exists'] else 'no'}")
    print(f"Index path: {info['index_path']}")
    print(f"Prompt exists: {'yes' if info['prompt_exists'] else 'no'}")
    print(f"Prompt path: {info['prompt_path']}")
    print(f"Model profile: {info['model_profile']}")
    print(f"Embedding model: {info['embedding_model']}")
    print(f"Generation model: {info['generation_model']}")
    print(f"Generation fallbacks: {', '.join(info['generation_fallback_models'])}")
    print(f"Top-k: {info['top_k']}")
    print(f"Candidate-k: {info['candidate_k']}")
    print(f"Max output tokens: {info['max_output_tokens']}")
    print(f"Embedding delay seconds: {info['embedding_delay_seconds']}")
    print(f"API retry attempts: {info['api_retry_attempts']}")
    print(f"API retry delay seconds: {info['api_retry_delay_seconds']}")


def run_build_index(args: argparse.Namespace, advisor: RicePestAdvisor) -> None:
    report = advisor.build_index(limit=args.limit, delay_seconds=args.delay)
    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


def run_ask(args: argparse.Namespace, advisor: RicePestAdvisor) -> None:
    question = args.question if args.command == "ask" else args.ask
    try:
        answer = advisor.answer(
            question,
            top_k=args.top_k,
            candidate_k=args.candidate_k,
            session_id=args.session or None,
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if args.json:
        print(json.dumps(answer.to_dict(), ensure_ascii=False, indent=2))
        return

    print(answer.text)
    if args.show_sources:
        print_sources(answer)


def run_retrieve(args: argparse.Namespace, advisor: RicePestAdvisor) -> None:
    results = advisor.retrieve(
        args.question,
        top_k=args.top_k,
        candidate_k=args.candidate_k,
    )
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "label": result.source_label,
                        "rank": result.rank,
                        "embedding_score": result.embedding_score,
                        "rerank_score": result.rerank_score,
                        "reasons": result.reasons,
                        "chunk": result.chunk,
                    }
                    for result in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print_retrieved(results)


def run_sessions(args: argparse.Namespace, config: AdvisorConfig) -> None:
    sessions_dir = config.paths.sessions_dir

    if args.session_command == "list":
        rows = list_sessions(sessions_dir)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return
        if not rows:
            print("Chua co session nao.")
            return
        for row in rows:
            print(
                f"{row['session_id']} | disease={row['disease']} "
                f"| turns={row['turn_count']} "
                f"| updated={row['updated_at']}"
            )
        return

    if args.session_command == "start":
        class_id = args.class_id.strip()
        disease = args.disease.strip() or YOLO_CLASS_LABELS.get(class_id, class_id)
        profile = {
            "source": args.source,
            "disease": disease,
            "class_id": class_id,
            "confidence": args.confidence,
            "image_path": args.image,
            "crop_stage": args.crop_stage,
            "location": args.location,
            "notes": args.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        session = start_session(
            sessions_dir,
            args.session_id,
            profile,
            overwrite=args.overwrite,
        )
        if args.json:
            print(json.dumps(session_to_dict(session), ensure_ascii=False, indent=2))
            return
        print(f"Da mo session: {session.session_id}")
        print(f"Benh/sau ban dau: {session.profile.get('disease')}")
        print(f"Class ID: {session.profile.get('class_id')}")
        print(f"So luot hoi dap hien co: {len(session.turns)}")
        return

    if args.session_command == "show":
        session = load_session(sessions_dir, args.session_id)
        if args.json:
            print(json.dumps(session_to_dict(session), ensure_ascii=False, indent=2))
            return
        print(f"Session: {session.session_id}")
        if session.profile:
            print("Profile:")
            for key, value in session.profile.items():
                print(f"  {key}: {value}")
        print(f"Turns: {len(session.turns)}")
        for index, turn in enumerate(session.turns, start=1):
            print(f"\n[{index}] {turn.created_at}")
            print(f"Q: {turn.question}")
            print(f"A: {turn.answer}")
        return

    if args.session_command == "delete":
        deleted = delete_session(sessions_dir, args.session_id)
        print("Da xoa session." if deleted else "Khong tim thay session.")
        return

    if args.session_command == "clear":
        count = clear_sessions(sessions_dir)
        print(f"Da xoa {count} session.")
        return

    raise SystemExit("Hay dung: sessions list/show/delete/clear.")


def main() -> None:
    args = parse_args()
    config = load_config(chunks_path=args.chunks, index_path=args.index)
    args.chunks = config.paths.chunks_path
    args.index = config.paths.index_path
    advisor = RicePestAdvisor(config=config)

    if args.command == "build-index" or args.build_index:
        run_build_index(args, advisor)
        return

    if args.command == "ask" or args.ask:
        run_ask(args, advisor)
        return

    if args.command == "retrieve":
        run_retrieve(args, advisor)
        return

    if args.command == "index-info":
        run_index_info(args)
        return

    if args.command == "doctor":
        run_doctor(args, config)
        return

    if args.command == "sessions":
        run_sessions(args, config)
        return

    raise SystemExit(
        "Hay dung command: build-index, ask, retrieve, index-info, doctor, sessions "
        "hoac flag cu --build-index / --ask."
    )


if __name__ == "__main__":
    main()
