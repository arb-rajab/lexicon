"""The stub-tier-vs-real-quality caveat banner (docs/adr/ADR-0004-real-llm-
verification-descoped.md) — shared by every harness in this repository that
prints a report whose numbers depend on which LLM tier produced them.
Extracted from Session 5's tests/eval/run_evaluation.py (originally
`_tier_caveat`) so Session 6's tests/security/run_adversarial_evaluation.py
reuses the identical wording and structural check instead of duplicating it
— one source of truth for what this project is and is not allowed to claim
about a given tier's output.
"""

_BANNER = "=" * 78


def render_tier_caveat(tier: str) -> str:
    if tier == "stub":
        return (
            f"{_BANNER}\n"
            "TIER: stub  (StubLLMClient — llm/stub_client.py's keyword-overlap\n"
            "             heuristic, NOT entailment reasoning)\n"
            f"{_BANNER}\n"
            "*** THE NUMBERS BELOW DESCRIBE StubLLMClient's DETERMINISTIC        ***\n"
            "*** BEHAVIOR. THEY ARE NOT A MEASUREMENT OF REAL MODEL QUALITY.     ***\n"
            "\n"
            "Per docs/adr/ADR-0004-real-llm-verification-descoped.md: no real LLM\n"
            "provider credential exists in this project's current lifecycle, by\n"
            "deliberate, permanent choice. What this run DOES prove: the\n"
            "evaluation methodology (golden dataset, recall@k, refusal-\n"
            "correctness, citation-accuracy scoring) executes for real against the\n"
            "real pipeline and produces a real, reproducible, regression-gated\n"
            "number for a known, documented heuristic. What it does NOT prove:\n"
            "that a real model's entailment reasoning would make the same calls\n"
            "on the adjacent-but-wrong cases below — that is this project's\n"
            "central, original differentiating claim, and it is permanently\n"
            "unprovable in this environment (ADR-0004). If ANTHROPIC_API_KEY is\n"
            "ever set, this exact harness produces real-tier evidence with ZERO\n"
            "code changes — see tests/eval/run_evaluation.py's \"THE SWAP POINT\"\n"
            "docstring for exactly what changes.\n"
            f"{_BANNER}\n"
        )
    return (
        f"{_BANNER}\n"
        "TIER: real  (AnthropicLLMClient — a live model call)\n"
        f"{_BANNER}\n"
        "*** ADR-0004's premise (no real credential exists) no longer holds in  ***\n"
        "*** this environment. The numbers below ARE real evidence about       ***\n"
        "*** verification/generation quality — every prior recorded run in     ***\n"
        "*** this project's history was stub-tier only; do not compare across  ***\n"
        "*** tiers as if they measured the same thing. Formally revisit        ***\n"
        "*** ADR-0004 (its own Revisit triggers) before treating this as       ***\n"
        "*** settled going forward.                                           ***\n"
        f"{_BANNER}\n"
    )
