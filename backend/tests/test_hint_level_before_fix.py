"""A fix records how far into the hints the student had gone before making it.

Fixing a mistake unaided, after the concept hint, or only once the targeted
hint had all but pointed at the line are different outcomes. Time to fix
cannot tell them apart; hint_level_before_fix on diagnostic_resolved can.
"""

import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db.storage import InMemoryStorage
from app.main import create_app
from app.services.learning_signal_service import deepest_hint_level_before

LOGIN = """class Login {
    boolean check(String name) {
        if (name == "admin") {
            return true;
        }
        return false;
    }
}
"""
FIXED = LOGIN.replace('name == "admin"', 'name.equals("admin")')

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def hint(level: str, diagnostic_id: str = "cc_a", *, event_type: str = "hint_level_requested", at: datetime = NOW) -> dict:
    return {"eventType": event_type, "occurredAt": at, "payload": {"diagnostic_id": diagnostic_id, "hint_level": level}}


class DeepestLevelTests(unittest.TestCase):
    def test_no_hints_is_none(self) -> None:
        self.assertEqual("none", deepest_hint_level_before([], "cc_a", NOW))

    def test_the_deepest_level_counts_whatever_the_order(self) -> None:
        events = [hint("targeted"), hint("concept"), hint("guidance")]
        self.assertEqual("targeted", deepest_hint_level_before(events, "cc_a", NOW))

    def test_a_popup_showing_the_concept_counts(self) -> None:
        self.assertEqual("concept", deepest_hint_level_before([hint("concept", event_type="hint_shown")], "cc_a", NOW))

    def test_hints_about_another_finding_do_not_count(self) -> None:
        self.assertEqual("none", deepest_hint_level_before([hint("targeted", "cc_other")], "cc_a", NOW))

    def test_a_hint_opened_after_the_fix_does_not_count(self) -> None:
        events = [hint("concept"), hint("targeted", at=NOW + timedelta(minutes=5))]
        self.assertEqual("concept", deepest_hint_level_before(events, "cc_a", NOW))

    def test_other_event_types_and_unknown_levels_are_ignored(self) -> None:
        events = [hint("targeted", event_type="code_diagnostic_detected"), hint("everything")]
        self.assertEqual("none", deepest_hint_level_before(events, "cc_a", NOW))


class ThroughTheApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(storage=InMemoryStorage()))
        registered = self.client.post(
            "/api/v1/auth/register",
            json={"full_name": "Hint Student", "email": "hints@example.com", "password": "Password123", "client_name": "code-coach-test"},
        )
        self.headers = {"Authorization": f"Bearer {registered.json()['tokens']['access_token']}"}
        self.session_id = self.client.post(
            "/api/v1/learning-sessions",
            json={"source_component": "code_coach", "language": "java", "task_id": "login_lab"},
            headers=self.headers,
        ).json()["learning_session_id"]

    def tearDown(self) -> None:
        self.client.close()

    def analyze(self, code: str) -> list[dict]:
        response = self.client.post(
            "/api/v1/code-coach/analyze",
            json={"language": "java", "code": code, "learning_session_id": self.session_id, "enable_logging": False},
            headers=self.headers,
        )
        self.assertEqual(200, response.status_code)
        return response.json()["diagnostics"]

    def send_hint(self, diagnostic_id: str, level: str) -> None:
        response = self.client.post(
            "/api/v1/events",
            json={
                "learning_session_id": self.session_id,
                "event_type": "hint_level_requested",
                "concept_tag": "string_comparison",
                "payload": {"diagnostic_id": diagnostic_id, "hint_level": level},
            },
            headers=self.headers,
        )
        self.assertEqual(200, response.status_code)

    def resolved_payload(self) -> dict:
        response = self.client.get("/api/v1/events/me", params={"event_type": "diagnostic_resolved"}, headers=self.headers)
        [event] = response.json()["events"]
        return event["payload"]

    def test_a_fix_after_the_guidance_hint_records_guidance(self) -> None:
        [finding] = self.analyze(LOGIN)
        self.send_hint(finding["diagnostic_id"], "concept")
        self.send_hint(finding["diagnostic_id"], "guidance")

        # An edit elsewhere first: under line-based ids this alone "resolved"
        # the finding, and the hints above belonged to a record already closed.
        self.analyze(LOGIN.replace("class Login {\n", "class Login {\n    // thinking\n"))
        self.assertEqual([], self.analyze(FIXED))

        self.assertEqual("guidance", self.resolved_payload()["hint_level_before_fix"])

    def test_a_fix_with_no_hints_records_none(self) -> None:
        self.analyze(LOGIN)
        self.analyze(FIXED)

        self.assertEqual("none", self.resolved_payload()["hint_level_before_fix"])


if __name__ == "__main__":
    unittest.main()
