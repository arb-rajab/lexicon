"""Pydantic request/response models matching 05-api-contracts.md."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class CorpusCreate(BaseModel):
    name: str = Field(min_length=1)


class CorpusOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime


class CorpusDetailOut(CorpusOut):
    document_count: int


class DocumentUploadOut(BaseModel):
    document_id: uuid.UUID
    # "ready" here, not "queued" — Session 4 ingestion is synchronous within
    # the request (see ingestion/service.py's module docstring), so there is
    # no async gap left for "queued"/"processing" to describe by the time
    # this response is returned. A stated deviation from the contract's
    # 202/"queued" async shape, not a silent one.
    status: str


class DocumentOut(BaseModel):
    id: uuid.UUID
    source_filename: str
    version: int
    status: str
    chunk_count: int


class DocumentDetailOut(DocumentOut):
    uploaded_at: datetime


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)


class CitationOut(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    source_filename: str
    section_heading: str
    claim_text: str


class QueryResponse(BaseModel):
    query_log_id: uuid.UUID
    answered: bool
    answer: str | None
    citations: list[CitationOut]
    refusal_reason: str | None
    retrieved_chunk_count: int


class QueryLogListItem(BaseModel):
    id: uuid.UUID
    query_text: str
    answered: bool
    refusal_reason: str | None
    created_at: datetime


class QueryLogListOut(BaseModel):
    items: list[QueryLogListItem]
    next_cursor: str | None


class RetrievedChunkOut(BaseModel):
    chunk_id: uuid.UUID
    keyword_rank: int | None
    vector_rank: int | None
    fusion_rank: int
    fusion_score: float


class CitationVerdictOut(BaseModel):
    chunk_id: uuid.UUID
    claim_text: str
    entailed: bool
    injection_suspected: bool
    verifier_rationale: str | None


class QueryLogDetailOut(BaseModel):
    id: uuid.UUID
    corpus_id: uuid.UUID
    query_text: str
    generated_answer: str | None
    self_refused: bool
    final_answered: bool
    refusal_reason: str | None
    created_at: datetime
    retrieved_chunks: list[RetrievedChunkOut]
    citation_verdicts: list[CitationVerdictOut]
