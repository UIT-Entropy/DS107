from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PestTaxonomy(BaseModel):
    label: str
    common_names_en: list[str]
    common_names_vi: list[str] = Field(default_factory=list)
    scientific_names: list[str]
    search_terms: list[str]


class ManualSource(BaseModel):
    class_id: str
    source_org: str | None = None
    url: str
    source_relation: Literal["exact", "related"] = "exact"
    relation_note: str | None = None
    relevance_terms: list[str] = Field(default_factory=list)


class CandidateUrl(BaseModel):
    class_id: str
    url: str
    domain: str
    source_tier: int | None = None
    discovery_method: str
    query: str | None = None
    source_org: str | None = None
    source_relation: Literal["exact", "related"] = "exact"
    relation_note: str | None = None
    relevance_terms: list[str] = Field(default_factory=list)
    score: int = 0
    reason: list[str] = Field(default_factory=list)


class FetchResult(BaseModel):
    url: str
    final_url: str
    status_code: int
    content_type: str
    content: bytes
    fetched_at: str


class ParsedText(BaseModel):
    title: str | None
    text: str
    page_count: int | None = None


class ParsedDocument(BaseModel):
    document_id: str
    class_id: str
    url: str
    domain: str
    source_tier: int | None
    source_type: Literal["html", "pdf"]
    title: str | None = None
    text: str
    raw_path: str | None = None
    text_hash: str
    fetched_at: str
    source_org: str | None = None
    source_relation: Literal["exact", "related"] = "exact"
    relation_note: str | None = None


class PestProfile(BaseModel):
    profile_id: str
    class_id: str
    common_name: str | None = None
    scientific_name: str | None = None
    source_org: str | None = None
    source_url: str
    source_tier: int | None = None
    source_relation: Literal["exact", "related", "taxonomy"] = "exact"
    relation_note: str | None = None
    language: str = "en"
    identity: str | None = None
    damage_symptoms: str | None = None
    life_cycle: str | None = None
    favorable_conditions: str | None = None
    field_diagnosis: str | None = None
    management_ipm: str | None = None
    chemical_control: str | None = None
    warnings: str | None = None
    source_quotes: list[str] = Field(default_factory=list)


class RagChunk(BaseModel):
    chunk_id: str
    class_id: str
    scientific_name: str | None = None
    common_name: str | None = None
    section: str
    source_org: str | None = None
    source_url: str
    source_tier: int | None = None
    source_relation: Literal["exact", "related", "taxonomy"] = "exact"
    relation_note: str | None = None
    language: str = "en"
    text: str
