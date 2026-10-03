"""POST /api/v1/internal/concepts - concepts in a piece of code, for PairPath.

Two things matter: it refuses anyone without the shared key, and it records
nothing. Code a pair wrote together is not one student's work, so analysing it
must leave no diagnostics, events or learning sessions behind.
"""

import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.storage import InMemoryStorage
from app.main import create_app

KEY = "test-internal-key-0123456789"

OFF_BY_ONE = """
public class Main {
    public static void main(String[] args) {
        int[] scores = {70, 85, 90};
        for (int i = 0; i <= scores.length; i++) {
            System.out.println(scores[i]);
        }
    }
}
"""


class InternalConceptsTests(unittest.TestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()
        self.env = mock.patch.dict(os.environ, {"INTERNAL_SERVICE_KEY": KEY})
        self.env.start()
        self.storage = InMemoryStorage()
        self.client = TestClient(create_app(storage=self.storage))

    def tearDown(self) -> None:
        self.client.close()
        self.env.stop()
        get_settings.cache_clear()

    def post(self, code: str, key: str | None = KEY):
        headers = {"X-Internal-Key": key} if key is not None else {}
        return self.client.post("/api/v1/internal/concepts", json={"code": code}, headers=headers)

    def test_no_key_is_refused(self):
        self.assertEqual(self.post(OFF_BY_ONE, key=None).status_code, 401)

    def test_wrong_key_is_refused(self):
        self.assertEqual(self.post(OFF_BY_ONE, key="nope").status_code, 403)

    def test_unconfigured_service_refuses_rather_than_accepting(self):
        with mock.patch.dict(os.environ, {"INTERNAL_SERVICE_KEY": ""}):
            get_settings.cache_clear()
            self.assertEqual(self.post(OFF_BY_ONE).status_code, 503)

    def test_returns_the_concepts_the_detector_finds(self):
        response = self.post(OFF_BY_ONE)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["concept_tags"], "an off-by-one loop should be found")
        self.assertEqual(len(body["concept_tags"]), len(set(body["concept_tags"])))

    def test_empty_code_has_no_concepts(self):
        self.assertEqual(self.post("   ").json(), {"concept_tags": [], "error_types": []})

    def test_records_nothing(self):
        self.post(OFF_BY_ONE)
        self.assertEqual(self.storage.list_learning_events_for_user("anyone", limit=10), [])


if __name__ == "__main__":
    unittest.main()
