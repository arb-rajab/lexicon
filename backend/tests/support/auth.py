"""ADR-0005 regression-test helper — every test that needs a caller
identity now has to go through the real register/login endpoints and
present a real, verified bearer token, exactly like a real caller would.
There is deliberately no shortcut back to a raw X-User-Id-style header
here: that shortcut existing in the test suite while it's gone from the
app itself would let a regression in `lexicon.api.auth` go unnoticed.
"""

from fastapi.testclient import TestClient

# Fixed, not randomly generated: readable test output, and Settings.
# login_rate_limit_per_5_minutes only ever sees a handful of calls per
# test run this way, never enough to trip real rate limiting.
_DEFAULT_PASSWORD = "correct-horse-battery-staple"  # noqa: S105


def bearer_headers_for(
    client: TestClient, username: str, password: str = _DEFAULT_PASSWORD
) -> dict[str, str]:
    """Registers `username`, or logs in if a prior call already registered
    it within this same test (calling this twice for the same "owner" to
    span multiple corpora is a legitimate, common test shape — conftest.py's
    autouse _clean_tables fixture only truncates app_user *between* tests,
    not between calls inside one). Returns the real
    `Authorization: Bearer <token>` headers a genuine caller would present.
    """
    resp = client.post("/api/v1/auth/register", json={"username": username, "password": password})
    if resp.status_code == 409:
        resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200, resp.text
    else:
        assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
