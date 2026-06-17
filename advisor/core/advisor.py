from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Protocol

from advisor.config import AdvisorConfig, load_config
from advisor.core.models import AdvisorAnswer, IndexBuildReport
from advisor.core.session import load_session, save_session
from advisor.embedding.formatting import (
    format_document_for_embedding,
    format_query_for_embedding,
)
from advisor.embedding.gemini_embedder import GeminiEmbedder
from advisor.embedding.index_store import (
    load_chunks,
    load_index,
    metadata_path,
    save_index,
)
from advisor.embedding.vector_search import vector_search
from advisor.gemini.client import GeminiGenerator
from advisor.prompts.prompt_builder import build_user_prompt, load_system_prompt
from advisor.reranker.domain_reranker import DomainReranker


class Embedder(Protocol):
    model: str

    def embed(self, text: str) -> list[float]:
        ...


class Generator(Protocol):
    def generate(self, prompt: str, system_instruction: str) -> str:
        ...


class RicePestAdvisor:
    def __init__(
        self,
        config: AdvisorConfig | None = None,
        chunks_path: Path | None = None,
        index_path: Path | None = None,
        sessions_dir: Path | None = None,
        embedder: Embedder | None = None,
        generator: Generator | None = None,
        reranker: DomainReranker | None = None,
    ) -> None:
        self.config = config or load_config()
        if chunks_path is not None or index_path is not None or sessions_dir is not None:
            self.config = self.config.with_paths(
                chunks_path=chunks_path,
                index_path=index_path,
                sessions_dir=sessions_dir,
            )

        self._embedder = embedder
        self._generator = generator
        self.reranker = reranker or DomainReranker()

    @property
    def chunks_path(self) -> Path:
        return self.config.paths.chunks_path

    @property
    def index_path(self) -> Path:
        return self.config.paths.index_path

    @property
    def sessions_dir(self) -> Path:
        return self.config.paths.sessions_dir

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = GeminiEmbedder(
                api_key=self.config.api_key,
                model=self.config.embedding_model,
                retry_attempts=self.config.api_retry_attempts,
                retry_delay_seconds=self.config.api_retry_delay_seconds,
            )
        return self._embedder

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

    def build_index(
        self,
        limit: int | None = None,
        delay_seconds: float | None = None,
    ) -> IndexBuildReport:
        chunks = load_chunks(self.chunks_path)
        if limit is not None:
            chunks = chunks[:limit]
        delay_seconds = (
            self.config.embedding_delay_seconds
            if delay_seconds is None
            else delay_seconds
        )

        indexed_rows = []
        for index, chunk in enumerate(chunks, start=1):
            print(f"Embedding {index}/{len(chunks)}: {chunk.get('chunk_id')}")
            indexed_rows.append(
                {
                    "chunk": chunk,
                    "embedding": self.embedder.embed(format_document_for_embedding(chunk)),
                }
            )
            if delay_seconds > 0 and index < len(chunks):
                sleep(delay_seconds)

        meta = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chunks_path": str(self.chunks_path),
            "index_path": str(self.index_path),
            "chunk_count": len(indexed_rows),
            "embedding_model": self.embedder.model,
            "delay_seconds": delay_seconds,
            "format": "jsonl rows with chunk and embedding fields",
        }
        save_index(self.index_path, indexed_rows, metadata=meta)
        print(f"Da luu embedding index vao: {self.index_path}")
        print(f"Da luu metadata vao: {metadata_path(self.index_path)}")
        return IndexBuildReport(
            chunks_path=str(self.chunks_path),
            index_path=str(self.index_path),
            metadata_path=str(metadata_path(self.index_path)),
            chunk_count=len(indexed_rows),
            embedding_model=self.embedder.model,
            delay_seconds=delay_seconds,
        )

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        candidate_k: int | None = None,
    ):
        top_k = top_k or self.config.top_k
        candidate_k = candidate_k or self.config.candidate_k
        indexed_rows = load_index(self.index_path)
        query_embedding = self.embedder.embed(format_query_for_embedding(question))
        candidates = vector_search(indexed_rows, query_embedding, candidate_k)
        return self.reranker.rerank(question, candidates, top_k)

    def answer(
        self,
        question: str,
        top_k: int | None = None,
        candidate_k: int | None = None,
        session_id: str | None = None,
    ) -> AdvisorAnswer:
        session = load_session(self.sessions_dir, session_id) if session_id else None
        history = session.recent_history() if session else []
        profile = session.profile if session else {}
        retrieval_question = self._retrieval_question(question, profile)
        sources = self.retrieve(retrieval_question, top_k=top_k, candidate_k=candidate_k)
        prompt = build_user_prompt(
            question,
            sources,
            history=history,
            profile=profile,
        )
        text = self.generator.generate(
            prompt,
            system_instruction=load_system_prompt(self.config.paths.system_prompt_path),
        )

        if session is not None:
            session.add_turn(question=question, answer=text)
            save_session(self.sessions_dir, session)

        return AdvisorAnswer(text=text, sources=sources, session_id=session_id)

    def _retrieval_question(self, question: str, profile: dict) -> str:
        disease = profile.get("disease") or profile.get("class_id")
        crop_stage = profile.get("crop_stage")
        notes = profile.get("notes")
        parts = []
        if disease:
            parts.append(f"Benh/sau da biet tu YOLO: {disease}.")
        if crop_stage:
            parts.append(f"Giai doan lua: {crop_stage}.")
        if notes:
            parts.append(f"Ghi chu ban dau: {notes}.")
        parts.append(question)
        return " ".join(parts)
