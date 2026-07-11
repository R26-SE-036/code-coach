"""Firestore implementation of the storage interface.

WHERE THIS FITS
    build_storage() (app/db/storage.py) picks one of three interchangeable
    adapters — FirestoreStorage (this file), MongoStorage, InMemoryStorage —
    based on settings. Routes and services only ever call the shared method
    set, so swapping the database never touches them.

DESIGN DECISIONS
    * Document IDs are the natural keys (userId, authSessionId,
      diagnosticRecordId, ...). By-id lookups become direct document reads —
      no query, no index.
    * Queries use AT MOST ONE equality filter (the most selective field,
      usually userId); any remaining filtering and all sorting happen in
      Python. Firestore demands composite indexes for multi-field
      queries-with-sort, and managing those is real operational overhead.
      At this project's scale (per-user documents, small counts) fetching a
      user's documents and filtering in Python is simpler and index-free.
      If the data ever grows large, add composite indexes and push the
      filters back into the queries.
    * Semantics mirror InMemoryStorage exactly (it is the tested reference
      implementation); the shared sort/copy helpers are imported from
      storage.py so the behavior cannot drift.

SETUP (see docs/firebase-setup.md for the console walkthrough)
    .env:
        FIREBASE_CREDENTIALS_PATH=secrets/firebase-service-account.json
    The key file is a secret: backend/secrets/ is gitignored — never commit it.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models import DiagnosticSyncResult
from app.db.storage import (
    REMEDIATION_PROGRESS_FIELDS,
    _copy_document,
    _sort_by_created_desc,
    _sort_by_last_updated_desc,
    _utcnow,
)


class FirestoreStorage:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if project_id:
            kwargs["project"] = project_id

        if credentials_path:
            # Local development: authenticate with an explicit service
            # account key file (docs/firebase-setup.md).
            key_path = Path(credentials_path)
            if not key_path.is_absolute():
                key_path = Path.cwd() / key_path
            if not key_path.exists():
                raise FileNotFoundError(
                    f"Firebase service account key not found: {key_path}\n"
                    "Generate one in the Firebase console (Project settings -> "
                    "Service accounts -> Generate new private key) and save it "
                    "at that path. See docs/firebase-setup.md."
                )
            self.client = firestore.Client.from_service_account_json(
                str(key_path), **kwargs
            )
        else:
            # Deployed on Google Cloud (e.g. Cloud Run): no key file — the
            # service's own identity is picked up via Application Default
            # Credentials. Only FIREBASE_PROJECT_ID needs to be set.
            self.client = firestore.Client(**kwargs)

    def close(self) -> None:
        self.client.close()

    def create_indexes(self) -> None:
        # Firestore auto-indexes every single field; the query strategy above
        # deliberately avoids composite indexes, so there is nothing to create.
        return None

    # ------------------------------------------------------------- internals

    def _get(self, collection: str, document_id: str) -> Optional[dict[str, Any]]:
        snapshot = self.client.collection(collection).document(document_id).get()
        if not snapshot.exists:
            return None
        return _copy_document(snapshot.to_dict())

    def _set(self, collection: str, document_id: str, document: dict[str, Any]) -> None:
        self.client.collection(collection).document(document_id).set(deepcopy(document))

    def _update(self, collection: str, document_id: str, updates: dict[str, Any]) -> None:
        self.client.collection(collection).document(document_id).update(deepcopy(updates))

    def _where(
        self,
        collection: str,
        field: str,
        value: Any,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        query = self.client.collection(collection).where(
            filter=FieldFilter(field, "==", value)
        )
        if limit is not None:
            query = query.limit(limit)
        documents = [snapshot.to_dict() for snapshot in query.stream()]
        return [copied for copied in (_copy_document(d) for d in documents) if copied is not None]

    # ----------------------------------------------------------------- users

    def create_user(self, document: dict[str, Any]) -> dict[str, Any]:
        self._set("users", document["userId"], document)
        return _copy_document(document) or {}

    def find_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        matches = self._where("users", "email", email.lower(), limit=1)
        return matches[0] if matches else None

    def find_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        return self._get("users", user_id)

    # --------------------------------------------------------- auth sessions

    def create_auth_session(self, document: dict[str, Any]) -> dict[str, Any]:
        self._set("authSessions", document["authSessionId"], document)
        return _copy_document(document) or {}

    def find_auth_session_by_id(self, auth_session_id: str) -> Optional[dict[str, Any]]:
        return self._get("authSessions", auth_session_id)

    def find_auth_session_by_refresh_hash(
        self, refresh_token_hash: str
    ) -> Optional[dict[str, Any]]:
        matches = self._where("authSessions", "refreshTokenHash", refresh_token_hash, limit=1)
        return matches[0] if matches else None

    def touch_auth_session(self, auth_session_id: str) -> None:
        self._update("authSessions", auth_session_id, {"lastSeenAt": _utcnow()})

    def rotate_auth_session_refresh(
        self,
        auth_session_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> None:
        self._update(
            "authSessions",
            auth_session_id,
            {
                "refreshTokenHash": refresh_token_hash,
                "expiresAt": expires_at,
                "lastSeenAt": _utcnow(),
                "status": "active",
            },
        )

    def revoke_auth_session(self, auth_session_id: str) -> None:
        self._update(
            "authSessions",
            auth_session_id,
            {
                "status": "revoked",
                "refreshTokenHash": None,
                "lastSeenAt": _utcnow(),
            },
        )

    # ------------------------------------------------------ learning sessions

    def create_learning_session(self, document: dict[str, Any]) -> dict[str, Any]:
        self._set("learningSessions", document["learningSessionId"], document)
        return _copy_document(document) or {}

    def find_learning_session_by_id(
        self, learning_session_id: str
    ) -> Optional[dict[str, Any]]:
        return self._get("learningSessions", learning_session_id)

    def find_active_learning_session(
        self,
        user_id: str,
        source_component: str,
        task_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        matches = [
            document
            for document in self._where("learningSessions", "userId", user_id)
            if document["sourceComponent"] == source_component
            and document["status"] == "active"
            and (task_id is None or document.get("taskId") == task_id)
        ]
        if not matches:
            return None
        return _sort_by_created_desc(matches)[0]

    def touch_learning_session(self, learning_session_id: str) -> None:
        self._update(
            "learningSessions",
            learning_session_id,
            {"lastAnalysisAt": _utcnow()},
        )

    # ------------------------------------------------------- code diagnostics

    def sync_code_diagnostics(
        self,
        user_id: str,
        learning_session_id: str,
        diagnostics: list[dict[str, Any]],
    ) -> DiagnosticSyncResult:
        now = _utcnow()
        active_documents = [
            document
            for document in self._where("codeDiagnostics", "userId", user_id)
            if document["learningSessionId"] == learning_session_id
            and document["status"] == "active"
        ]
        active_by_diagnostic_id = {
            document["diagnosticId"]: document for document in active_documents
        }
        current_ids = {document["diagnosticId"] for document in diagnostics}

        resolved_documents: list[dict[str, Any]] = []
        for document in active_documents:
            if document["diagnosticId"] not in current_ids:
                document["status"] = "resolved"
                document["resolvedAt"] = now
                document["lastSeenAt"] = now
                self._update(
                    "codeDiagnostics",
                    document["diagnosticRecordId"],
                    {"status": "resolved", "resolvedAt": now, "lastSeenAt": now},
                )
                resolved_documents.append(document)

        newly_detected_documents: list[dict[str, Any]] = []
        stored_current_documents: list[dict[str, Any]] = []
        for incoming in diagnostics:
            existing = active_by_diagnostic_id.get(incoming["diagnosticId"])
            if existing is not None:
                # Same bug still present: update in place, preserving the
                # record id and original createdAt (repeat-struggle tracking).
                merged = deepcopy(incoming)
                merged["diagnosticRecordId"] = existing["diagnosticRecordId"]
                merged["createdAt"] = existing["createdAt"]
                merged["status"] = "active"
                merged["resolvedAt"] = None
                merged["lastSeenAt"] = now
                self._set("codeDiagnostics", merged["diagnosticRecordId"], merged)
                stored_current_documents.append(merged)
                continue

            stored = deepcopy(incoming)
            stored["lastSeenAt"] = now
            self._set("codeDiagnostics", stored["diagnosticRecordId"], stored)
            newly_detected_documents.append(stored)
            stored_current_documents.append(stored)

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
            document
            for document in self._where("codeDiagnostics", "userId", user_id)
            if (learning_session_id is None or document["learningSessionId"] == learning_session_id)
            and (error_type is None or document["errorType"] == error_type)
            and (status is None or document["status"] == status)
        ]
        return _sort_by_created_desc(documents)[:limit]

    def list_diagnostics_for_session(
        self,
        learning_session_id: str,
        *,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        documents = [
            document
            for document in self._where(
                "codeDiagnostics", "learningSessionId", learning_session_id
            )
            if user_id is None or document["userId"] == user_id
        ]
        return _sort_by_created_desc(documents)

    def find_diagnostic_by_id(
        self,
        user_id: str,
        diagnostic_id: str,
    ) -> Optional[dict[str, Any]]:
        for document in self._where("codeDiagnostics", "userId", user_id):
            if document["diagnosticId"] == diagnostic_id:
                return document
        return None

    # -------------------------------------------------------- learning events

    def create_learning_events(
        self,
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not documents:
            return []
        batch = self.client.batch()
        for document in documents:
            reference = self.client.collection("learningEvents").document(
                document["eventId"]
            )
            batch.set(reference, deepcopy(document))
        batch.commit()
        stored = [_copy_document(document) or {} for document in documents]
        return _sort_by_created_desc(stored)

    def list_learning_events_for_user(
        self,
        user_id: str,
        *,
        learning_session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        documents = [
            document
            for document in self._where("learningEvents", "userId", user_id)
            if (learning_session_id is None or document["learningSessionId"] == learning_session_id)
            and (event_type is None or document["eventType"] == event_type)
        ]
        return _sort_by_created_desc(documents)[:limit]

    # -------------------------------------------------- collaboration sessions

    def create_collaboration_session(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        self._set("collaborationSessions", document["pairSessionId"], document)
        return _copy_document(document) or {}

    def find_collaboration_session_by_id(
        self,
        pair_session_id: str,
    ) -> Optional[dict[str, Any]]:
        return self._get("collaborationSessions", pair_session_id)

    def update_collaboration_session(
        self,
        pair_session_id: str,
        updates: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        if self._get("collaborationSessions", pair_session_id) is None:
            return None
        self._update("collaborationSessions", pair_session_id, updates)
        return self._get("collaborationSessions", pair_session_id)

    # ----------------------------------------------------- remediation triggers

    def upsert_remediation_trigger(
        self,
        document: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        for stored in self._where("remediationTriggers", "userId", document["userId"]):
            if (
                stored["triggerSource"] == document["triggerSource"]
                and stored["conceptTag"] == document["conceptTag"]
                and stored["errorType"] == document["errorType"]
                and stored["status"] == "active"
            ):
                merged = deepcopy(document)
                merged["triggerId"] = stored["triggerId"]
                merged["createdAt"] = stored["createdAt"]
                for key in REMEDIATION_PROGRESS_FIELDS:
                    if merged.get(key) is None and stored.get(key) is not None:
                        merged[key] = stored[key]
                self._set("remediationTriggers", merged["triggerId"], merged)
                return (merged, False)

        self._set("remediationTriggers", document["triggerId"], document)
        return (_copy_document(document) or {}, True)

    def find_remediation_trigger_by_id(
        self,
        trigger_id: str,
    ) -> Optional[dict[str, Any]]:
        return self._get("remediationTriggers", trigger_id)

    def update_remediation_trigger(
        self,
        trigger_id: str,
        updates: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        if self._get("remediationTriggers", trigger_id) is None:
            return None
        self._update("remediationTriggers", trigger_id, updates)
        return self._get("remediationTriggers", trigger_id)

    def list_remediation_triggers_for_user(
        self,
        user_id: str,
        *,
        status: Optional[str] = None,
        trigger_source: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        documents = [
            document
            for document in self._where("remediationTriggers", "userId", user_id)
            if (status is None or document["status"] == status)
            and (trigger_source is None or document["triggerSource"] == trigger_source)
        ]
        return _sort_by_created_desc(documents)[:limit]

    # --------------------------------------------------------- concept mastery

    def upsert_concept_mastery(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        for stored in self._where("conceptMastery", "userId", document["userId"]):
            if stored["conceptTag"] == document["conceptTag"]:
                merged = deepcopy(document)
                merged["masteryId"] = stored["masteryId"]
                merged["createdAt"] = stored["createdAt"]
                self._set("conceptMastery", merged["masteryId"], merged)
                return merged

        self._set("conceptMastery", document["masteryId"], document)
        return _copy_document(document) or {}

    def list_concept_mastery_for_user(
        self,
        user_id: str,
        *,
        concept_tag: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        documents = [
            document
            for document in self._where("conceptMastery", "userId", user_id)
            if concept_tag is None or document["conceptTag"] == concept_tag
        ]
        return _sort_by_last_updated_desc(documents)[:limit]
