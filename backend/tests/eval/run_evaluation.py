"""Session 5's CI-gated evaluation harness — the executable proof that the
evaluation *methodology* (not real model quality; see docs/adr/
ADR-0004-real-llm-verification-descoped.md) is sound.

Runs the committed golden dataset (golden_dataset.py) through the real
pipeline (retrieve -> generate -> verify -> decide, pipeline/
query_pipeline.py) via whichever LLM tier llm.factory.get_llm_client()
selects — the exact same seam the application and
tests/test_proof_session1_oauth2_case.py already use. Prints a report that
states, unmissably and in the harness's own output (not only in this
docstring), which tier produced the numbers below and what that does and
does not prove. See "THE SWAP POINT" below for exactly what changes the
moment a real ANTHROPIC_API_KEY exists.

THE SWAP POINT: this module never imports StubLLMClient or AnthropicLLMClient
directly for execution — only `from lexicon.llm.factory import
get_llm_client`, called once, below. `get_llm_client()` reads
Settings.anthropic_api_key (config.py) and returns AnthropicLLMClient if set,
StubLLMClient otherwise (llm/factory.py). Setting ANTHROPIC_API_KEY in the
environment before running this script is the ENTIRE change required to
produce real-tier numbers — zero lines of this file, golden_dataset.py, or
metrics.py would need to change. That is what "provider-agnostic" means
here, demonstrated by the absence of a tier-specific import, not merely
claimed.

Run directly: `python -m tests.eval.run_evaluation` (from backend/, with the
same DATABASE_URL/DATABASE_ADMIN_URL env this repo's tests already require —
see tests/conftest.py). Also wired into pytest as
test_evaluation_harness.py::test_evaluation_harness_meets_thresholds, so
`pytest -q` (already a CI step) gates on it too; the standalone script exists
so CI can also print the full report unconditionally, not only on failure.
"""

import sys
from dataclasses import dataclass

from sqlalchemy.orm import Session

from lexicon.llm.base import LLMClient
from lexicon.llm.factory import get_llm_client
from lexicon.pipeline.query_pipeline import QueryPipelineResult, run_query_pipeline
from lexicon.retrieval.service import RetrievedChunkContext, hybrid_retrieve
from tests.eval import metrics
from tests.eval.golden_dataset import GOLDEN_DATASET, GoldenCase
from tests.support.tier_caveat import render_tier_caveat

# Recall@k uses top_n=3 to match the existing NFR-001 baseline convention
# (tests/test_ingestion_and_retrieval.py) so this number is directly
# comparable to that already-real measurement. The full pipeline run uses
# Settings.top_n_chunks's default (5) — the same top_n the application
# actually uses in production, since that's what refusal-correctness and
# citation-accuracy are meant to reflect.
RECALL_K = 3
PIPELINE_TOP_N = 5

# --- CI-gate thresholds ---
# Real, measured numbers from an actual run against the stub tier, 2026-08-27
# (docs/project-memory/12-session-handoff.md's Session 5 entry records this
# exact run). Retrieval recall@k is a real quality floor (retrieval never
# calls an LLM provider, ADR-0004 doesn't touch it) — measured 9/9 (100%).
#
# The refusal-correctness and citation-accuracy thresholds are NOT quality
# targets — they are regression floors set AT the measured stub-tier
# baseline itself, with zero slack, so a future change that makes this
# harness disagree with what StubLLMClient's documented heuristic previously
# did fails CI immediately, whether that change is a real pipeline
# regression or an accidental change to this dataset's own expectations.
# Measured baseline, this run:
#   refusal-correctness: 11/16 (68.75%) — mismatches on
#     legit-websocket-broadcast, legit-dependencies-shared (the stub's
#     overlap heuristic false-negatived two genuinely correct queries) and
#     adv-celery-redis-background-jobs, adv-middleware-rate-limiting,
#     adv-cors-per-role-headers (the stub false-positived three adjacent-
#     but-wrong queries whose passages happen to share >=50% of the
#     question's content words without actually answering it — the exact
#     failure shape Session 1 Finding 2 predicts, now demonstrated across
#     three different corpus documents, not only the canonical OAuth2 case).
#   citation-accuracy: 7/10 (70%), of the 10 cases the stub actually
#     answered — the 3 adjacent-wrong false-positives above account for
#     every mismatch (any citation on a case with no correct document is
#     inaccurate by construction); all 7 answered LEGITIMATE cases cited
#     their correct source document.
# Neither number says anything about real verification quality (ADR-0004) —
# both say the harness correctly and reproducibly detects this exact,
# already-known heuristic behavior, and will keep detecting it.
RECALL_AT_K_THRESHOLD = 1.0
REFUSAL_CORRECTNESS_THRESHOLD = 11 / 16
CITATION_ACCURACY_THRESHOLD = 7 / 10

