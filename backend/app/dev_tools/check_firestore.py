"""Verify the Firestore connection and exercise every storage operation.

Run this ONCE after completing docs/firebase-setup.md (service account key
saved, FIREBASE_CREDENTIALS_PATH set in .env). It creates a disposable
smoke-test user, walks the entire storage interface against the REAL
Firestore database — auth session rotation, the diagnostic active/resolved
lifecycle, remediation dedupe, mastery upserts — and then deletes everything
it created. If every line prints OK, the backend is safe to point at
Firestore.

USAGE (from backend/)
    python -m app.dev_tools.check_firestore
"""

from datetime import timedelta

from app.core.config import get_settings
from app.db.storage import build_storage, _utcnow


def main() -> int:
    settings = get_settings()
    if not settings.firebase_credentials_path:
        print(
            "FIREBASE_CREDENTIALS_PATH is not set in backend/.env.\n"
            "Follow docs/firebase-setup.md first (generate the service "
            "account key, save it under backend/secrets/, uncomment the "
            ".env line), then rerun this tool."
        )
        return 1

    storage = build_storage()
    now = _utcnow()
    created: list[tuple[str, str]] = []  # (collection, document_id) for cleanup

    def check(label: str, ok: bool) -> None:
        print(f"  {'OK ' if ok else 'FAIL'} {label}")
        if not ok:
            raise AssertionError(label)

    try:
        # --- users -----------------------------------------------------------
        user = {
            "userId": "user_smoketest",
            "fullName": "Smoke Test",
            "email": "smoketest@example.com",
            "passwordHash": "not-a-real-hash",
            "role": "student",
            "status": "active",
            "createdAt": now,
            "updatedAt": now,
        }
        storage.create_user(user)
        created.append(("users", "user_smoketest"))
        check("create_user / find_user_by_id",
              storage.find_user_by_id("user_smoketest") is not None)
        check("find_user_by_email (case-insensitive)",
              storage.find_user_by_email("SMOKETEST@example.com") is not None)

        # --- auth sessions ---------------------------------------------------
        session = {
            "authSessionId": "auth_smoketest",
            "userId": "user_smoketest",
            "clientName": "smoke",
            "status": "active",
            "refreshTokenHash": "hash_original",
            "createdAt": now,
            "lastSeenAt": now,
            "expiresAt": now + timedelta(days=7),
        }
        storage.create_auth_session(session)
        created.append(("authSessions", "auth_smoketest"))
        check("find_auth_session_by_refresh_hash",
              storage.find_auth_session_by_refresh_hash("hash_original") is not None)

        storage.rotate_auth_session_refresh(
            "auth_smoketest", "hash_rotated", now + timedelta(days=7)
        )
        check("rotate: old hash gone",
              storage.find_auth_session_by_refresh_hash("hash_original") is None)
        check("rotate: new hash findable",
              storage.find_auth_session_by_refresh_hash("hash_rotated") is not None)

        storage.revoke_auth_session("auth_smoketest")
        revoked = storage.find_auth_session_by_id("auth_smoketest")
        check("revoke_auth_session", revoked is not None and revoked["status"] == "revoked")

        # --- learning sessions ------------------------------------------------
        storage.create_learning_session({
            "learningSessionId": "ls_smoketest",
            "userId": "user_smoketest",
            "sourceComponent": "code_coach",
            "taskId": None,
            "status": "active",
            "startedAt": now,
            "lastAnalysisAt": None,
        })
        created.append(("learningSessions", "ls_smoketest"))
        active = storage.find_active_learning_session("user_smoketest", "code_coach")
        check("find_active_learning_session",
              active is not None and active["learningSessionId"] == "ls_smoketest")
        storage.touch_learning_session("ls_smoketest")
        touched = storage.find_learning_session_by_id("ls_smoketest")
        check("touch_learning_session", touched is not None and touched["lastAnalysisAt"] is not None)

        # --- diagnostics: the active/resolved lifecycle ------------------------
        def diag(diagnostic_id: str, record_id: str) -> dict:
            return {
                "diagnosticRecordId": record_id,
                "diagnosticId": diagnostic_id,
                "userId": "user_smoketest",
                "learningSessionId": "ls_smoketest",
                "errorType": "OFF_BY_ONE_LOOP_BOUNDARY",
                "status": "active",
                "createdAt": now,
                "resolvedAt": None,
            }

        first = storage.sync_code_diagnostics(
            "user_smoketest", "ls_smoketest",
            [diag("cc_aaa", "rec_smoke_1"), diag("cc_bbb", "rec_smoke_2")],
        )
        created.append(("codeDiagnostics", "rec_smoke_1"))
        created.append(("codeDiagnostics", "rec_smoke_2"))
        check("sync #1: two newly detected", len(first.newly_detected_documents) == 2)

        second = storage.sync_code_diagnostics(
            "user_smoketest", "ls_smoketest",
            [diag("cc_aaa", "rec_smoke_3")],  # cc_bbb fixed by the student
        )
        check("sync #2: cc_bbb resolved",
              len(second.resolved_documents) == 1
              and second.resolved_documents[0]["diagnosticId"] == "cc_bbb")
        check("sync #2: cc_aaa still active, record id preserved",
              len(second.active_documents) == 1
              and second.active_documents[0]["diagnosticRecordId"] == "rec_smoke_1")
        check("list_diagnostics_for_user (status filter)",
              len(storage.list_diagnostics_for_user(
                  "user_smoketest", status="resolved")) == 1)

        # --- learning events ----------------------------------------------------
        storage.create_learning_events([{
            "eventId": "evt_smoketest",
            "userId": "user_smoketest",
            "learningSessionId": "ls_smoketest",
            "eventType": "hint_shown",
            "createdAt": now,
        }])
        created.append(("learningEvents", "evt_smoketest"))
        check("create/list learning events",
              len(storage.list_learning_events_for_user(
                  "user_smoketest", event_type="hint_shown")) == 1)

        # --- remediation triggers (dedupe on active) ----------------------------
        trigger = {
            "triggerId": "trig_smoketest",
            "userId": "user_smoketest",
            "triggerSource": "code_coach",
            "conceptTag": "loops",
            "errorType": "OFF_BY_ONE_LOOP_BOUNDARY",
            "status": "active",
            "createdAt": now,
            "interventionStatus": "pending",
        }
        _, created_new = storage.upsert_remediation_trigger(trigger)
        created.append(("remediationTriggers", "trig_smoketest"))
        check("remediation upsert: first insert", created_new is True)
        again = dict(trigger, triggerId="trig_smoketest_dup")
        merged, created_new = storage.upsert_remediation_trigger(again)
        check("remediation upsert: dedupe keeps original id",
              created_new is False and merged["triggerId"] == "trig_smoketest")

        # --- concept mastery -----------------------------------------------------
        mastery = {
            "masteryId": "mast_smoketest",
            "userId": "user_smoketest",
            "conceptTag": "loops",
            "masteryScore": 0.4,
            "createdAt": now,
            "lastUpdatedAt": now,
        }
        storage.upsert_concept_mastery(mastery)
        created.append(("conceptMastery", "mast_smoketest"))
        updated = storage.upsert_concept_mastery(dict(mastery, masteryScore=0.7,
                                                      masteryId="mast_smoketest_dup"))
        check("mastery upsert: same concept keeps original id",
              updated["masteryId"] == "mast_smoketest"
              and updated["masteryScore"] == 0.7)

        print("\nALL CHECKS PASSED — Firestore is wired correctly.")
        print(f"Project: {storage.client.project}")
        print("You can watch documents appear/disappear live in the Firebase "
              "console (Firestore Database -> Data).")
        return 0

    finally:
        print("\nCleaning up smoke-test documents...")
        for collection, document_id in created:
            storage.client.collection(collection).document(document_id).delete()
        storage.close()
        print("Cleanup done.")


if __name__ == "__main__":
    raise SystemExit(main())
