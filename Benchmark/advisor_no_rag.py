from __future__ import annotations

from pathlib import Path
from typing import Protocol

from advisor.config import AdvisorConfig, load_config
from advisor.core.models import AdvisorAnswer
from advisor.core.session import load_session, save_session
from advisor.gemini.client import GeminiGenerator


class Generator(Protocol):
    def generate(
        self,
        prompt: str,
        system_instruction: str,
    ) -> str:
        ...


class RicePestAdvisorNoRAG:

    def __init__(
        self,
        config: AdvisorConfig | None = None,
        sessions_dir: Path | None = None,
        generator: Generator | None = None,
    ) -> None:

        self.config = config or load_config()

        if sessions_dir is not None:
            self.config = self.config.with_paths(
                sessions_dir=sessions_dir
            )

        self._generator = generator

    @property
    def generator(self) -> Generator:

        if self._generator is None:

            self._generator = GeminiGenerator(
                api_key=self.config.api_key,
                model=self.config.generation_model,
                fallback_models=self.config.generation_fallback_models,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_output_tokens,
                retry_attempts=self.config.api_retry_attempts,
                retry_delay_seconds=self.config.api_retry_delay_seconds,
            )

        return self._generator

    @property
    def sessions_dir(self) -> Path:
        return self.config.paths.sessions_dir

    def answer(
        self,
        question: str,
        class_id: str,
        session_id: str | None = None,
    ) -> AdvisorAnswer:

        session = (
            load_session(self.sessions_dir, session_id)
            if session_id
            else None
        )

        prompt = f"""
Bạn là chuyên gia sâu bệnh hại lúa.

YOLO đã nhận diện:
{class_id}

Hãy trả lời câu hỏi sau:

{question}

Chỉ sử dụng kiến thức của mô hình.
Không được viện dẫn tài liệu ngoài.
"""

        text = self.generator.generate(
            prompt,
            system_instruction=""
        )

        if session is not None:
            session.add_turn(
                question=question,
                answer=text
            )
            save_session(self.sessions_dir, session)

        return AdvisorAnswer(
            text=text,
            sources=[],
            session_id=session_id,
        )