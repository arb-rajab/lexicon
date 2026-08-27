"""The retrieve -> generate -> verify -> decide pipeline (ADR-0001,
03-architecture.md's Key flows: "Ask a question"). This is where the
"cited or refused" invariant is actually enforced — deterministically, in
application code, never left to the LLM to self-certify (04-data-model.md's
invariant note on QUERY_LOG.final_answered).
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from lexicon.db import models
from lexicon.llm.base import LLMClient, VerificationVerdict
from lexicon.retrieval.service import RetrievedChunkContext, hybrid_retrieve


@dataclass
class CitationOut:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    source_filename: str
    section_heading: str
    claim_text: str


@dataclass
class QueryPipelineResult:
    query_log_id: uuid.UUID
    answered: bool
    answer: str | None
    citations: list[CitationOut]
    refusal_reason: str | None
    retrieved_chunk_count: int


@dataclass
class _ClaimVerdict:
    claim_text: str
    chunk: RetrievedChunkContext
    raw_verdict: VerificationVerdict
    enforced_entailed: bool = field(init=False)

    def __post_init__(self) -> None:
        # ADR-0003 item 3: injection_suspected auto-fails entailment
        # regardless of the model's own `entailed` value — enforced here,
        # in application code, not merely requested of the prompt.
        self.enforced_entailed = (
            self.raw_verdict.entailed and not self.raw_verdict.injection_suspected
        )


def _rationale_for(verdict: VerificationVerdict, enforced_entailed: bool) -> str:
    # Application-generated text, not model free text — see db/models.py's
    # module docstring on why (ADR-0003's structured-output hardening gives
    # the verifier model no free-text field to write into).
    if verdict.injection_suspected:
        return "auto-failed: injection_suspected flag set by verifier"
    if not enforced_entailed:
        return "not entailed: cited passage does not support the claim"
    return "entailed"


def _write_retrieved_chunks(
    db: Session, query_log_id: uuid.UUID, retrieved: list[RetrievedChunkContext]
) -> None:
    for chunk in retrieved:
        db.add(
            models.RetrievedChunk(
                query_log_id=query_log_id,
                chunk_id=chunk.chunk_id,
                keyword_rank=chunk.keyword_rank,
                vector_rank=chunk.vector_rank,
                fusion_rank=chunk.fusion_rank,
                fusion_score=chunk.fusion_score,
            )
        )


def _write_citation_verdicts(
    db: Session, query_log_id: uuid.UUID, verdicts: list[_ClaimVerdict]
) -> None:
    for v in verdicts:
        db.add(
            models.CitationVerdict(
                query_log_id=query_log_id,
                chunk_id=v.chunk.chunk_id,
                claim_text=v.claim_text,
                entailed=v.enforced_entailed,
                injection_suspected=v.raw_verdict.injection_suspected,
                verifier_rationale=_rationale_for(v.raw_verdict, v.enforced_entailed),
            )
        )


def run_query_pipeline(
    db: Session, llm: LLMClient, corpus_id: uuid.UUID, question: str, top_n: int
) -> QueryPipelineResult:
    retrieved = hybrid_retrieve(db, corpus_id, question, top_n)

    if not retrieved:
        # 03-architecture.md Failure handling: short-circuits directly to
        # refusal without invoking generation — nothing to spend LLM cost on.
        query_log = models.QueryLog(
            corpus_id=corpus_id,
            query_text=question,
            self_refused=False,
            final_answered=False,
            refusal_reason="no_candidates_retrieved",
        )
        db.add(query_log)
        db.commit()
        return QueryPipelineResult(
            query_log_id=query_log.id,
            answered=False,
            answer=None,
            citations=[],
            refusal_reason="no_candidates_retrieved",
            retrieved_chunk_count=0,
        )

    # A provider-call failure (LLMProviderError) is intentionally allowed to
    # propagate uncaught here — the API layer (api/query.py) turns it into a
    # 502, per 05-api-contracts.md: "never represented as a successful 200
    # response with refusal_reason". No QUERY_LOG row is written for a call
    # that never reached a decision.
    generation = llm.generate(question, retrieved)

    if generation.self_refused:
        query_log = models.QueryLog(
            corpus_id=corpus_id,
            query_text=question,
            self_refused=True,
            final_answered=False,
            refusal_reason="self_refused",
        )
        db.add(query_log)
        db.flush()
        _write_retrieved_chunks(db, query_log.id, retrieved)
        db.commit()
        return QueryPipelineResult(
            query_log_id=query_log.id,
            answered=False,
            answer=None,
            citations=[],
            refusal_reason="self_refused",
            retrieved_chunk_count=len(retrieved),
        )

    chunk_by_id = {c.chunk_id: c for c in retrieved}
    verdicts: list[_ClaimVerdict] = []
    for claim in generation.claims:
        chunk = chunk_by_id.get(claim.chunk_id)
        # A citation pointing outside the retrieved set is treated as
        # unsupported (empty passage never entails anything) rather than
        # raised — a schema-constrained generator citing an unknown
        # chunk_id is itself a form of the "wrong claim, confident citation"
        # failure mode this pipeline exists to catch.
        passage_text = chunk.content if chunk is not None else ""
        raw_verdict = llm.verify(claim.claim_text, passage_text)
        verdicts.append(
            _ClaimVerdict(
                claim_text=claim.claim_text,
                chunk=chunk if chunk is not None else retrieved[0],
                raw_verdict=raw_verdict,
            )
        )

    final_answered = bool(verdicts) and all(v.enforced_entailed for v in verdicts)
    refusal_reason = None if final_answered else "verification_failed"

    query_log = models.QueryLog(
        corpus_id=corpus_id,
        query_text=question,
        # The draft answer is retained in the audit log even when refused
        # (US-005 traceability — an operator investigating a disputed
        # refusal needs to see what was generated and why it was blocked).
        # It is never surfaced to the caller unless final_answered — see the
        # `answer=` field below, which is the user-facing contract FR-009
        # governs.
        generated_answer=generation.answer_text,
        self_refused=False,
        final_answered=final_answered,
        refusal_reason=refusal_reason,
    )
    db.add(query_log)
    db.flush()
    _write_retrieved_chunks(db, query_log.id, retrieved)
    _write_citation_verdicts(db, query_log.id, verdicts)
    db.commit()

    citations = (
        [
            CitationOut(
                chunk_id=v.chunk.chunk_id,
                document_id=v.chunk.document_id,
                source_filename=v.chunk.source_filename,
                section_heading=v.chunk.section_heading,
                claim_text=v.claim_text,
            )
            for v in verdicts
        ]
        if final_answered
        else []
    )

    return QueryPipelineResult(
        query_log_id=query_log.id,
        answered=final_answered,
        answer=generation.answer_text if final_answered else None,
        citations=citations,
        refusal_reason=refusal_reason,
        retrieved_chunk_count=len(retrieved),
    )
