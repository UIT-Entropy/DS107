from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from advisor.api_key import GEMINI_API_KEY


MODEL_PROFILE = "free"

YOLO_CLASS_LABELS = {
    "normal": "lúa bình thường",
    "asiatic_rice_borer": "sâu đục thân lúa",
    "brown_plant_hopper": "rầy nâu",
    "paddy_stem_maggot": "ruồi đục nõn lúa",
    "rice_gall_midge": "muỗi hành",
    "rice_leaf_caterpillar": "sâu ăn lá lúa",
    "rice_leaf_hopper": "rầy xanh",
    "rice_leaf_roller": "sâu cuốn lá lúa",
    "rice_water_weevil": "mọt nước hại lúa",
    "small_brown_plant_hopper": "rầy nâu nhỏ",
    "yellow_rice_borer": "sâu đục thân vàng",
}

MODEL_PROFILES = {
    "free": {
        "embedding_model": "gemini-embedding-001",
        "generation_model": "gemini-2.5-flash-lite",
        "generation_fallback_models": [
            "gemini-2.5-flash",
            "gemini-3.5-flash",
        ],
        "top_k": 4,
        "candidate_k": 12,
        "temperature": 0.2,
        "max_output_tokens": 1100,
        "embedding_delay_seconds": 1.0,
        "api_retry_attempts": 3,
        "api_retry_delay_seconds": 2.0,
    },
    "balanced": {
        "embedding_model": "gemini-embedding-2",
        "generation_model": "gemini-2.5-flash",
        "generation_fallback_models": [
            "gemini-2.5-flash-lite",
            "gemini-3.5-flash",
        ],
        "top_k": 6,
        "candidate_k": 24,
        "temperature": 0.2,
        "max_output_tokens": 1000,
        "embedding_delay_seconds": 0.25,
        "api_retry_attempts": 3,
        "api_retry_delay_seconds": 2.0,
    },
    "quality": {
        "embedding_model": "gemini-embedding-2",
        "generation_model": "gemini-3.5-flash",
        "generation_fallback_models": [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ],
        "top_k": 8,
        "candidate_k": 32,
        "temperature": 0.2,
        "max_output_tokens": 1300,
        "embedding_delay_seconds": 0.25,
        "api_retry_attempts": 3,
        "api_retry_delay_seconds": 2.0,
    },
}


def find_workspace_root(start: str | Path | None = None) -> Path:
    current = Path(start) if start is not None else Path(__file__)
    current = current.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "advisor").is_dir() and (candidate / "rice_pest_crawler").is_dir():
            return candidate

    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AdvisorPaths:
    workspace_root: Path
    advisor_root: Path
    crawler_root: Path
    data_dir: Path
    chunks_path: Path
    index_path: Path
    sessions_dir: Path
    system_prompt_path: Path

    @classmethod
    def default(cls) -> "AdvisorPaths":
        workspace_root = find_workspace_root()
        advisor_root = workspace_root / "advisor"
        crawler_root = workspace_root / "rice_pest_crawler"
        data_dir = advisor_root / "data"
        return cls(
            workspace_root=workspace_root,
            advisor_root=advisor_root,
            crawler_root=crawler_root,
            data_dir=data_dir,
            chunks_path=crawler_root / "data" / "rag" / "all_chunks.jsonl",
            index_path=data_dir / "gemini_embeddings.jsonl",
            sessions_dir=data_dir / "sessions",
            system_prompt_path=advisor_root / "prompts" / "expert_system.txt",
        )

    def resolve(self, path: str | Path) -> Path:
        resolved = Path(path)
        if not resolved.is_absolute():
            resolved = self.workspace_root / resolved
        return resolved

    def with_overrides(
        self,
        *,
        chunks_path: str | Path | None = None,
        index_path: str | Path | None = None,
        sessions_dir: str | Path | None = None,
        system_prompt_path: str | Path | None = None,
    ) -> "AdvisorPaths":
        updates = {}
        if chunks_path is not None:
            updates["chunks_path"] = self.resolve(chunks_path)
        if index_path is not None:
            updates["index_path"] = self.resolve(index_path)
        if sessions_dir is not None:
            updates["sessions_dir"] = self.resolve(sessions_dir)
        if system_prompt_path is not None:
            updates["system_prompt_path"] = self.resolve(system_prompt_path)
        return replace(self, **updates)


@dataclass(frozen=True)
class AdvisorConfig:
    paths: AdvisorPaths
    api_key: str
    model_profile: str
    embedding_model: str
    generation_model: str
    generation_fallback_models: tuple[str, ...]
    top_k: int
    candidate_k: int
    temperature: float
    max_output_tokens: int
    embedding_delay_seconds: float
    api_retry_attempts: int
    api_retry_delay_seconds: float

    def with_paths(
        self,
        *,
        chunks_path: str | Path | None = None,
        index_path: str | Path | None = None,
        sessions_dir: str | Path | None = None,
        system_prompt_path: str | Path | None = None,
    ) -> "AdvisorConfig":
        return replace(
            self,
            paths=self.paths.with_overrides(
                chunks_path=chunks_path,
                index_path=index_path,
                sessions_dir=sessions_dir,
                system_prompt_path=system_prompt_path,
            ),
        )


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


def load_config(
    *,
    chunks_path: str | Path | None = None,
    index_path: str | Path | None = None,
    sessions_dir: str | Path | None = None,
    system_prompt_path: str | Path | None = None,
) -> AdvisorConfig:
    paths = AdvisorPaths.default()
    profile_name = MODEL_PROFILE.strip().lower()
    if profile_name not in MODEL_PROFILES:
        raise ValueError(
            f"MODEL_PROFILE khong hop le: {MODEL_PROFILE}. "
            f"Hay chon mot trong: {', '.join(MODEL_PROFILES)}"
        )
    profile = MODEL_PROFILES[profile_name]

    paths = paths.with_overrides(
        chunks_path=chunks_path or os.getenv("ADVISOR_CHUNKS_PATH"),
        index_path=index_path or os.getenv("ADVISOR_INDEX_PATH"),
        sessions_dir=sessions_dir or os.getenv("ADVISOR_SESSIONS_DIR"),
        system_prompt_path=system_prompt_path or os.getenv("ADVISOR_SYSTEM_PROMPT_PATH"),
    )

    return AdvisorConfig(
        paths=paths,
        api_key=GEMINI_API_KEY.strip(),
        model_profile=profile_name,
        embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", profile["embedding_model"]),
        generation_model=os.getenv("GEMINI_GENERATION_MODEL", profile["generation_model"]),
        generation_fallback_models=tuple(profile["generation_fallback_models"]),
        top_k=_env_int("ADVISOR_TOP_K", profile["top_k"]),
        candidate_k=_env_int("ADVISOR_CANDIDATE_K", profile["candidate_k"]),
        temperature=_env_float("ADVISOR_TEMPERATURE", profile["temperature"]),
        max_output_tokens=_env_int(
            "ADVISOR_MAX_OUTPUT_TOKENS",
            profile["max_output_tokens"],
        ),
        embedding_delay_seconds=_env_float(
            "ADVISOR_EMBEDDING_DELAY_SECONDS",
            profile["embedding_delay_seconds"],
        ),
        api_retry_attempts=_env_int(
            "ADVISOR_API_RETRY_ATTEMPTS",
            profile["api_retry_attempts"],
        ),
        api_retry_delay_seconds=_env_float(
            "ADVISOR_API_RETRY_DELAY_SECONDS",
            profile["api_retry_delay_seconds"],
        ),
    )


CONFIG = load_config()
