"""Exercises the pipeline's refusal_reason decision logic (FR-009/FR-010,
US-004, 05-api-contracts.md) against a fully-controllable fake LLM client —
deterministic in a way the real stub's heuristic isn't, so each of the
three refusal paths plus the happy path is tested in isolation from
retrieval/embedding behavior.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from lexicon.db import models
from lexicon.llm.base import (
    GenerationClaim,
    GenerationResult,
    LLMProviderError,
    VerificationVerdict,
)
from lexicon.pipeline.query_pipeline import run_query_pipeline
from lexicon.retrieval.service import RetrievedChunkContext
from tests.support.spike_corpus import load_spike_corpus


class _ScriptedLLMClient:
    tier = "stub"

    def __init__(
        self, generation_result: GenerationResult, verdicts: list[VerificationVerdict]
    ) -> None:
        self._generation_result = generation_result
        self._verdicts = iter(verdicts)
        self.generate_calls = 0
        self.verify_calls = 0

    def generate(self, question: str, chunks: list[RetrievedChunkContext]) -> GenerationResult:
        self.generate_calls += 1
        return self._generation_result

    def verify(self, claim_text: str, passage_text: str) -> VerificationVerdict:
        self.verify_calls += 1
        return next(self._verdicts)


class _RaisingLLMClient:
    tier = "stub"

    def generate(self, question: str, chunks: list[RetrievedChunkContext]) -> GenerationResult:
        raise LLMProviderError("simulated provider outage")

    def verify(self, claim_text: str, passage_text: str) -> VerificationVerdict:
        raise AssertionError("verify() should never be reached when generate() raises")


def test_empty_corpus_refuses_with_no_candidates_retrieved(db: Session) -> None:
    corpus = models.Corpus(name="empty")
    db.add(corpus)
    db.commit()

    llm = _ScriptedLLMClient(GenerationResult(self_refused=True), [])
    result = run_query_pipeline(db, llm, corpus.id, "anything?", top_n=5)

    assert result.refusal_reason == "no_candidates_retrieved"
    assert result.answered is False
    assert result.retrieved_chunk_count == 0


def test_generator_self_refusal_short_circuits_before_verification(db: Session) -> None:
    corpus_id = load_spike_corpus(db, filenames=("cors.md",))
    llm = _ScriptedLLMClient(GenerationResult(self_refused=True), [])

    result = run_query_pipeline(db, llm, corpus_id, "What class do I import for CORS?", top_n=3)

    assert result.refusal_reason == "self_refused"
    assert result.answered is False
    assert llm.verify_calls == 0  # ADR-0001: nothing to verify on self-refusal

    log = db.get(models.QueryLog, result.query_log_id)
    assert log is not None
    assert log.self_refused is True
    assert log.final_answered is False


def test_failed_verification_discards_draft_answer_from_the_response(db: Session) -> None:
    corpus_id = load_spike_corpus(db, filenames=("cors.md",))
    chunk_id = _retrieve_top_chunk_id(db, corpus_id, "some question", top_n=3)

    generation = GenerationResult(
        self_refused=False,
        answer_text="A confident but wrong answer.",
        claims=[GenerationClaim(claim_text="a wrong claim", chunk_id=chunk_id)],
    )
    llm = _ScriptedLLMClient(
        generation, [VerificationVerdict(entailed=False, injection_suspected=False)]
    )

    result = run_query_pipeline(db, llm, corpus_id, "some question", top_n=3)

    assert result.refusal_reason == "verification_failed"
    assert result.answered is False
    assert result.answer is None  # FR-009: never shown, even partially
    assert result.citations == []

    # US-005: the draft is still retained in the audit log for traceability,
    # even though it is withheld from the API response above.
    log = db.get(models.QueryLog, result.query_log_id)
    assert log is not None
    assert log.generated_answer == "A confident but wrong answer."
    assert log.final_answered is False


def test_verified_answer_is_returned_with_citations(db: Session) -> None:
    corpus_id = load_spike_corpus(db, filenames=("cors.md",))
    chunk_id = _retrieve_top_chunk_id(db, corpus_id, "some question", top_n=3)

    generation = GenerationResult(
        self_refused=False,
        answer_text="A correct, grounded answer.",
        claims=[GenerationClaim(claim_text="a supported claim", chunk_id=chunk_id)],
    )
    llm = _ScriptedLLMClient(
        generation, [VerificationVerdict(entailed=True, injection_suspected=False)]
    )

    result = run_query_pipeline(db, llm, corpus_id, "some question", top_n=3)

    assert result.answered is True
    assert result.refusal_reason is None
    assert result.answer == "A correct, grounded answer."
    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == chunk_id


def test_injection_suspected_forces_refusal_even_when_model_reports_entailed_true(
    db: Session,
) -> None:
    corpus_id = load_spike_corpus(db, filenames=("cors.md",))
    chunk_id = _retrieve_top_chunk_id(db, corpus_id, "some question", top_n=3)

    generation = GenerationResult(
        self_refused=False,
        answer_text="answer",
        claims=[GenerationClaim(claim_text="claim", chunk_id=chunk_id)],
    )
    # The model itself says entailed=True but also flags injection_suspected
    # — ADR-0003 item 3 requires this to still refuse.
    llm = _ScriptedLLMClient(
        generation, [VerificationVerdict(entailed=True, injection_suspected=True)]
    )

    result = run_query_pipeline(db, llm, corpus_id, "some question", top_n=3)

    assert result.answered is False
    assert result.refusal_reason == "verification_failed"

    log = db.get(models.QueryLog, result.query_log_id)
    verdict_row = log.citation_verdicts[0]
    assert verdict_row.injection_suspected is True
    assert verdict_row.entailed is False  # the enforced value, not the model's raw True


def test_provider_error_during_generation_propagates_and_writes_no_query_log(db: Session) -> None:
    corpus_id = load_spike_corpus(db, filenames=("cors.md",))

    with pytest.raises(LLMProviderError):
        run_query_pipeline(db, _RaisingLLMClient(), corpus_id, "some question", top_n=3)

    assert db.query(models.QueryLog).filter_by(corpus_id=corpus_id).count() == 0


def _retrieve_top_chunk_id(
    db: Session, corpus_id: uuid.UUID, question: str, top_n: int
) -> uuid.UUID:
    # Must be a chunk hybrid_retrieve will actually surface for this exact
    # question/top_n — an arbitrary chunk from the corpus isn't guaranteed
    # to be among the retrieved set, and the pipeline's chunk_by_id lookup
    # (query_pipeline.py) would then fall back to retrieved[0] for the
    # citation, silently invalidating a test that assumed otherwise.
    from lexicon.retrieval.service import hybrid_retrieve

    results = hybrid_retrieve(db, corpus_id, question, top_n)
    assert results, "expected at least one retrieved chunk for test setup"
    return results[0].chunk_id
