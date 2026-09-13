"""A finished PairPath session, reported back into the student's record.

Code Coach had a collaboration API that nothing called, and PairPath sent
nothing out except sign-in - so a student could struggle through a pair
session on loop_control and neither their mastery nor Study Guider would ever
know. These cover what a report changes, and just as much what it must not
change: a repeat report, a session nobody ran, a session from before grading
existed, somebody else's record.
"""

import unittest

from fastapi.testclient import TestClient

from app.db.storage import InMemoryStorage
from app.main import create_app

REPORT = "/api/v1/collaboration/me/pair-session-results"


class PairSessionResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = InMemoryStorage()
        self.client = TestClient(create_app(storage=self.storage))

    def tearDown(self) -> None:
        self.client.close()

    @staticmethod
    def auth(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def sign_up(self, email: str) -> str:
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Pair Student",
                "email": email,
                "password": "Password123",
                "client_name": "code-coach-test",
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()["tokens"]["access_token"]

    def learning_session(self, token: str, task_id: str = "q-loop-control-countdown") -> str:
        response = self.client.post(
            "/api/v1/learning-sessions",
            json={
                "source_component": "collaborative_studio",
                "language": "java",
                "task_id": task_id,
            },
            headers=self.auth(token),
        )
        self.assertEqual(200, response.status_code)
        return response.json()["learning_session_id"]

    def report(self, token: str, learning_session_id: str, **overrides):
        payload = {
            "learning_session_id": learning_session_id,
            "pair_session_id": "cmtpair0001",
            "task_id": "q-loop-control-countdown",
            "concept_tags": ["loop_control"],
            "error_type": "LOOP_UPDATE_WRONG_DIRECTION",
            "difficulty_level": "BEGINNER",
            "solved": True,
            "run_count": 3,
            "correct_run_count": 1,
            "seconds_to_solve": 240,
            "duration_seconds": 600,
            "review_score_percent": 80,
        }
        payload.update(overrides)
        return self.client.post(REPORT, json=payload, headers=self.auth(token))

    def mastery_scores(self) -> dict:
        return {
            (document["userId"], document["conceptTag"]): (
                document["masteryScore"],
                document["struggleScore"],
            )
            for document in self.storage.concept_mastery.values()
        }

    def unsolved(self, **overrides) -> dict:
        values = {"solved": False, "run_count": 4, "correct_run_count": 0, "seconds_to_solve": None}
        values.update(overrides)
        return values

    def test_a_solved_session_moves_mastery_and_opens_no_lesson(self) -> None:
        token = self.sign_up("solved@example.com")
        response = self.report(token, self.learning_session(token))

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertFalse(body["already_recorded"])
        self.assertEqual(["pair_session_completed", "mastery_updated"], body["created_event_types"])
        self.assertEqual(["loop_control"], [item["concept_tag"] for item in body["mastery"]])
        self.assertEqual([], body["trigger_ids"])

    def test_reporting_the_same_session_again_changes_nothing(self) -> None:
        # The results page reports on every visit. A reload must not count
        # the same session twice.
        token = self.sign_up("twice@example.com")
        learning_session_id = self.learning_session(token)

        self.report(token, learning_session_id)
        before = self.mastery_scores()
        again = self.report(token, learning_session_id)

        self.assertEqual(200, again.status_code)
        self.assertTrue(again.json()["already_recorded"])
        self.assertEqual([], again.json()["created_event_types"])
        self.assertEqual(before, self.mastery_scores())

    def test_both_partners_are_recorded_for_the_same_session(self) -> None:
        # Both members report one PairPath session id, each into their own
        # record - so the record is keyed by student AND session.
        driver = self.sign_up("driver@example.com")
        navigator = self.sign_up("navigator@example.com")

        first = self.report(driver, self.learning_session(driver))
        second = self.report(navigator, self.learning_session(navigator))

        self.assertFalse(first.json()["already_recorded"])
        self.assertFalse(second.json()["already_recorded"])
        self.assertEqual(2, len(self.mastery_scores()))

    def test_an_unsolved_session_opens_a_lesson_study_guider_can_see(self) -> None:
        token = self.sign_up("unsolved@example.com")
        response = self.report(token, self.learning_session(token), **self.unsolved())

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["trigger_ids"]))
        self.assertIn("struggle_signal_created", response.json()["created_event_types"])

        # /me/recommendations used to return code_coach triggers only, so this
        # trigger would have been stored and offered to nobody.
        recommendations = self.client.get(
            "/api/v1/remediation/me/recommendations",
            headers=self.auth(token),
        ).json()["recommendations"]
        self.assertEqual(1, len(recommendations))
        self.assertEqual("collaborative_studio", recommendations[0]["trigger_source"])
        self.assertEqual("loop_control", recommendations[0]["concept_tag"])
        self.assertIn("partner", recommendations[0]["rationale"])

    def test_an_unsolved_session_lowers_mastery_below_a_solved_one(self) -> None:
        solved_token = self.sign_up("better@example.com")
        unsolved_token = self.sign_up("worse@example.com")

        solved = self.report(solved_token, self.learning_session(solved_token)).json()
        unsolved = self.report(
            unsolved_token, self.learning_session(unsolved_token), **self.unsolved()
        ).json()

        self.assertGreater(
            solved["mastery"][0]["mastery_score"],
            unsolved["mastery"][0]["mastery_score"],
        )

    def test_one_unsolved_exercise_opens_one_lesson_however_many_concepts_it_has(self) -> None:
        token = self.sign_up("twotags@example.com")
        response = self.report(
            token,
            self.learning_session(token),
            concept_tags=["loop_control", "loop_boundaries"],
            **self.unsolved(run_count=2),
        )

        body = response.json()
        self.assertEqual(2, len(body["mastery"]))
        self.assertEqual(1, len(body["trigger_ids"]))

    def test_a_session_with_nothing_graded_records_completion_only(self) -> None:
        # Nobody ran anything, or the session predates grading. Neither is
        # evidence of mastery or of struggle.
        token = self.sign_up("ungraded@example.com")
        response = self.report(
            token,
            self.learning_session(token),
            solved=None,
            run_count=0,
            correct_run_count=0,
            seconds_to_solve=None,
        )

        body = response.json()
        self.assertEqual(["pair_session_completed"], body["created_event_types"])
        self.assertEqual([], body["mastery"])
        self.assertEqual([], body["trigger_ids"])
        self.assertEqual({}, self.mastery_scores())

    def test_no_lesson_without_an_error_type_to_attach_it_to(self) -> None:
        token = self.sign_up("noerror@example.com")
        response = self.report(
            token, self.learning_session(token), error_type=None, **self.unsolved()
        )

        self.assertEqual([], response.json()["trigger_ids"])

    def test_cannot_record_against_another_students_learning_session(self) -> None:
        owner = self.sign_up("owner@example.com")
        intruder = self.sign_up("intruder@example.com")

        response = self.report(intruder, self.learning_session(owner))

        self.assertEqual(404, response.status_code)
        self.assertEqual({}, self.mastery_scores())


if __name__ == "__main__":
    unittest.main()
