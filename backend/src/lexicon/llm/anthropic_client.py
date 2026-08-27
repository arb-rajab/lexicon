"""Real LLM client (ADR-0001, ADR-0003) — the StripePaymentIntentGateway
counterpart in bookslot's pattern: this is the implementation that talks to
the actual Anthropic API. Written against the documented current SDK
surface (client.messages.parse with output_format, Anthropic Python SDK
1.x), but **not exercised against a live API in this environment** — no
ANTHROPIC_API_KEY exists here as of Session 4. See docs/project-memory/
12-session-handoff.md for the credential situation and what that does and
does not prove about this file's correctness.
"""

import uuid

import anthropic

from lexicon.llm.base import (
    GenerationClaim,
    GenerationResult,
    LLMProviderError,
    VerificationVerdict,
)
from lexicon.llm.prompts import (
    GENERATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    build_generation_user_content,
    build_verification_user_content,
)
from lexicon.llm.schemas import GenerationOutput, VerificationOutput
from lexicon.retrieval.service import RetrievedChunkContext


class AnthropicLLMClient:
    tier = "real"

    def __init__(self, api_key: str, generation_model: str, verification_model: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._generation_model = generation_model
        self._verification_model = verification_model

    def generate(self, question: str, chunks: list[RetrievedChunkContext]) -> GenerationResult:
        try:
            response = self._client.messages.parse(
                model=self._generation_model,
                max_tokens=2048,
                system=GENERATION_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": build_generation_user_content(question, chunks)}
                ],
                output_format=GenerationOutput,
            )
            parsed = response.parsed_output
        except anthropic.APIError as exc:
            raise LLMProviderError(f"generation call failed: {exc}") from exc
        except (ValueError, TypeError) as exc:
            # Response returned but did not validate against GenerationOutput —
            # unlike verify() below, generation has no ADR-mandated fail-
            # closed-to-refusal behavior for this case, so it is treated the
            # same as a provider-call failure (03-architecture.md: fails
            # closed as an operational error, never a silent guess).
            raise LLMProviderError(f"generation response did not parse: {exc}") from exc

        if parsed is None:
            raise LLMProviderError("generation call returned no parsed output (e.g. model refusal)")

        if parsed.self_refused:
            return GenerationResult(self_refused=True, answer_text=None, claims=[])

        return GenerationResult(
            self_refused=False,
            answer_text=parsed.answer_text,
            claims=[
                GenerationClaim(claim_text=claim.claim_text, chunk_id=uuid.UUID(claim.chunk_id))
                for claim in parsed.claims
            ],
        )

    def verify(self, claim_text: str, passage_text: str) -> VerificationVerdict:
        try:
            response = self._client.messages.parse(
                model=self._verification_model,
                max_tokens=256,
                system=VERIFICATION_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": build_verification_user_content(claim_text, passage_text),
                    }
                ],
                output_format=VerificationOutput,
            )
        except anthropic.APIError as exc:
            # A genuine provider-call failure (network, auth, rate limit,
            # timeout) — 03-architecture.md's fail-closed rule for provider
            # outages maps this to a 502 upstream, never to `entailed=False`
            # disguised as a normal refusal. Distinct from the except block
            # below, which is ADR-0003 item 4's fail-closed-on-ambiguity.
            raise LLMProviderError(f"verification call failed: {exc}") from exc
        except (ValueError, TypeError):
            # ADR-0003 item 4: the call succeeded but the response could not
            # be parsed/validated against VerificationOutput — fail closed,
            # not raised, exactly like an unparseable-but-technically-
            # successful response.
            return VerificationVerdict(entailed=False, injection_suspected=False)

        parsed = response.parsed_output
        if parsed is None:
            # No structured output at all (e.g. a model-level safety
            # refusal, stop_reason="refusal") — same fail-closed rule.
            return VerificationVerdict(entailed=False, injection_suspected=False)

        return VerificationVerdict(
            entailed=parsed.entailed, injection_suspected=parsed.injection_suspected
        )
