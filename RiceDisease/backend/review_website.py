"""Presentation + smoke test script for RiceCare AI.

What this script does:
- prints a short talk track you can use to present the web app
- checks the frontend shell
- checks core backend endpoints
- uploads one sample image to /predict to verify the YOLO flow

Run from the repo root:
    python RiceDisease/backend/review_website.py

Optional args:
    --frontend-url http://localhost:5173
    --backend-url http://localhost:8000
    --image RiceDisease/backend/uploads/02926.jpg
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


BACKEND_ROOT = Path(__file__).resolve().parent
WEB_ROOT = BACKEND_ROOT.parent
REPO_ROOT = WEB_ROOT.parent

DEFAULT_FRONTEND_URL = "http://localhost:5173"
DEFAULT_BACKEND_URL = "http://localhost:8000"


PRESENTATION_SCRIPT = [
    "Xin chào, đây là RiceCare AI, một web app hỗ trợ chẩn đoán và tư vấn sâu hại lúa.",
    "Người dùng tải ảnh ruộng lúa lên, backend sẽ chạy YOLO để phát hiện dấu hiệu sâu bệnh và tạo session theo class dự đoán.",
    "Sau đó hệ thống dùng advisor RAG của Gemini để trả lời tiếp theo ngữ cảnh session đó, nên không chỉ chẩn đoán mà còn gợi ý hướng xử lý.",
    "Giao diện frontend cho phép gửi ảnh, chọn mức độ trả lời nhanh hoặc kỹ, và xem lại lịch sử hội thoại trong cùng một phiên.",
    "Bây giờ mình sẽ test nhanh ba phần: trang chủ frontend, API models của backend, và luồng upload ảnh dự đoán YOLO.",
]


class _PageScanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.headings: list[str] = []
        self.root_found = False
        self._capture_title = False
        self._capture_heading = False
        self._heading_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._capture_title = True
            return

        if tag in {"h1", "h2", "h3"}:
            self._capture_heading = True
            self._heading_buffer = []
            return

        if tag == "div":
            attrs_dict = dict(attrs)
            if attrs_dict.get("id") == "root":
                self.root_found = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._capture_title = False
        elif tag in {"h1", "h2", "h3"}:
            self._capture_heading = False
            heading = "".join(self._heading_buffer).strip()
            if heading:
                self.headings.append(heading)
            self._heading_buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self.title += data
        if self._capture_heading:
            self._heading_buffer.append(data)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def fetch_text(url: str, timeout: float = 10.0) -> str:
    request = Request(url, headers={"User-Agent": "RiceCare-AI-Review/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_json(url: str, timeout: float = 10.0) -> Any:
    request = Request(url, headers={"User-Agent": "RiceCare-AI-Review/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
        return json.loads(payload)


def build_multipart_form_data(field_name: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----RiceCareBoundary{uuid4().hex}"
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()

    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return body, f"multipart/form-data; boundary={boundary}"


def post_file(url: str, file_path: Path, field_name: str = "file", timeout: float = 30.0) -> Any:
    body, content_type = build_multipart_form_data(field_name, file_path)
    request = Request(
        url,
        data=body,
        headers={
            "User-Agent": "RiceCare-AI-Review/1.0",
            "Content-Type": content_type,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
        return json.loads(payload)


def check_frontend_shell(frontend_url: str) -> CheckResult:
    try:
        html = fetch_text(frontend_url)
    except HTTPError as exc:
        return CheckResult("frontend /", False, f"HTTP {exc.code}: {exc.reason}")
    except URLError as exc:
        return CheckResult("frontend /", False, str(exc.reason))
    except Exception as exc:  # noqa: BLE001
        return CheckResult("frontend /", False, str(exc))

    scanner = _PageScanner()
    scanner.feed(html)

    title = scanner.title.strip() or "<no title>"
    if not scanner.root_found:
        return CheckResult("frontend /", False, "Missing #root mount point")

    if "ricecare" not in title.lower():
        return CheckResult("frontend /", False, f"Unexpected title: {title}")

    return CheckResult(
        "frontend /",
        True,
        f"title={title!r}, headings={scanner.headings[:3]!r}, root_found={scanner.root_found}",
    )


def check_backend_health(base_url: str) -> CheckResult:
    try:
        data = fetch_json(f"{base_url.rstrip('/')}/")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("backend /", False, str(exc))

    message = data.get("message") if isinstance(data, dict) else None
    if message == "RiceCare AI Running":
        return CheckResult("backend /", True, message)

    return CheckResult("backend /", False, f"Unexpected payload: {data!r}")


def check_models_endpoint(base_url: str) -> CheckResult:
    try:
        data = fetch_json(f"{base_url.rstrip('/')}/models")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("backend /models", False, str(exc))

    if not isinstance(data, dict):
        return CheckResult("backend /models", False, f"Unexpected payload type: {type(data).__name__}")

    models = data.get("models")
    modes = data.get("modes")
    default_mode = data.get("default_mode")
    if isinstance(models, list) and isinstance(modes, list) and default_mode:
        return CheckResult(
            "backend /models",
            True,
            f"{len(models)} models, {len(modes)} modes, default={default_mode}",
        )

    return CheckResult("backend /models", False, f"Unexpected payload: {data!r}")


def check_prediction(base_url: str, image_path: Path) -> CheckResult:
    if not image_path.exists():
        return CheckResult("backend /predict", False, f"Sample image not found: {image_path}")

    try:
        data = post_file(f"{base_url.rstrip('/')}/predict", image_path)
    except HTTPError as exc:
        return CheckResult("backend /predict", False, f"HTTP {exc.code}: {exc.reason}")
    except URLError as exc:
        return CheckResult("backend /predict", False, str(exc.reason))
    except Exception as exc:  # noqa: BLE001
        return CheckResult("backend /predict", False, str(exc))

    if not isinstance(data, dict):
        return CheckResult("backend /predict", False, f"Unexpected payload: {data!r}")

    if data.get("success") is True:
        disease = data.get("disease") or data.get("class_id") or "unknown"
        confidence = data.get("confidence")
        return CheckResult(
            "backend /predict",
            True,
            f"disease={disease!r}, confidence={confidence!r}, session_id={data.get('session_id')!r}",
        )

    return CheckResult("backend /predict", False, f"Prediction failed: {data!r}")


def choose_sample_image(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        if path.is_absolute() or path.exists():
            return path
        return REPO_ROOT / path

    candidates = sorted((BACKEND_ROOT / "uploads").glob("*.jpg"))
    if candidates:
        return candidates[0]

    return None


def build_report(frontend_url: str, backend_url: str, image_path: Path | None) -> list[CheckResult]:
    results = [
        check_frontend_shell(frontend_url),
        check_backend_health(backend_url),
        check_models_endpoint(backend_url),
    ]
    if image_path is not None:
        results.append(check_prediction(backend_url, image_path))
    else:
        results.append(CheckResult("backend /predict", False, "No sample image available"))
    return results


def print_presentation() -> None:
    print("Loi thuyet trinh ngan")
    print("=" * 24)
    for line in PRESENTATION_SCRIPT:
        print(f"- {line}")
    print()


def print_report(results: list[CheckResult]) -> int:
    passed = sum(result.ok for result in results)
    total = len(results)

    print("Ket qua test nhanh")
    print("=" * 18)
    print(f"Passed: {passed}/{total}\n")

    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

    print()
    print("Tong quan san pham")
    print("- Frontend: React + Vite chat UI de gui anh va hoi tiep theo boi canh")
    print("- Backend: FastAPI nhan anh, chay YOLO, tao session, goi Gemini RAG")
    print("- Luong chinh: anh -> YOLO -> session -> tra loi advisor")

    return 0 if passed == total else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Presentation and smoke test for RiceCare AI.")
    parser.add_argument("--frontend-url", default=DEFAULT_FRONTEND_URL)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--image", default=None, help="Optional sample image path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    sample_image = choose_sample_image(args.image)

    print_presentation()
    results = build_report(args.frontend_url, args.backend_url, sample_image)
    return print_report(results)


if __name__ == "__main__":
    raise SystemExit(main())
