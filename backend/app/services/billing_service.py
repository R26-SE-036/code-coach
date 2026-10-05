"""Free and Pro: who has Pro, how they get it, how it ends, and what Free may open.

==================== WHERE THIS SITS ====================
Code Coach is the platform's identity provider: Study Guider, the gamification
engine and PairPath all ask it who a student is. So it is also where the
answer to "does this student have Pro?" lives. The web app asks it once per
request (cached briefly) and enforces the answer in its proxy - the only way a
browser reaches the other services - so none of them change.
=========================================================

==================== HOW PRO IS GRANTED ====================
Only two ways, and neither is a browser saying so:

  PayHere   the student pays on PayHere's own page (card details never touch
            this platform). PayHere then calls /billing/payhere/notify server
            to server. That call is believed only if its md5sig - a hash over
            the payment and our merchant secret - checks out, and only for an
            order this service created for that student.
  Demo      a no-card "demo payment", only while BILLING_DEMO_MODE is on: a
            backup for the viva, and for local development, where PayHere
            cannot reach a laptop to send the notification.

/api/v1/* is public (the VS Code extension uses it), which is exactly why
there is no endpoint that simply sets a plan.
============================================================

==================== HOW PRO ENDS ====================
  Cancel     stop renewing. Pro lasts to the end of what was paid for. Undone
             by Resume, unless the recurring charge was already stopped at
             PayHere - then it cannot be restarted from here.
  Downgrade  back to Free now. Renewal is stopped too. No refund: this is a
             student's choice to stop early, and the sandbox moves no money.
  Expiry     the paid period simply runs out; nothing is written.
======================================================

Pure functions first, so the signing, the plan rules and the quota can be
tested without a database; the storage-touching functions follow.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.common import generate_prefixed_id

logger = logging.getLogger(__name__)

CURRENCY = "LKR"
INTERVALS = {"month": timedelta(days=30), "year": timedelta(days=365)}
PERIOD = INTERVALS["month"]
RECURRENCE = {"month": "1 Month", "year": "1 Year"}
# Sri Lanka time, so "this month" turns over at local midnight on the 1st.
LOCAL = timezone(timedelta(hours=5, minutes=30))

PAYHERE_CHECKOUT = {True: "https://sandbox.payhere.lk/pay/checkout", False: "https://www.payhere.lk/pay/checkout"}
PAYHERE_API = {True: "https://sandbox.payhere.lk/merchant/v1", False: "https://www.payhere.lk/merchant/v1"}

# PayHere's status_code values.
PAID, PENDING, CANCELLED, FAILED, CHARGED_BACK = 2, 0, -1, -2, -3


# ── Pure rules ───────────────────────────────────────────────────────────────


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def interval_of(value: Optional[str]) -> str:
    return value if value in INTERVALS else "month"


def price_for(settings: Any, interval: str) -> int:
    return settings.pro_yearly_price_lkr if interval == "year" else settings.pro_price_lkr


def is_pro(subscription: Optional[dict[str, Any]], now: datetime) -> bool:
    """Pro while the paid period lasts - including after Cancel, until it ends."""
    if not subscription:
        return False
    end = _aware(subscription.get("currentPeriodEnd"))
    return subscription.get("status") in {"active", "cancelled"} and end is not None and end > now


def plan_view(subscription: Optional[dict[str, Any]], now: datetime) -> dict[str, Any]:
    if not is_pro(subscription, now):
        return {"tier": "free", "status": "free", "provider": None, "interval": None, "renews_at": None,
                "ends_at": None, "cancel_at_period_end": False, "can_resume": False, "started_at": None}
    end = _aware(subscription["currentPeriodEnd"])
    cancelling = bool(subscription.get("cancelAtPeriodEnd"))
    return {
        "tier": "pro",
        "status": "cancelled" if cancelling else "active",
        "provider": subscription.get("provider"),
        "interval": interval_of(subscription.get("interval")),
        "renews_at": None if cancelling else end,
        "ends_at": end,
        "cancel_at_period_end": cancelling,
        # A renewal stopped at PayHere cannot be restarted from here.
        "can_resume": cancelling and not subscription.get("providerCancelled"),
        "started_at": subscription.get("startedAt"),
    }


def month_key(now: datetime) -> str:
    return now.astimezone(LOCAL).strftime("%Y-%m")


def next_month_start(now: datetime) -> datetime:
    """When this month's free lessons come back: midnight on the 1st, Colombo time."""
    local = now.astimezone(LOCAL)
    first = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return (first + timedelta(days=32)).replace(day=1).astimezone(timezone.utc)


def amount_text(amount_lkr: int) -> str:
    """PayHere signs the amount as it is sent: two decimals, no separators."""
    return f"{amount_lkr:.2f}"


