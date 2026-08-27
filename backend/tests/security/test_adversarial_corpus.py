"""Wires run_adversarial_evaluation.py into `pytest -q` (ci.yml), the same
way tests/eval/test_evaluation_harness.py wires in Session 5's harness — see
that file and run_adversarial_evaluation.py's own module docstring for why
both a pytest-wired test and a standalone `python -m` entry point exist.
"""

from sqlalchemy.orm import Session

from tests.security.run_adversarial_evaluation import (
    NEGATIVE_CONTROL_FALSE_POSITIVE_BASELINE,
    RETRIEVAL_CORRECTNESS_THRESHOLD,
    STUB_DETECTION_THRESHOLD,
    run_adversarial_evaluation,
)


def test_adversarial_corpus_meets_thresholds(db: Session) -> None:
    report = run_adversarial_evaluation(db)
    rendered = report.render()
    print(rendered)

    if report.tier == "stub":
        assert "NOT A MEASUREMENT OF REAL MODEL QUALITY" in rendered
        assert "ADR-0004" in rendered

    # --- Claim 1: application-layer enforcement, hard invariants, zero
    # slack, any tier. A failure here is a real code regression in
    # pipeline/query_pipeline.py or llm/prompts.py, never a model-quality
    # result — see run_adversarial_evaluation.py's module docstring. ---
    assert report.structural.rate >= 1.0, (
        f"ADR-0003 structural delimiting broke for at least one corpus document: "
        f"{report.structural.failures}"
    )
    assert not report.enforcement.violations, (
        f"ADR-0003 item 3's injection_suspected -> enforced_entailed=False "
        f"invariant was violated by a REAL pipeline run against a REAL "
        f"database row — this is a genuine application-layer regression: "
        f"{report.enforcement.violations}"
    )

    # --- Claim 2: stub-tier self-check regression floors, measured-baseline
    # gates (same pattern as tests/eval/run_evaluation.py) — describe only
    # StubLLMClient's own known, deterministic behavior; see module
    # docstring and ADR-0004 for what this does and does not prove. ---
    assert report.retrieval.rate >= RETRIEVAL_CORRECTNESS_THRESHOLD, (
        f"adversarial-corpus retrieval regressed: {report.retrieval.correct}/"
        f"{report.retrieval.total}, misses: {report.retrieval.misses}"
    )
    assert report.stub_detection.rate >= STUB_DETECTION_THRESHOLD, (
        f"stub marker-detection self-check regressed against the stub's own "
        f"documented heuristic: {report.stub_detection.matched_expected}/"
        f"{report.stub_detection.total}, mismatches: {report.stub_detection.mismatches}"
    )
    assert report.false_positive.rate <= NEGATIVE_CONTROL_FALSE_POSITIVE_BASELINE + 1e-9, (
        f"Category 4 negative-control false-positive rate regressed above the "
        f"measured stub-tier baseline: {report.false_positive.false_positives}/"
        f"{report.false_positive.total}, cases: {report.false_positive.cases}"
    )
