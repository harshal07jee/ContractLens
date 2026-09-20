from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source_id: str | None = None
    chunk_id: str | None = None
    page: int = Field(ge=1)
    section: str | None = None
    excerpt: str


class CitedValue(BaseModel):
    value: str
    evidence: Evidence


class ContractOverview(BaseModel):
    parties: list[CitedValue] = Field(default_factory=list)
    effective_date: CitedValue | None = None
    expiration_date: CitedValue | None = None
    renewal_terms: list[CitedValue] = Field(default_factory=list)
    payment_terms: list[CitedValue] = Field(default_factory=list)
    termination_terms: list[CitedValue] = Field(default_factory=list)
    important_terms: list[CitedValue] = Field(default_factory=list)


class Obligation(BaseModel):
    party: str | None = None
    description: str
    frequency: str | None = None
    deadline: str | None = None
    evidence: Evidence


class TimelineEvent(BaseModel):
    title: str
    date: str | None = None
    relative_deadline: str | None = None
    description: str
    evidence: Evidence


class ContractStatus(BaseModel):
    id: str
    filename: str
    page_count: int
    status: Literal["processing", "processed", "failed"]
    uploaded_at: datetime


class ContractAnalysis(ContractStatus):
    overview: ContractOverview
    obligations: list[Obligation]
    timeline: list[TimelineEvent]


class ChatQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)


class SourceCitation(Evidence):
    pass


class ChatAnswer(BaseModel):
    answer: str
    answer_status: Literal["supported", "insufficient_evidence"]
    citations: list[SourceCitation] = Field(default_factory=list)


class SourceChunk(SourceCitation):
    contract_id: str
    text: str
