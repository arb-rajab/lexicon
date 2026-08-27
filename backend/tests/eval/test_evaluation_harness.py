"""Wires run_evaluation.py into the existing `pytest -q` CI step (ci.yml) so
the golden-dataset evaluation is gated the same way every other real-
database test in this repo is, in addition to the standalone
`python -m tests.eval.run_evaluation` CI step that prints the full report
unconditionally (see run_evaluation.py's own module docstring for why both
exist).
"""

from sqlalchemy.orm import Session

from tests.eval.run_evaluation import (
    CITATION_ACCURACY_THRESHOLD,
    RECALL_AT_K_THRESHOLD,
    REFUSAL_CORRECTNESS_THRESHOLD,
    run_evaluation,
)


def test_evaluation_harness_meets_thresholds(db: Session) -> None:
    report = run_evaluation(db)
    rendered = report.render()
    # Visible on failure via pytest's default output capture; the dedicated
    # `python -m tests.eval.run_evaluation` CI step (ci.yml) prints this
    # same report unconditionally, including on success.
    print(rendered)

    # Requirement (this session's scope item 4): the stub-tier-vs-real-
    # quality distinction must be visible in the harness's OWN output, not
    # only in surrounding docs — asserted structurally here, not just
    # eyeballed, so a future refactor that accidentally drops the caveat
    # fails this test rather than silently shipping an unlabeled report.
    if report.tier == "stub":
        assert "NOT A MEASUREMENT OF REAL MODEL QUALITY" in rendered
        assert "ADR-0004" in rendered

    assert report.recall.recall >= RECALL_AT_K_THRESHOLD, (
        f"retrieval recall@k regressed: {report.recall.hits}/{report.recall.total}, "
        f"misses: {report.recall.misses}"
    )
    assert report.refusal.rate >= REFUSAL_CORRECTNESS_THRESHOLD, (
        f"refusal-correctness regressed against the {report.tier}-tier baseline: "
        f"{report.refusal.correct}/{report.refusal.total}, "
        f"mismatches: {report.refusal.mismatches}"
    )
    assert report.citation.rate >= CITATION_ACCURACY_THRESHOLD, (
        f"citation-accuracy regressed against the {report.tier}-tier baseline: "
        f"{report.citation.correct}/{report.citation.total}, "
        f"mismatches: {report.citation.mismatches}"
    )
