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
    ) -> dict:
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": full_name,
                "email": email,
                "password": "Password123",
                "client_name": "code-coach-test",
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def create_learning_session(
        self,
        access_token: str,
        task_id: str,
        *,
        source_component: str = "code_coach",
    ) -> str:
        response = self.client.post(
            "/api/v1/learning-sessions",
            json={
                "source_component": source_component,
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
        component: str = "code_coach",
        event_type: str,
        concept_tag: str,
        payload: dict,
    ) -> dict:
        response = self.client.post(
            "/api/v1/events",
            json={
                "learning_session_id": learning_session_id,
                "component": component,
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
            "/api/v1/students/me/diagnostics/summary",
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
            "/api/v1/students/me/struggling-concepts",
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

        recommendations_response = self.client.get(
            "/api/v1/remediation/me/recommendations",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, recommendations_response.status_code)
        recommendations_payload = recommendations_response.json()
        self.assertEqual(1, recommendations_payload["total"])
        recommendation = recommendations_payload["recommendations"][0]
        self.assertEqual("array_indexing", recommendation["concept_tag"])
        self.assertEqual(
            "lesson_arrays_01",
            recommendation["lesson"]["lesson_id"],
        )
        self.assertEqual(
            "quiz_arrays_01",
            recommendation["quiz"]["quiz_id"],
        )
        self.assertEqual("high", recommendation["priority"])
        self.assertIn("array_indexing", recommendation["rationale"])

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
            "/api/v1/students/me/diagnostics/summary",
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
            "/api/v1/students/me/diagnostics/summary",
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
            "/api/v1/students/me/struggling-concepts",
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
        )
        first_access_token = first_user_auth["tokens"]["access_token"]
        learning_session_id = self.create_learning_session(
            first_access_token,
            "arrays_lab_05",
        )

        second_user_auth = self.register_user(
            email="intruder@example.com",
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

    def test_study_guider_feedback_loop_updates_trigger_lifecycle(self) -> None:
        auth_payload = self.register_user(
            email="loop@example.com",
        )
        access_token = auth_payload["tokens"]["access_token"]

        for task_id in ("arrays_lab_07", "arrays_lab_08", "arrays_lab_09"):
            learning_session_id = self.create_learning_session(access_token, task_id)
            self.analyze_code(
                access_token,
                learning_session_id,
                "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
            )

        recommendations_response = self.client.get(
            "/api/v1/remediation/me/recommendations",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, recommendations_response.status_code)
        recommendation = recommendations_response.json()["recommendations"][0]
        trigger_id = recommendation["trigger_id"]
        lesson_id = recommendation["lesson"]["lesson_id"]
        quiz_id = recommendation["quiz"]["quiz_id"]

        lesson_opened_response = self.client.post(
            f"/api/v1/remediation/me/triggers/{trigger_id}/lesson-opened",
            json={"lesson_id": lesson_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, lesson_opened_response.status_code)
        lesson_payload = lesson_opened_response.json()
        self.assertEqual("lesson_opened", lesson_payload["trigger"]["intervention_status"])
        self.assertEqual(lesson_id, lesson_payload["trigger"]["lesson_id"])
        self.assertEqual(["micro_lesson_viewed"], lesson_payload["created_event_types"])

        lesson_events_response = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "micro_lesson_viewed"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, lesson_events_response.status_code)
        self.assertEqual(1, lesson_events_response.json()["total"])

        quiz_completed_response = self.client.post(
            f"/api/v1/remediation/me/triggers/{trigger_id}/quiz-completed",
            json={"quiz_id": quiz_id, "score_percent": 84},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, quiz_completed_response.status_code)
        quiz_payload = quiz_completed_response.json()
        self.assertEqual("completed", quiz_payload["trigger"]["status"])
        self.assertEqual(
            "quiz_completed_passed",
            quiz_payload["trigger"]["intervention_status"],
        )
        self.assertEqual(quiz_id, quiz_payload["trigger"]["quiz_id"])
        self.assertEqual(84, quiz_payload["trigger"]["quiz_score_percent"])
        self.assertTrue(quiz_payload["trigger"]["quiz_passed"])
        self.assertEqual(
            ["quiz_completed", "mastery_updated"],
            quiz_payload["created_event_types"],
        )

        active_triggers_response = self.client.get(
            "/api/v1/remediation/me/triggers",
            params={"status": "active", "trigger_source": "code_coach"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, active_triggers_response.status_code)
        self.assertEqual(0, active_triggers_response.json()["total"])

        completed_triggers_response = self.client.get(
            "/api/v1/remediation/me/triggers",
            params={"status": "completed", "trigger_source": "code_coach"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, completed_triggers_response.status_code)
        self.assertEqual(1, completed_triggers_response.json()["total"])

        recommendations_after_completion = self.client.get(
            "/api/v1/remediation/me/recommendations",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, recommendations_after_completion.status_code)
        self.assertEqual(0, recommendations_after_completion.json()["total"])

        quiz_events_response = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "quiz_completed"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, quiz_events_response.status_code)
        self.assertEqual(1, quiz_events_response.json()["total"])

        mastery_events_response = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "mastery_updated"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, mastery_events_response.status_code)
        self.assertEqual(1, mastery_events_response.json()["total"])

        mastery_response = self.client.get(
            "/api/v1/students/me/concept-mastery",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, mastery_response.status_code)
        mastery_payload = mastery_response.json()
        self.assertEqual(1, mastery_payload["total_concepts"])
        concept = mastery_payload["concepts"][0]
        self.assertEqual("array_indexing", concept["concept_tag"])
        self.assertEqual(0.84, concept["mastery_score"])
        self.assertEqual(0.16, concept["struggle_score"])
        self.assertEqual("strong", concept["mastery_level"])
        self.assertEqual("quiz_completed", concept["update_source"])
        self.assertEqual(quiz_id, concept["last_quiz_id"])
        self.assertEqual(84, concept["last_quiz_score_percent"])
        self.assertTrue(concept["last_quiz_passed"])

    def test_gamification_recommendations_use_concept_struggles(self) -> None:
        auth_payload = self.register_user(
            email="game-struggle@example.com",
        )
        access_token = auth_payload["tokens"]["access_token"]

        for task_id in ("arrays_game_01", "arrays_game_02", "arrays_game_03"):
            learning_session_id = self.create_learning_session(access_token, task_id)
            self.analyze_code(
                access_token,
                learning_session_id,
                "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
            )

        recommendations_response = self.client.get(
            "/api/v1/gamification/me/recommendations",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, recommendations_response.status_code)
        payload = recommendations_response.json()
        self.assertGreaterEqual(payload["total"], 1)
        recommendation = payload["recommendations"][0]
        self.assertEqual("array_indexing", recommendation["concept_tag"])
        self.assertEqual("concept_struggle", recommendation["recommendation_source"])
        self.assertEqual("remediation", recommendation["adaptation_goal"])
        self.assertEqual("bug_hunt", recommendation["game_type"])
        self.assertEqual("beginner", recommendation["difficulty_level"])
        self.assertEqual("high", recommendation["support_level"])
        self.assertEqual("high", recommendation["priority"])

    def test_gamification_recommendations_shift_to_mastery_reinforcement(self) -> None:
        auth_payload = self.register_user(
            email="game-mastery@example.com",
        )
        access_token = auth_payload["tokens"]["access_token"]
        session_ids: list[str] = []

        for task_id in ("arrays_game_04", "arrays_game_05", "arrays_game_06"):
            learning_session_id = self.create_learning_session(access_token, task_id)
            session_ids.append(learning_session_id)
            self.analyze_code(
                access_token,
                learning_session_id,
                "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
            )

        recommendations_response = self.client.get(
            "/api/v1/remediation/me/recommendations",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, recommendations_response.status_code)
        recommendation = recommendations_response.json()["recommendations"][0]
        trigger_id = recommendation["trigger_id"]
        quiz_id = recommendation["quiz"]["quiz_id"]

        for learning_session_id in session_ids:
            self.analyze_code(
                access_token,
                learning_session_id,
                "class A{void m(){int[] a={1,2}; int x=a[a.length - 1];}}",
            )

        quiz_completed_response = self.client.post(
            f"/api/v1/remediation/me/triggers/{trigger_id}/quiz-completed",
            json={"quiz_id": quiz_id, "score_percent": 84},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, quiz_completed_response.status_code)

        gamification_response = self.client.get(
            "/api/v1/gamification/me/recommendations",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, gamification_response.status_code)
        payload = gamification_response.json()
        self.assertGreaterEqual(payload["total"], 1)
        recommendation = payload["recommendations"][0]
        self.assertEqual("array_indexing", recommendation["concept_tag"])
        self.assertEqual("mastery_summary", recommendation["recommendation_source"])
        self.assertEqual("reinforcement", recommendation["adaptation_goal"])
        self.assertEqual("strong", recommendation["based_on_mastery_level"])
        self.assertEqual("intermediate", recommendation["difficulty_level"])
        self.assertEqual("light", recommendation["support_level"])
        self.assertEqual("low", recommendation["priority"])

    def test_gamification_feedback_loop_records_events_and_updates_mastery(self) -> None:
        auth_payload = self.register_user(
            email="game-feedback@example.com",
        )
        access_token = auth_payload["tokens"]["access_token"]
        learning_session_id = self.create_learning_session(
            access_token,
            "loops_game_01",
            source_component="adaptive_gamification",
        )

        adaptation_response = self.client.post(
            "/api/v1/gamification/me/adaptation-decisions",
            json={
                "learning_session_id": learning_session_id,
                "concept_tag": "loop_boundaries",
                "recommendation_id": "grec_demo_01",
                "game_id": "game_loops_trace_01",
                "game_type": "loop_tracer",
                "difficulty_level": "beginner",
                "support_level": "high",
                "rationale": "Repeated off-by-one issues need guided practice.",
                "based_on_struggle_level": "high",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, adaptation_response.status_code)
        self.assertEqual(
            ["game_adaptation_decision_created"],
            adaptation_response.json()["created_event_types"],
        )

        adaptation_events = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "game_adaptation_decision_created"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, adaptation_events.status_code)
        self.assertEqual(1, adaptation_events.json()["total"])
        self.assertEqual(
            "adaptive_gamification",
            adaptation_events.json()["events"][0]["component"],
        )

        result_response = self.client.post(
            "/api/v1/gamification/me/session-results",
            json={
                "learning_session_id": learning_session_id,
                "concept_tag": "loop_boundaries",
                "recommendation_id": "grec_demo_01",
                "game_id": "game_loops_trace_01",
                "game_type": "loop_tracer",
                "difficulty_level": "beginner",
                "support_level": "high",
                "score_percent": 76,
                "error_count": 1,
                "attempt_count": 1,
                "hint_usage": 1,
                "time_taken_seconds": 140
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, result_response.status_code)
        result_payload = result_response.json()
        self.assertEqual(
            ["game_session_completed", "mastery_updated"],
            result_payload["created_event_types"],
        )
        self.assertEqual("loop_boundaries", result_payload["mastery"]["concept_tag"])
        self.assertEqual("game_session_completed", result_payload["mastery"]["update_source"])
        self.assertEqual("game_loops_trace_01", result_payload["mastery"]["last_game_id"])
        self.assertEqual("loop_tracer", result_payload["mastery"]["last_game_type"])
        self.assertEqual(76, result_payload["mastery"]["last_game_score_percent"])
        self.assertEqual("beginner", result_payload["mastery"]["last_game_difficulty_level"])
        self.assertEqual(0.73, result_payload["mastery"]["mastery_score"])
        self.assertEqual(0.27, result_payload["mastery"]["struggle_score"])
        self.assertEqual("developing", result_payload["mastery"]["mastery_level"])

        completed_events = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "game_session_completed"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, completed_events.status_code)
        self.assertEqual(1, completed_events.json()["total"])

        mastery_response = self.client.get(
            "/api/v1/students/me/concept-mastery",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, mastery_response.status_code)
        mastery_payload = mastery_response.json()
        self.assertEqual(1, mastery_payload["total_concepts"])
        concept = mastery_payload["concepts"][0]
        self.assertEqual("loop_boundaries", concept["concept_tag"])
        self.assertEqual("game_session_completed", concept["update_source"])
        self.assertEqual("game_loops_trace_01", concept["last_game_id"])
        self.assertEqual(76, concept["last_game_score_percent"])

    def test_collaboration_prompts_use_code_coach_diagnostics(self) -> None:
        auth_payload = self.register_user(
            email="collab-prompts@example.com",
        )
        access_token = auth_payload["tokens"]["access_token"]
        learning_session_id = self.create_learning_session(access_token, "arrays_collab_01")
        analysis_response = self.analyze_code(
            access_token,
            learning_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
        )
        diagnostic_id = analysis_response["diagnostics"][0]["diagnostic_id"]

        prompts_response = self.client.get(
            "/api/v1/collaboration/me/prompts",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, prompts_response.status_code)
        payload = prompts_response.json()
        self.assertGreaterEqual(payload["total"], 1)
        prompt = payload["prompts"][0]
        self.assertEqual("array_indexing", prompt["concept_tag"])
        self.assertEqual("reasoning_prompt", prompt["prompt_type"])
        self.assertEqual("pair_programming", prompt["collaboration_mode"])
        self.assertEqual(diagnostic_id, prompt["linked_diagnostic_id"])
        self.assertEqual("high", prompt["priority"])

    def test_collaboration_feedback_loop_records_pair_session_prompt_and_review(self) -> None:
        auth_payload = self.register_user(
            email="collab-feedback@example.com",
        )
        access_token = auth_payload["tokens"]["access_token"]
        code_session_id = self.create_learning_session(access_token, "arrays_collab_02")
        analysis_response = self.analyze_code(
            access_token,
            code_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
        )
        diagnostic_id = analysis_response["diagnostics"][0]["diagnostic_id"]

        collab_session_id = self.create_learning_session(
            access_token,
            "arrays_collab_web_01",
            source_component="collaborative_studio",
        )
        pair_session_response = self.client.post(
            "/api/v1/collaboration/me/pair-sessions",
            json={
                "learning_session_id": collab_session_id,
                "collaboration_mode": "pair_programming",
                "partner_user_id": "peer_001",
                "task_id": "arrays_collab_web_01",
                "linked_learning_session_id": code_session_id,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, pair_session_response.status_code)
        pair_payload = pair_session_response.json()
        self.assertEqual(["pair_session_started"], pair_payload["created_event_types"])
        pair_session_id = pair_payload["session"]["pair_session_id"]
        self.assertEqual(code_session_id, pair_payload["session"]["linked_learning_session_id"])

        prompt_shown_response = self.client.post(
            "/api/v1/collaboration/me/prompts/shown",
            json={
                "learning_session_id": collab_session_id,
                "pair_session_id": pair_session_id,
                "prompt_id": "cpr_demo_01",
                "prompt_type": "reasoning_prompt",
                "concept_tag": "array_indexing",
                "linked_diagnostic_id": diagnostic_id,
                "linked_learning_session_id": code_session_id,
                "target_role": "navigator",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, prompt_shown_response.status_code)
        self.assertEqual(
            ["collaboration_prompt_shown"],
            prompt_shown_response.json()["created_event_types"],
        )

        review_response = self.client.post(
            "/api/v1/collaboration/me/peer-reviews",
            json={
                "learning_session_id": collab_session_id,
                "pair_session_id": pair_session_id,
                "concept_tag": "array_indexing",
                "linked_diagnostic_id": diagnostic_id,
                "linked_learning_session_id": code_session_id,
                "rubric_score": 4,
                "feedback_quality_score": 0.82,
                "review_comment": "The reviewer correctly explained the safe last index.",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, review_response.status_code)
        self.assertEqual(
            ["peer_review_submitted"],
            review_response.json()["created_event_types"],
        )

        pair_events = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "pair_session_started"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, pair_events.status_code)
        self.assertEqual(1, pair_events.json()["total"])
        self.assertEqual("collaborative_studio", pair_events.json()["events"][0]["component"])

        prompt_events = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "collaboration_prompt_shown"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, prompt_events.status_code)
        self.assertEqual(1, prompt_events.json()["total"])

        review_events = self.client.get(
            "/api/v1/events/me",
            params={"event_type": "peer_review_submitted"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, review_events.status_code)
        self.assertEqual(1, review_events.json()["total"])

        stored_session = self.storage.find_collaboration_session_by_id(pair_session_id)
        self.assertIsNotNone(stored_session)
        self.assertEqual(code_session_id, stored_session["linkedLearningSessionId"])
        self.assertEqual("active", stored_session["status"])

    def test_dashboard_overview_summarizes_cross_component_activity(self) -> None:
        auth_payload = self.register_user(
            email="dashboard@example.com",
        )
        access_token = auth_payload["tokens"]["access_token"]

        code_session_id = self.create_learning_session(access_token, "dashboard_code_01")
        analysis_response = self.analyze_code(
            access_token,
            code_session_id,
            "class A{void m(){int[] a={1,2}; int x=a[a.length];}}",
        )
        diagnostic_id = analysis_response["diagnostics"][0]["diagnostic_id"]
        self.create_learning_event(
            access_token,
            code_session_id,
            event_type="hint_shown",
            concept_tag="array_indexing",
            payload={"diagnostic_id": diagnostic_id, "hint_level": "concept"},
        )

        collab_session_id = self.create_learning_session(
            access_token,
            "dashboard_collab_01",
            source_component="collaborative_studio",
        )
        pair_session_response = self.client.post(
            "/api/v1/collaboration/me/pair-sessions",
            json={
                "learning_session_id": collab_session_id,
                "collaboration_mode": "pair_programming",
                "partner_user_id": "peer_002",
                "task_id": "dashboard_collab_01",
                "linked_learning_session_id": code_session_id,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, pair_session_response.status_code)
        pair_session_id = pair_session_response.json()["session"]["pair_session_id"]

        prompt_shown_response = self.client.post(
            "/api/v1/collaboration/me/prompts/shown",
            json={
                "learning_session_id": collab_session_id,
                "pair_session_id": pair_session_id,
                "prompt_id": "cpr_dash_01",
                "prompt_type": "reasoning_prompt",
                "concept_tag": "array_indexing",
                "linked_diagnostic_id": diagnostic_id,
                "linked_learning_session_id": code_session_id,
                "target_role": "navigator",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, prompt_shown_response.status_code)

        review_response = self.client.post(
            "/api/v1/collaboration/me/peer-reviews",
            json={
                "learning_session_id": collab_session_id,
                "pair_session_id": pair_session_id,
                "concept_tag": "array_indexing",
                "linked_diagnostic_id": diagnostic_id,
                "linked_learning_session_id": code_session_id,
                "rubric_score": 4,
                "feedback_quality_score": 0.8,
                "review_comment": "Solid review of the array boundary issue.",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, review_response.status_code)

        game_session_id = self.create_learning_session(
            access_token,
            "dashboard_game_01",
            source_component="adaptive_gamification",
        )
        game_result_response = self.client.post(
            "/api/v1/gamification/me/session-results",
            json={
                "learning_session_id": game_session_id,
                "concept_tag": "loop_boundaries",
                "game_id": "game_loops_trace_01",
                "game_type": "loop_tracer",
                "difficulty_level": "beginner",
                "support_level": "guided",
                "score_percent": 76,
                "error_count": 1,
                "attempt_count": 1,
                "hint_usage": 1,
                "time_taken_seconds": 145
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, game_result_response.status_code)

        overview_response = self.client.get(
            "/api/v1/dashboard/me/overview",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, overview_response.status_code)
        overview = overview_response.json()
        self.assertEqual(1, overview["counts"]["total_diagnostics"])
        self.assertEqual(1, overview["counts"]["total_hint_events"])
        self.assertEqual(1, overview["counts"]["total_game_sessions"])
        self.assertEqual(1, overview["counts"]["total_pair_sessions"])
        self.assertEqual(1, overview["counts"]["total_peer_reviews"])
        self.assertEqual(1, overview["mastery"]["total_concepts"])
        trend_concepts = {item["concept_tag"] for item in overview["concept_trends"]}
        self.assertIn("array_indexing", trend_concepts)
        self.assertIn("loop_boundaries", trend_concepts)
        self.assertGreaterEqual(len(overview["recent_timeline"]), 5)

        timeline_response = self.client.get(
            "/api/v1/dashboard/me/timeline",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(200, timeline_response.status_code)
        timeline_payload = timeline_response.json()
        self.assertGreaterEqual(timeline_payload["total"], 5)
        event_types = {item["event_type"] for item in timeline_payload["events"]}
        self.assertIn("game_session_completed", event_types)
        self.assertIn("peer_review_submitted", event_types)


if __name__ == "__main__":
    unittest.main()
