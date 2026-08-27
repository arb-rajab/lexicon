"""End-to-end API wiring test — corpus create -> document upload -> query
-> query-log detail, through the real FastAPI app and real Postgres, with
the stub LLM tier (no ANTHROPIC_API_KEY in the test environment, matching
conftest.py's deliberate non-override of that).
"""

from pathlib import Path

from fastapi.testclient import TestClient

from lexicon.main import app

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[2]
CORS_MD = REPO_ROOT / "docs" / "spikes" / "session1-hybrid-retrieval" / "corpus" / "cors.md"


def test_full_ingest_and_query_flow_through_the_api(db) -> None:
    create_resp = client.post("/api/v1/corpora", json={"name": "api-flow-test"})
    assert create_resp.status_code == 201
    corpus_id = create_resp.json()["id"]

    with open(CORS_MD, "rb") as f:
        upload_resp = client.post(
            f"/api/v1/corpora/{corpus_id}/documents",
            files={"file": ("cors.md", f, "text/markdown")},
        )
    assert upload_resp.status_code == 201
    assert upload_resp.json()["status"] == "ready"

    docs_resp = client.get(f"/api/v1/corpora/{corpus_id}/documents")
    assert docs_resp.status_code == 200
    assert docs_resp.json()[0]["chunk_count"] > 0

    query_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query",
        json={"question": "What class do I import to add CORS support in FastAPI?"},
    )
    assert query_resp.status_code == 200
    body = query_resp.json()
    assert body["retrieved_chunk_count"] > 0
    # Answered or refused — both are valid stub-tier outcomes depending on
    # the crude keyword-overlap heuristic; what matters here is that the
    # response shape and refusal_reason contract hold either way.
    assert body["answered"] in (True, False)
    if body["answered"]:
        assert body["refusal_reason"] is None
        assert len(body["citations"]) >= 1
    else:
        assert body["refusal_reason"] in ("self_refused", "verification_failed")

    detail_resp = client.get(f"/api/v1/corpora/{corpus_id}/query-logs/{body['query_log_id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["query_text"] == "What class do I import to add CORS support in FastAPI?"
    assert len(detail["retrieved_chunks"]) == body["retrieved_chunk_count"]


def test_unsupported_document_type_returns_415(db) -> None:
    create_resp = client.post("/api/v1/corpora", json={"name": "bad-upload-test"})
    corpus_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/corpora/{corpus_id}/documents",
        files={"file": ("scan.pdf", b"%PDF-1.4 not a real pdf", "application/pdf")},
    )
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "unsupported_document_type"


def test_query_against_unknown_corpus_returns_404(db) -> None:
    resp = client.post(
        "/api/v1/corpora/00000000-0000-0000-0000-000000000000/query",
        json={"question": "anything?"},
    )
    assert resp.status_code == 404


def test_question_over_length_limit_returns_422(db) -> None:
    create_resp = client.post("/api/v1/corpora", json={"name": "length-test"})
    corpus_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query",
        json={"question": "x" * 5000},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "question_too_long"
