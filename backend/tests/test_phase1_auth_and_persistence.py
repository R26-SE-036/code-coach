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

    def register_user(
        self,
        *,
        full_name: str = "Sample Student",
        email: str = "student@example.com",
        student_number: str = "it22203380",
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

    def create_learning_session(
        self,
        access_token: str,
        *,
        task_id: str = "arrays_lab_01",
    ) -> dict:
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
        return response.json()

    def analyze_code(
        self,
        access_token: str,
        learning_session_id: str,
        code: str,
    ) -> dict:
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

    def test_register_create_session_and_persist_diagnostics(self) -> None:
        auth_payload = self.register_user()
        access_token = auth_payload["tokens"]["access_token"]
        user_id = auth_payload["user"]["user_id"]

        learning_session = self.create_learning_session(access_token)
        learning_session_id = learning_session["learning_session_id"]

        analyze_payload = self.analyze_code(
            access_token,
            learning_session_id,
            (
                "class A{void m(){int[] a={1,2};"
                "for(int i=0;i<=a.length;i++){System.out.println(a[i]);}}}"
            ),
        )
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

    def test_diagnostic_read_endpoints_return_only_authenticated_user_data(self) -> None:
        auth_payload = self.register_user()
        access_token = auth_payload["tokens"]["access_token"]
        learning_session = self.create_learning_session(access_token)
        learning_session_id = learning_session["learning_session_id"]

        self.analyze_code(
            access_token,
            learning_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
        )

        my_diagnostics_response = self.client.get(
            "/api/v1/diagnostics/me",
            params={
                "learning_session_id": learning_session_id,
                "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
                "status": "active",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, my_diagnostics_response.status_code)
        my_diagnostics_payload = my_diagnostics_response.json()
        self.assertEqual(1, my_diagnostics_payload["total"])
        self.assertEqual(
            "ARRAY_LENGTH_INDEX_MISUSE",
            my_diagnostics_payload["diagnostics"][0]["error_type"],
        )
        self.assertEqual(
            learning_session_id,
            my_diagnostics_payload["diagnostics"][0]["learning_session_id"],
        )

        session_diagnostics_response = self.client.get(
            f"/api/v1/learning-sessions/{learning_session_id}/diagnostics",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, session_diagnostics_response.status_code)
        session_diagnostics_payload = session_diagnostics_response.json()
        self.assertEqual(1, session_diagnostics_payload["total"])

        self.analyze_code(
            access_token,
            learning_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length - 1];}}",
        )

        resolved_response = self.client.get(
            "/api/v1/diagnostics/me",
            params={
                "learning_session_id": learning_session_id,
                "status": "resolved",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, resolved_response.status_code)
        resolved_payload = resolved_response.json()
        self.assertEqual(1, resolved_payload["total"])
        self.assertEqual("resolved", resolved_payload["diagnostics"][0]["status"])

    def test_learning_session_diagnostics_enforce_session_ownership(self) -> None:
        first_user_auth = self.register_user()
        first_access_token = first_user_auth["tokens"]["access_token"]
        first_session = self.create_learning_session(first_access_token)
        first_learning_session_id = first_session["learning_session_id"]

        self.analyze_code(
            first_access_token,
            first_learning_session_id,
            (
                "class A{void m(){int[] a={1,2};"
                "for(int i=0;i<=a.length;i++){System.out.println(a[i]);}}}"
            ),
        )

        second_user_auth = self.register_user(
            full_name="Second Student",
            email="second@example.com",
            student_number="it22230942",
        )
        second_access_token = second_user_auth["tokens"]["access_token"]

        forbidden_response = self.client.get(
            f"/api/v1/learning-sessions/{first_learning_session_id}/diagnostics",
            headers={"Authorization": f"Bearer {second_access_token}"},
        )
        self.assertEqual(404, forbidden_response.status_code)

        second_user_diagnostics_response = self.client.get(
            "/api/v1/diagnostics/me",
            headers={"Authorization": f"Bearer {second_access_token}"},
        )
        self.assertEqual(200, second_user_diagnostics_response.status_code)
        self.assertEqual(0, second_user_diagnostics_response.json()["total"])

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
