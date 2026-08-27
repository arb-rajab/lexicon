"""Pure, tier-agnostic metric computations for Session 5's evaluation
harness (test_evaluation_harness.py). These functions score whatever the
real pipeline actually returned against tests/eval/golden_dataset.py's
expectations — they do not know or care which LLM tier produced that
result. The score's *meaning* depends entirely on the tier, which is why
run_evaluation.py stamps that fact into the report these functions feed,
rather than leaving it to be inferred from a bare number (docs/adr/
ADR-0004-real-llm-verification-descoped.md).
"""

from dataclasses import dataclass, field

from lexicon.pipeline.query_pipeline import QueryPipelineResult
from lexicon.retrieval.service import RetrievedChunkContext
from tests.eval.golden_dataset import CaseKind, GoldenCase


@dataclass
class RecallAtKResult:
    hits: int
    total: int
    misses: list[str] = field(default_factory=list)

    @property
    def recall(self) -> float:
        return self.hits / self.total if self.total else 1.0


def recall_at_k(
    cases: list[GoldenCase],
    retrieved_by_case: dict[str, list[RetrievedChunkContext]],
) -> RecallAtKResult:
    """Retrieval recall@k over LEGITIMATE cases only — recall is undefined
    for a query with no correct document (ADJACENT_WRONG/OUT_OF_CORPUS).
    Real for any LLM tier: hybrid_retrieve never calls an LLM provider
    (retrieval/service.py), so this number is unaffected by ADR-0004.
    """
    legit = [c for c in cases if c.kind is CaseKind.LEGITIMATE]
    hits = 0
    misses: list[str] = []
    for case in legit:
        sources = {r.source_filename for r in retrieved_by_case[case.id]}
        if case.expected_source_document in sources:
            hits += 1
        else:
            misses.append(case.id)
    return RecallAtKResult(hits=hits, total=len(legit), misses=misses)


@dataclass
class RefusalCorrectnessResult:
    correct: int
    total: int
    mismatches: list[str] = field(default_factory=list)

    @property
    def rate(self) -> float:
        return self.correct / self.total if self.total else 1.0


def refusal_correctness(
    cases: list[GoldenCase],
    result_by_case: dict[str, QueryPipelineResult],
) -> RefusalCorrectnessResult:
    """Does the pipeline's answered/refused decision match this dataset's
    expected_answered — correctly answering LEGITIMATE cases and correctly
    refusing ADJACENT_WRONG/OUT_OF_CORPUS cases. Whatever tier produced
    result_by_case determines what this number is evidence OF (see module
    docstring) — the comparison itself is real and executed either way.
    """
    correct = 0
    mismatches: list[str] = []
    for case in cases:
        result = result_by_case[case.id]
        if result.answered == case.expected_answered:
            correct += 1
        else:
            mismatches.append(case.id)
    return RefusalCorrectnessResult(correct=correct, total=len(cases), mismatches=mismatches)


@dataclass
class CitationAccuracyResult:
    correct: int
    total: int
    mismatches: list[str] = field(default_factory=list)

    @property
    def rate(self) -> float:
        return self.correct / self.total if self.total else 1.0


def citation_accuracy(
    cases: list[GoldenCase],
    result_by_case: dict[str, QueryPipelineResult],
) -> CitationAccuracyResult:
    """Of the cases the pipeline actually answered, does the returned
    citation correspond to the claim — i.e. does it point at the one
    correct source document (LEGITIMATE), or, for ADJACENT_WRONG/
    OUT_OF_CORPUS cases where no document supports the claim by
    construction, any citation at all is by definition inaccurate. A case
    the pipeline refused is excluded — there is no citation to score.
    """
    answered = [c for c in cases if result_by_case[c.id].answered]
    correct = 0
    mismatches: list[str] = []
    for case in answered:
        cited_sources = {c.source_filename for c in result_by_case[case.id].citations}
        accurate = (
            case.expected_source_document in cited_sources
            if case.kind is CaseKind.LEGITIMATE
            else False
        )
        if accurate:
            correct += 1
        else:
            mismatches.append(case.id)
    return CitationAccuracyResult(correct=correct, total=len(answered), mismatches=mismatches)
