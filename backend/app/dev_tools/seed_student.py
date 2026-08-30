"""Create a test student with real remediation triggers, in one command.

WHY THIS EXISTS

Study Guider (and later the Gamification Engine) shows nothing until Code Coach
has raised a remediation trigger for the signed-in student, and a trigger only
appears once the same concept has failed repeatedly. That left a teammate who
just wanted to work on a lesson card with two bad options: install and configure
the whole VS Code extension, or hand-chain four curl calls copying tokens
between them.

This does it in one command, and prints the access token to use afterwards.

HOW IT WORKS

Entirely through the public HTTP API — no database access. That matters twice
over: it runs against a Cloudflare tunnel, so teammates can seed themselves on
the shared Code Coach; and it walks the exact path a real student walks, so a
successful seed is evidence the real flow works rather than a shortcut around
it.

    register (or log in if the account already exists)
      -> create a learning session
      -> analyze Java containing the same mistake three times over
      -> wait for the background trigger sync
      -> print the triggers and the token

Re-running is safe: the account is reused, and Code Coach de-duplicates both
diagnostics and triggers, so you get one student and one trigger per concept
however many times you run it.

USAGE (from backend/)

    python -m app.dev_tools.seed_student
    python -m app.dev_tools.seed_student --concepts array_indexing conditional_logic
    python -m app.dev_tools.seed_student --base-url https://<tunnel>.trycloudflare.com
    python -m app.dev_tools.seed_student --email me@example.com --password secret123
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any, Optional

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_EMAIL = "seed.student@example.com"
DEFAULT_PASSWORD = "seed-student-1234"
DEFAULT_NAME = "Seed Student"
CLIENT_NAME = "codeguru-seed-tool"

# One program per concept, each containing the SAME mistake three times.
#
# Three is not arbitrary: Code Coach scores a struggle from how often a concept
# repeats and how many instances are still unresolved, and only a *high* score
# raises a trigger. Three unresolved repeats of one concept clears it; two does
# not. Keep each file to a single kind of mistake — mixing them splits the
# count across concepts and no single one crosses the line.
CONCEPT_PROGRAMS: dict[str, str] = {
    "array_indexing": """public class ArrayIndexingDemo {
    public static void main(String[] args) {
        int[] marks = new int[5];
        int[] scores = new int[4];
        int[] totals = new int[3];
        System.out.println(marks[marks.length]);
        System.out.println(scores[scores.length]);
        System.out.println(totals[totals.length]);
    }
}""",
    "loop_boundaries": """public class LoopBoundaryDemo {
    public static void main(String[] args) {
        int[] a = new int[4];
        int[] b = new int[6];
        int[] c = new int[8];
        for (int i = 0; i <= a.length; i++) { System.out.println(a[i]); }
        for (int j = 0; j <= b.length; j++) { System.out.println(b[j]); }
        for (int k = 0; k <= c.length; k++) { System.out.println(c[k]); }
    }
}""",
    "conditional_logic": """public class ConditionalDemo {
    public static void main(String[] args) {
        int total = 0;
        int count = 0;
        int flag = 0;
        if (total = 10) { System.out.println("ten"); }
        if (count = 5) { System.out.println("five"); }
        if (flag = 1) { System.out.println("one"); }
    }
}""",
}

# Study Guider ships real lessons for exactly these three (see its
# study_guider_service.py); anything else falls back to a generic lesson.
DEFAULT_CONCEPTS = ["array_indexing", "loop_boundaries", "conditional_logic"]


class SeedError(Exception):
    """Something went wrong that the user needs to act on."""


def _post(base_url: str, path: str, body: dict, token: Optional[str] = None) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return requests.post(base_url + path, json=body, headers=headers, timeout=30)
    except requests.RequestException as error:
        raise SeedError(
            f"Cannot reach Code Coach at {base_url}\n"
            f"  {error}\n"
            f"  Is the backend running? (cd backend && uvicorn app.main:app --port 8000)"
        ) from error


def _get(base_url: str, path: str, token: str, params: Optional[dict] = None) -> requests.Response:
    try:
        return requests.get(
            base_url + path,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
    except requests.RequestException as error:
        raise SeedError(f"Cannot reach Code Coach at {base_url}: {error}") from error


def _detail(response: requests.Response) -> str:
    try:
        return response.json().get("detail", response.text[:200])
    except ValueError:
        return response.text[:200]


def sign_in(base_url: str, email: str, password: str, name: str) -> dict[str, Any]:
    """Register the student, or log in if they already exist.

    A 409 means a previous run already created them — the whole point of the
    tool being safe to re-run, so it is a normal path rather than an error.
    """
    response = _post(
        base_url,
        "/api/v1/auth/register",
        {"full_name": name, "email": email, "password": password, "client_name": CLIENT_NAME},
    )

    if response.status_code == 409:
        print(f"  account already exists, signing in instead")
        response = _post(
            base_url,
            "/api/v1/auth/login",
            {"identifier": email, "password": password, "client_name": CLIENT_NAME},
        )
        if response.status_code == 401:
            raise SeedError(
                f"The account {email} exists but the password did not match.\n"
                f"  Pass --password with the right one, or --email to use a different account."
            )

    if not response.ok:
        raise SeedError(f"Sign-in failed ({response.status_code}): {_detail(response)}")

    return response.json()


def create_learning_session(base_url: str, token: str) -> str:
    response = _post(
        base_url,
        "/api/v1/learning-sessions",
        {"source_component": "code_coach", "language": "java"},
        token=token,
    )
    if not response.ok:
        raise SeedError(f"Could not create a learning session: {_detail(response)}")
    return response.json()["learning_session_id"]


def analyze(base_url: str, token: str, learning_session_id: str, code: str) -> list[dict]:
    response = _post(
        base_url,
        "/api/v1/code-coach/analyze",
        {"language": "java", "code": code, "learningSessionId": learning_session_id},
        token=token,
    )
    if not response.ok:
        raise SeedError(f"Analysis failed: {_detail(response)}")
    return response.json().get("diagnostics", [])


def wait_for_concept(base_url: str, token: str, concept: str, timeout: float) -> bool:
    """Block until a trigger exists for `concept`, or give up.

    Serialising the analyses this way is what keeps Code Coach's trigger
    creation from racing itself; see the call site.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = _get(base_url, "/api/v1/remediation/me/triggers", token, {"status": "active"})
        if response.ok:
            if any(t["concept_tag"] == concept for t in response.json().get("triggers", [])):
                return True
        time.sleep(1.0)
    return False


