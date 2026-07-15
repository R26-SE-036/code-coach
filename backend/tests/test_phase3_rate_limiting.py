"""Brute-force protection on the credential endpoints."""

from fastapi.testclient import TestClient

from app.core.rate_limit import SlidingWindowLimiter
from app.db.storage import InMemoryStorage
from app.main import create_app


def _make_client(max_attempts: int) -> TestClient:
    app = create_app(storage=InMemoryStorage())
    # Deterministic strict limiter for the test (conftest raises the default).
    app.state.auth_limiter = SlidingWindowLimiter(max_attempts, window_seconds=60)
    return TestClient(app)


def _login_attempt(client: TestClient) -> int:
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "nobody@example.com", "password": "WrongPass123", "client_name": "test"},
    )
    return response.status_code


def test_login_blocked_after_limit():
    client = _make_client(max_attempts=3)

    for _ in range(3):
        assert _login_attempt(client) == 401  # wrong password, but allowed through

    blocked = client.post(
        "/api/v1/auth/login",
        json={"identifier": "nobody@example.com", "password": "WrongPass123", "client_name": "test"},
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert int(blocked.headers["Retry-After"]) >= 1


def test_limits_are_per_endpoint():
    client = _make_client(max_attempts=3)

    for _ in range(3):
        assert _login_attempt(client) == 401
    assert _login_attempt(client) == 429

    # /register has its own bucket — still reachable after login is blocked.
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rate Limit Test",
            "email": "ratelimit@example.com",
            "password": "GoodPass123!",
            "client_name": "test",
        },
    )
    assert response.status_code == 200


def test_limits_are_per_client_ip():
    client = _make_client(max_attempts=3)

    for _ in range(3):
        assert _login_attempt(client) == 401
    assert _login_attempt(client) == 429

    # A different client IP (X-Forwarded-For, as set by Cloud Run's proxy)
    # has its own bucket.
    other = client.post(
        "/api/v1/auth/login",
        json={"identifier": "nobody@example.com", "password": "WrongPass123", "client_name": "test"},
        headers={"X-Forwarded-For": "203.0.113.7"},
    )
    assert other.status_code == 401
