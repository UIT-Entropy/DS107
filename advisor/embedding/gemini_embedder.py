from __future__ import annotations

from advisor.config import CONFIG
from advisor.gemini.client import create_client
from advisor.gemini.retry import retry_api_call


class GeminiEmbedder:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        retry_attempts: int | None = None,
        retry_delay_seconds: float | None = None,
    ) -> None:
        self.model = model or CONFIG.embedding_model
        self.retry_attempts = retry_attempts or CONFIG.api_retry_attempts
        self.retry_delay_seconds = (
            retry_delay_seconds
            if retry_delay_seconds is not None
            else CONFIG.api_retry_delay_seconds
        )
        self.client = create_client(api_key if api_key is not None else CONFIG.api_key)

    def embed(self, text: str) -> list[float]:
        result = retry_api_call(
            lambda: self.client.models.embed_content(
                model=self.model,
                contents=text,
            ),
            attempts=self.retry_attempts,
            delay_seconds=self.retry_delay_seconds,
            label=f"goi embedding model {self.model}",
        )
        if not result.embeddings:
            raise RuntimeError("Gemini khong tra ve embedding.")
        return list(result.embeddings[0].values)