_BANNER = "=" * 78


@dataclass
class EvaluationReport:
    tier: str
    recall: metrics.RecallAtKResult
    refusal: metrics.RefusalCorrectnessResult
    citation: metrics.CitationAccuracyResult

    @property
    def passed(self) -> bool:
        return (
            self.recall.recall >= RECALL_AT_K_THRESHOLD
            and self.refusal.rate >= REFUSAL_CORRECTNESS_THRESHOLD
            and self.citation.rate >= CITATION_ACCURACY_THRESHOLD
        )

    def render(self) -> str:
        lines = [
            render_tier_caveat(self.tier),
            "Session 5 evaluation harness — lexicon (docs/adr/ADR-0004)",
            f"Golden dataset: {len(GOLDEN_DATASET)} cases "
            f"({self.recall.total} legitimate, "
            f"{len(GOLDEN_DATASET) - self.recall.total} adversarial/out-of-corpus)",
            "",
            f"retrieval recall@{RECALL_K}:     "
            f"{self.recall.hits}/{self.recall.total} = {self.recall.recall:.0%}  "
            f"(threshold {RECALL_AT_K_THRESHOLD:.0%}) "
            f"{'PASS' if self.recall.recall >= RECALL_AT_K_THRESHOLD else 'FAIL'}"
            "  [real for any tier — no LLM call in retrieval]",
        ]
        if self.recall.misses:
            lines.append(f"  misses: {self.recall.misses}")
        lines += [
            f"refusal-correctness:      "
            f"{self.refusal.correct}/{self.refusal.total} = {self.refusal.rate:.0%}  "
            f"(threshold {REFUSAL_CORRECTNESS_THRESHOLD:.0%}) "
            f"{'PASS' if self.refusal.rate >= REFUSAL_CORRECTNESS_THRESHOLD else 'FAIL'}"
            f"  [{self.tier}-tier self-check]",
        ]
        if self.refusal.mismatches:
            lines.append(f"  mismatches: {self.refusal.mismatches}")
        lines += [
            f"citation-accuracy:        "
            f"{self.citation.correct}/{self.citation.total} = {self.citation.rate:.0%}  "
            f"(threshold {CITATION_ACCURACY_THRESHOLD:.0%}) "
            f"{'PASS' if self.citation.rate >= CITATION_ACCURACY_THRESHOLD else 'FAIL'}"
            f"  [{self.tier}-tier self-check, of {self.citation.total} answered cases]",
        ]
        if self.citation.mismatches:
            lines.append(f"  mismatches: {self.citation.mismatches}")
        lines += [
            "",
            f"OVERALL: {'PASS' if self.passed else 'FAIL'}",
            _BANNER,
        ]
        return "\n".join(lines)


def run_evaluation(db: Session, llm: LLMClient | None = None) -> EvaluationReport:
    from tests.support.spike_corpus import load_spike_corpus

    llm = llm or get_llm_client()
    corpus_id = load_spike_corpus(db)

    retrieved_by_case: dict[str, list[RetrievedChunkContext]] = {}
    result_by_case: dict[str, QueryPipelineResult] = {}
    case: GoldenCase
    for case in GOLDEN_DATASET:
        retrieved_by_case[case.id] = hybrid_retrieve(db, corpus_id, case.query, RECALL_K)
        result_by_case[case.id] = run_query_pipeline(
            db, llm, corpus_id, case.query, PIPELINE_TOP_N
        )

    return EvaluationReport(
        tier=llm.tier,
        recall=metrics.recall_at_k(GOLDEN_DATASET, retrieved_by_case),
        refusal=metrics.refusal_correctness(GOLDEN_DATASET, result_by_case),
        citation=metrics.citation_accuracy(GOLDEN_DATASET, result_by_case),
    )


def main() -> int:
    from lexicon.db.session import SessionLocal

    db = SessionLocal()
    try:
        report = run_evaluation(db)
    finally:
        db.close()

    print(report.render())
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