def _md5_upper(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest().upper()


def checkout_hash(merchant_id: str, order_id: str, amount: str, currency: str, secret: str) -> str:
    """The hash PayHere requires on a checkout request."""
    return _md5_upper(f"{merchant_id}{order_id}{amount}{currency}{_md5_upper(secret)}")


def notify_signature(fields: dict[str, str], secret: str) -> str:
    """The md5sig PayHere sends with a payment notification, recomputed."""
    return _md5_upper(
        f"{fields.get('merchant_id', '')}{fields.get('order_id', '')}{fields.get('payhere_amount', '')}"
        f"{fields.get('payhere_currency', '')}{fields.get('status_code', '')}{_md5_upper(secret)}"
    )


def signature_valid(fields: dict[str, str], merchant_id: str, secret: str) -> bool:
    given = (fields.get("md5sig") or "").upper()
    return (
        bool(given)
        and fields.get("merchant_id") == merchant_id
        and hmac.compare_digest(given, notify_signature(fields, secret))
    )


def split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "Student").strip().split()
    return parts[0], " ".join(parts[1:]) or parts[0]


def describe(interval: str) -> str:
    return f"Code Guru Pro ({'yearly' if interval == 'year' else 'monthly'})"


# ── Storage-touching operations ──────────────────────────────────────────────


def _event(storage: Any, user_id: str, kind: str, now: datetime, **detail: Any) -> None:
    storage.record_subscription_event({"userId": user_id, "type": kind, "at": now, **detail})


def extend_pro(storage: Any, user_id: str, provider: str, now: datetime,
               provider_subscription_id: Optional[str] = None, interval: str = "month") -> dict[str, Any]:
    """Add one paid period: from the end of the current one, or from now."""
    interval = interval_of(interval)
    existing = storage.get_subscription(user_id)
    renewing = is_pro(existing, now)
    current_end = _aware(existing.get("currentPeriodEnd")) if existing else None
    start = current_end if current_end and current_end > now else now
    document = {
        "userId": user_id,
        "plan": "pro",
        "status": "active",
        "provider": provider,
        "interval": interval,
        "providerSubscriptionId": provider_subscription_id
        or ((existing or {}).get("providerSubscriptionId") if renewing else None),
        "providerCancelled": False,
        "currentPeriodEnd": start + INTERVALS[interval],
        "cancelAtPeriodEnd": False,
        "startedAt": (existing or {}).get("startedAt") if renewing else now,
        "updatedAt": now,
    }
    storage.save_subscription(document)
    _event(storage, user_id, "renewed" if renewing else "upgraded", now, provider=provider, interval=interval)
    return document


def create_checkout(storage: Any, settings: Any, user: dict[str, Any], phone: str, city: str,
                    now: datetime, interval: str = "month") -> dict[str, Any]:
    """The order, and the signed fields the browser posts to PayHere's page."""
    interval = interval_of(interval)
    order_id = generate_prefixed_id("ord")
    amount = amount_text(price_for(settings, interval))
    storage.create_checkout({
        "orderId": order_id,
        "userId": user["userId"],
        "amount": amount,
        "currency": CURRENCY,
        "interval": interval,
        "status": "created",
        "createdAt": now,
    })

    base = settings.public_web_url.rstrip("/")
    first, last = split_name(user.get("fullName", ""))
    fields = {
        "merchant_id": settings.payhere_merchant_id,
        "return_url": f"{base}/pro/return?order={order_id}",
        "cancel_url": f"{base}/pro?cancelled=1",
        # Caddy sends /api/v1/* to Code Coach, so this is reachable from PayHere.
        "notify_url": f"{base}/api/v1/billing/payhere/notify",
        "order_id": order_id,
        "items": describe(interval),
        "currency": CURRENCY,
        "amount": amount,
        "recurrence": RECURRENCE[interval],
        "duration": "Forever",
        "first_name": first,
        "last_name": last,
        "email": user["email"],
        "phone": phone,
        "address": city,
        "city": city,
        "country": "Sri Lanka",
        "custom_1": user["userId"],
        "hash": checkout_hash(settings.payhere_merchant_id, order_id, amount, CURRENCY,
                              settings.payhere_merchant_secret),
    }
    return {"order_id": order_id, "action_url": PAYHERE_CHECKOUT[settings.payhere_sandbox], "fields": fields}


