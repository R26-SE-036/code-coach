"""The editor's browser sign-in, at Code Coach's end: one-time handoff codes.

The web app mints a code for the student it has signed in (POST /auth/handoff),
and the VS Code extension redeems it (POST /auth/handoff/redeem) - from outside
the compose network, now that Caddy routes /api/v1 to this service. A code
travels in a URL to a loopback listener, so it has to be single use, short
lived, and good only for a session of the editor's own.

The rate-limit tests are here too, because two of those limits decide whether
sign-in works for a whole class: redeem is called from every student's
machine, and refresh is called by the web server on every student's behalf,
which only stays per-student if the student's address is forwarded.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core import cache as cache_module
from app.core.rate_limit import SlidingWindowLimiter
from app.db.storage import InMemoryStorage
from app.main import create_app

EDITOR = "codeguru-vscode"


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def app(storage):
    # Codes live in one module-level cache; start every test without any.
    auth_routes._handoff_codes._entries.clear()
    return create_app(storage=storage)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client: TestClient, email: str = "student@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Sample Student",
            "email": email,
            "password": "Password123",
            "client_name": "codeguru-web",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def mint(client: TestClient, access_token: str) -> dict:
    response = client.post("/api/v1/auth/handoff", json={"client_name": EDITOR}, headers=bearer(access_token))
    assert response.status_code == 200, response.text
    return response.json()


def redeem(client: TestClient, code: str, **kwargs):
    return client.post("/api/v1/auth/handoff/redeem", json={"code": code}, **kwargs)


def test_minting_a_code_needs_a_signed_in_student(client):
    assert client.post("/api/v1/auth/handoff", json={"client_name": EDITOR}).status_code == 401


def test_a_code_starts_a_session_of_the_editors_own(client):
    browser = register(client)
    minted = mint(client, browser["tokens"]["access_token"])
    assert minted["expires_in"] == 120

    response = redeem(client, minted["code"])

    assert response.status_code == 200, response.text
    editor = response.json()
    assert editor["user"]["email"] == browser["user"]["email"]
    # Its own session under its own client name. Sharing the browser's would
    # share one rotating refresh token, and each client would sign the other out.
    assert editor["auth_session"]["client_name"] == EDITOR
    assert editor["auth_session"]["auth_session_id"] != browser["auth_session"]["auth_session_id"]
    assert editor["tokens"]["refresh_token"] != browser["tokens"]["refresh_token"]

    me = client.get("/api/v1/auth/me", headers=bearer(editor["tokens"]["access_token"]))
    assert me.status_code == 200
    assert me.json()["user"]["user_id"] == browser["user"]["user_id"]


def test_a_code_works_once(client):
    browser = register(client)
    code = mint(client, browser["tokens"]["access_token"])["code"]

    assert redeem(client, code).status_code == 200

    replayed = redeem(client, code)
    assert replayed.status_code == 400
    assert replayed.json()["detail"] == "That sign-in code has already been used or has expired."


def test_a_code_expires_after_two_minutes(client, monkeypatch):
    browser = register(client)
    code = mint(client, browser["tokens"]["access_token"])["code"]

    # Only the cache's clock moves; the app's own timing is left alone.
    later = cache_module.time.monotonic() + 121
    monkeypatch.setattr(cache_module, "time", SimpleNamespace(monotonic=lambda: later))

    assert redeem(client, code).status_code == 400


def test_an_invented_code_is_refused_without_revealing_anything(client):
    response = redeem(client, "x" * 32)

    assert response.status_code == 400
    assert response.json()["detail"] == "That sign-in code has already been used or has expired."


def test_a_deactivated_account_cannot_redeem_a_code_minted_before(client, storage):
    browser = register(client)
    code = mint(client, browser["tokens"]["access_token"])["code"]

    storage.users[browser["user"]["user_id"]]["status"] = "suspended"

    assert redeem(client, code).status_code == 401


def test_signing_the_editor_out_leaves_the_browser_signed_in(client):
    browser = register(client)
    editor = redeem(client, mint(client, browser["tokens"]["access_token"])["code"]).json()

    signed_out = client.post("/api/v1/auth/logout", headers=bearer(editor["tokens"]["access_token"]))
    assert signed_out.status_code == 200

    assert client.get("/api/v1/auth/me", headers=bearer(editor["tokens"]["access_token"])).status_code == 401
    assert client.get("/api/v1/auth/me", headers=bearer(browser["tokens"]["access_token"])).status_code == 200


@pytest.fixture
def strict_client(app):
    app.state.auth_limiter = SlidingWindowLimiter(2, window_seconds=60)
    with TestClient(app) as test_client:
        yield test_client


def test_redeeming_is_limited_per_student_address(strict_client):
    first = {"X-Forwarded-For": "203.0.113.7"}
    second = {"X-Forwarded-For": "198.51.100.9"}

    assert redeem(strict_client, "a" * 32, headers=first).status_code == 400
    assert redeem(strict_client, "b" * 32, headers=first).status_code == 400
    assert redeem(strict_client, "c" * 32, headers=first).status_code == 429

    # Another student's machine has its own allowance.
    assert redeem(strict_client, "d" * 32, headers=second).status_code == 400


def test_refresh_is_limited_per_student_when_the_web_server_forwards_the_address(strict_client):
    """The web server refreshes on behalf of every student. Without the student's
    address it is one client, and the platform's third refresh in a minute here
    (the tenth in production) would be refused - signing that student out."""

    def refresh(address: str):
        return strict_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not-a-real-refresh-token"},
            headers={"X-Forwarded-For": address},
        )

    assert refresh("203.0.113.7").status_code != 429
    assert refresh("203.0.113.7").status_code != 429
    assert refresh("203.0.113.7").status_code == 429

    assert refresh("198.51.100.9").status_code != 429
