from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import get_settings
from app.models import DiagnosticSyncResult

try:
    from pymongo import ASCENDING, DESCENDING, MongoClient
except ImportError:  # pragma: no cover - exercised only when pymongo missing
    ASCENDING = 1
    DESCENDING = -1
    MongoClient = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _copy_document(document: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if document is None:
        return None

    copied = deepcopy(document)
    copied.pop("_id", None)
    return copied


def _sort_by_created_desc(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        documents,
        key=lambda item: item.get("createdAt") or item.get("startedAt") or _utcnow(),
        reverse=True,
    )


class InMemoryStorage:
    def __init__(self) -> None:
        self.users: dict[str, dict[str, Any]] = {}
        self.auth_sessions: dict[str, dict[str, Any]] = {}
        self.learning_sessions: dict[str, dict[str, Any]] = {}
        self.code_diagnostics: dict[str, dict[str, Any]] = {}
        self.learning_events: dict[str, dict[str, Any]] = {}

    def create_indexes(self) -> None:
        return None

    def close(self) -> None:
        return None

    def create_user(self, document: dict[str, Any]) -> dict[str, Any]:
        stored = deepcopy(document)
        self.users[stored["userId"]] = stored
        return _copy_document(stored) or {}

    def find_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        for document in self.users.values():
            if document["email"].lower() == email.lower():
                return _copy_document(document)
        return None

    def find_user_by_student_number(self, student_number: str) -> Optional[dict[str, Any]]:
        for document in self.users.values():
            if document["studentNumber"] == student_number:
                return _copy_document(document)
        return None

    def find_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        return _copy_document(self.users.get(user_id))

    def create_auth_session(self, document: dict[str, Any]) -> dict[str, Any]:
        stored = deepcopy(document)
        self.auth_sessions[stored["authSessionId"]] = stored
        return _copy_document(stored) or {}

    def find_auth_session_by_id(self, auth_session_id: str) -> Optional[dict[str, Any]]:
        return _copy_document(self.auth_sessions.get(auth_session_id))

    def find_auth_session_by_refresh_hash(self, refresh_token_hash: str) -> Optional[dict[str, Any]]:
        for document in self.auth_sessions.values():
            if document.get("refreshTokenHash") == refresh_token_hash:
                return _copy_document(document)
        return None

    def touch_auth_session(self, auth_session_id: str) -> None:
        document = self.auth_sessions.get(auth_session_id)
        if document is not None:
            document["lastSeenAt"] = _utcnow()

    def rotate_auth_session_refresh(
        self,
        auth_session_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> None:
        document = self.auth_sessions.get(auth_session_id)
        if document is not None:
            document["refreshTokenHash"] = refresh_token_hash
            document["expiresAt"] = expires_at
            document["lastSeenAt"] = _utcnow()
            document["status"] = "active"

    def revoke_auth_session(self, auth_session_id: str) -> None:
        document = self.auth_sessions.get(auth_session_id)
        if document is not None:
            document["status"] = "revoked"
            document["refreshTokenHash"] = None
            document["lastSeenAt"] = _utcnow()

    def create_learning_session(self, document: dict[str, Any]) -> dict[str, Any]:
        stored = deepcopy(document)
        self.learning_sessions[stored["learningSessionId"]] = stored
        return _copy_document(stored) or {}

    def find_learning_session_by_id(self, learning_session_id: str) -> Optional[dict[str, Any]]:
        return _copy_document(self.learning_sessions.get(learning_session_id))

    def find_active_learning_session(
        self,
        user_id: str,
        source_component: str,
        task_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        matches = [
            _copy_document(document)
            for document in self.learning_sessions.values()
            if document["userId"] == user_id
            and document["sourceComponent"] == source_component
            and document["status"] == "active"
            and (task_id is None or document.get("taskId") == task_id)
        ]
        matches = [item for item in matches if item is not None]
        if not matches:
            return None
        return _sort_by_created_desc(matches)[0]

    def touch_learning_session(self, learning_session_id: str) -> None:
        document = self.learning_sessions.get(learning_session_id)
        if document is not None:
            document["lastAnalysisAt"] = _utcnow()

    def sync_code_diagnostics(
        self,
        user_id: str,
        learning_session_id: str,
        diagnostics: list[dict[str, Any]],
    ) -> DiagnosticSyncResult:
        now = _utcnow()
        active_documents = [
            document
            for document in self.code_diagnostics.values()
            if document["userId"] == user_id
            and document["learningSessionId"] == learning_session_id
            and document["status"] == "active"
        ]
        active_by_diagnostic_id = {
            document["diagnosticId"]: document for document in active_documents
        }
        current_ids = {document["diagnosticId"] for document in diagnostics}
        resolved_documents: list[dict[str, Any]] = []
        newly_detected_documents: list[dict[str, Any]] = []

        for document in active_documents:
            if document["diagnosticId"] not in current_ids:
                document["status"] = "resolved"
                document["resolvedAt"] = now
                document["lastSeenAt"] = now
                resolved_documents.append(_copy_document(document) or {})

        stored_current_documents: list[dict[str, Any]] = []
        for incoming in diagnostics:
            existing = active_by_diagnostic_id.get(incoming["diagnosticId"])
            if existing is not None:
                preserved_record_id = existing.get("diagnosticRecordId")
                preserved_created_at = existing.get("createdAt")
                existing.update(deepcopy(incoming))
                if preserved_record_id is not None:
                    existing["diagnosticRecordId"] = preserved_record_id
                if preserved_created_at is not None:
                    existing["createdAt"] = preserved_created_at
                existing["status"] = "active"
                existing["resolvedAt"] = None
                existing["lastSeenAt"] = now
                stored_current_documents.append(_copy_document(existing) or {})
                continue

            stored = deepcopy(incoming)
            stored["lastSeenAt"] = now
            self.code_diagnostics[stored["diagnosticRecordId"]] = stored
            stored_copy = _copy_document(stored) or {}
            newly_detected_documents.append(stored_copy)
            stored_current_documents.append(stored_copy)

        return DiagnosticSyncResult(
            active_documents=_sort_by_created_desc(stored_current_documents),
            newly_detected_documents=_sort_by_created_desc(newly_detected_documents),
            resolved_documents=_sort_by_created_desc(resolved_documents),
        )

    def list_diagnostics_for_user(
        self,
        user_id: str,
        *,
        learning_session_id: Optional[str] = None,
        error_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        documents = [
            _copy_document(document)
            for document in self.code_diagnostics.values()
            if document["userId"] == user_id
            and (learning_session_id is None or document["learningSessionId"] == learning_session_id)
            and (error_type is None or document["errorType"] == error_type)
            and (status is None or document["status"] == status)
        ]
        documents = [item for item in documents if item is not None]
        return _sort_by_created_desc(documents)[:limit]

    def list_diagnostics_for_session(
        self,
        learning_session_id: str,
        *,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        documents = [
            _copy_document(document)
            for document in self.code_diagnostics.values()
            if document["learningSessionId"] == learning_session_id
            and (user_id is None or document["userId"] == user_id)
        ]
        documents = [item for item in documents if item is not None]
        return _sort_by_created_desc(documents)

    def create_learning_events(
        self,
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        stored_documents: list[dict[str, Any]] = []
        for document in documents:
            stored = deepcopy(document)
            self.learning_events[stored["eventId"]] = stored
            stored_documents.append(_copy_document(stored) or {})
        return _sort_by_created_desc(stored_documents)

    def list_learning_events_for_user(
        self,
        user_id: str,
        *,
        learning_session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        documents = [
            _copy_document(document)
            for document in self.learning_events.values()
            if document["userId"] == user_id
            and (learning_session_id is None or document["learningSessionId"] == learning_session_id)
            and (event_type is None or document["eventType"] == event_type)
        ]
        documents = [item for item in documents if item is not None]
        return _sort_by_created_desc(documents)[:limit]


class MongoStorage:
    def __init__(self, mongo_uri: str, database_name: str) -> None:
        if MongoClient is None:
            raise RuntimeError("pymongo is required for MongoDB storage.")

        self.client = MongoClient(mongo_uri, tz_aware=True)
        self.db = self.client[database_name]

    def close(self) -> None:
        self.client.close()

    def create_indexes(self) -> None:
        self.db.users.create_index([("userId", ASCENDING)], unique=True)
        self.db.users.create_index([("email", ASCENDING)], unique=True)
        self.db.users.create_index([("studentNumber", ASCENDING)], unique=True)

        self.db.authSessions.create_index([("authSessionId", ASCENDING)], unique=True)
        self.db.authSessions.create_index([("userId", ASCENDING), ("status", ASCENDING)])
        self.db.authSessions.create_index([("refreshTokenHash", ASCENDING)])

        self.db.learningSessions.create_index(
            [("learningSessionId", ASCENDING)],
            unique=True,
        )
        self.db.learningSessions.create_index(
            [("userId", ASCENDING), ("status", ASCENDING), ("startedAt", DESCENDING)],
        )
        self.db.learningSessions.create_index(
            [("userId", ASCENDING), ("sourceComponent", ASCENDING), ("taskId", ASCENDING), ("status", ASCENDING)],
        )

        self.db.codeDiagnostics.create_index(
            [("diagnosticRecordId", ASCENDING)],
            unique=True,
        )
        self.db.codeDiagnostics.create_index(
            [("userId", ASCENDING), ("createdAt", DESCENDING)],
        )
        self.db.codeDiagnostics.create_index(
            [("learningSessionId", ASCENDING), ("createdAt", DESCENDING)],
        )
        self.db.codeDiagnostics.create_index(
            [("userId", ASCENDING), ("errorType", ASCENDING), ("createdAt", DESCENDING)],
        )
        self.db.codeDiagnostics.create_index(
            [("userId", ASCENDING), ("learningSessionId", ASCENDING), ("diagnosticId", ASCENDING), ("status", ASCENDING)],
        )
        self.db.learningEvents.create_index(
            [("eventId", ASCENDING)],
            unique=True,
        )
        self.db.learningEvents.create_index(
            [("userId", ASCENDING), ("createdAt", DESCENDING)],
        )
        self.db.learningEvents.create_index(
            [("learningSessionId", ASCENDING), ("createdAt", DESCENDING)],
        )
        self.db.learningEvents.create_index(
            [("eventType", ASCENDING), ("createdAt", DESCENDING)],
        )

    def create_user(self, document: dict[str, Any]) -> dict[str, Any]:
        self.db.users.insert_one(deepcopy(document))
        return _copy_document(document) or {}

    def find_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        return _copy_document(self.db.users.find_one({"email": email.lower()}))

    def find_user_by_student_number(self, student_number: str) -> Optional[dict[str, Any]]:
        return _copy_document(self.db.users.find_one({"studentNumber": student_number}))

    def find_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        return _copy_document(self.db.users.find_one({"userId": user_id}))

    def create_auth_session(self, document: dict[str, Any]) -> dict[str, Any]:
        self.db.authSessions.insert_one(deepcopy(document))
        return _copy_document(document) or {}

    def find_auth_session_by_id(self, auth_session_id: str) -> Optional[dict[str, Any]]:
        return _copy_document(
            self.db.authSessions.find_one({"authSessionId": auth_session_id}),
        )

    def find_auth_session_by_refresh_hash(self, refresh_token_hash: str) -> Optional[dict[str, Any]]:
        return _copy_document(
            self.db.authSessions.find_one({"refreshTokenHash": refresh_token_hash}),
        )

    def touch_auth_session(self, auth_session_id: str) -> None:
        self.db.authSessions.update_one(
            {"authSessionId": auth_session_id},
            {"$set": {"lastSeenAt": _utcnow()}},
        )

    def rotate_auth_session_refresh(
        self,
        auth_session_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> None:
        self.db.authSessions.update_one(
            {"authSessionId": auth_session_id},
            {
                "$set": {
                    "refreshTokenHash": refresh_token_hash,
                    "expiresAt": expires_at,
                    "lastSeenAt": _utcnow(),
                    "status": "active",
                },
            },
        )

    def revoke_auth_session(self, auth_session_id: str) -> None:
        self.db.authSessions.update_one(
            {"authSessionId": auth_session_id},
            {
                "$set": {
                    "status": "revoked",
                    "refreshTokenHash": None,
                    "lastSeenAt": _utcnow(),
                },
            },
        )

    def create_learning_session(self, document: dict[str, Any]) -> dict[str, Any]:
        self.db.learningSessions.insert_one(deepcopy(document))
        return _copy_document(document) or {}

    def find_learning_session_by_id(self, learning_session_id: str) -> Optional[dict[str, Any]]:
        return _copy_document(
            self.db.learningSessions.find_one({"learningSessionId": learning_session_id}),
        )

    def find_active_learning_session(
        self,
        user_id: str,
        source_component: str,
        task_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        query: dict[str, Any] = {
            "userId": user_id,
            "sourceComponent": source_component,
            "status": "active",
        }
        if task_id is not None:
            query["taskId"] = task_id

        document = self.db.learningSessions.find_one(
            query,
            sort=[("startedAt", DESCENDING)],
        )
        return _copy_document(document)

    def touch_learning_session(self, learning_session_id: str) -> None:
        self.db.learningSessions.update_one(
            {"learningSessionId": learning_session_id},
            {"$set": {"lastAnalysisAt": _utcnow()}},
        )

    def sync_code_diagnostics(
        self,
        user_id: str,
        learning_session_id: str,
        diagnostics: list[dict[str, Any]],
    ) -> DiagnosticSyncResult:
        now = _utcnow()
        existing_active_documents = [
            _copy_document(document) or {}
            for document in self.db.codeDiagnostics.find(
                {
                    "userId": user_id,
                    "learningSessionId": learning_session_id,
                    "status": "active",
                },
            )
        ]
        active_by_diagnostic_id = {
            document["diagnosticId"]: document for document in existing_active_documents
        }
        current_ids = {document["diagnosticId"] for document in diagnostics}
        resolved_documents = [
            {
                **document,
                "status": "resolved",
                "resolvedAt": now,
                "lastSeenAt": now,
            }
            for document in existing_active_documents
            if document["diagnosticId"] not in current_ids
        ]
        newly_detected_ids: set[str] = set()

        self.db.codeDiagnostics.update_many(
            {
                "userId": user_id,
                "learningSessionId": learning_session_id,
                "status": "active",
                "diagnosticId": {"$nin": list(current_ids)},
            },
            {
                "$set": {
                    "status": "resolved",
                    "resolvedAt": now,
                    "lastSeenAt": now,
                },
            },
        )

        for incoming in diagnostics:
            update_fields = deepcopy(incoming)
            diagnostic_record_id = update_fields.pop("diagnosticRecordId")
            created_at = update_fields.pop("createdAt")
            if incoming["diagnosticId"] not in active_by_diagnostic_id:
                newly_detected_ids.add(incoming["diagnosticId"])
            self.db.codeDiagnostics.update_one(
                {
                    "userId": user_id,
                    "learningSessionId": learning_session_id,
                    "diagnosticId": incoming["diagnosticId"],
                    "status": "active",
                },
                {
                    "$set": {
                        **update_fields,
                        "status": "active",
                        "resolvedAt": None,
                        "lastSeenAt": now,
                    },
                    "$setOnInsert": {
                        "diagnosticRecordId": diagnostic_record_id,
                        "createdAt": created_at,
                    },
                },
                upsert=True,
            )

        active_documents = [
            _copy_document(document) or {}
            for document in self.db.codeDiagnostics.find(
                {
                    "userId": user_id,
                    "learningSessionId": learning_session_id,
                    "status": "active",
                },
                sort=[("createdAt", DESCENDING)],
            )
        ]
        newly_detected_documents = [
            document
            for document in active_documents
            if document["diagnosticId"] in newly_detected_ids
        ]
        return DiagnosticSyncResult(
            active_documents=active_documents,
            newly_detected_documents=newly_detected_documents,
            resolved_documents=_sort_by_created_desc(resolved_documents),
        )

    def list_diagnostics_for_user(
        self,
        user_id: str,
        *,
        learning_session_id: Optional[str] = None,
        error_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"userId": user_id}
        if learning_session_id is not None:
            query["learningSessionId"] = learning_session_id
        if error_type is not None:
            query["errorType"] = error_type
        if status is not None:
            query["status"] = status

        cursor = self.db.codeDiagnostics.find(
            query,
            sort=[("createdAt", DESCENDING)],
            limit=limit,
        )
        return [_copy_document(document) or {} for document in cursor]

    def list_diagnostics_for_session(
        self,
        learning_session_id: str,
        *,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"learningSessionId": learning_session_id}
        if user_id is not None:
            query["userId"] = user_id

        cursor = self.db.codeDiagnostics.find(
            {
                **query,
            },
            sort=[("createdAt", DESCENDING)],
        )
        return [_copy_document(document) or {} for document in cursor]

    def create_learning_events(
        self,
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not documents:
            return []
        self.db.learningEvents.insert_many([deepcopy(document) for document in documents])
        return [_copy_document(document) or {} for document in documents]

    def list_learning_events_for_user(
        self,
        user_id: str,
        *,
        learning_session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"userId": user_id}
        if learning_session_id is not None:
            query["learningSessionId"] = learning_session_id
        if event_type is not None:
            query["eventType"] = event_type

        cursor = self.db.learningEvents.find(
            query,
            sort=[("createdAt", DESCENDING)],
            limit=limit,
        )
        return [_copy_document(document) or {} for document in cursor]


def build_storage() -> InMemoryStorage | MongoStorage:
    settings = get_settings()

    if settings.mongodb_uri:
        storage = MongoStorage(settings.mongodb_uri, settings.mongodb_db_name)
    else:
        storage = InMemoryStorage()

    storage.create_indexes()
    return storage
