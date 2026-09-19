"""T-05 regression coverage (06-security-threat-model.md) — the query
endpoint's Redis-backed per-corpus rate limit and daily spend ceiling
(lexicon.api.rate_limit), both enforced in api/query.py *before* the
pipeline would make any real LLM call. Settings are overridden per test
(monkeypatching the `get_settings` name api/query.py actually calls, since
it isn't wired through FastAPI's own Depends(get_settings) and so isn't
reachable via app.dependency_overrides) to keep these tests fast and
independent of the project-wide default thresholds.

The query embedding call (retrieval/service.py's embed_query, real ONNX
inference via fastembed) is stubbed here too — what's under test is the
rate-limit/spend-ceiling gate itself, not retrieval or embedding quality
(those already have real, non-stubbed coverage elsewhere, e.g.
test_ingestion_and_retrieval.py), and stubbing it removes an unrelated,
real-network dependency (fastembed's first-run model download) from a test
suite whose whole point is to run fast and deterministically.
"""

import pytest
from fastapi.testclient import TestClient

from lexicon.config import Settings
from lexicon.main import app

client = TestClient(app)

AUTH_HEADERS = {"X-User-Id": "rate-limit-user"}


@pytest.fixture(autouse=True)
def _stub_query_embedding(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setattr("lexicon.retrieval.service.embed_query", lambda text: [0.0] * 384)


def _create_corpus(name: str) -> str:
    resp = client.post("/api/v1/corpora", json={"name": name}, headers=AUTH_HEADERS)
    assert resp.status_code == 201
    return str(resp.json()["id"])


def test_query_rate_limit_returns_429_with_retry_after(db, monkeypatch) -> None:
    corpus_id = _create_corpus("rate-limit-test")
    test_settings = Settings(query_rate_limit_per_minute=2)
    monkeypatch.setattr("lexicon.api.query.get_settings", lambda: test_settings)

    for _ in range(2):
        resp = client.post(
            f"/api/v1/corpora/{corpus_id}/query",
            json={"question": "anything?"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code in (200, 502)

    limited_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query",
        json={"question": "anything?"},
        headers=AUTH_HEADERS,
    )
    assert limited_resp.status_code == 429
    assert limited_resp.json()["error"]["code"] == "rate_limited"
    assert int(limited_resp.headers["retry-after"]) > 0


def test_query_spend_ceiling_returns_429_once_reached(db, monkeypatch) -> None:
    corpus_id = _create_corpus("spend-ceiling-test")
    # A high rate limit so only the spend ceiling can trip in this test.
    test_settings = Settings(query_rate_limit_per_minute=1000, query_daily_spend_ceiling=2)
    monkeypatch.setattr("lexicon.api.query.get_settings", lambda: test_settings)

    for _ in range(2):
        resp = client.post(
            f"/api/v1/corpora/{corpus_id}/query",
            json={"question": "anything?"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code in (200, 502)

    blocked_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query",
        json={"question": "anything?"},
        headers=AUTH_HEADERS,
    )
    assert blocked_resp.status_code == 429
    assert blocked_resp.json()["error"]["code"] == "spend_ceiling_exceeded"
    assert int(blocked_resp.headers["retry-after"]) > 0


def test_rate_limit_is_scoped_per_corpus(db, monkeypatch) -> None:
    corpus_a = _create_corpus("rate-limit-scope-a")
    corpus_b = _create_corpus("rate-limit-scope-b")
    test_settings = Settings(query_rate_limit_per_minute=1)
    monkeypatch.setattr("lexicon.api.query.get_settings", lambda: test_settings)

    resp_a = client.post(
        f"/api/v1/corpora/{corpus_a}/query", json={"question": "anything?"}, headers=AUTH_HEADERS
    )
    assert resp_a.status_code in (200, 502)

    # Corpus A is now at its limit; corpus B's own counter is untouched.
    resp_a_again = client.post(
        f"/api/v1/corpora/{corpus_a}/query", json={"question": "anything?"}, headers=AUTH_HEADERS
    )
    assert resp_a_again.status_code == 429

    resp_b = client.post(
        f"/api/v1/corpora/{corpus_b}/query", json={"question": "anything?"}, headers=AUTH_HEADERS
    )
    assert resp_b.status_code in (200, 502)
