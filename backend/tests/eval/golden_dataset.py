"""The committed golden dataset — Session 5's evaluation-methodology proof
artifact (docs/adr/ADR-0004-real-llm-verification-descoped.md; docs/
project-memory/12-session-handoff.md).

READ docs/adr/ADR-0004 BEFORE INTERPRETING ANY NUMBER PRODUCED FROM THIS
FILE. This dataset is executed against the real pipeline
(pipeline/query_pipeline.py) via whatever LLM tier llm.factory.get_llm_client()
selects. In this environment that is always StubLLMClient (llm/stub_client.py
— a keyword-overlap heuristic, not entailment reasoning). A case "passing"
here means the pipeline's decision matched this file's expected_answered
value for whichever tier actually ran — for the stub tier, that is a
methodology self-check (does the harness correctly detect and score a known,
deterministic heuristic's behavior), never evidence that a real verifier
would make the same call. See eval/metrics.py and
tests/test_evaluation_harness.py for where that distinction is enforced in
the harness's own output, not just here in a docstring.

Dataset design, against the real Session 1 spike corpus (docs/spikes/
session1-hybrid-retrieval/corpus/, 8 source documents):

- LEGITIMATE cases: the query is genuinely answerable from one specific
  source document. Reuses the Session 1 spike's own 9 hand-written queries
  (docs/spikes/session1-hybrid-retrieval/spike.py's TEST_QUERIES, the same
  set tests/test_ingestion_and_retrieval.py's NFR-001 regression test
  measures recall@3 against) so this file's retrieval-quality numbers are
  directly comparable to that existing, already-real baseline.
- ADJACENT_WRONG cases: reuse Session 1 Finding 2's exact discovery — a
  query that is topically close enough to score inside the range of
  genuinely correct retrievals, but whose specific claim the corpus does
  not actually support. The canonical case (OAUTH2_GOOGLE, verbatim from
  spike.py) is required by ADR-0001's own Consequences section to be the
  harness's first test case; the rest are freshly authored in the same
  spirit, each against a different corpus document, so this dataset's
  discriminating power isn't tested against only one document's failure
  mode. A dataset made only of easy, clearly-correct or clearly-unrelated
  queries would not actually test whether the harness (or a future real
  verifier) can catch the failure class ADR-0001 exists to prevent — see
  06-security-threat-model.md's Category 4 reasoning for the same principle
  applied to the injection corpus.
- OUT_OF_CORPUS cases: fully unrelated queries, no plausible source
  document at all (Session 1's other negative-control kind — the tungsten
  case, reused verbatim, plus one fresh case in the same spirit).

None of these categories depend on which LLM tier is active except in what
their PASS/FAIL verdict is capable of proving (see module docstring above).
Retrieval recall@k is measured only over LEGITIMATE cases, matching
NFR-001's existing convention (recall is undefined for a query with no
correct document).
"""

from dataclasses import dataclass
from enum import StrEnum


class CaseKind(StrEnum):
    LEGITIMATE = "legitimate"
    ADJACENT_WRONG = "adjacent_wrong"
    OUT_OF_CORPUS = "out_of_corpus"


@dataclass(frozen=True)
class GoldenCase:
    id: str
    query: str
    kind: CaseKind
    # Set only for LEGITIMATE cases — the one source document that actually
    # answers the query. None for ADJACENT_WRONG/OUT_OF_CORPUS: there is no
    # correct document, by construction.
    expected_source_document: str | None
    # What a CORRECT system (real entailment reasoning, ADR-0001) should do.
    # This is the methodology's target, not a prediction of what
    # StubLLMClient will actually produce — see module docstring.
    expected_answered: bool
    rationale: str


