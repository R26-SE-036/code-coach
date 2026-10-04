"""Free and Pro: how Pro is granted, how it ends, and what Free may open.

The property everything else rests on: only a PayHere notification that
verifies against our merchant secret - or, with demo mode on, a demo payment -
gives a student Pro. The routes are public, so anything a browser could send
to claim Pro is a hole.
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.storage import InMemoryStorage
from app.main import create_app
from app.services import billing_service as billing

MERCHANT_ID = "1211149"
SECRET = "test-merchant-secret"


@pytest.fixture
def settings(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "payhere_merchant_id", MERCHANT_ID)
    monkeypatch.setattr(s, "payhere_merchant_secret", SECRET)
    monkeypatch.setattr(s, "payhere_app_id", None)
    monkeypatch.setattr(s, "payhere_app_secret", None)
    monkeypatch.setattr(s, "billing_demo_mode", False)
    monkeypatch.setattr(s, "public_web_url", "https://codeguru.example")
    monkeypatch.setattr(s, "pro_price_lkr", 490)
    monkeypatch.setattr(s, "free_lessons_per_month", 3)
    return s


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def client(storage, settings):
    return TestClient(create_app(storage=storage))


def student(client, email="ana@example.com"):
    body = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ana Perera", "email": email, "password": "Password123", "client_name": "test"},
    ).json()
    return {"Authorization": f"Bearer {body['tokens']['access_token']}"}, body["user"]["user_id"]


def signed(fields: dict, secret: str = SECRET) -> dict:
    fields = {"merchant_id": MERCHANT_ID, "payhere_currency": "LKR", **fields}
    return {**fields, "md5sig": billing.notify_signature(fields, secret)}


def notify(client, fields: dict):
    return client.post(
        "/api/v1/billing/payhere/notify",
        content=urlencode(fields),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def checkout(client, headers):
    response = client.post("/api/v1/billing/me/checkout", json={"phone": "0771234567", "city": "Colombo"},
                           headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def tier(client, headers):
    return client.get("/api/v1/billing/me", headers=headers).json()["plan"]["tier"]


# ── Signing ──────────────────────────────────────────────────────────────────


def test_checkout_hash_matches_payhere_formula():
    # strtoupper(md5(merchant_id . order_id . amount . currency . strtoupper(md5(secret))))
    import hashlib

    inner = hashlib.md5(SECRET.encode()).hexdigest().upper()
    expected = hashlib.md5(f"{MERCHANT_ID}ord_1490.00LKR{inner}".encode()).hexdigest().upper()
    assert billing.checkout_hash(MERCHANT_ID, "ord_1", "490.00", "LKR", SECRET) == expected


def test_checkout_is_signed_and_points_back_at_this_site(client, settings):
    headers, user_id = student(client)
    body = checkout(client, headers)
    fields = body["fields"]

    assert body["action_url"] == "https://sandbox.payhere.lk/pay/checkout"
    assert fields["amount"] == "490.00" and fields["currency"] == "LKR"
    assert fields["recurrence"] == "1 Month"
    assert fields["notify_url"] == "https://codeguru.example/api/v1/billing/payhere/notify"
    assert fields["hash"] == billing.checkout_hash(MERCHANT_ID, fields["order_id"], "490.00", "LKR", SECRET)
    # The secret itself never leaves the server.
    assert SECRET not in str(body)


# ── Getting Pro ──────────────────────────────────────────────────────────────


def test_everyone_starts_on_free(client):
    headers, _ = student(client)
    assert tier(client, headers) == "free"


def test_a_verified_payment_gives_pro_for_a_month(client):
    headers, _ = student(client)
    order = checkout(client, headers)["order_id"]

    response = notify(client, signed({"order_id": order, "payment_id": "320025", "payhere_amount": "490.00",
                                      "status_code": "2", "subscription_id": "420001",
                                      "message_type": "AUTHORIZATION_SUCCESS"}))

    assert response.status_code == 200 and response.text == "activated"
    plan = client.get("/api/v1/billing/me", headers=headers).json()["plan"]
    assert plan["tier"] == "pro" and plan["provider"] == "payhere"


def test_a_forged_notification_does_not_give_pro(client):
    headers, _ = student(client)
    order = checkout(client, headers)["order_id"]

    response = notify(client, signed({"order_id": order, "payment_id": "1", "payhere_amount": "490.00",
                                      "status_code": "2"}, secret="a-guessed-secret"))

    assert response.text == "bad_signature"
    assert tier(client, headers) == "free"


def test_a_notification_for_an_order_we_never_made_is_ignored(client):
    headers, _ = student(client)
    response = notify(client, signed({"order_id": "ord_made_up", "payment_id": "1", "payhere_amount": "490.00",
                                      "status_code": "2"}))
    assert response.text == "unknown_order"
    assert tier(client, headers) == "free"


def test_a_failed_payment_leaves_free(client):
    headers, _ = student(client)
    order = checkout(client, headers)["order_id"]
    assert notify(client, signed({"order_id": order, "payment_id": "2", "payhere_amount": "490.00",
                                  "status_code": "-2"})).text == "failed"
    assert tier(client, headers) == "free"


def test_a_retried_notification_does_not_add_a_second_month(client, storage):
    headers, user_id = student(client)
    order = checkout(client, headers)["order_id"]
    fields = signed({"order_id": order, "payment_id": "77", "payhere_amount": "490.00", "status_code": "2"})

    assert notify(client, fields).text == "activated"
    first_end = storage.get_subscription(user_id)["currentPeriodEnd"]
    assert notify(client, fields).text == "duplicate"
    assert storage.get_subscription(user_id)["currentPeriodEnd"] == first_end


def test_a_monthly_renewal_extends_from_the_end_of_the_paid_period(client, storage):
    headers, user_id = student(client)
    order = checkout(client, headers)["order_id"]
    notify(client, signed({"order_id": order, "payment_id": "a", "payhere_amount": "490.00", "status_code": "2",
                           "subscription_id": "420002"}))
    first_end = storage.get_subscription(user_id)["currentPeriodEnd"]

    notify(client, signed({"order_id": order, "payment_id": "b", "payhere_amount": "490.00", "status_code": "2",
                           "subscription_id": "420002", "message_type": "RECURRING_INSTALLMENT_SUCCESS"}))

    assert storage.get_subscription(user_id)["currentPeriodEnd"] == first_end + billing.PERIOD


def test_checkout_is_refused_without_payhere_settings(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "payhere_merchant_secret", None)
    headers, _ = student(client)
    response = client.post("/api/v1/billing/me/checkout", json={"phone": "0771234567", "city": "Colombo"},
                           headers=headers)
    assert response.status_code == 503


# ── Demo mode ────────────────────────────────────────────────────────────────


def test_demo_payment_and_reset_are_refused_unless_demo_mode_is_on(client):
    headers, _ = student(client)
    assert client.post("/api/v1/billing/me/demo-payment", headers=headers).status_code == 403
    assert client.post("/api/v1/billing/me/reset", headers=headers).status_code == 403
    assert tier(client, headers) == "free"


def test_demo_payment_gives_pro_and_reset_takes_it_back(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "billing_demo_mode", True)
    headers, _ = student(client)

    assert client.post("/api/v1/billing/me/demo-payment", headers=headers).json()["plan"]["tier"] == "pro"
    assert client.get("/api/v1/billing/me", headers=headers).json()["payments"][0]["provider"] == "demo"

    client.post("/api/v1/billing/me/reset", headers=headers)
    assert tier(client, headers) == "free"


# ── Cancelling ───────────────────────────────────────────────────────────────


def test_cancel_keeps_pro_until_the_paid_period_ends(storage, settings):
    now = datetime(2026, 10, 4, tzinfo=timezone.utc)
    billing.activate_demo(storage, "u1", now)

    result = billing.cancel(storage, settings, "u1", now)
    plan = billing.plan_view(storage.get_subscription("u1"), now)

    assert result["cancelled"] is True
    assert plan["tier"] == "pro" and plan["cancel_at_period_end"] is True and plan["renews_at"] is None
    assert billing.plan_view(storage.get_subscription("u1"), now + billing.PERIOD + timedelta(seconds=1))["tier"] == "free"


def test_cancel_stops_the_payhere_subscription_when_it_can(storage, settings):
    now = datetime(2026, 10, 4, tzinfo=timezone.utc)
    billing.extend_pro(storage, "u1", "payhere", now, provider_subscription_id="420009")
    asked = []

    result = billing.cancel(storage, settings, "u1", now,
                            provider_cancel=lambda _s, sub_id: asked.append(sub_id) or True)

    assert asked == ["420009"] and result["provider_cancelled"] is True


def test_cancelling_without_pro_is_refused(client):
    headers, _ = student(client)
    assert client.post("/api/v1/billing/me/cancel", headers=headers).status_code == 409


# ── The free lesson quota ────────────────────────────────────────────────────


def test_free_students_get_three_lessons_a_month(client):
    headers, _ = student(client)
    unlock = lambda t: client.post("/api/v1/billing/me/lesson-unlocks", json={"trigger_id": t, "error_type": "E"},
                                   headers=headers)

    assert [unlock(t).status_code for t in ("t1", "t2", "t3")] == [200, 200, 200]
    # Re-opening a lesson already unlocked this month does not use another.
    assert unlock("t1").status_code == 200
    assert unlock("t4").status_code == 402
    assert client.get("/api/v1/billing/me", headers=headers).json()["free_lessons"]["used"] == 3


def test_pro_students_have_no_lesson_limit(storage, settings):
    now = datetime(2026, 10, 4, tzinfo=timezone.utc)
    billing.activate_demo(storage, "u1", now)
    for n in range(10):
        assert billing.unlock_lesson(storage, settings, "u1", f"t{n}", None, None, now)["allowed"]


def test_the_quota_resets_on_the_first_of_the_month_in_sri_lanka(storage, settings):
    # 18:45 UTC on 31 Oct is already 00:15 on 1 Nov in Colombo.
    late = datetime(2026, 10, 31, 18, 45, tzinfo=timezone.utc)
    assert billing.month_key(late) == "2026-11"
    assert billing.month_key(datetime(2026, 10, 31, 18, 0, tzinfo=timezone.utc)) == "2026-10"
