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
        self.assertEqual(
            "ARRAY_LENGTH_INDEX_MISUSE",
            summary_payload["top_error_types"][0]["error_type"],
        )
        self.assertEqual(
            "array_indexing",
            summary_payload["top_concepts"][0]["concept_tag"],
        )

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


if __name__ == "__main__":
    unittest.main()
