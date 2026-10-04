"""Subscription routes: the student's plan, upgrading, cancelling, the free quota.

Every route takes the student's bearer token except the PayHere notification,
which is PayHere's server calling ours and is proved by its signature instead -
see app/services/billing_service.py.
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from app.core.common import utcnow
from app.core.config import get_settings
from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.services import billing_service as billing

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

Interval = Literal["month", "year"]


def _payhere_ready(settings: Any) -> bool:
    return bool(settings.payhere_merchant_id and settings.payhere_merchant_secret)


def _payment_view(p: dict) -> dict:
    return {
        "payment_id": p["paymentId"],
        "order_id": p.get("orderId"),
        "description": p.get("description") or billing.describe(p.get("interval") or "month"),
        "interval": p.get("interval"),
        "status": p["status"],
        "provider": p["provider"],
        "provider_payment_id": p.get("providerPaymentId"),
        "method": p.get("method"),
        "amount": p.get("amount"),
        "currency": p.get("currency"),
        "created_at": p["createdAt"],
    }


@router.get("/me")
def my_plan(auth: AuthContext = Depends(get_current_auth), storage: Any = Depends(get_storage)) -> dict:
    settings = get_settings()
    now = utcnow()
    usage = billing.lesson_usage(storage, settings, auth.user_id, now)
    return {
        "plan": billing.plan_view(storage.get_subscription(auth.user_id), now),
        # Kept for clients that read the monthly price alone.
        "price": {"amount": settings.pro_price_lkr, "currency": billing.CURRENCY, "interval": "month"},
        "prices": {
            "month": settings.pro_price_lkr,
            "year": settings.pro_yearly_price_lkr,
            "currency": billing.CURRENCY,
        },
        "free_lessons": {
            "used": usage["used"],
            "limit": usage["limit"],
            "opened": usage["opened"],
            "resets_at": usage["resets_at"],
            # The quiz for a lesson opened this month is part of that lesson.
            "unlocked": [
                {"trigger_id": u["triggerId"], "error_type": u.get("errorType"), "concept_tag": u.get("conceptTag")}
                for u in usage["unlocked"]
            ],
        },
        "payments": [_payment_view(p) for p in storage.list_payments(auth.user_id, limit=24)],
        "events": [
            {"type": e["type"], "at": e["at"], "interval": e.get("interval"), "provider": e.get("provider"),
             "by": e.get("by")}
            for e in storage.list_subscription_events(auth.user_id, limit=20)
        ],
        "checkout": {"payhere": _payhere_ready(settings), "demo": settings.billing_demo_mode,
                     "sandbox": settings.payhere_sandbox},
    }


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    interval: Interval = "month"
    # PayHere requires a phone number and an address with every payment.
    phone: str = Field(min_length=9, max_length=20, pattern=r"^\+?[0-9 ]{9,20}$")
    city: str = Field(min_length=2, max_length=60)


@router.post("/me/checkout")
def start_checkout(payload: CheckoutRequest, auth: AuthContext = Depends(get_current_auth),
                   storage: Any = Depends(get_storage)) -> dict:
    settings = get_settings()
    if not _payhere_ready(settings):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Card payments are not set up on this server.")
    if billing.is_pro(storage.get_subscription(auth.user_id), utcnow()):
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have Pro.")
    return billing.create_checkout(storage, settings, auth.user, payload.phone, payload.city, utcnow(),
                                   payload.interval)


@router.post("/payhere/notify", response_class=PlainTextResponse)
async def payhere_notify(request: Request) -> str:
    """PayHere's server-to-server payment notification (form-encoded).

    Always 200 once it has been read: a refusal makes PayHere retry, and a
    notification that does not verify never will.
    """
    raw = (await request.body()).decode("utf-8", errors="replace")
    fields = {key: values[0] for key, values in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}
    return billing.apply_notification(request.app.state.storage, get_settings(), fields, utcnow())


class DemoPaymentRequest(BaseModel):
    interval: Interval = "month"


@router.post("/me/demo-payment")
def demo_payment(payload: Optional[DemoPaymentRequest] = None, auth: AuthContext = Depends(get_current_auth),
                 storage: Any = Depends(get_storage)) -> dict:
    settings = get_settings()
    if not settings.billing_demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Demo payments are turned off on this server.")
    now = utcnow()
    if billing.is_pro(storage.get_subscription(auth.user_id), now):
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have Pro.")
    billing.activate_demo(storage, auth.user_id, now, settings, (payload or DemoPaymentRequest()).interval)
    return {"plan": billing.plan_view(storage.get_subscription(auth.user_id), now)}


@router.post("/me/cancel")
def cancel_subscription(auth: AuthContext = Depends(get_current_auth), storage: Any = Depends(get_storage)) -> dict:
    """Stop renewing; Pro lasts to the end of what was paid for."""
    now = utcnow()
    result = billing.cancel(storage, get_settings(), auth.user_id, now)
    if not result["cancelled"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "There is no active Pro subscription to cancel.")
    return {**result, "plan": billing.plan_view(storage.get_subscription(auth.user_id), now)}


@router.post("/me/resume")
def resume_subscription(auth: AuthContext = Depends(get_current_auth), storage: Any = Depends(get_storage)) -> dict:
    now = utcnow()
    if not billing.resume(storage, auth.user_id, now):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This subscription cannot be resumed - it is not cancelled, or its renewal was already stopped at "
            "PayHere. Subscribe again once it ends.",
        )
    return {"plan": billing.plan_view(storage.get_subscription(auth.user_id), now)}


@router.post("/me/downgrade")
def downgrade_now(auth: AuthContext = Depends(get_current_auth), storage: Any = Depends(get_storage)) -> dict:
    """Back to Free immediately. Renewal is stopped too; nothing is refunded."""
    now = utcnow()
    result = billing.downgrade(storage, get_settings(), auth.user_id, now)
    if not result["downgraded"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "You are already on Free.")
    return {**result, "plan": billing.plan_view(None, now)}


@router.post("/me/reset")
def reset_to_free(auth: AuthContext = Depends(get_current_auth), storage: Any = Depends(get_storage)) -> dict:
    """Put a demo account back on Free, to rehearse the upgrade again."""
    if not get_settings().billing_demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Resetting a plan is only possible in demo mode.")
    now = utcnow()
    billing.reset(storage, auth.user_id, now)
    return {"plan": billing.plan_view(None, now)}


class LessonUnlockRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    trigger_id: str = Field(min_length=1, max_length=120)
    error_type: Optional[str] = Field(default=None, max_length=120)
    concept_tag: Optional[str] = Field(default=None, max_length=120)


@router.post("/me/lesson-unlocks")
def unlock_lesson(payload: LessonUnlockRequest, auth: AuthContext = Depends(get_current_auth),
                  storage: Any = Depends(get_storage)) -> dict:
    """Called by the web app before it opens a Study Guider lesson for this student."""
    result = billing.unlock_lesson(storage, get_settings(), auth.user_id, payload.trigger_id,
                                   payload.error_type, payload.concept_tag, utcnow())
    if not result["allowed"]:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"You have opened all {result['limit']} free lessons this month. Upgrade to Pro for unlimited lessons.",
        )
    return result
