"""Help on demand: explanations, compiler errors, worked examples, the catalogue.

The model is never called for real here. What is held is everything around
it: the button always answers (templates when there is no key, the allowance
is used up, or the model fails), an answer is cached by the code it explains,
the allowance is per student per day, corrected code is taken out of an
answer, and the routes need a signed-in student.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.storage import InMemoryStorage
from app.main import create_app
from app.services import explanation_service, llm_client

CODE = """public class Probe {
    static boolean contains(int[] values, int target) {
        for (int i = 0; i < values.length; i++) {
            if (values[i] == target) return true;
            else return false;
        }
        return false;
    }
}
"""


@pytest.fixture
def client():
    with TestClient(create_app(storage=InMemoryStorage())) as test_client:
        yield test_client


def signed_in(client: TestClient, email: str = "student@example.com") -> dict:
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Sample Student", "email": email, "password": "Password123", "client_name": "codeguru-web",
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


def explain(client, headers, line=5, code=CODE):
    return client.post("/api/v1/code-coach/explain", headers=headers,
                       json={"error_type": "EARLY_RETURN_IN_LOOP", "code": code, "line": line})


@pytest.fixture
def fake_model(monkeypatch):
    calls = []

    def complete(prompt, **kwargs):
        calls.append(prompt)
        return "Your loop looks at `values[0]` and leaves. ```java\nreturn true;\n``` What happens for {3, 8}?"

    monkeypatch.setattr(llm_client, "configured", lambda: True)
    monkeypatch.setattr(llm_client, "complete", complete)
    return calls


def test_the_catalogue_is_public_and_names_all_thirty(client):
    response = client.get("/api/v1/code-coach/catalog")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 30
    assert all(entry["title"] and "_" not in entry["title"] for entry in entries)
    assert sum(entry["detection_mode"] == "candidate_ml" for entry in entries) == 24


def test_every_model_decided_type_has_a_public_model_card(client):
    index = client.get("/api/v1/code-coach/model-cards")
    assert index.status_code == 200
    catalogue = client.get("/api/v1/code-coach/catalog").json()
    model_types = {entry["error_type"] for entry in catalogue if entry["detection_mode"] == "candidate_ml"}
    assert {entry["error_type"] for entry in index.json()} == model_types

    for error_type in model_types:
        card = client.get(f"/api/v1/code-coach/model-cards/{error_type}").json()
        assert card["in_use"] is True
        assert card["detects"] and card["considers"] and card["example"]["mistake"] and card["example"]["lookalike"]
        assert card["unreliable_when"] and card["general_limitations"]
        test = card["performance"]["test"]
        assert 0 <= test["precision"] <= 1 and 0 <= test["recall"] <= 1
        assert card["training_data"]["test_sites"] > 0


def test_a_rule_has_no_model_card(client):
    assert client.get("/api/v1/code-coach/model-cards/SELF_ASSIGNMENT").status_code == 404


def test_the_help_routes_need_a_signed_in_student(client):
    assert explain(client, {}).status_code == 401
    assert client.post("/api/v1/code-coach/explain-compiler-error", json={"message": "x", "code": "", "line": 1}).status_code == 401
    assert client.post("/api/v1/code-coach/similar-example", json={"error_type": "EARLY_RETURN_IN_LOOP"}).status_code == 401


def test_without_a_key_the_hints_answer(client, monkeypatch):
    monkeypatch.setattr(llm_client, "configured", lambda: False)
    body = explain(client, signed_in(client)).json()
    assert body["source"] == "template"
    assert "return inside a loop" in body["explanation"]


def test_the_model_answer_is_cached_and_its_code_removed(client, fake_model):
    headers = signed_in(client)
    longer = CODE + "\n".join("// more of the file" for _ in range(12))
    first = explain(client, headers, code=longer).json()
    assert first["source"] == "llm"
    assert "```" not in first["explanation"] and "`values[0]`" in first["explanation"]
    assert first["remaining_today"] == get_settings().llm_daily_limit - 1
    # An edit outside the lines explained (8 either side) still hits the cache.
    again = explain(client, headers, code=longer + "\n// done\n").json()
    assert again["source"] == "cache"
    assert len(fake_model) == 1
    # The prompt carries the student's lines, numbered, with the flagged one marked.
    assert "5> " in fake_model[0] and "values[i] == target" in fake_model[0]


def test_the_daily_allowance_is_per_student(client, fake_model, monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_daily_limit", 1)
    alice, bob = signed_in(client, "a@example.com"), signed_in(client, "b@example.com")
    assert explain(client, alice).json()["source"] == "llm"
    other_code = CODE.replace("target", "wanted")
    spent = explain(client, alice, code=other_code).json()
    assert spent["source"] == "template" and spent["limit_reached"] is True
    assert explain(client, bob, code=other_code).json()["source"] == "llm"


def test_a_failing_model_falls_back(client, monkeypatch):
    def broken(*args, **kwargs):
        raise llm_client.LLMUnavailable("down")

    monkeypatch.setattr(llm_client, "configured", lambda: True)
    monkeypatch.setattr(llm_client, "complete", broken)
    body = explain(client, signed_in(client)).json()
    assert body["source"] == "template" and body["explanation"]


@pytest.mark.parametrize("message, phrase", [
    ("';' expected", "semicolon"),
    ('Syntax error, insert ";" to complete BlockStatements', "semicolon"),
    ("cannot find symbol", "does not know this name"),
    ("total cannot be resolved to a variable", "does not know this name"),
    ("This method must return a result of type int", "promises to return"),
    ("The local variable count may not have been initialized", "starting value"),
    ("Type mismatch: cannot convert from double to int", "not the type"),
])
def test_compiler_errors_have_plain_explanations_in_both_wordings(message, phrase):
    assert phrase in explanation_service.compiler_error_template(message)


def test_a_similar_example_comes_from_the_same_mistake(client, monkeypatch):
    monkeypatch.setattr(llm_client, "configured", lambda: False)
    body = client.post("/api/v1/code-coach/similar-example", headers=signed_in(client),
                       json={"error_type": "EARLY_RETURN_IN_LOOP", "code": CODE, "line": 5}).json()
    assert body["course_path"] == "/study/course/EARLY_RETURN_IN_LOOP"
    assert body["examples"] and body["examples"][0]["buggy"] and body["examples"][0]["fixed"]
    assert "embedding" not in body["examples"][0]


def test_the_code_window_numbers_lines_like_the_editor():
    window = explanation_service.code_window("a\nb\nc\nd", 2, radius=1)
    assert window.splitlines() == ["1  a", "2> b", "3  c"]
