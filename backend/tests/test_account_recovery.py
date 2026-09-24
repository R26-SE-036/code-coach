"""Forgot password, reset password, the recovery email, and per-account limits.

No mail server is involved: `send_mail` is replaced by a recorder, and the link
it would have sent is read back from what it recorded - the same link a student
would click.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.routes import account as account_routes
from app.core.rate_limit import SlidingWindowLimiter
from app.db.storage import InMemoryStorage
from app.main import create_app

PASSWORD = "GoodPass123!"


@pytest.fixture
def outbox(monkeypatch):
    sent: list[dict] = []

    def record(recipients, subject, body, *, link="", html=None):
        sent.append(
            {"to": [r for r in recipients if r], "subject": subject, "link": link, "text": body, "html": html}
        )
        return True

    monkeypatch.setattr(account_routes, "send_mail", record)
    return sent


@pytest.fixture
def client(outbox):
    return TestClient(create_app(storage=InMemoryStorage()))


def register(client, email="ana@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ana Student", "email": email, "password": PASSWORD, "client_name": "test"},
    )
    assert response.status_code == 200
    return response.json()["tokens"]["access_token"]


def login(client, password=PASSWORD, email="ana@example.com"):
    return client.post(
        "/api/v1/auth/login",
        json={"identifier": email, "password": password, "client_name": "test"},
    )


def token_from(link: str) -> str:
    # The token travels in the fragment, never the query string.
    assert "#token=" in link and "?" not in link
    return link.split("#token=", 1)[1]


# ── Forgot and reset ─────────────────────────────────────────────────────


def test_a_reset_link_sets_a_new_password_and_ends_every_session(client, outbox):
    access = register(client)

    answer = client.post("/api/v1/auth/password/forgot", json={"email": "Ana@Example.com"})
    assert answer.status_code == 202
    assert outbox[0]["to"] == ["ana@example.com"]
    assert "/reset-password#token=" in outbox[0]["link"]

    reset = client.post(
        "/api/v1/auth/password/reset",
        json={"token": token_from(outbox[0]["link"]), "new_password": "BrandNew456!"},
    )
    assert reset.status_code == 200

    assert login(client).status_code == 401
    assert login(client, password="BrandNew456!").status_code == 200
    # The session from before the reset no longer works.
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 401


def test_a_reset_link_works_once(client, outbox):
    register(client)
    client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})
    token = token_from(outbox[0]["link"])

    first = client.post("/api/v1/auth/password/reset", json={"token": token, "new_password": "BrandNew456!"})
    again = client.post("/api/v1/auth/password/reset", json={"token": token, "new_password": "Another789!"})

    assert first.status_code == 200
    assert again.status_code == 400


def test_asking_again_retires_the_earlier_link(client, outbox):
    register(client)
    client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})
    client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})

    old = client.post(
        "/api/v1/auth/password/reset",
        json={"token": token_from(outbox[0]["link"]), "new_password": "BrandNew456!"},
    )
    assert old.status_code == 400


def test_an_unknown_email_gets_the_same_answer_and_no_mail(client, outbox):
    register(client)
    known = client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})
    unknown = client.post("/api/v1/auth/password/forgot", json={"email": "nobody@example.com"})

    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    assert len(outbox) == 1


def test_the_form_cannot_flood_an_inbox(client, outbox):
    register(client)
    client.app.state.reset_mail_limiter = SlidingWindowLimiter(3, window_seconds=900)

    answers = [
        client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"}).status_code
        for _ in range(5)
    ]

    assert answers == [202] * 5  # nothing tells the caller they were limited
    assert len(outbox) == 3


# ── Recovery email ───────────────────────────────────────────────────────


def test_a_recovery_email_is_used_only_after_it_is_confirmed(client, outbox):
    access = register(client)
    auth = {"Authorization": f"Bearer {access}"}

    asked = client.put(
        "/api/v1/auth/me/recovery-email",
        json={"recovery_email": "ana.backup@example.org", "password": PASSWORD},
        headers=auth,
    )
    assert asked.status_code == 200
    assert outbox[-1]["to"] == ["ana.backup@example.org"]

    # Not confirmed yet: a reset goes to the sign-in address only.
    client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})
    assert outbox[-1]["to"] == ["ana@example.com"]

    confirmed = client.post(
        "/api/v1/auth/recovery-email/confirm", json={"token": token_from(outbox[0]["link"])}
    )
    assert confirmed.status_code == 200

    client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})
    assert outbox[-1]["to"] == ["ana@example.com", "ana.backup@example.org"]


def test_setting_a_recovery_email_needs_the_current_password(client, outbox):
    access = register(client)
    response = client.put(
        "/api/v1/auth/me/recovery-email",
        json={"recovery_email": "ana.backup@example.org", "password": "WrongPass999"},
        headers={"Authorization": f"Bearer {access}"},
    )
    # 403, not 401: clients treat 401 as signed out.
    assert response.status_code == 403
    assert outbox == []


def test_a_confirmation_link_cannot_be_used_as_a_reset_link(client, outbox):
    access = register(client)
    client.put(
        "/api/v1/auth/me/recovery-email",
        json={"recovery_email": "ana.backup@example.org", "password": PASSWORD},
        headers={"Authorization": f"Bearer {access}"},
    )

    misuse = client.post(
        "/api/v1/auth/password/reset",
        json={"token": token_from(outbox[0]["link"]), "new_password": "Hijacked123!"},
    )
    assert misuse.status_code == 400


def test_the_recovery_email_can_be_removed(client, outbox):
    access = register(client)
    auth = {"Authorization": f"Bearer {access}"}
    client.put(
        "/api/v1/auth/me/recovery-email",
        json={"recovery_email": "ana.backup@example.org", "password": PASSWORD},
        headers=auth,
    )
    client.post("/api/v1/auth/recovery-email/confirm", json={"token": token_from(outbox[0]["link"])})

    removed = client.put(
        "/api/v1/auth/me/recovery-email", json={"recovery_email": None, "password": PASSWORD}, headers=auth
    )
    assert removed.status_code == 200

    client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})
    assert outbox[-1]["to"] == ["ana@example.com"]


# ── Rate limits: per account, and roomy per address ──────────────────────


def test_a_class_on_one_network_can_all_sign_in(client):
    """Twenty students behind one address, all signing in within the minute."""
    client.app.state.auth_limiter = SlidingWindowLimiter(60, window_seconds=60)
    client.app.state.account_limiter = SlidingWindowLimiter(10, window_seconds=60)

    for n in range(20):
        register(client, email=f"student{n}@example.com")
    statuses = [login(client, email=f"student{n}@example.com").status_code for n in range(20)]

    assert statuses == [200] * 20


def test_guessing_one_account_is_still_stopped(client):
    client.app.state.account_limiter = SlidingWindowLimiter(10, window_seconds=60)
    register(client)

    statuses = [login(client, password=f"Guess{n:05d}!").status_code for n in range(11)]

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429
    # A classmate on the same network is unaffected.
    register(client, email="ben@example.com")
    assert login(client, email="ben@example.com").status_code == 200


# ── The emails themselves ────────────────────────────────────────────────


def test_both_emails_are_sent_as_html_with_the_link_in_the_text_too(client, outbox):
    access = register(client)
    client.post("/api/v1/auth/password/forgot", json={"email": "ana@example.com"})
    client.put(
        "/api/v1/auth/me/recovery-email",
        json={"recovery_email": "ana.backup@example.org", "password": PASSWORD},
        headers={"Authorization": f"Bearer {access}"},
    )

    for mail in outbox:
        assert mail["html"] and 'src="cid:logo"' in mail["html"]
        # Mail clients that show only text still get a working link.
        assert mail["link"] in mail["text"]
        assert f'href="{mail["link"]}"' in mail["html"]


def test_a_name_is_escaped_in_the_html():
    from app.services.email_templates import password_reset_email

    email = password_reset_email(
        name='<img src=x onerror="alert(1)">', account_email="a@b.co", link="https://x/#token=t", minutes=30
    )

    assert "<img src=x" not in email.html
    assert "&lt;img src=x" in email.html


def test_the_sent_message_carries_text_html_and_the_logo_inline(monkeypatch):
    from app.services import mailer

    sent = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def starttls(self):
            pass

        def login(self, *args):
            pass

        def send_message(self, message):
            sent.append(message)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    settings = mailer.get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "mail_from", "codeguru@example.com")
    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)

    assert mailer.send_mail(["ana@example.com"], "Subject", "plain body", html="<p>rich</p>")

    parts = {part.get_content_type(): part for part in sent[0].walk()}
    assert "plain body" in parts["text/plain"].get_content()
    assert "rich" in parts["text/html"].get_content()
    assert parts["image/png"]["Content-ID"] == "<logo>"
    assert parts["image/png"].get_content_disposition() == "inline"
