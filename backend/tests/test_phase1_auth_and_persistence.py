import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.storage import InMemoryStorage


class Phase1AuthAndPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = InMemoryStorage()
        self.app = create_app(storage=self.storage)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()

    def register_user(self) -> dict:
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Sample Student",
                "email": "student@example.com",
                "student_number": "it22203380",
                "password": "Password123",
                "client_name": "code-coach-test",
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def create_learning_session(self, access_token: str) -> dict:
        response = self.client.post(
            "/api/v1/learning-sessions",
            json={
                "source_component": "code_coach",
                "language": "java",
                "task_id": "arrays_lab_01",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def test_register_create_session_and_persist_diagnostics(self) -> None:
        auth_payload = self.register_user()
        access_token = auth_payload["tokens"]["access_token"]
        user_id = auth_payload["user"]["user_id"]

        learning_session = self.create_learning_session(access_token)
        learning_session_id = learning_session["learning_session_id"]

        analyze_response = self.client.post(
            "/api/v1/code-coach/analyze",
            json={
                "language": "java",
                "code": (
                    "class A{void m(){int[] a={1,2};"
                    "for(int i=0;i<=a.length;i++){System.out.println(a[i]);}}}"
                ),
                "learning_session_id": learning_session_id,
                "enable_logging": False,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, analyze_response.status_code)
        analyze_payload = analyze_response.json()
        self.assertEqual("ok", analyze_payload["status"])
        self.assertEqual(learning_session_id, analyze_payload["learning_session_id"])
        self.assertGreater(len(analyze_payload["diagnostics"]), 0)

        stored_diagnostics = self.storage.list_diagnostics_for_session(
            learning_session_id,
            user_id=user_id,
        )
        self.assertGreater(len(stored_diagnostics), 0)
        stored_diagnostic = stored_diagnostics[0]

        self.assertEqual(user_id, stored_diagnostic["userId"])
        self.assertEqual(learning_session_id, stored_diagnostic["learningSessionId"])
        self.assertIn("codeContextHash", stored_diagnostic)
        self.assertNotIn("codeContext", stored_diagnostic)
        self.assertEqual("active", stored_diagnostic["status"])

        session_document = self.storage.find_learning_session_by_id(learning_session_id)
        self.assertIsNotNone(session_document)
        self.assertIsNotNone(session_document.get("lastAnalysisAt"))

    def test_refresh_then_logout_revokes_authenticated_routes(self) -> None:
        auth_payload = self.register_user()
        access_token = auth_payload["tokens"]["access_token"]
        refresh_token = auth_payload["tokens"]["refresh_token"]

        me_response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, me_response.status_code)

        refresh_response = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        self.assertEqual(200, refresh_response.status_code)
        refreshed_access_token = refresh_response.json()["tokens"]["access_token"]

        logout_response = self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {refreshed_access_token}"},
        )
        self.assertEqual(200, logout_response.status_code)

        revoked_me_response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refreshed_access_token}"},
        )
        self.assertEqual(401, revoked_me_response.status_code)


if __name__ == "__main__":
    unittest.main()
