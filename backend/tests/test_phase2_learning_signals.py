import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.db.storage import InMemoryStorage


class Phase2LearningSignalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = InMemoryStorage()
        self.app = create_app(storage=self.storage)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()

    def register_user(
        self,
        *,
        full_name: str = "Signal Student",
        email: str = "signals@example.com",
        student_number: str = "it22990001",
    ) -> dict:
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": full_name,
                "email": email,
                "student_number": student_number,
                "password": "Password123",
                "client_name": "code-coach-test",
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def create_learning_session(self, access_token: str, task_id: str) -> str:
        response = self.client.post(
            "/api/v1/learning-sessions",
            json={
                "source_component": "code_coach",
                "language": "java",
                "task_id": task_id,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, response.status_code)
        return response.json()["learning_session_id"]

    def analyze_code(self, access_token: str, learning_session_id: str, code: str) -> dict:
        response = self.client.post(
            "/api/v1/code-coach/analyze",
            json={
                "language": "java",
                "code": code,
                "learning_session_id": learning_session_id,
                "enable_logging": False,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def create_learning_event(
        self,
        access_token: str,
        learning_session_id: str,
        *,
        event_type: str,
        concept_tag: str,
        payload: dict,
    ) -> dict:
        response = self.client.post(
            "/api/v1/events",
            json={
                "learning_session_id": learning_session_id,
                "component": "code_coach",
                "event_type": event_type,
                "concept_tag": concept_tag,
                "payload": payload,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def test_analysis_emits_learning_events_and_user_summary(self) -> None:
        auth_payload = self.register_user()
        access_token = auth_payload["tokens"]["access_token"]
        learning_session_id = self.create_learning_session(access_token, "arrays_lab_01")

        self.analyze_code(
            access_token,
            learning_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
        )

        detected_events_response = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "code_diagnostic_detected"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, detected_events_response.status_code)
        detected_events = detected_events_response.json()
        self.assertEqual(1, detected_events["total"])
        self.assertEqual(
            "ARRAY_LENGTH_INDEX_MISUSE",
            detected_events["events"][0]["payload"]["error_type"],
        )

        summary_response = self.client.get(
            "/api/v1/users/me/diagnostic-summary",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, summary_response.status_code)
        summary_payload = summary_response.json()
        self.assertEqual(1, summary_payload["total_diagnostics"])
        self.assertEqual(0, summary_payload["total_hint_events"])
        self.assertEqual(0, summary_payload["concepts_with_hint_usage"])
        self.assertEqual(
            "ARRAY_LENGTH_INDEX_MISUSE",
            summary_payload["top_error_types"][0]["error_type"],
        )
        self.assertEqual(
            "array_indexing",
            summary_payload["top_concepts"][0]["concept_tag"],
        )
        self.assertEqual(0, summary_payload["top_concepts"][0]["hint_event_count"])

        self.analyze_code(
            access_token,
            learning_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length - 1];}}",
        )

        resolved_events_response = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "diagnostic_resolved"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, resolved_events_response.status_code)
        resolved_events = resolved_events_response.json()
        self.assertEqual(1, resolved_events["total"])
        self.assertGreaterEqual(
            resolved_events["events"][0]["payload"]["time_to_fix_seconds"],
            0,
        )

    def test_concept_struggles_escalate_after_repeated_failures(self) -> None:
        auth_payload = self.register_user(
            email="repeat@example.com",
            student_number="it22990002",
        )
        access_token = auth_payload["tokens"]["access_token"]

        for task_id in ("arrays_lab_01", "arrays_lab_02", "arrays_lab_03"):
            learning_session_id = self.create_learning_session(access_token, task_id)
            self.analyze_code(
                access_token,
                learning_session_id,
                "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
            )

        struggles_response = self.client.get(
            "/api/v1/users/me/concept-struggles",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, struggles_response.status_code)
        struggles_payload = struggles_response.json()
        self.assertEqual(1, struggles_payload["total_concepts"])
        self.assertEqual(
            "array_indexing",
            struggles_payload["struggles"][0]["concept_tag"],
        )
        self.assertEqual(3, struggles_payload["struggles"][0]["repeat_count"])
        self.assertEqual("high", struggles_payload["struggles"][0]["struggle_level"])
        self.assertEqual(
            "trigger_study_guider",
            struggles_payload["struggles"][0]["recommended_action"],
        )

        triggers_response = self.client.get(
            "/api/v1/remediation/me/triggers",
            params={"status": "active", "trigger_source": "code_coach"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, triggers_response.status_code)
        triggers_payload = triggers_response.json()
        self.assertEqual(1, triggers_payload["total"])
        self.assertEqual(
            "array_indexing",
            triggers_payload["triggers"][0]["concept_tag"],
        )
        self.assertEqual(
            "ARRAY_LENGTH_INDEX_MISUSE",
            triggers_payload["triggers"][0]["error_type"],
        )
        self.assertEqual(
            "trigger_study_guider",
            triggers_payload["triggers"][0]["recommended_action"],
        )

        signal_events_response = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "struggle_signal_created"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, signal_events_response.status_code)
        self.assertEqual(1, signal_events_response.json()["total"])

        extra_session_id = self.create_learning_session(access_token, "arrays_lab_04")
        self.analyze_code(
            access_token,
            extra_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
        )

        triggers_response_after_repeat = self.client.get(
            "/api/v1/remediation/me/triggers",
            params={"status": "active", "trigger_source": "code_coach"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, triggers_response_after_repeat.status_code)
        self.assertEqual(1, triggers_response_after_repeat.json()["total"])

        signal_events_after_repeat = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "struggle_signal_created"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, signal_events_after_repeat.status_code)
        self.assertEqual(1, signal_events_after_repeat.json()["total"])

    def test_hint_interaction_events_can_be_recorded_and_filtered(self) -> None:
        auth_payload = self.register_user(
            email="hints@example.com",
            student_number="it22990003",
        )
        access_token = auth_payload["tokens"]["access_token"]
        learning_session_id = self.create_learning_session(access_token, "arrays_lab_04")

        self.create_learning_event(
            access_token,
            learning_session_id,
            event_type="hint_shown",
            concept_tag="array_indexing",
            payload={
                "diagnostic_id": "cc_test_001",
                "hint_level": "concept",
                "surface": "warning_popup",
            },
        )
        self.create_learning_event(
            access_token,
            learning_session_id,
            event_type="hint_navigation_used",
            concept_tag="array_indexing",
            payload={
                "diagnostic_id": "cc_test_001",
                "hint_level": "guidance",
                "direction": "next",
            },
        )

        shown_events_response = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "hint_shown"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, shown_events_response.status_code)
        shown_events_payload = shown_events_response.json()
        self.assertEqual(1, shown_events_payload["total"])
        self.assertEqual(
            "warning_popup",
            shown_events_payload["events"][0]["payload"]["surface"],
        )

        all_events_response = self.client.get(
            "/api/v1/events/me",
            params={"learning_session_id": learning_session_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, all_events_response.status_code)
        self.assertEqual(2, all_events_response.json()["total"])

        summary_response = self.client.get(
            "/api/v1/users/me/diagnostic-summary",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, summary_response.status_code)
        summary_payload = summary_response.json()
        self.assertEqual(0, summary_payload["total_diagnostics"])
        self.assertEqual(2, summary_payload["total_hint_events"])
        self.assertEqual(1, summary_payload["concepts_with_hint_usage"])

    def test_summary_and_struggles_include_hint_dependency_signals(self) -> None:
        auth_payload = self.register_user(
            email="dependency@example.com",
            student_number="it22990006",
        )
        access_token = auth_payload["tokens"]["access_token"]
        learning_session_id = self.create_learning_session(access_token, "arrays_lab_06")

        self.analyze_code(
            access_token,
            learning_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
        )
        self.create_learning_event(
            access_token,
            learning_session_id,
            event_type="hint_shown",
            concept_tag="array_indexing",
            payload={
                "diagnostic_id": "cc_test_003",
                "hint_level": "concept",
            },
        )
        self.create_learning_event(
            access_token,
            learning_session_id,
            event_type="hint_level_requested",
            concept_tag="array_indexing",
            payload={
                "diagnostic_id": "cc_test_003",
                "hint_level": "guidance",
            },
        )
        self.create_learning_event(
            access_token,
            learning_session_id,
            event_type="hint_navigation_used",
            concept_tag="array_indexing",
            payload={
                "diagnostic_id": "cc_test_003",
                "direction": "next",
            },
        )

        summary_response = self.client.get(
            "/api/v1/users/me/diagnostic-summary",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, summary_response.status_code)
        top_concept = summary_response.json()["top_concepts"][0]
        self.assertEqual("array_indexing", top_concept["concept_tag"])
        self.assertEqual(3, top_concept["hint_event_count"])
        self.assertEqual(1, top_concept["hint_shown_count"])
        self.assertEqual(1, top_concept["hint_request_count"])
        self.assertEqual(1, top_concept["hint_navigation_count"])
        self.assertGreater(top_concept["hint_dependency_score"], 0)
        self.assertIn(top_concept["hint_dependency_level"], {"medium", "high"})

        struggles_response = self.client.get(
            "/api/v1/users/me/concept-struggles",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, struggles_response.status_code)
        struggle = struggles_response.json()["struggles"][0]
        self.assertEqual(3, struggle["hint_event_count"])
        self.assertGreater(struggle["hint_dependency_score"], 0)
        self.assertIn(struggle["hint_dependency_level"], {"medium", "high"})

    def test_hint_interaction_event_rejects_another_users_session(self) -> None:
        first_user_auth = self.register_user(
            email="owner@example.com",
            student_number="it22990004",
        )
        first_access_token = first_user_auth["tokens"]["access_token"]
        learning_session_id = self.create_learning_session(
            first_access_token,
            "arrays_lab_05",
        )

        second_user_auth = self.register_user(
            email="intruder@example.com",
            student_number="it22990005",
        )
        second_access_token = second_user_auth["tokens"]["access_token"]

        response = self.client.post(
            "/api/v1/events",
            json={
                "learning_session_id": learning_session_id,
                "component": "code_coach",
                "event_type": "hint_shown",
                "concept_tag": "array_indexing",
                "payload": {
                    "diagnostic_id": "cc_test_002",
                    "hint_level": "concept",
                },
            },
            headers={"Authorization": f"Bearer {second_access_token}"},
        )
        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
