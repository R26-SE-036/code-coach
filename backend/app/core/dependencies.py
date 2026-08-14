from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.common import utcnow

logger = logging.getLogger(__name__)

from app.core.cache import TTLCache
from app.core.security import TokenError, decode_access_token

_bearer = HTTPBearer(auto_error=False)

# Auth used to cost FOUR Firestore round trips per request (session read, user
# read, lastSeenAt write, session re-read). Every authenticated call paid it,
# including the analysis triggered on each typing pause. These caches collapse
# that to zero for repeat requests within the TTL. Entries are dropped on
# sign-out (revoke_cached_auth), and the TTL is short enough that a revoked
# session cannot outlive it meaningfully.
_AUTH_CACHE = TTLCache(ttl_seconds=30.0)
_SESSION_TOUCH_CACHE = TTLCache(ttl_seconds=120.0)


def revoke_cached_auth(auth_session_id: str) -> None:
    """Drop cached auth for a session (called on sign-out)."""
    _AUTH_CACHE.invalidate_prefix(f"{auth_session_id}:")
    _SESSION_TOUCH_CACHE.invalidate(auth_session_id)

# provides reusable FastAPI dependencies

@dataclass
class AuthContext:
    user_id: str
    role: str
    auth_session_id: str
    user: dict[str, Any]
    auth_session: dict[str, Any]


def get_storage(request: Request) -> Any:
    return request.app.state.storage


def _client_ip(request: Request) -> str:
    # Behind Cloud Run / any proxy the real client is the first entry of
    # X-Forwarded-For; locally it is the socket peer.
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_auth_rate_limit(request: Request) -> None:
    """Dependency for credential endpoints: cap attempts per IP per endpoint."""
    limiter = getattr(request.app.state, "auth_limiter", None)
    if limiter is None:
        return
    retry_after = limiter.check(f"{request.url.path}:{_client_ip(request)}")
    if retry_after > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait a moment and try again.",
            headers={"Retry-After": str(max(1, int(retry_after + 0.5)))},
        )


def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    storage: Any = Depends(get_storage),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    try:
        token_payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    cache_key = f"{token_payload.auth_session_id}:{token_payload.user_id}"
    cached = _AUTH_CACHE.get(cache_key)
    if cached is not None:
        return cached

    auth_session = storage.find_auth_session_by_id(token_payload.auth_session_id)
    if auth_session is None or auth_session.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The authentication session is no longer active.",
        )

    if auth_session.get("userId") != token_payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The authentication session does not match the user.",
        )

    user = storage.find_user_by_id(token_payload.user_id)
    if user is None or user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user account is unavailable.",
        )

    # lastSeenAt is presence telemetry, not correctness: writing it on every
    # request added a round trip per keystroke-triggered analysis. Throttle it
    # to at most once per TTL window, and never re-read the session afterwards
    # (we already know what the write changed).
    if _SESSION_TOUCH_CACHE.get(token_payload.auth_session_id) is None:
        _SESSION_TOUCH_CACHE.set(token_payload.auth_session_id, True)
        try:
            storage.touch_auth_session(token_payload.auth_session_id)
            auth_session["lastSeenAt"] = utcnow()
        except Exception:  # presence telemetry must never fail a request
            logger.warning("touch_auth_session failed", exc_info=True)

    context = AuthContext(
        user_id=token_payload.user_id,
        role=token_payload.role,
        auth_session_id=token_payload.auth_session_id,
        user=user,
        auth_session=auth_session,
    )
    _AUTH_CACHE.set(cache_key, context)
    return context
