"""THE non-negotiable proof test — ADR-0001's Consequences section:

  "When Session 5 builds the evaluation harness, its FIRST required test
  case must be the exact failure mode this ADR exists to prevent: feed the
  verifier a wrong-but-topically-adjacent claim (ideally reusing Session 1's
  actual 0.701-scoring OAuth2/JWT case, or an equivalent) and confirm it
  correctly flags the claim as NOT grounded — not merely confirming the
  happy path where a genuinely correct, well-supported claim passes."

This is NOT Session 5's full evaluation harness (a golden query set, a
false-refusal-rate measurement, etc.) — it is the one sanity check that
must exist the moment the verifier is first built, so the core safety
mechanism this repository exists to prove is never shipped even briefly
unverified. Reproduces Session 1's actual query and corpus through the
real ingestion -> retrieval -> generation -> verification -> decide
pipeline (docs/spikes/session1-hybrid-retrieval/RESULTS.md Finding 2: this
exact query scored 0.701 top vector similarity — inside the 0.706-0.848
range of genuinely correct retrievals, and NOT separable by similarity
alone).

READ THIS BEFORE TRUSTING THIS TEST'S RESULT:

Whether this test's assertion holds against `lexicon.llm.stub_client.
StubLLMClient` (the tier active in this environment as of Session 4 — no
ANTHROPIC_API_KEY exists here, see docs/project-memory/12-session-
handoff.md) is NOT evidence that ADR-0001's verification mechanism works.
The stub's verify() is a crude keyword-overlap heuristic, not entailment
reasoning (llm/stub_client.py's own module docstring). A pass here proves
the pipeline WIRING is correct end-to-end — ingestion, retrieval,
generation, verification, and the refusal-decision gate all executed and
reached a terminal decision without the mechanism being bypassed. It does
NOT prove a real LLM verifier would correctly resist this case. That claim
requires `llm.tier == "real"`, i.e. a configured ANTHROPIC_API_KEY, which
this environment does not have. This distinction is asserted explicitly
below, not left for a reader to infer from a green checkmark.
"""

from sqlalchemy.orm import Session

from lexicon.llm.factory import get_llm_client
from lexicon.pipeline.query_pipeline import run_query_pipeline
from tests.support.spike_corpus import load_spike_corpus

# Verbatim from docs/spikes/session1-hybrid-retrieval/spike.py's TEST_QUERIES
# — the "adjacent-but-absent" negative control, Finding 2's central case.
OAUTH2_GOOGLE_QUERY = "How do I set up 'Sign in with Google' as an OAuth2 identity provider?"


def test_session1_oauth2_adjacent_case_is_flagged_not_grounded(db: Session) -> None:
    corpus_id = load_spike_corpus(db)  # the real, full 8-document spike corpus
    llm = get_llm_client()

    result = run_query_pipeline(db, llm, corpus_id, OAUTH2_GOOGLE_QUERY, top_n=5)

    # Retrieval must actually surface something — this is what makes the
    # case dangerous in the first place (Finding 2: a topically-adjacent
    # chunk scores inside the range of genuinely correct answers, so
    # similarity-based refusal would confidently hand it to generation).
    # If nothing were retrieved, the pipeline would short-circuit to
    # no_candidates_retrieved and this test would not be exercising
    # ADR-0001's actual mechanism at all.
    assert result.retrieved_chunk_count > 0, (
        "expected retrieval to surface at least one topically-adjacent chunk "
        "(spike Finding 2's 0.701-similarity case) — got zero, so this run "
        "isn't exercising the generate/verify pipeline the ADR is about"
    )

    if llm.tier == "stub":
        # WIRING-ONLY EVIDENCE — see module docstring. We assert only that
        # the pipeline reached a well-formed terminal decision without
        # crashing or silently bypassing the gate (an answered=True result
        # with zero citations, or a refusal with no refusal_reason set,
        # would both indicate a wiring bug, independent of whether the
        # heuristic's judgment itself was "right").
        assert result.answered is (len(result.citations) > 0)
        if not result.answered:
            assert result.refusal_reason in ("self_refused", "verification_failed")
        return

    # Reached only with llm.tier == "real", i.e. a configured
    # ANTHROPIC_API_KEY — this is the actual evidence ADR-0001's
    # Consequences section requires and that this environment cannot
    # produce today.
    assert result.answered is False
    assert result.refusal_reason in ("self_refused", "verification_failed")
