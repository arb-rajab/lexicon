"""The LLMClient seam (ADR-0001, ADR-0003) — the interface both
AnthropicLLMClient (real) and StubLLMClient (fake) implement.

This is deliberately the same shape as bookslot's PaymentIntentGateway /
FakePaymentIntentGateway split: application code (pipeline/query_pipeline.py)
depends only on this Protocol, never on the concrete provider, so swapping
a real Anthropic key in later (llm/factory.py) is a config change, not a
rewrite. See docs/project-memory/12-session-handoff.md (Session 4) for why
that pattern was reused here.
"""

import uuid
from dataclasses import dataclass, field
from typing import Protocol

from lexicon.retrieval.service import RetrievedChunkContext


class LLMProviderError(Exception):
    """The underlying provider call itself failed — network error, auth
    failure, rate limit, timeout, or (real client only) a response that
    doesn't even parse as the requested schema after the call succeeded at
    the transport level. Distinct from ADR-0003's "verifier response is
    ambiguous" case, which fails closed inside verify() and never raises.

    03-architecture.md's Failure handling: this is what the API layer turns
    into a 502, never into `refusal_reason`.
    """


@dataclass
class GenerationClaim:
    claim_text: str
    chunk_id: uuid.UUID


@dataclass
class GenerationResult:
    self_refused: bool
    answer_text: str | None = None
    claims: list[GenerationClaim] = field(default_factory=list)


@dataclass
class VerificationVerdict:
    entailed: bool
    injection_suspected: bool


class LLMClient(Protocol):
    # "real" (AnthropicLLMClient) or "stub" (StubLLMClient) — read by the
    # pipeline/tests so a stub-tier result is never reported as if it were
    # real evidence. Not part of 05-api-contracts.md's response shape.
    tier: str

    def generate(
        self, question: str, chunks: list[RetrievedChunkContext]
    ) -> GenerationResult: ...

    def verify(self, claim_text: str, passage_text: str) -> VerificationVerdict: ...