def apply_notification(storage: Any, settings: Any, fields: dict[str, str], now: datetime) -> str:
    """Act on a PayHere notification. Returns what happened, for the log and tests.

    Answers are never errors to PayHere for a notification that is merely not
    ours or already handled: a non-200 makes it retry, and retrying a
    notification that will never verify only fills the log.
    """
    if not (settings.payhere_merchant_id and settings.payhere_merchant_secret):
        return "not_configured"
    if not signature_valid(fields, settings.payhere_merchant_id, settings.payhere_merchant_secret):
        logger.warning("PayHere notification with a bad signature for order %s", fields.get("order_id"))
        return "bad_signature"

    checkout = storage.find_checkout(fields.get("order_id", ""))
    if checkout is None:
        return "unknown_order"
    user_id = checkout["userId"]
    interval = interval_of(checkout.get("interval"))

    try:
        status_code = int(fields.get("status_code", ""))
    except ValueError:
        return "bad_status"
    message_type = fields.get("message_type") or ""
    subscription_id = fields.get("subscription_id") or None

    payment = {
        "paymentId": generate_prefixed_id("pay"),
        "userId": user_id,
        "orderId": checkout["orderId"],
        "provider": "payhere",
        "providerPaymentId": fields.get("payment_id") or None,
        "providerSubscriptionId": subscription_id,
        "description": describe(interval),
        "interval": interval,
        "amount": fields.get("payhere_amount"),
        "currency": fields.get("payhere_currency"),
        "status": {PAID: "paid", PENDING: "pending", CANCELLED: "cancelled",
                   FAILED: "failed", CHARGED_BACK: "charged_back"}.get(status_code, "unknown"),
        "statusCode": status_code,
        "messageType": message_type or None,
        "method": fields.get("method") or None,
        "createdAt": now,
    }
    if not storage.record_payment(payment):
        return "duplicate"

    if message_type == "RECURRING_STOPPED":
        subscription = storage.get_subscription(user_id)
        if subscription:
            subscription.update({"cancelAtPeriodEnd": True, "providerCancelled": True,
                                 "status": "cancelled", "updatedAt": now})
            storage.save_subscription(subscription)
            _event(storage, user_id, "cancelled", now, by="payhere")
        return "stopped"

    if status_code == PAID:
        extend_pro(storage, user_id, "payhere", now, subscription_id, interval)
        storage.update_checkout(checkout["orderId"], {"status": "paid", "paidAt": now})
        return "activated"

    if status_code in {CANCELLED, FAILED}:
        if checkout.get("status") == "created":
            storage.update_checkout(checkout["orderId"], {"status": payment["status"]})
        return payment["status"]

    if status_code == CHARGED_BACK:
        subscription = storage.get_subscription(user_id)
        if subscription:
            subscription.update({"currentPeriodEnd": now, "status": "expired", "updatedAt": now})
            storage.save_subscription(subscription)
            _event(storage, user_id, "downgraded", now, by="chargeback")
        return "charged_back"

    return "pending"


def activate_demo(storage: Any, user_id: str, now: datetime, settings: Any = None,
                  interval: str = "month") -> dict[str, Any]:
    interval = interval_of(interval)
    storage.record_payment({
        "paymentId": generate_prefixed_id("pay"),
        "userId": user_id,
        "orderId": generate_prefixed_id("ord"),
        "provider": "demo",
        "providerPaymentId": None,
        "providerSubscriptionId": None,
        "description": f"{describe(interval)} - demo payment",
        "interval": interval,
        # The price it would have cost, so a receipt reads like one. No money moved.
        "amount": amount_text(price_for(settings, interval)) if settings else None,
        "currency": CURRENCY,
        "status": "paid",
        "statusCode": PAID,
        "messageType": "DEMO",
        "method": "demo",
        "createdAt": now,
    })
    return extend_pro(storage, user_id, "demo", now, interval=interval)