def wait_for_triggers(base_url: str, token: str, expected: int, timeout: float = 30.0) -> list[dict]:
    """Poll until the triggers appear, or we run out of patience.

    Code Coach persists diagnostics and evaluates struggles in a FastAPI
    background task that runs AFTER the analyze response is sent — so the
    triggers genuinely are not there yet when analyze() returns. Polling beats
    a fixed sleep: it is faster when the backend is local and still correct
    when it is behind a tunnel on a bad connection.
    """
    deadline = time.monotonic() + timeout
    triggers: list[dict] = []

    while time.monotonic() < deadline:
        response = _get(base_url, "/api/v1/remediation/me/recommendations", token)
        if response.ok:
            triggers = response.json().get("recommendations", [])
            if len(triggers) >= expected:
                return triggers
        time.sleep(1.5)

    return triggers


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed a Code Guru student with real remediation triggers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help=f"Code Coach base URL (default {DEFAULT_BASE_URL}). "
                             "Use your Cloudflare tunnel URL to seed against a shared backend.")
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--concepts", nargs="+", default=DEFAULT_CONCEPTS,
                        choices=sorted(CONCEPT_PROGRAMS),
                        help="Which concepts to make the student struggle with.")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="Seconds to wait for triggers to appear (default 30).")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    try:
        print(f"Code Coach: {base_url}\n")

        print("1. Signing the student in")
        auth = sign_in(base_url, args.email, args.password, args.name)
        token = auth["tokens"]["access_token"]
        user = auth["user"]
        print(f"  {user['full_name']} <{user['email']}>")
        print(f"  user_id: {user['user_id']}\n")

        print("2. Creating a learning session")
        learning_session_id = create_learning_session(base_url, token)
        print(f"  {learning_session_id}\n")

        print(f"3. Submitting {len(args.concepts)} program(s) for analysis")
        for concept in args.concepts:
            diagnostics = analyze(base_url, token, learning_session_id, CONCEPT_PROGRAMS[concept])
            kinds = {d["error_type"] for d in diagnostics}
            print(f"  {concept:20} {len(diagnostics)} diagnostic(s)  {', '.join(sorted(kinds)) or '(none)'}")
            if len(diagnostics) < 3:
                print(f"  {'':20} ! fewer than 3 - this concept may not reach a trigger")

            # Wait for THIS concept's trigger before submitting the next.
            #
            # Not politeness — correctness. Each analyze spawns a background
            # task that reads every existing trigger, looks for a match, and
            # writes if it finds none. Firing the next analysis before that
            # finishes puts two of those read-then-write cycles in flight at
            # once, they both see "no trigger yet", and both create one. Doing
            # it in sequence produces exactly one trigger per concept, which is
            # also what a real student generates by coding over time.
            if not wait_for_concept(base_url, token, concept, args.timeout):
                print(f"  {'':20} ! no trigger yet for {concept}")
        print()

        print("4. Collecting the triggers")
        triggers = wait_for_triggers(base_url, token, len(args.concepts), args.timeout)

        if not triggers:
            print("  none appeared.\n")
            print("  The analysis ran but no trigger crossed the threshold. Most likely the")
            print("  background task has not finished - re-run with a longer --timeout, or")
            print("  just run this tool again; it is safe to repeat.")
            return 1

        print(f"  {len(triggers)} trigger(s) ready\n")
        for t in triggers:
            print(f"  {t['concept_tag']:20} {t['error_type']}")
            print(f"  {'':20} struggle={t['struggle_level']}  lesson={t['lesson']['title']}")

        print("\n" + "-" * 68)
        print("Access token (valid 1 hour) - send as: Authorization: Bearer <token>\n")
        print(token)
        print("\n" + "-" * 68)
        print("Try it:\n")
        print(f'  curl {base_url}/api/v1/remediation/me/recommendations \\')
        print(f'    -H "Authorization: Bearer <token>"\n')
        print("Or sign into Study Guider / the portal as:")
        print(f"  {args.email} / {args.password}")

        return 0

    except SeedError as error:
        print(f"\n{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