GOLDEN_DATASET: list[GoldenCase] = [
    # --- LEGITIMATE (9) — verbatim from the Session 1 spike's scoreable
    # queries, spike.py's TEST_QUERIES / tests/test_ingestion_and_retrieval.py
    # SCOREABLE_QUERIES. ---
    GoldenCase(
        id="legit-cors-class",
        query="What class do I import to add CORS support in FastAPI?",
        kind=CaseKind.LEGITIMATE,
        expected_source_document="cors.md",
        expected_answered=True,
        rationale="cors.md names CORSMiddleware explicitly as the class to import.",
    ),
    GoldenCase(
        id="legit-cors-cookies",
        query="How do I allow cookies to be sent on cross-origin requests?",
        kind=CaseKind.LEGITIMATE,
        expected_source_document="cors.md",
        expected_answered=True,
        rationale="cors.md documents allow_credentials for this exact purpose.",
    ),
    GoldenCase(
        id="legit-background-tasks-after-response",
        query=(
            "How can I run some code after already sending the response back to the client?"
        ),
        kind=CaseKind.LEGITIMATE,
        expected_source_document="background-tasks.md",
        expected_answered=True,
        rationale="background-tasks.md's entire subject is exactly this.",
    ),
    GoldenCase(
        id="legit-sql-session-close",
        query="How do I make sure a database session gets closed after each request?",
        kind=CaseKind.LEGITIMATE,
        expected_source_document="sql-databases.md",
        expected_answered=True,
        rationale="sql-databases.md's yield-based session dependency documents this.",
    ),
    GoldenCase(
        id="legit-oauth2-password-check",
        query="How do I check a plaintext password against a stored hash at login?",
        kind=CaseKind.LEGITIMATE,
        expected_source_document="oauth2-jwt.md",
        expected_answered=True,
        rationale="oauth2-jwt.md's Password hashing section documents verify_password.",
    ),
    GoldenCase(
        id="legit-websocket-broadcast",
        query="How do I broadcast a message to every client connected over a socket?",
        kind=CaseKind.LEGITIMATE,
        expected_source_document="websockets.md",
        expected_answered=True,
        rationale="websockets.md's handling-disconnections example broadcasts to all clients.",
    ),
    GoldenCase(
        id="legit-docker-base-image",
        query="What's the recommended base image for containerizing a FastAPI app?",
        kind=CaseKind.LEGITIMATE,
        expected_source_document="docker.md",
        expected_answered=True,
        rationale="docker.md names the official Python base image explicitly.",
    ),
    GoldenCase(
        id="legit-dependencies-shared",
        query=(
            "How do I share one dependency function across several different path operations?"
        ),
        kind=CaseKind.LEGITIMATE,
        expected_source_document="dependencies.md",
        expected_answered=True,
        rationale="dependencies.md's Annotated shared-dependency section documents this.",
    ),
    GoldenCase(
        id="legit-middleware-custom-header",
        query="How do I add a custom header to every single HTTP response my app sends?",
        kind=CaseKind.LEGITIMATE,
        expected_source_document="middleware.md",
        expected_answered=True,
        rationale="middleware.md's X-Process-Time example documents this exact pattern.",
    ),
    # --- ADJACENT_WRONG (5) — topically close, factually unsupported.
    # Discriminating power test: each targets a different corpus document,
    # not just repeats of the OAuth2/Google shape. ---
    GoldenCase(
        id="adv-oauth2-google-signin",
        query="How do I set up 'Sign in with Google' as an OAuth2 identity provider?",
        kind=CaseKind.ADJACENT_WRONG,
        expected_source_document=None,
        expected_answered=False,
        rationale=(
            "Session 1 Finding 2's canonical case, reused verbatim per ADR-0001's "
            "Consequences section. oauth2-jwt.md covers the OAuth2 password + JWT "
            "flow and mentions Google only once, as an example of 'big authentication "
            "providers' in its Recap — it never documents third-party/social sign-in. "
            "Top vector similarity measured at 0.701 (inside the 0.706-0.848 range "
            "of genuinely correct retrievals) — not separable by similarity alone."
        ),
    ),
    GoldenCase(
        id="adv-celery-redis-background-jobs",
        query="How do I use Celery with Redis to process background jobs reliably at scale?",
        kind=CaseKind.ADJACENT_WRONG,
        expected_source_document=None,
        expected_answered=False,
        rationale=(
            "background-tasks.md's own Caveat section names Celery and Redis "
            "verbatim ('you might benefit from using other bigger tools like "
            "Celery... a message/job queue manager, like RabbitMQ or Redis') but "
            "gives zero setup or usage instructions — it only says such tools exist "
            "as an alternative to BackgroundTasks. Lexically as close to the query "
            "as a document can get without actually answering it, mirroring the "
            "OAuth2/Google case's shape on a different document."
        ),
    ),
    GoldenCase(
        id="adv-kubernetes-hpa",
        query="How do I configure Kubernetes horizontal pod autoscaling for my FastAPI container?",
        kind=CaseKind.ADJACENT_WRONG,
        expected_source_document=None,
        expected_answered=False,
        rationale=(
            "docker.md discusses Kubernetes and container replication at length "
            "(cluster-level replication, load balancers, one-process-per-container) "
            "but never mentions autoscaling or HPA configuration specifically."
        ),
    ),
    GoldenCase(
        id="adv-middleware-rate-limiting",
        query="How do I rate-limit requests per client IP using FastAPI middleware?",
        kind=CaseKind.ADJACENT_WRONG,
        expected_source_document=None,
        expected_answered=False,
        rationale=(
            "middleware.md explains the general middleware mechanism (request/"
            "response interception, the X-Process-Time example) but contains no "
            "rate-limiting, IP-tracking, or throttling content at all."
        ),
    ),
    GoldenCase(
        id="adv-cors-per-role-headers",
        query=(
            "How do I configure CORS to allow specific Authorization header values "
            "per user role?"
        ),
        kind=CaseKind.ADJACENT_WRONG,
        expected_source_document=None,
        expected_answered=False,
        rationale=(
            "cors.md documents allow_headers/allow_credentials as global, "
            "corpus-wide middleware configuration — it has no concept of per-role "
            "header authorization, which is an application-layer concern CORS "
            "middleware doesn't perform."
        ),
    ),
    # --- OUT_OF_CORPUS (2) — fully unrelated, no plausible source at all. ---
    GoldenCase(
        id="ooc-tungsten",
        query="What is the boiling point of tungsten?",
        kind=CaseKind.OUT_OF_CORPUS,
        expected_source_document=None,
        expected_answered=False,
        rationale=(
            "Session 1's other negative control, reused verbatim. Top vector "
            "similarity measured at 0.515 — cleanly separable from every genuinely "
            "correct retrieval, unlike the adjacent-but-wrong case above."
        ),
    ),
    GoldenCase(
        id="ooc-vitamin-d",
        query="What's the recommended vitamin D dosage for infants?",
        kind=CaseKind.OUT_OF_CORPUS,
        expected_source_document=None,
        expected_answered=False,
        rationale="No plausible relationship to a FastAPI documentation corpus at all.",
    ),
]

LEGITIMATE_CASES = [c for c in GOLDEN_DATASET if c.kind is CaseKind.LEGITIMATE]
ADJACENT_WRONG_CASES = [c for c in GOLDEN_DATASET if c.kind is CaseKind.ADJACENT_WRONG]
OUT_OF_CORPUS_CASES = [c for c in GOLDEN_DATASET if c.kind is CaseKind.OUT_OF_CORPUS]
NEGATIVE_CASES = ADJACENT_WRONG_CASES + OUT_OF_CORPUS_CASES
