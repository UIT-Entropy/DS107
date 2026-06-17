from __future__ import annotations

from collections.abc import Callable
from time import sleep
from typing import TypeVar


T = TypeVar("T")


def is_retryable_api_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {429, 500, 502, 503, 504}:
        return True

    message = str(exc).lower()
    return any(
        signal in message
        for signal in (
            "429",
            "500",
            "502",
            "503",
            "504",
            "connecterror",
            "connect error",
            "connection",
            "eof occurred",
            "high demand",
            "network",
            "protocol",
            "rate limit",
            "remote protocol",
            "ssl",
            "temporarily",
            "timeout",
            "timed out",
            "unexpected_eof",
            "unavailable",
        )
    )


def retry_api_call(
    operation: Callable[[], T],
    *,
    attempts: int,
    delay_seconds: float,
    label: str,
) -> T:
    attempts = max(1, attempts)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            if not is_retryable_api_error(exc):
                raise
            last_error = exc
            if attempt < attempts:
                sleep(delay_seconds * attempt)

    raise RuntimeError(
        f"Gemini API loi tam thoi khi {label} sau {attempts} lan thu. "
        "Thu lai sau vai phut hoac kiem tra mang/VPN/firewall. "
        f"Chi tiet: {last_error}"
    ) from last_error
