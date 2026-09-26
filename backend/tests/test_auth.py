"""ADR-0005 regression coverage — the real auth boundary.

Before this session, `lexicon.api.auth.get_caller` trusted whatever
`X-User-Id` value a caller supplied directly, with no verification of any
kind. Every corpus-ownership check downstream of it (`lexicon.api.
ownership`, T-04) was real, correct authorisation logic — but it was being
fed an attacker-controlled identity. Concretely, against the code as it
existed before this session:

    requests.get(f"{base_url}/api/v1/corpora/{victim_corpus_id}",
                 headers={"X-User-Id": "victim"})

...returned the victim's corpus detail to anyone, full stop — no
credential, no session, nothing but a guessed or known username string.
This file proves that specific request now fails (`test_x_user_id_header_
alone_no_longer_authenticates_anyone`, and the fuller version in
`test_corpus_authorization.py`'s `test_forged_x_user_id_header_no_longer_
grants_access`), and that the real replacement — password login issuing a
verified session token — actually works end-to-end.
"""

import time

import jwt
from fastapi.testclient import TestClient

from lexicon.config import get_settings
from lexicon.main import app
from lexicon.security.tokens import issue_access_token

client = TestClient(app)


# --- The vulnerability itself: proven closed --------------------------------


def test_x_user_id_header_alone_no_longer_authenticates_anyone(db) -> None:
    """THE regression test for the reported vulnerability. Pre-fix, this
    exact request — no password, no token, just a claimed identity in a
    client-controlled header — was indistinguishable from a real
    authenticated request by `victim`. Post-fix, X-User-Id is never read by
    this application at all; the request must be rejected as
    unauthenticated, not merely as "wrong identity."
    """
    resp = client.post(
        "/api/v1/corpora",
        json={"name": "should-never-be-created"},
        headers={"X-User-Id": "victim"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


def test_no_authorization_header_is_unauthenticated(db) -> None:
    resp = client.get("/api/v1/corpora")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


def test_malformed_authorization_header_is_unauthenticated(db) -> None:
    for bad_header in ("not-a-bearer-token", "Bearer", "Basic dXNlcjpwYXNz"):
        resp = client.get("/api/v1/corpora", headers={"Authorization": bad_header})
        assert resp.status_code == 401, bad_header
        assert resp.json()["error"]["code"] == "unauthenticated"


# --- Register / login issue real, working tokens ----------------------------


def test_register_then_use_token_round_trips(db) -> None:
    register_resp = client.post(
        "/api/v1/auth/register", json={"username": "alice", "password": "hunter2-but-long-enough"}
    )
    assert register_resp.status_code == 201
    body = register_resp.json()
    assert body["username"] == "alice"
    assert body["token_type"] == "bearer"
    token = body["access_token"]

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "alice"

    create_resp = client.post(
        "/api/v1/corpora",
        json={"name": "alices-corpus"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201


def test_duplicate_registration_is_rejected(db) -> None:
    first = client.post(
        "/api/v1/auth/register", json={"username": "bob", "password": "first-password-1"}
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register", json={"username": "bob", "password": "different-pw-2"}
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "username_taken"


def test_login_with_correct_password_succeeds(db) -> None:
    client.post(
        "/api/v1/auth/register", json={"username": "carol", "password": "carols-real-password"}
    )

    login_resp = client.post(
        "/api/v1/auth/login", json={"username": "carol", "password": "carols-real-password"}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["username"] == "carol"


def test_login_with_wrong_password_is_rejected(db) -> None:
    client.post(
        "/api/v1/auth/register", json={"username": "dave", "password": "daves-real-password"}
    )

    login_resp = client.post(
        "/api/v1/auth/login", json={"username": "dave", "password": "totally-wrong-password"}
    )
    assert login_resp.status_code == 401
    assert login_resp.json()["error"]["code"] == "invalid_credentials"


def test_login_for_unknown_username_gets_same_error_as_wrong_password(db) -> None:
    """Not a distinct error code/message — that would let a caller
    enumerate which usernames are registered."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody-has-ever-registered-this", "password": "whatever"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


def test_password_is_never_returned_or_stored_in_plaintext(db) -> None:
    resp = client.post(
        "/api/v1/auth/register", json={"username": "erin", "password": "erins-secret-password"}
    )
    assert "password" not in resp.text
    assert "erins-secret-password" not in resp.text

    from lexicon.db import models
    from lexicon.db.session import SessionLocal

    session = SessionLocal()
    try:
        user = session.query(models.AppUser).filter_by(username="erin").one()
        assert user.password_hash != "erins-secret-password"
        assert "erins-secret-password" not in user.password_hash
    finally:
        session.close()


# --- Forged / tampered / expired tokens are all rejected --------------------


def test_token_signed_with_wrong_secret_is_rejected(db) -> None:
    settings = get_settings()
    forged = jwt.encode(
        {"sub": "victim", "type": "access", "iat": time.time(), "exp": time.time() + 3600},
        "not-the-real-secret",
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/api/v1/corpora", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


def test_token_with_alg_none_is_rejected(db) -> None:
    """Classic JWT algorithm-confusion attack: a token claiming `alg: none`
    with no signature at all. `verify_access_token` pins `algorithms=` to
    the configured algorithm explicitly, so this must never be accepted."""
    settings = get_settings()
    header = jwt.utils.base64url_encode(b'{"alg":"none","typ":"JWT"}').decode()
    payload = jwt.utils.base64url_encode(
        f'{{"sub":"victim","type":"access","iat":0,"exp":{time.time() + 3600}}}'.encode()
    ).decode()
    forged = f"{header}.{payload}."
    assert settings.jwt_algorithm != "none"

    resp = client.get("/api/v1/corpora", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


def test_expired_token_is_rejected(db) -> None:
    settings = get_settings()
    now = time.time()
    expired = jwt.encode(
        {"sub": "someone", "type": "access", "iat": now - 7200, "exp": now - 3600},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/api/v1/corpora", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


def test_token_with_wrong_type_claim_is_rejected(db) -> None:
    settings = get_settings()
    now = time.time()
    wrong_type = jwt.encode(
        {"sub": "someone", "type": "refresh", "iat": now, "exp": now + 3600},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get("/api/v1/corpora", headers={"Authorization": f"Bearer {wrong_type}"})
    assert resp.status_code == 401


def test_a_real_token_for_one_user_does_not_authenticate_as_another(db) -> None:
    """A verified token's `sub` is authoritative and cannot be overridden by
    any other request data (headers, body) — the actual property that
    closes the impersonation vulnerability."""
    settings = get_settings()
    token_for_alice = issue_access_token("alice", settings)

    create_resp = client.post(
        "/api/v1/corpora",
        json={"name": "alices-real-corpus"},
        headers={"Authorization": f"Bearer {token_for_alice}"},
    )
    assert create_resp.status_code == 201
    corpus_id = create_resp.json()["id"]

    token_for_mallory = issue_access_token("mallory", settings)
    # Mallory's own valid token, plus a forged X-User-Id claiming Alice —
    # the header must be completely ignored.
    resp = client.get(
        f"/api/v1/corpora/{corpus_id}",
        headers={"Authorization": f"Bearer {token_for_mallory}", "X-User-Id": "alice"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


# --- T-12: rate-limited login -----------------------------------------------


def test_login_is_rate_limited_after_repeated_failures(db, monkeypatch) -> None:
    from lexicon.config import Settings

    test_settings = Settings(login_rate_limit_per_5_minutes=3)
    monkeypatch.setattr("lexicon.api.auth_routes.get_settings", lambda: test_settings)

    client.post(
        "/api/v1/auth/register", json={"username": "frank", "password": "franks-real-password"}
    )

    for _ in range(3):
        resp = client.post(
            "/api/v1/auth/login", json={"username": "frank", "password": "wrong-password-guess"}
        )
        assert resp.status_code == 401

    limited_resp = client.post(
        "/api/v1/auth/login", json={"username": "frank", "password": "wrong-password-guess"}
    )
    assert limited_resp.status_code == 429
    assert limited_resp.json()["error"]["code"] == "rate_limited"
    assert int(limited_resp.headers["retry-after"]) > 0
