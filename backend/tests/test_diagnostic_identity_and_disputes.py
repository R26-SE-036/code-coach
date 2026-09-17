"""A finding keeps its identity while the student edits, and a disputed one stops counting.

Storage recognises a finding from one analysis to the next by its id, and
turns what it sees into "resolved" and "newly detected" records. Repeat
counts, time to fix, mastery and Study Guider's struggle triggers are all
computed from those records - so an id that changes when the finding has not
invents fixes and mistakes, and nothing downstream can tell.

That is what happened. The id hashed the line number, and analysis re-runs
900 ms after every pause in typing: one comment line added above the first
finding in each of the extension's sample files turned all fifteen findings
into fifteen fixes and fifteen new mistakes.

And a student who reported a finding as a false positive went on being
counted for it, because the report was stored and never read.
"""

import unittest

from fastapi.testclient import TestClient

from app.analysis.analyzer import analyze_code
from app.db.storage import InMemoryStorage
from app.main import create_app
from app.services.diagnostic_matching import match_diagnostics

# STRING_EQUALITY_WITH_OPERATOR is found by a rule alone, with no model
# deciding, so these tests are about identity and not about a threshold.
LOGIN = """class Login {
    boolean check(String name) {
        if (name == "admin") {
            return true;
        }
        return false;
    }
}
"""


def ids(code: str) -> list[str]:
    return sorted(item.diagnostic_id for item in analyze_code(code))


class IdentityTests(unittest.TestCase):
    def test_the_example_is_found(self) -> None:
        found = analyze_code(LOGIN)
        self.assertEqual(["STRING_EQUALITY_WITH_OPERATOR"], [item.error_type for item in found])

    def test_an_edit_above_a_finding_keeps_its_id(self) -> None:
        edited = LOGIN.replace("class Login {\n", "class Login {\n    // checked by hand\n\n")
        before, after = analyze_code(LOGIN), analyze_code(edited)

        # The finding moved two lines down, and is still the same finding.
        self.assertEqual(before[0].line + 2, after[0].line)
        self.assertEqual(before[0].diagnostic_id, after[0].diagnostic_id)

    def test_re_indenting_the_flagged_line_keeps_its_id(self) -> None:
        reindented = LOGIN.replace('        if (name == "admin") {', '    if (name  ==  "admin")   {')
        self.assertEqual(ids(LOGIN), ids(reindented))

    def test_changing_the_flagged_line_changes_its_id(self) -> None:
        # Still the same kind of mistake, but not the same one.
        changed = LOGIN.replace('"admin"', '"root"')
        self.assertEqual(1, len(ids(changed)))
        self.assertNotEqual(ids(LOGIN), ids(changed))

    def test_two_identical_mistakes_are_two_findings(self) -> None:
        twice = LOGIN.replace(
            "        return false;\n",
            '        if (name == "admin") {\n            return true;\n        }\n        return false;\n',
        )
        found = ids(twice)
        self.assertEqual(2, len(found))
        self.assertEqual(2, len(set(found)))


class MatchingTests(unittest.TestCase):
    @staticmethod
    def record(diagnostic_id: str, error_type: str = "X", context_hash: str = "h1") -> dict:
        return {"diagnosticId": diagnostic_id, "errorType": error_type, "codeContextHash": context_hash}

    def test_a_record_from_before_ids_stopped_using_the_line_is_carried_over(self) -> None:
        # Its id is one no analysis will produce again. Resolving it would
        # record a fix the student never made, on the first analysis after
        # the change, for every finding that was open at the time.
        stored = self.record("cc_line_based")
        match = match_diagnostics([stored], [self.record("cc_stable")])

        self.assertEqual([(stored, self.record("cc_stable"))], match.carried)
        self.assertEqual([], match.resolved)
        self.assertEqual([], match.new)

    def test_an_exact_id_is_matched_before_a_looser_match_can_take_its_record(self) -> None:
        first, second = self.record("cc_a"), self.record("cc_b")
        match = match_diagnostics([first, second], [self.record("cc_b"), self.record("cc_c")])

        carried = {incoming["diagnosticId"]: stored["diagnosticId"] for stored, incoming in match.carried}
        self.assertEqual({"cc_b": "cc_b", "cc_c": "cc_a"}, carried)
        self.assertEqual([], match.resolved)

    def test_a_different_mistake_on_the_same_line_is_not_the_same_finding(self) -> None:
        match = match_diagnostics([self.record("cc_a", "X")], [self.record("cc_b", "Y")])

        self.assertEqual([], match.carried)
        self.assertEqual(1, len(match.resolved))
        self.assertEqual(1, len(match.new))


class ThroughTheApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = InMemoryStorage()
        self.client = TestClient(create_app(storage=self.storage))

    def tearDown(self) -> None:
        self.client.close()

    def student(self, email: str) -> tuple[dict, str]:
        registered = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Identity Student",
                "email": email,
                "password": "Password123",
                "client_name": "code-coach-test",
            },
        )
        self.assertEqual(200, registered.status_code)
        headers = {"Authorization": f"Bearer {registered.json()['tokens']['access_token']}"}

        session = self.client.post(
            "/api/v1/learning-sessions",
            json={"source_component": "code_coach", "language": "java", "task_id": "login_lab"},
            headers=headers,
        )
        self.assertEqual(200, session.status_code)
        return headers, session.json()["learning_session_id"]

    def analyze(self, headers: dict, session_id: str, code: str) -> list[dict]:
        response = self.client.post(
            "/api/v1/code-coach/analyze",
            json={"language": "java", "code": code, "learning_session_id": session_id, "enable_logging": False},
            headers=headers,
        )
        self.assertEqual(200, response.status_code)
        return response.json()["diagnostics"]

    def events(self, headers: dict, event_type: str) -> int:
        response = self.client.get("/api/v1/events/me", params={"event_type": event_type}, headers=headers)
        self.assertEqual(200, response.status_code)
        return response.json()["total"]

    def total_diagnostics(self, headers: dict) -> int:
        response = self.client.get("/api/v1/students/me/diagnostics/summary", headers=headers)
        self.assertEqual(200, response.status_code)
        return response.json()["total_diagnostics"]

    def dispute(self, headers: dict, session_id: str, payload: dict) -> None:
        response = self.client.post(
            "/api/v1/events",
            json={
                "learning_session_id": session_id,
                "component": "code_coach",
                "event_type": "diagnostic_disputed",
                "concept_tag": "string_comparison",
                "payload": payload,
            },
            headers=headers,
        )
        self.assertEqual(200, response.status_code)

    def test_an_unrelated_edit_records_no_fix_and_no_new_mistake(self) -> None:
        headers, session_id = self.student("edits@example.com")

        self.analyze(headers, session_id, LOGIN)
        self.analyze(headers, session_id, LOGIN.replace("class Login {\n", "class Login {\n    // a note\n"))
        self.analyze(headers, session_id, LOGIN.replace("class Login {\n", "class Login {\n    // a note\n\n\n"))

        self.assertEqual(0, self.events(headers, "diagnostic_resolved"))
        self.assertEqual(1, self.events(headers, "code_diagnostic_detected"))
        self.assertEqual(1, self.total_diagnostics(headers))

    def test_fixing_the_mistake_is_still_a_fix(self) -> None:
        headers, session_id = self.student("fixes@example.com")

        self.analyze(headers, session_id, LOGIN)
        self.analyze(headers, session_id, LOGIN.replace('name == "admin"', 'name.equals("admin")'))

        self.assertEqual(1, self.events(headers, "diagnostic_resolved"))

    def test_a_disputed_finding_stops_counting_and_is_not_shown_again(self) -> None:
        headers, session_id = self.student("disputes@example.com")
        [finding] = self.analyze(headers, session_id, LOGIN)
        self.assertEqual(1, self.total_diagnostics(headers))

        self.dispute(
            headers,
            session_id,
            {
                "diagnostic_id": finding["diagnostic_id"],
                "error_type": finding["error_type"],
                "detection_engine": finding["detection_engine"],
                "dispute_reason": "false_positive",
            },
        )

        # Out of every count that reads the student's diagnostics...
        self.assertEqual(0, self.total_diagnostics(headers))

        # ...and out of the editor, including after edits elsewhere in the file.
        self.assertEqual([], self.analyze(headers, session_id, LOGIN))
        self.assertEqual([], self.analyze(headers, session_id, LOGIN.replace("class Login {\n", "class Login {\n\n")))
        self.assertEqual(0, self.total_diagnostics(headers))
        self.assertEqual(1, self.events(headers, "code_diagnostic_detected"))

        # In a new session too: a dispute is about the finding, not the session.
        other_session = self.client.post(
            "/api/v1/learning-sessions",
            json={"source_component": "code_coach", "language": "java", "task_id": "login_lab_2"},
            headers=headers,
        ).json()["learning_session_id"]
        self.assertEqual([], self.analyze(headers, other_session, LOGIN))

    def test_a_dispute_that_names_no_finding_changes_nothing(self) -> None:
        headers, session_id = self.student("empty-dispute@example.com")
        self.analyze(headers, session_id, LOGIN)

        self.dispute(headers, session_id, {"dispute_reason": "false_positive"})

        self.assertEqual(1, self.total_diagnostics(headers))
        self.assertEqual(1, len(self.analyze(headers, session_id, LOGIN)))

    def test_one_students_dispute_does_not_hide_the_finding_from_another(self) -> None:
        first, first_session = self.student("first@example.com")
        [finding] = self.analyze(first, first_session, LOGIN)
        self.dispute(first, first_session, {"diagnostic_id": finding["diagnostic_id"]})

        second, second_session = self.student("second@example.com")
        self.assertEqual(1, len(self.analyze(second, second_session, LOGIN)))
        self.assertEqual(1, self.total_diagnostics(second))


if __name__ == "__main__":
    unittest.main()
