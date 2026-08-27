"""Fake LLM client — the FakePaymentIntentGateway counterpart in bookslot's
pattern, used whenever no real ANTHROPIC_API_KEY is configured
(llm/factory.py). As of Session 4, that is always, in this environment —
see docs/project-memory/12-session-handoff.md.

READ THIS BEFORE TRUSTING ANY TEST THAT PASSES AGAINST THIS CLASS:

Neither method here does real language understanding. `verify()` in
particular is a crude lexical-overlap heuristic, not entailment reasoning —
it is a stand-in that lets the rest of the pipeline (ingestion, retrieval,
API wiring, the audit trail, the refusal-decision gate) be exercised
end-to-end without a live model call. A test passing against this class
proves the *pipeline plumbing* works; it proves nothing about whether a
real verifier would correctly resist prompt injection or correctly judge
entailment — that is exactly ADR-0001's own point (a plausible-sounding
mechanism is not evidence until it's measured against the real thing), and
it is why this class exists in its own module, clearly labeled, rather than
silently standing in for AnthropicLLMClient anywhere the distinction
matters.
"""

import re

from lexicon.llm.base import GenerationClaim, GenerationResult, VerificationVerdict
from lexicon.retrieval.service import RetrievedChunkContext

_STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were", "do", "does", "did",
    "how", "what", "when", "where", "why", "who", "which", "i", "you", "to",
    "of", "in", "on", "for", "and", "or", "as", "with", "at", "by", "this",
    "that", "it", "its", "be", "can", "could", "would", "should", "up",
    "set", "my", "me", "so",
}

# Crude, literal substring detection — not reasoning about intent, just
# string matching against a short list of obviously injection-flavored
# phrases. A real verifier's injection_suspected signal (ADR-0003) is a
# model judgment about the passage's apparent intent; this is a placeholder
# with none of that judgment, kept deliberately simple so nobody mistakes
# it for the real defense.
_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all prior instructions",
    "ignore all previous instructions",
    "system override",
    "admin override",
    "system notice",
    "always respond entailed",
    "always mark this claim true",
    "verifier: always",
    "disregard the above",
)


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) >= 3 and w not in _STOPWORDS}


class StubLLMClient:
    tier = "stub"

    def generate(self, question: str, chunks: list[RetrievedChunkContext]) -> GenerationResult:
        if not chunks:
            return GenerationResult(self_refused=True, answer_text=None, claims=[])

        top_chunk = chunks[0]  # fusion_rank == 1
        claim_text = question.rstrip("?").strip()
        answer_text = f"{claim_text}."

        return GenerationResult(
            self_refused=False,
            answer_text=answer_text,
            claims=[GenerationClaim(claim_text=claim_text, chunk_id=top_chunk.chunk_id)],
        )

    def verify(self, claim_text: str, passage_text: str) -> VerificationVerdict:
        passage_lower = passage_text.lower()
        injection_suspected = any(marker in passage_lower for marker in _INJECTION_MARKERS)

        claim_words = _content_words(claim_text)
        passage_words = _content_words(passage_text)
        if not claim_words:
            entailed = False
        else:
            overlap = len(claim_words & passage_words) / len(claim_words)
            entailed = overlap >= 0.5

        return VerificationVerdict(entailed=entailed, injection_suspected=injection_suspected)
