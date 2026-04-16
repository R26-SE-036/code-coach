from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import TokenError, decode_access_token

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user_id: str
    role: str
    auth_session_id: str
    user: dict[str, Any]
    auth_session: dict[str, Any]


def get_storage(request: Request) -> Any:
    return request.app.state.storage


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

    storage.touch_auth_session(token_payload.auth_session_id)

    refreshed_auth_session = storage.find_auth_session_by_id(token_payload.auth_session_id)
    return AuthContext(
        user_id=token_payload.user_id,
        role=token_payload.role,
        auth_session_id=token_payload.auth_session_id,
        user=user,
        auth_session=refreshed_auth_session or auth_session,
    )
