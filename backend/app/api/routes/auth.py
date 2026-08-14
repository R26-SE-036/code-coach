from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.common import generate_prefixed_id, utcnow
from app.core.config import get_settings
from app.core.dependencies import (
    AuthContext,
    enforce_auth_rate_limit,
    get_current_auth,
    get_storage,
    revoke_cached_auth,
)
from app.models import (
    AuthResponse,
    AuthSessionView,
    AuthUser,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    StatusResponse,
    TokenBundle,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _serialize_user(document: dict[str, Any]) -> AuthUser:
    return AuthUser(
        user_id=document["userId"],
        full_name=document["fullName"],
        email=document["email"],
        role=document["role"],
        status=document["status"],
        created_at=document["createdAt"],
    )


def _serialize_auth_session(document: dict[str, Any]) -> AuthSessionView:
    return AuthSessionView(
        auth_session_id=document["authSessionId"],
        client_name=document["clientName"],
        status=document["status"],
        created_at=document["createdAt"],
        last_seen_at=document["lastSeenAt"],
        expires_at=document["expiresAt"],
    )


def _create_session_and_tokens(
    storage: Any,
    user: dict[str, Any],
    client_name: str,
) -> tuple[dict[str, Any], str, str]:
    auth_session_id = generate_prefixed_id("auth")
    refresh_token = create_refresh_token()
    refresh_token_hash = hash_refresh_token(refresh_token)
    expires_at = refresh_token_expiry()
    created_at = utcnow()
    session_document = {
        "authSessionId": auth_session_id,
        "userId": user["userId"],
        "clientName": client_name,
        "status": "active",
        "refreshTokenHash": refresh_token_hash,
        "createdAt": created_at,
        "lastSeenAt": created_at,
        "expiresAt": expires_at,
    }
    storage.create_auth_session(session_document)

    access_token = create_access_token(user["userId"], auth_session_id, user["role"])
    return session_document, access_token, refresh_token


def _auth_response(
    message: str,
    user: dict[str, Any],
    auth_session: dict[str, Any],
    access_token: str,
    refresh_token: str,
) -> AuthResponse:
    settings = get_settings()
    return AuthResponse(
        status="ok",
        message=message,
        user=_serialize_user(user),
        auth_session=_serialize_auth_session(auth_session),
        tokens=TokenBundle(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_ttl_seconds,
        ),
    )


@router.post("/register", response_model=AuthResponse)
def register(
    payload: RegisterRequest,
    storage: Any = Depends(get_storage),
    _rate_limit: None = Depends(enforce_auth_rate_limit),
) -> AuthResponse:
    normalized_email = _normalize_email(str(payload.email))

    if storage.find_user_by_email(normalized_email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )

    created_at = utcnow()
    user_document: dict[str, Any] = {
        "userId": generate_prefixed_id("user"),
        "fullName": payload.full_name,
        "email": normalized_email,
        "passwordHash": hash_password(payload.password),
        "role": "student",
        "status": "active",
        "createdAt": created_at,
        "updatedAt": created_at,
    }
    storage.create_user(user_document)

    session_document, access_token, refresh_token = _create_session_and_tokens(
        storage,
        user_document,
        payload.client_name,
    )

    return _auth_response(
        "Registration successful.",
        user_document,
        session_document,
        access_token,
        refresh_token,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    storage: Any = Depends(get_storage),
    _rate_limit: None = Depends(enforce_auth_rate_limit),
) -> AuthResponse:
    identifier = payload.identifier.strip()
    user_document = storage.find_user_by_email(_normalize_email(identifier))

    if user_document is None or not verify_password(
        payload.password,
        user_document["passwordHash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if user_document.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user account is not active.",
        )

    session_document, access_token, refresh_token = _create_session_and_tokens(
        storage,
        user_document,
        payload.client_name,
    )

    return _auth_response(
        "Login successful.",
        user_document,
        session_document,
        access_token,
        refresh_token,
    )


@router.get("/me", response_model=MeResponse)
def me(auth: AuthContext = Depends(get_current_auth)) -> MeResponse:
    return MeResponse(
        status="ok",
        user=_serialize_user(auth.user),
        auth_session=_serialize_auth_session(auth.auth_session),
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    payload: RefreshRequest,
    storage: Any = Depends(get_storage),
    _rate_limit: None = Depends(enforce_auth_rate_limit),
) -> AuthResponse:
    refresh_token_hash = hash_refresh_token(payload.refresh_token)
    auth_session = storage.find_auth_session_by_refresh_hash(refresh_token_hash)

    if auth_session is None or auth_session.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The refresh token is invalid.",
        )

    if auth_session["expiresAt"] <= utcnow():
        storage.revoke_auth_session(auth_session["authSessionId"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The refresh token has expired.",
        )

    user_document = storage.find_user_by_id(auth_session["userId"])
    if user_document is None or user_document.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user account is unavailable.",
        )

    next_refresh_token = create_refresh_token()
    next_refresh_hash = hash_refresh_token(next_refresh_token)
    next_expires_at = refresh_token_expiry()
    storage.rotate_auth_session_refresh(
        auth_session["authSessionId"],
        next_refresh_hash,
        next_expires_at,
    )

    updated_auth_session = storage.find_auth_session_by_id(auth_session["authSessionId"])
    access_token = create_access_token(
        user_document["userId"],
        auth_session["authSessionId"],
        user_document["role"],
    )

    return _auth_response(
        "Token refresh successful.",
        user_document,
        updated_auth_session or auth_session,
        access_token,
        next_refresh_token,
    )


@router.post("/logout", response_model=StatusResponse)
def logout(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> StatusResponse:
    storage.revoke_auth_session(auth.auth_session_id)
    # Drop the cached auth context so the revoked session cannot be used for
    # the remainder of the cache TTL.
    revoke_cached_auth(auth.auth_session_id)
    return StatusResponse(status="ok", message="Logout successful.")
