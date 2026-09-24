"""Account recovery: forgot password, reset password, and a recovery email.

    POST /api/v1/auth/password/forgot         email a reset link (always 202)
    POST /api/v1/auth/password/reset          set a new password from that link
    PUT  /api/v1/auth/me/recovery-email       set, change or remove the address
    POST /api/v1/auth/recovery-email/confirm  prove the new address is theirs

Links go to the website (settings.public_web_url) and carry the token in the
URL FRAGMENT - `/reset-password#token=...` - which a browser never sends to a
server, so the token does not end up in any access log on the way. The page
reads it and posts it here.

A token is single-use, stored only as a hash, and short-lived: 30 minutes for a
reset, 24 hours to confirm a recovery address.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.core.common import generate_prefixed_id, utcnow
from app.core.config import get_settings
from app.core.dependencies import (
    AuthContext,
    enforce_account_rate_limit,
    enforce_auth_rate_limit,
    get_current_auth,
    get_storage,
    revoke_cached_auth,
)
from app.core.security import create_refresh_token, hash_password, hash_refresh_token, verify_password
from app.models import (
    ConfirmTokenRequest,
    ForgotPasswordRequest,
    RecoveryEmailRequest,
    ResetPasswordRequest,
    StatusResponse,
)
from app.services.email_templates import password_reset_email, recovery_email_confirmation
from app.services.mailer import send_mail

router = APIRouter(prefix="/api/v1/auth", tags=["account"])

RESET = "password_reset"
RECOVERY = "recovery_email"

_FORGOT_ANSWER = (
    "If an account uses that email, a link to reset the password is on its way. "
    "It works once, for 30 minutes."
)


def _issue_token(storage: Any, user_id: str, purpose: str, lifetime: timedelta, **extra: Any) -> str:
    """Mint a link token, keep only its hash, and retire older ones of its kind."""
    storage.invalidate_account_tokens(user_id, purpose)
    token = create_refresh_token()
    now = utcnow()
    storage.create_account_token(
        {
            "tokenId": generate_prefixed_id("tok"),
            "userId": user_id,
            "purpose": purpose,
            "tokenHash": hash_refresh_token(token),
            "createdAt": now,
            "expiresAt": now + lifetime,
            "usedAt": None,
            **extra,
        }
    )
    return token


def _link(path: str, token: str) -> str:
    return f"{get_settings().public_web_url.rstrip('/')}{path}#token={token}"


@router.post("/password/forgot", response_model=StatusResponse, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background: BackgroundTasks,
    storage: Any = Depends(get_storage),
    _rate_limit: None = Depends(enforce_auth_rate_limit),
) -> StatusResponse:
    """Send a reset link to the account's email and its confirmed recovery email.

    The answer is identical whether or not the account exists, and the email is
    sent after the response, so neither the words nor the timing tell a caller
    which addresses have accounts.
    """
    settings = get_settings()
    email = str(payload.email).strip().lower()
    user = storage.find_user_by_email(email)

    # Too many for this address: answer as usual and send nothing. Saying
    # "too many" would confirm the account exists.
    flooded = request.app.state.reset_mail_limiter.check(f"forgot:{email}") > 0

    if user is not None and user.get("status") == "active" and not flooded:
        token = _issue_token(
            storage, user["userId"], RESET, timedelta(minutes=settings.password_reset_ttl_minutes)
        )
        link = _link("/reset-password", token)
        email = password_reset_email(
            name=user["fullName"],
            account_email=user["email"],
            link=link,
            minutes=settings.password_reset_ttl_minutes,
        )
        background.add_task(
            send_mail,
            [user["email"], user.get("recoveryEmail")],
            email.subject,
            email.text,
            link=link,
            html=email.html,
        )

    return StatusResponse(status="ok", message=_FORGOT_ANSWER)


@router.post("/password/reset", response_model=StatusResponse)
def reset_password(
    payload: ResetPasswordRequest,
    storage: Any = Depends(get_storage),
    _rate_limit: None = Depends(enforce_auth_rate_limit),
) -> StatusResponse:
    """Set the new password and sign the account out everywhere.

    Every session ends, because a reset usually means the old password is no
    longer trusted - a session started with it should not survive.
    """
    entry = storage.consume_account_token(hash_refresh_token(payload.token), RESET)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That reset link has expired or has already been used. Ask for a new one.",
        )

    user = storage.find_user_by_id(entry["userId"])
    if user is None or user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That account is not available.",
        )

    storage.update_user(user["userId"], {"passwordHash": hash_password(payload.new_password)})
    for auth_session_id in storage.revoke_auth_sessions_for_user(user["userId"]):
        revoke_cached_auth(auth_session_id)

    return StatusResponse(status="ok", message="Your password has been changed. Sign in with the new one.")


@router.put("/me/recovery-email", response_model=StatusResponse)
def set_recovery_email(
    payload: RecoveryEmailRequest,
    request: Request,
    background: BackgroundTasks,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> StatusResponse:
    """Ask to use a recovery address, or remove the current one.

    A new address is not used until the student clicks the confirmation sent
    to it - a typo would otherwise send reset links to a stranger.
    """
    settings = get_settings()
    user_id = auth.user["userId"]
    enforce_account_rate_limit(request, f"recovery:{user_id}")

    # 403, not 401: every client reads 401 as "you are signed out".
    user = storage.find_user_by_id(user_id) or {}
    if not user.get("passwordHash") or not verify_password(payload.password, user["passwordHash"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="That password is not correct.")

    if payload.recovery_email is None:
        storage.invalidate_account_tokens(user_id, RECOVERY)
        storage.update_user(user_id, {}, unset=("recoveryEmail",))
        return StatusResponse(status="ok", message="The recovery email has been removed.")

    address = str(payload.recovery_email).strip().lower()
    if address == user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use a different address from the one you sign in with.",
        )

    token = _issue_token(
        storage, user_id, RECOVERY, timedelta(hours=settings.recovery_email_ttl_hours), email=address
    )
    link = _link("/confirm-email", token)
    email = recovery_email_confirmation(
        name=user.get("fullName", ""),
        account_email=user.get("email", ""),
        link=link,
        hours=settings.recovery_email_ttl_hours,
    )
    background.add_task(send_mail, [address], email.subject, email.text, link=link, html=email.html)
    return StatusResponse(
        status="ok",
        message=f"We sent a confirmation link to {address}. The address is used once you open it.",
    )


@router.post("/recovery-email/confirm", response_model=StatusResponse)
def confirm_recovery_email(
    payload: ConfirmTokenRequest,
    storage: Any = Depends(get_storage),
    _rate_limit: None = Depends(enforce_auth_rate_limit),
) -> StatusResponse:
    entry = storage.consume_account_token(hash_refresh_token(payload.token), RECOVERY)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That confirmation link has expired or has already been used.",
        )

    # /auth/me caches the user for 30 seconds, so the address can take that
    # long to appear there.
    storage.update_user(entry["userId"], {"recoveryEmail": entry["email"]})
    return StatusResponse(status="ok", message=f"{entry['email']} is now your recovery email.")
