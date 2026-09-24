"""Keeping analysed code for research: only with consent, only when switched on.

The conditions are the whole feature, so each has its own test: collection
off, no salt, no decision, a decision under an older version, and withdrawal.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import research_consent
from app.core.config import get_settings
from app.db.storage import InMemoryStorage
from app.dev_tools.export_code_snapshots import exportable, label_row, mask_emails
from app.main import create_app
from app.services.research_collection import participant_id

LOGIN = """class Login {
    boolean check(String name) {
        if (name == "admin") {
            return true;
        }
        return false;
    }
}
"""


@pytest.fixture
def switched_on(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "research_collection_enabled", True)
    monkeypatch.setattr(settings, "research_id_salt", "test-salt-that-is-long-enough")


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def client(storage):
    return TestClient(create_app(storage=storage))


def student(client, email="ana@example.com"):
    registered = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ana", "email": email, "password": "Password123", "client_name": "test"},
    )
    body = registered.json()
    headers = {"Authorization": f"Bearer {body['tokens']['access_token']}"}
    session = client.post(
        "/api/v1/learning-sessions",
        json={"source_component": "code_coach", "language": "java", "task_id": "t"},
        headers=headers,
    )
    return headers, session.json()["learning_session_id"], body["user"]["user_id"]


def analyze(client, headers, session_id, code=LOGIN):
    response = client.post(
        "/api/v1/code-coach/analyze",
        json={"language": "java", "code": code, "learning_session_id": session_id},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["diagnostics"]


def decide(client, headers, decision):
    response = client.post("/api/v1/research/consent", json={"decision": decision}, headers=headers)
    assert response.status_code == 200
    return response.json()


def kept(storage):
    return storage.list_code_snapshots()


# ── When code is kept ────────────────────────────────────────────────────


def test_code_is_kept_with_consent_under_a_participant_code(client, storage, switched_on):
    headers, session_id, user_id = student(client)
    decide(client, headers, "GRANTED")

    analyze(client, headers, session_id)

    [snapshot] = kept(storage)
    assert snapshot["code"] == LOGIN
    assert snapshot["participant"] == participant_id(user_id)
    # Nothing that says who the student is.
    assert user_id not in str(snapshot) and "ana@example.com" not in str(snapshot)
    assert snapshot["findings"] and snapshot["findings"][0]["errorType"]


def test_nothing_is_kept_without_a_decision(client, storage, switched_on):
    headers, session_id, _ = student(client)
    analyze(client, headers, session_id)
    assert kept(storage) == []


def test_nothing_is_kept_while_collection_is_switched_off(client, storage):
    headers, session_id, _ = student(client)
    state = decide(client, headers, "GRANTED")

    analyze(client, headers, session_id)

    assert state["collecting"] is False
    assert kept(storage) == []


def test_nothing_is_kept_without_a_salt(client, storage, monkeypatch):
    monkeypatch.setattr(get_settings(), "research_collection_enabled", True)
    monkeypatch.setattr(get_settings(), "research_id_salt", None)
    headers, session_id, _ = student(client)
    decide(client, headers, "GRANTED")

    analyze(client, headers, session_id)

    assert kept(storage) == []


def test_agreeing_to_older_wording_does_not_count(client, storage, switched_on, monkeypatch):
    headers, session_id, _ = student(client)
    decide(client, headers, "GRANTED")
    # The statement changes after they agreed.
    monkeypatch.setattr("app.services.research_collection.RESEARCH_CONSENT_VERSION", "v-next")
    monkeypatch.setattr("app.api.routes.research.RESEARCH_CONSENT_VERSION", "v-next")

    analyze(client, headers, session_id)

    assert kept(storage) == []
    assert client.get("/api/v1/research/consent", headers=headers).json()["decision"] is None


def test_an_unchanged_file_is_kept_once(client, storage, switched_on):
    headers, session_id, _ = student(client)
    decide(client, headers, "GRANTED")

    analyze(client, headers, session_id)
    analyze(client, headers, session_id)
    analyze(client, headers, session_id, LOGIN.replace("admin", "root"))

    snapshots = kept(storage)
    assert len(snapshots) == 2
    assert sorted(s["timesAnalysed"] for s in snapshots) == [1, 2]


def test_withdrawing_deletes_what_was_kept(client, storage, switched_on):
    headers, session_id, _ = student(client)
    decide(client, headers, "GRANTED")
    analyze(client, headers, session_id)
    assert client.get("/api/v1/research/consent", headers=headers).json()["files_kept"] == 1

    state = decide(client, headers, "DECLINED")

    assert state["files_kept"] == 0
    assert kept(storage) == []
    analyze(client, headers, session_id)
    assert kept(storage) == []


def test_the_page_gets_the_exact_statement_and_version(client):
    headers, _, _ = student(client)
    state = client.get("/api/v1/research/consent", headers=headers).json()

    assert state["version"] == research_consent.RESEARCH_CONSENT_VERSION
    assert state["statement"]["title"]
    assert state["decision"] is None


# ── Export ───────────────────────────────────────────────────────────────


def test_export_takes_only_students_whose_current_decision_is_yes(switched_on):
    now = "2026-09-25T10:00:00"
    consents = [
        {"userId": "u_yes", "decision": "GRANTED", "version": research_consent.RESEARCH_CONSENT_VERSION, "decidedAt": now},
        {"userId": "u_no", "decision": "DECLINED", "version": research_consent.RESEARCH_CONSENT_VERSION, "decidedAt": now},
        {"userId": "u_old", "decision": "GRANTED", "version": "older", "decidedAt": now},
    ]
    snapshots = [{"participant": participant_id(u), "snapshotId": u} for u in ("u_yes", "u_no", "u_old")]

    assert [s["snapshotId"] for s in exportable(snapshots, consents)] == ["u_yes"]


def test_export_masks_emails_and_leaves_labels_for_the_rater():
    assert mask_emails("// by ana.s@uni.lk\nint x;") == "// by [email removed]\nint x;"

    row = label_row(
        {
            "snapshotId": "snap_1",
            "participant": "p_1",
            "findings": [{"errorType": "INCORRECT_CONDITIONAL_OPERATOR", "line": 3, "disputed": True}],
        },
        "snippets/snap_1.java",
    )
    assert row["detector_findings"] == "INCORRECT_CONDITIONAL_OPERATOR@line3"
    assert row["disputed_findings"] == "INCORRECT_CONDITIONAL_OPERATOR@line3"
    assert row["has_off_by_one"] == "" and row["rater"] == ""


def test_export_refuses_a_folder_inside_the_repository(tmp_path):
    from app.dev_tools import export_code_snapshots

    inside = export_code_snapshots.PROJECT_ROOT / "data" / "ml" / "raw_snippets_real"
    assert export_code_snapshots.main(["--out", str(inside), "--dry-run"]) == 2
