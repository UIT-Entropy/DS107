from __future__ import annotations

import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parent
WEB_ROOT = BACKEND_ROOT.parent
REPO_ROOT = WEB_ROOT.parent
CV_MODULE_ROOT = WEB_ROOT / "DS107_CVModule-main"


def _runtime_path(env_name: str, default: Path) -> Path:
    value = os.getenv(env_name)
    if not value:
        return default

    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


UPLOAD_DIR = _runtime_path("RICECARE_UPLOAD_DIR", BACKEND_ROOT / "uploads")
CACHE_DIR = _runtime_path("RICECARE_CACHE_DIR", CV_MODULE_ROOT / "cache")


def add_project_import_paths() -> None:
    for path in (CV_MODULE_ROOT, REPO_ROOT):
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)


def validate_project_paths() -> None:
    required_paths = {
        "repository advisor module": REPO_ROOT / "advisor",
        "repository crawler module": REPO_ROOT / "rice_pest_crawler",
        "CV module": CV_MODULE_ROOT / "cv_module",
        "YOLO weight": CV_MODULE_ROOT / "E08_yolo11s_img416_default_best.pt",
    }
    missing = [f"{label}: {path}" for label, path in required_paths.items() if not path.exists()]

    if missing:
        details = "\n".join(f"- {item}" for item in missing)
        raise RuntimeError(
            "RiceCare AI project paths are incomplete. Clone the full repository and "
            f"run the backend from the repo layout documented in README.md.\n{details}"
        )
