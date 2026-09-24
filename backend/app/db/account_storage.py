"""Storage for account recovery: one-time tokens, password changes, recovery email.

Kept apart from storage.py, which is already long, and mixed into both
backends there so the routes see one interface.

A token is stored as a SHA-256 hash, never as itself - the same rule the
refresh tokens follow. Whoever can read the database still cannot use a link
that is waiting in someone's inbox.

`purpose` separates the two kinds of link, so a recovery-email confirmation can
never be replayed as a password reset:

    password_reset   emailed from "forgot password"; sets a new password
    recovery_email   emailed to a new recovery address; proves the student owns it
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from pymongo import ASCENDING, ReturnDocument
except ImportError:  # pragma: no cover - the in-memory backend needs neither
    ASCENDING = 1
    ReturnDocument = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class InMemoryAccountStorage:
    """The in-memory half. Expects `self.users` and `self.auth_sessions`."""

    def _account_tokens(self) -> dict[str, dict[str, Any]]:
        if not hasattr(self, "account_tokens"):
            self.account_tokens = {}
        return self.account_tokens

    def update_user(self, user_id: str, fields: dict[str, Any], unset: tuple[str, ...] = ()) -> None:
        document = self.users.get(user_id)
        if document is None:
            return
        document.update(deepcopy(fields))
        for name in unset:
            document.pop(name, None)
        document["updatedAt"] = _now()

    def revoke_auth_sessions_for_user(self, user_id: str) -> list[str]:
        revoked = []
        for document in self.auth_sessions.values():
            if document.get("userId") == user_id and document.get("status") == "active":
                document["status"] = "revoked"
                document["refreshTokenHash"] = None
                document["lastSeenAt"] = _now()
                revoked.append(document["authSessionId"])
        return revoked

    def create_account_token(self, document: dict[str, Any]) -> None:
        self._account_tokens()[document["tokenHash"]] = deepcopy(document)

    def consume_account_token(self, token_hash: str, purpose: str) -> Optional[dict[str, Any]]:
        document = self._account_tokens().get(token_hash)
        if (
            document is None
            or document["purpose"] != purpose
            or document.get("usedAt") is not None
            or _aware(document["expiresAt"]) <= _now()
        ):
            return None
        document["usedAt"] = _now()
        return deepcopy(document)

    def invalidate_account_tokens(self, user_id: str, purpose: str) -> None:
        for document in self._account_tokens().values():
            if (
                document["userId"] == user_id
                and document["purpose"] == purpose
                and document.get("usedAt") is None
            ):
                document["usedAt"] = _now()


class MongoAccountStorage:
    """The MongoDB half. Expects `self.db`."""

    def create_account_indexes(self) -> None:
        self.db.accountTokens.create_index([("tokenHash", ASCENDING)], unique=True)
        self.db.accountTokens.create_index([("userId", ASCENDING), ("purpose", ASCENDING)])
        # Expired links delete themselves; nothing else needs to clean up.
        self.db.accountTokens.create_index([("expiresAt", ASCENDING)], expireAfterSeconds=0)

    def update_user(self, user_id: str, fields: dict[str, Any], unset: tuple[str, ...] = ()) -> None:
        update: dict[str, Any] = {"$set": {**fields, "updatedAt": _now()}}
        if unset:
            update["$unset"] = {name: "" for name in unset}
        self.db.users.update_one({"userId": user_id}, update)

    def revoke_auth_sessions_for_user(self, user_id: str) -> list[str]:
        active = [
            document["authSessionId"]
            for document in self.db.authSessions.find(
                {"userId": user_id, "status": "active"},
                {"authSessionId": 1},
            )
        ]
        if active:
            self.db.authSessions.update_many(
                {"authSessionId": {"$in": active}},
                {"$set": {"status": "revoked", "refreshTokenHash": None, "lastSeenAt": _now()}},
            )
        return active

    def create_account_token(self, document: dict[str, Any]) -> None:
        self.db.accountTokens.insert_one(deepcopy(document))

    def consume_account_token(self, token_hash: str, purpose: str) -> Optional[dict[str, Any]]:
        # One atomic update, so two clicks on the same link cannot both win.
        document = self.db.accountTokens.find_one_and_update(
            {
                "tokenHash": token_hash,
                "purpose": purpose,
                "usedAt": None,
                "expiresAt": {"$gt": _now()},
            },
            {"$set": {"usedAt": _now()}},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            return None
        document.pop("_id", None)
        return document

    def invalidate_account_tokens(self, user_id: str, purpose: str) -> None:
        self.db.accountTokens.update_many(
            {"userId": user_id, "purpose": purpose, "usedAt": None},
            {"$set": {"usedAt": _now()}},
        )
