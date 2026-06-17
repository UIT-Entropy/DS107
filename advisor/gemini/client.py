from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from advisor.config import CONFIG
from advisor.gemini.retry import is_retryable_api_error, retry_api_call


def require_api_key(api_key: str) -> str:
    if not api_key:
        raise RuntimeError(
            "Chua co GEMINI_API_KEY. Hay dien key vao advisor/api_key.py."
        )
    return api_key


def create_client(api_key: str) -> Any:
    try:
        from google import genai
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Thieu thu vien google-genai. Hay chay: "
            "python -m pip install -r advisor/requirements.txt"
        ) from exc

    return genai.Client(api_key=require_api_key(api_key))


class GeminiGenerator:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_models: Sequence[str] | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        retry_attempts: int | None = None,
        retry_delay_seconds: float | None = None,
    ) -> None:
        self.model = model or CONFIG.generation_model
        self.fallback_models = tuple(fallback_models or CONFIG.generation_fallback_models)
        self.temperature = temperature if temperature is not None else CONFIG.temperature
        self.max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else CONFIG.max_output_tokens
        )
        self.retry_attempts = retry_attempts or CONFIG.api_retry_attempts
        self.retry_delay_seconds = (
            retry_delay_seconds
            if retry_delay_seconds is not None
            else CONFIG.api_retry_delay_seconds
        )
        self.client = create_client(api_key if api_key is not None else CONFIG.api_key)

    def generate(self, prompt: str, system_instruction: str) -> str:
        try:
            from google.genai import types
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Thieu thu vien google-genai. Hay chay: "
                "python -m pip install -r advisor/requirements.txt"
            ) from exc

        errors: list[str] = []
        for model in self._model_chain():
            try:
                response = retry_api_call(
                    lambda: self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=self.temperature,
                            max_output_tokens=self.max_output_tokens,
                        ),
                    ),
                    attempts=self.retry_attempts,
                    delay_seconds=self.retry_delay_seconds,
                    label=f"goi generation model {model}",
                )
                text = response.text or ""
                if model != self.model:
                    return f"(Dung model du phong: {model})\n\n{text}"
                return text
            except Exception as exc:
                if not is_retryable_api_error(exc):
                    raise
                errors.append(f"{model}: {exc}")

        raise RuntimeError(
            "Gemini dang qua tai hoac tam thoi khong kha dung cho cac model generation. "
            "Thu lai sau vai phut, hoac doi MODEL_PROFILE trong advisor/config.py. "
            f"Chi tiet: {' | '.join(errors[-3:])}"
        )

    def _model_chain(self) -> tuple[str, ...]:
        models = [self.model]
        for fallback in self.fallback_models:
            if fallback not in models:
                models.append(fallback)
        return tuple(models)


def is_retryable_generation_error(exc: Exception) -> bool:
    return is_retryable_api_error(exc)
