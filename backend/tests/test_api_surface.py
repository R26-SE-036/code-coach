"""Every route is authenticated unless it is deliberately not.

This exists because two were not, and nothing said so.

`POST /analyze` and `POST /debug-ast` predated the versioned API and outlived
their callers - the VS Code extension posts to /api/v1/code-coach/analyze and
the web frontend does not analyse code at all. Both took a request body with
no credentials, and rate limiting on this service is applied through a
dependency that only the credential endpoints use, so either one could be run
by anyone who could reach the port, as often as they liked. /analyze also
appended to the evaluation log, putting anonymous submissions into the record
this component's results are drawn from.

Neither was caught by a test, because every test that mattered went through
the authenticated route and passed. The endpoints were only visible by listing
the routes and looking at what was missing - so that is what this does, on
every route, every run.

The check is behavioural rather than a search for decorators: it calls each
route with no credentials and requires a refusal. A guard that is present but
wired up wrongly still fails here.
"""

import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.db.storage import InMemoryStorage

# Routes that are meant to answer without credentials, each with the reason.
#
# Adding to this set is how a new public endpoint is declared. That is the
# point: it takes an edit to this file and a reason next to it, rather than
# happening silently because nobody enumerated the surface.
PUBLIC = {
    ("GET", "/"): "liveness banner, no data",
    ("GET", "/health"): "liveness probe, no data",
    ("GET", "/docs"): "API documentation",
    ("GET", "/redoc"): "API documentation",
    ("GET", "/docs/oauth2-redirect"): "API documentation",
    ("GET", "/openapi.json"): "API schema",
    # The credential endpoints. They cannot require a credential, and they are
    # the only routes covered by enforce_auth_rate_limit for that reason.
    ("POST", "/api/v1/auth/register"): "issues the first credential",
    ("POST", "/api/v1/auth/login"): "exchanges a password for a token",
    ("POST", "/api/v1/auth/refresh"): "presents a refresh token, not an access one",
    ("POST", "/api/v1/auth/handoff/redeem"): "presents a handoff code, not an access token",
    # Account recovery. Whoever uses these has lost their password, or is
    # confirming an address from an email - neither has an access token.
    ("POST", "/api/v1/auth/password/forgot"): "asks for a reset email; same answer for every address",
    ("POST", "/api/v1/auth/password/reset"): "presents a single-use emailed reset token",
    ("POST", "/api/v1/auth/recovery-email/confirm"): "presents a single-use emailed confirmation token",
}

REFUSALS = {401, 403}


def routes_of(app):
    """(method, path) for every real route, ignoring HEAD and OPTIONS."""
    found = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in sorted(m for m in methods if m not in {"HEAD", "OPTIONS"}):
            found.append((method, route.path))
    return sorted(set(found))


class ApiSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(storage=InMemoryStorage())
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()

    def test_every_route_without_a_token_is_refused_or_declared_public(self):
        for method, path in routes_of(self.app):
            with self.subTest(route=f"{method} {path}"):
                # Path parameters are filled with a value that no record will
                # match. A route that answers 404 for an unknown id before
                # checking the token is still leaking whether the id exists,
                # so "not found" is not accepted as a refusal either.
                url = path
                for placeholder in ("{learning_session_id}", "{trigger_id}"):
                    url = url.replace(placeholder, "does-not-exist")

                response = self.client.request(method, url, json={})

                if (method, path) in PUBLIC:
                    self.assertNotIn(
                        response.status_code,
                        REFUSALS,
                        f"{method} {path} is declared public but refused anyway",
                    )
                    continue

                self.assertIn(
                    response.status_code,
                    REFUSALS,
                    f"{method} {path} answered {response.status_code} with no credentials. "
                    f"Either it needs an auth dependency, or it belongs in PUBLIC with a reason.",
                )

    def test_the_public_list_has_no_stale_entries(self):
        # A route removed from the app but left in PUBLIC would quietly widen
        # the allowlist for whatever took its path next.
        actual = set(routes_of(self.app))
        for entry in PUBLIC:
            self.assertIn(entry, actual, f"{entry} is in PUBLIC but no longer exists")

    def test_the_legacy_analysis_endpoints_are_gone(self):
        # Named explicitly, so removing them cannot be undone by a merge that
        # restores main.py without anybody noticing what came back.
        for path in ("/analyze", "/debug-ast"):
            self.assertEqual(
                404,
                self.client.post(path, json={"language": "java", "code": "class A {}"}).status_code,
                f"{path} is back. It runs the analyser without a credential or a rate limit.",
            )


if __name__ == "__main__":
    unittest.main()
