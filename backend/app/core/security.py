import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_PASSWORD_HASHER = PasswordHasher()


def hash_password(password: str) -> str:
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _PASSWORD_HASHER.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sign(header_b64: str, payload_b64: str, secret: str) -> str:
    message = f"{header_b64}.{payload_b64}".encode("ascii")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _base64url_encode(digest)


def _timestamp_after(seconds: int) -> int:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    return int(expires_at.timestamp())


def create_access_token(user_id: str, auth_session_id: str, role: str) -> str:
    settings = get_settings()
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    payload = {
        "sub": user_id,
        "authSessionId": auth_session_id,
        "role": role,
        "tokenType": "access",
        "exp": _timestamp_after(settings.access_token_ttl_seconds),
    }

    header_b64 = _base64url_encode(_json_bytes(header))
    payload_b64 = _base64url_encode(_json_bytes(payload))
    signature_b64 = _sign(header_b64, payload_b64, settings.jwt_secret)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


@dataclass
class TokenPayload:
    user_id: str
    auth_session_id: str
    role: str
    token_type: str
    exp: int


class TokenError(ValueError):
    pass


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()

    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise TokenError("Invalid token format.") from exc

    expected_signature = _sign(header_b64, payload_b64, settings.jwt_secret)
    if not hmac.compare_digest(signature_b64, expected_signature):
        raise TokenError("Invalid token signature.")

    try:
        payload_data = json.loads(_base64url_decode(payload_b64))
    except json.JSONDecodeError as exc:
        raise TokenError("Invalid token payload.") from exc

    exp = int(payload_data.get("exp", 0))
    if exp <= int(datetime.now(timezone.utc).timestamp()):
        raise TokenError("Token has expired.")

    token_type = str(payload_data.get("tokenType", ""))
    if token_type != "access":
        raise TokenError("Unsupported token type.")

    return TokenPayload(
        user_id=str(payload_data.get("sub", "")),
        auth_session_id=str(payload_data.get("authSessionId", "")),
        role=str(payload_data.get("role", "")),
        token_type=token_type,
        exp=exp,
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(timezone.utc) + timedelta(
        seconds=settings.refresh_token_ttl_seconds,
    )