def _payhere_cancel(settings: Any, subscription_id: str) -> bool:
    """Stop the recurring charge at PayHere through its Merchant API."""
    if not (settings.payhere_app_id and settings.payhere_app_secret):
        return False
    api = PAYHERE_API[settings.payhere_sandbox]
    basic = base64.b64encode(f"{settings.payhere_app_id}:{settings.payhere_app_secret}".encode()).decode()
    try:
        token_request = urllib.request.Request(
            f"{api}/oauth/token",
            data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(token_request, timeout=15) as response:
            token = json.loads(response.read().decode())["access_token"]
        cancel_request = urllib.request.Request(
            f"{api}/subscription/cancel",
            data=json.dumps({"subscription_id": subscription_id}).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(cancel_request, timeout=15) as response:
            body = json.loads(response.read().decode() or "{}")
        return body.get("status") in (1, "1", True, "success") or response.status == 200
    except Exception as error:  # the local cancellation stands either way
        logger.warning("PayHere did not confirm cancelling subscription %s: %s", subscription_id, error)
        return False


def _stop_provider_renewal(settings: Any, subscription: dict[str, Any], provider_cancel) -> bool:
    if subscription.get("providerCancelled"):
        return True
    if subscription.get("provider") == "payhere" and subscription.get("providerSubscriptionId"):
        return bool((provider_cancel or _payhere_cancel)(settings, subscription["providerSubscriptionId"]))
    return False


def cancel(storage: Any, settings: Any, user_id: str, now: datetime, provider_cancel=None) -> dict[str, Any]:
    """Stop renewing. Pro lasts until the end of what was paid for."""
    subscription = storage.get_subscription(user_id)
    if not is_pro(subscription, now):
        return {"cancelled": False, "provider_cancelled": False}
    provider_cancelled = _stop_provider_renewal(settings, subscription, provider_cancel)
    subscription.update({"cancelAtPeriodEnd": True, "status": "cancelled",
                         "providerCancelled": provider_cancelled, "updatedAt": now})
    storage.save_subscription(subscription)
    _event(storage, user_id, "cancelled", now, ends_at=subscription["currentPeriodEnd"])
    return {"cancelled": True, "provider_cancelled": provider_cancelled}


def resume(storage: Any, user_id: str, now: datetime) -> bool:
    """Undo Cancel before the period ends - if the charge was not stopped at PayHere."""
    subscription = storage.get_subscription(user_id)
    if not is_pro(subscription, now) or not subscription.get("cancelAtPeriodEnd"):
        return False
    if subscription.get("providerCancelled"):
        return False
    subscription.update({"cancelAtPeriodEnd": False, "status": "active", "updatedAt": now})
    storage.save_subscription(subscription)
    _event(storage, user_id, "resumed", now)
    return True


def downgrade(storage: Any, settings: Any, user_id: str, now: datetime, provider_cancel=None) -> dict[str, Any]:
    """Back to Free now, and no more renewals."""
    subscription = storage.get_subscription(user_id)
    if not is_pro(subscription, now):
        return {"downgraded": False, "provider_cancelled": False}
    provider_cancelled = _stop_provider_renewal(settings, subscription, provider_cancel)
    subscription.update({
        "status": "downgraded",
        "cancelAtPeriodEnd": True,
        "providerCancelled": provider_cancelled,
        "currentPeriodEnd": now,
        "updatedAt": now,
    })
    storage.save_subscription(subscription)
    _event(storage, user_id, "downgraded", now)
    return {"downgraded": True, "provider_cancelled": provider_cancelled}


def reset(storage: Any, user_id: str, now: datetime) -> None:
    """Back to Free, with this month's free lessons restored. Demo mode only."""
    storage.delete_subscription(user_id)
    storage.delete_lesson_unlocks(user_id, month_key(now))
    _event(storage, user_id, "reset", now)


def lesson_usage(storage: Any, settings: Any, user_id: str, now: datetime) -> dict[str, Any]:
    """This month's lessons: every one opened, and those that count against Free."""
    unlocks = storage.list_lesson_unlocks(user_id, month_key(now))
    on_free = [u for u in unlocks if u.get("plan", "free") == "free"]
    return {
        "opened": len(unlocks),
        "used": len(on_free),
        "limit": settings.free_lessons_per_month,
        "resets_at": next_month_start(now),
        "unlocked": on_free,
    }


def unlock_lesson(storage: Any, settings: Any, user_id: str, trigger_id: str, error_type: Optional[str],
                  concept_tag: Optional[str], now: datetime) -> dict[str, Any]:
    """May this student open this lesson? Uses one of Free's monthly lessons if so."""
    limit = settings.free_lessons_per_month
    month = month_key(now)
    record = {"userId": user_id, "month": month, "triggerId": trigger_id,
              "errorType": error_type, "conceptTag": concept_tag, "at": now}

    if is_pro(storage.get_subscription(user_id), now):
        # Recorded for the usage page, never counted against Free.
        storage.add_lesson_unlock({**record, "plan": "pro"})
        return {"allowed": True, "pro": True, "used": None, "limit": None}

    unlocks = storage.list_lesson_unlocks(user_id, month)
    if any(u["triggerId"] == trigger_id for u in unlocks):
        used = sum(1 for u in unlocks if u.get("plan", "free") == "free")
        return {"allowed": True, "pro": False, "used": used, "limit": limit}
    used = sum(1 for u in unlocks if u.get("plan", "free") == "free")
    if used >= limit:
        return {"allowed": False, "pro": False, "used": used, "limit": limit}
    storage.add_lesson_unlock({**record, "plan": "free"})
    return {"allowed": True, "pro": False, "used": used + 1, "limit": limit}
