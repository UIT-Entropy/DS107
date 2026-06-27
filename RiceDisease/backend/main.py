from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import List
import shutil
import traceback
import uuid

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from .paths import CACHE_DIR, UPLOAD_DIR, add_project_import_paths, validate_project_paths
except ImportError:
    from paths import CACHE_DIR, UPLOAD_DIR, add_project_import_paths, validate_project_paths

validate_project_paths()
add_project_import_paths()

from advisor.config import load_config  # noqa: E402
from advisor.core.advisor import RicePestAdvisor  # noqa: E402
from advisor.core.session import load_session, save_session, session_path, start_session  # noqa: E402
from advisor.gemini.client import GeminiGenerator  # noqa: E402
from advisor.prompts.prompt_builder import build_user_prompt, load_system_prompt  # noqa: E402
from cv_module.inference import classify_image  # noqa: E402


app = FastAPI(title="RiceCare AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

advisor_config = load_config()
advisor = RicePestAdvisor(config=advisor_config)

MODEL_OPTIONS = {
    "gemini-2.5-flash-lite": {
        "label": "Gemini 2.5 Flash-Lite",
        "note": "Fast default model used by the DS107 advisor.",
    },
    "gemini-2.5-flash": {
        "label": "Gemini 2.5 Flash",
        "note": "Balanced quality and speed.",
    },
    "gemini-3.5-flash": {
        "label": "Gemini 3.5 Flash",
        "note": "Higher-quality fallback when available.",
    },
}

ANSWER_MODES = {
    "fast": {
        "label": "Fast",
        "models": ["gemini-2.5-flash-lite"],
        "top_k": 4,
        "candidate_k": 12,
        "max_output_tokens": 1800,
    },
    "standard": {
        "label": "Standard",
        "models": ["gemini-2.5-flash"],
        "top_k": 6,
        "candidate_k": 24,
        "max_output_tokens": 2600,
    },
    "deep": {
        "label": "Deep",
        "models": ["gemini-2.5-flash"],
        "top_k": 8,
        "candidate_k": 32,
        "max_output_tokens": 3600,
    },
    "compare": {
        "label": "Compare",
        "models": ["gemini-2.5-flash-lite", "gemini-3.5-flash"],
        "top_k": 6,
        "candidate_k": 24,
        "max_output_tokens": 2200,
    },
}

MODE_PROMPT_INSTRUCTIONS = {
    "fast": "\n".join(
        [
            "Do dai che do Fast: tra loi ngan gon nhung phai tron y, khong duoc dung cut ngang.",
            "Neu cau hoi hoi ca 'gay hai' va 'xu ly', bat buoc co 2 muc: 'Cach gay hai' va 'Huong xu ly'.",
            "Moi muc co 2-3 bullet thuc dung, gan citation [S1] khi y lay tu context.",
        ]
    ),
    "standard": "\n".join(
        [
            "Do dai che do Standard: tra loi day du de nguoi xem demo thay ro gia tri cua RAG.",
            "Bat buoc co 4 muc: 'Nhan dinh nhanh', 'Cach gay hai', 'Huong xu ly/IPM', 'Luu y khi ap dung'.",
            "Viet khoang 8-12 bullet tong cong; moi bullet nen la mot hanh dong/nhan dinh cu the.",
            "Neu context du thong tin, khong tra loi qua ngan; uu tien giai thich bang tieng Viet tu nhien.",
            "Gan citation [S1], [S2] cho cac y quan trong lay tu context.",
        ]
    ),
    "deep": "\n".join(
        [
            "Do dai che do Deep: tra loi chi tiet hon Standard.",
            "Bat buoc co cac muc: 'Nhan dinh tu YOLO', 'Trieu chung va cach gay hai', 'Kiem tra ngoai dong', 'Huong xu ly/IPM', 'Canh bao va thong tin can hoi them'.",
            "Viet khoang 12-16 bullet tong cong, uu tien thong tin co citation.",
        ]
    ),
    "compare": "\n".join(
        [
            "Do dai che do Compare: moi model tra loi theo cau truc Standard, du y va co citation.",
        ]
    ),
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/cache", StaticFiles(directory=str(CACHE_DIR)), name="cache")


class AskRequest(BaseModel):
    question: str
    session_id: str
    mode: str | None = None
    models: list[str] | None = None


def save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix.lower() or ".jpg"
    image_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

    with open(image_path, "wb") as output:
        shutil.copyfileobj(file.file, output)

    return image_path


def create_session(result: dict, image_path: Path) -> str | None:
    summary = result.get("summary", {})
    class_id = summary.get("predicted_label")

    if not class_id:
        return None

    session_id = str(uuid.uuid4())
    confidence_ir = result.get("confidence_ir") or {}
    notes = " ".join(
        str(item)
        for item in [
            confidence_ir.get("level"),
            confidence_ir.get("llm_strategy"),
            confidence_ir.get("reason"),
        ]
        if item
    )

    start_session(
        advisor_config.paths.sessions_dir,
        session_id,
        {
            "source": "yolo",
            "class_id": class_id,
            "disease": summary.get("predicted_label_vi") or class_id,
            "confidence": summary.get("predicted_confidence"),
            "image_path": str(image_path),
            "notes": notes,
        },
        overwrite=True,
    )

    return session_id


@app.get("/")
def home():
    return {"message": "RiceCare AI Running"}


@app.get("/models")
def models():
    return {
        "models": [{"id": model_id, **metadata} for model_id, metadata in MODEL_OPTIONS.items()],
        "modes": [
            {
                "id": mode_id,
                "label": metadata["label"],
                "models": metadata["models"],
                "top_k": metadata["top_k"],
                "candidate_k": metadata["candidate_k"],
            }
            for mode_id, metadata in ANSWER_MODES.items()
        ],
        "default_mode": "standard",
    }


def format_prediction_response(result: dict, session_id: str | None, request: Request):
    summary = result.get("summary", {})
    annotated_file = result.get("annotated_image")
    image_url = None

    if annotated_file:
        image_url = str(request.url_for("cache", path=f"bbox/{Path(annotated_file).name}"))

    return {
        "success": True,
        "session_id": session_id,
        "disease": summary.get("predicted_label_vi"),
        "class_id": summary.get("predicted_label"),
        "confidence": summary.get("predicted_confidence"),
        "has_detection": summary.get("has_detection"),
        "count": summary.get("count"),
        "image_url": image_url,
    }


def is_gemini_permission_error(error: Exception) -> bool:
    message = str(error)
    return (
        "PERMISSION_DENIED" in message
        or "denied access" in message
        or ("403" in message and "permission" in message.lower())
    )


def build_gemini_permission_fallback(req: AskRequest, error: Exception) -> str:
    session = load_session(advisor_config.paths.sessions_dir, req.session_id)
    profile = session.profile or {}
    disease = profile.get("disease") or profile.get("class_id") or "unknown"
    confidence = profile.get("confidence")
    confidence_text = (
        f"{float(confidence) * 100:.1f}%"
        if isinstance(confidence, (int, float))
        else "unknown"
    )

    return "\n\n".join(
        [
            "Gemini denied access for the configured API key/project, so the RAG advisor could not be called.",
            f"YOLO still completed: **{disease}** with confidence **{confidence_text}**.",
            "Please confirm symptoms, pest density, spread, crop stage, and recent field conditions before taking action. Ask a local agricultural officer before pesticide use when infestation is severe.",
            "To enable AI chat, set a valid Gemini API key in `advisor/api_key.py` at the repository root and restart the backend.",
            f"`{str(error).splitlines()[0]}`",
        ]
    )


def mode_profile(mode: str | None) -> dict:
    return ANSWER_MODES.get(mode or "standard", ANSWER_MODES["standard"])


def mode_prompt_instruction(mode: str | None) -> str:
    return MODE_PROMPT_INSTRUCTIONS.get(mode or "standard", MODE_PROMPT_INSTRUCTIONS["standard"])


def selected_models(models: list[str] | None, mode: str | None) -> list[str]:
    cleaned = []
    requested_models = models or mode_profile(mode)["models"]

    for model in requested_models:
        if model in MODEL_OPTIONS and model not in cleaned:
            cleaned.append(model)

    return cleaned or mode_profile(mode)["models"]


def ensure_session(session_id: str):
    if not session_id:
        session_id = str(uuid.uuid4())

    if not session_path(advisor_config.paths.sessions_dir, session_id).exists():
        start_session(
            advisor_config.paths.sessions_dir,
            session_id,
            {"source": "web_chat"},
            overwrite=True,
        )

    return load_session(advisor_config.paths.sessions_dir, session_id)


def serialize_sources(sources):
    rows = []
    excerpt_limit = 160

    for source in sources:
        chunk = source.chunk
        text = str(chunk.get("text") or "").strip()
        excerpt = text[:excerpt_limit].rstrip()
        if len(text) > excerpt_limit:
            excerpt += "..."

        rows.append(
            {
                "label": source.source_label,
                "rank": source.rank,
                "title": chunk.get("common_name") or chunk.get("class_id") or chunk.get("section"),
                "section": chunk.get("section"),
                "source_org": chunk.get("source_org"),
                "source_url": chunk.get("source_url"),
                "source_relation": chunk.get("source_relation"),
                "rerank_score": source.rerank_score,
                "embedding_score": source.embedding_score,
                "excerpt": excerpt,
            }
        )

    return rows


def answer_with_models(req: AskRequest):
    profile_config = mode_profile(req.mode)
    session = ensure_session(req.session_id)
    history = session.recent_history()
    profile = session.profile
    retrieval_question = advisor._retrieval_question(req.question, profile)
    sources = advisor.retrieve(
        retrieval_question,
        top_k=profile_config["top_k"],
        candidate_k=profile_config["candidate_k"],
    )
    prompt = "\n\n".join(
        [
            build_user_prompt(req.question, sources, history=history, profile=profile),
            "YEU CAU DO DAI VA CAU TRUC THEO CHE DO:",
            mode_prompt_instruction(req.mode),
        ]
    )
    system_instruction = load_system_prompt(advisor_config.paths.system_prompt_path)
    answers = []

    for model in selected_models(req.models, req.mode):
        model_config = replace(
            advisor_config,
            generation_model=model,
            generation_fallback_models=tuple(),
            max_output_tokens=profile_config["max_output_tokens"],
        )
        generator = GeminiGenerator(
            api_key=model_config.api_key,
            model=model_config.generation_model,
            fallback_models=model_config.generation_fallback_models,
            temperature=model_config.temperature,
            max_output_tokens=model_config.max_output_tokens,
            retry_attempts=model_config.api_retry_attempts,
            retry_delay_seconds=model_config.api_retry_delay_seconds,
        )
        try:
            model_answer = generator.generate(prompt, system_instruction=system_instruction)
            model_error = None
        except Exception as exc:
            if is_gemini_permission_error(exc):
                raise
            model_answer = f"Could not call this model: {exc}"
            model_error = str(exc)

        answers.append(
            {
                "model": model,
                "label": MODEL_OPTIONS[model]["label"],
                "answer": model_answer,
                "error": model_error,
            }
        )

    combined_answer = "\n\n---\n\n".join(
        f"## {answer['label']}\n\n{answer['answer']}" for answer in answers
    )
    session.add_turn(question=req.question, answer=combined_answer)
    save_session(advisor_config.paths.sessions_dir, session)

    return {
        "answers": answers,
        "answer": answers[0]["answer"] if len(answers) == 1 else combined_answer,
        "mode": req.mode or "standard",
        "sources": serialize_sources(sources),
    }


@app.post("/predict")
async def predict(request: Request, file: UploadFile = File(...)):
    try:
        image_path = save_upload(file)
        result = classify_image(
            image_path=image_path,
            cache_upload=True,
            include_ds107_payload=True,
        )
        session_id = create_session(result, image_path)
        return format_prediction_response(result, session_id, request)
    except Exception as exc:
        traceback.print_exc()
        return {"success": False, "error": str(exc)}


@app.post("/predict-multiple")
async def predict_multiple(request: Request, files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        try:
            image_path = save_upload(file)
            result = classify_image(
                image_path=image_path,
                cache_upload=True,
                include_ds107_payload=True,
            )
            session_id = create_session(result, image_path)
            response = format_prediction_response(result, session_id, request)
            response["filename"] = file.filename
            results.append(response)
        except Exception as exc:
            traceback.print_exc()
            results.append({"filename": file.filename, "success": False, "error": str(exc)})

    return {"success": True, "count": len(results), "results": results}


@app.post("/ask")
async def ask(req: AskRequest):
    try:
        return {"success": True, **answer_with_models(req)}
    except Exception as exc:
        if is_gemini_permission_error(exc):
            return {
                "success": True,
                "answer": build_gemini_permission_fallback(req, exc),
                "fallback": True,
                "code": "GEMINI_PERMISSION_DENIED",
            }

        traceback.print_exc()
        return {"success": False, "error": str(exc)}
