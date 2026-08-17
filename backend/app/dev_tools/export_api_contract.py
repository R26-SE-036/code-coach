"""Generate the API contract for the sibling Code Guru services.

Two artifacts, both derived from the LIVE FastAPI app so they can never drift
from the running code:

  docs/api/openapi.json  — machine readable; teammates import it into Postman
                           or Swagger UI, or generate a typed client from it
  docs/api/API_CONTRACT.md — human readable; every endpoint with its real
                           request and response fields, resolved from the
                           Pydantic models (no hand-written examples)

USAGE (from backend/):  python -m app.dev_tools.export_api_contract
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.db.storage import InMemoryStorage
from app.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "docs" / "api"

# Endpoints grouped by the consumer that needs them; anything not listed is
# reported under "Other" so a new route can never silently go undocumented.
GROUPS: list[tuple[str, str, list[str]]] = [
    ("Authentication (every service)",
     "One account for the whole platform. Sign in through Code Coach, then send the "
     "returned access token on every request to any service. To validate a token your "
     "service receives, call GET /api/v1/auth/me with it.",
     ["/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/refresh",
      "/api/v1/auth/logout", "/api/v1/auth/me"]),
    ("Learning sessions (every service)",
     "A learning session groups a student's activity. Create or reuse one before "
     "submitting analysis or events.",
     ["/api/v1/learning-sessions", "/api/v1/learning-sessions/{learning_session_id}",
      "/api/v1/learning-sessions/{learning_session_id}/diagnostics"]),
    ("Student data (Study Guider · Gamification · Website)",
     "Everything Code Coach knows about the signed-in student. 'me' always means the "
     "user identified by the bearer token.",
     ["/api/v1/students/me/diagnostics", "/api/v1/students/me/diagnostics/summary",
      "/api/v1/students/me/struggling-concepts", "/api/v1/students/me/concept-mastery"]),
    ("Remediation (Study Guider)",
     "Struggle triggers raised by Code Coach, and the callbacks Study Guider uses to "
     "report lesson and quiz progress back.",
     ["/api/v1/remediation/me/triggers", "/api/v1/remediation/me/recommendations",
      "/api/v1/remediation/me/triggers/{trigger_id}/lesson-opened",
      "/api/v1/remediation/me/triggers/{trigger_id}/quiz-completed"]),
    ("Gamification engine",
     "Recommendation and result endpoints for adaptive practice.",
     ["/api/v1/gamification/me/recommendations",
      "/api/v1/gamification/me/adaptation-decisions",
      "/api/v1/gamification/me/session-results"]),
    ("Collaboration (PairPath)",
     "Pairing prompts derived from struggle signals, plus session and peer-review records.",
     ["/api/v1/collaboration/me/prompts", "/api/v1/collaboration/me/prompts/shown",
      "/api/v1/collaboration/me/pair-sessions", "/api/v1/collaboration/me/peer-reviews"]),
    ("Dashboard (Website)",
     "Pre-aggregated views for the student home page.",
     ["/api/v1/dashboard/me/overview", "/api/v1/dashboard/me/timeline"]),
    ("Learning events (every service)",
     "The shared activity log. Emit an event whenever a student interacts with your "
     "component; read them back for analytics.",
     ["/api/v1/events", "/api/v1/events/me"]),
    ("Code analysis (Code Coach internal)",
     "Used by the VS Code extension. Included for completeness.",
     ["/api/v1/code-coach/analyze"]),
    ("Service health",
     "No authentication required.",
     ["/health"]),
]

SKIP_PATHS = {"/", "/analyze", "/debug-ast"}  # legacy/debug, not part of the contract


def resolve(schema: dict[str, Any], spec: dict[str, Any], depth: int = 0) -> Any:
    """Turn a JSON-schema node into a readable example-shaped structure."""
    if depth > 4 or not isinstance(schema, dict):
        return "..."

    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        return resolve(spec["components"]["schemas"].get(name, {}), spec, depth + 1)

    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            options = [s for s in schema[key] if s.get("type") != "null"]
            if options:
                return resolve(options[0], spec, depth)

    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        return {k: resolve(v, spec, depth + 1) for k, v in schema.get("properties", {}).items()}
    if kind == "array":
        return [resolve(schema.get("items", {}), spec, depth + 1)]
    if kind == "string":
        fmt = schema.get("format")
        if fmt == "date-time":
            return "2026-07-12T10:22:41Z"
        if fmt == "email":
            return "student@example.com"
        return schema.get("default", "string")
    if kind == "integer":
        return schema.get("default", 0)
    if kind == "number":
        return schema.get("default", 0.0)
    if kind == "boolean":
        return schema.get("default", False)
    return "..."


def block(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def render_endpoint(path: str, method: str, operation: dict, spec: dict) -> list[str]:
    lines: list[str] = [f"### `{method.upper()} {path}`", ""]

    summary = operation.get("summary", "").strip()
    if summary:
        lines += [summary, ""]

    needs_auth = path not in {"/health", "/api/v1/auth/register", "/api/v1/auth/login",
                              "/api/v1/auth/refresh"}
    lines.append(f"Auth: {'`Authorization: Bearer <access_token>`' if needs_auth else 'none required'}")
    lines.append("")

    params = [p for p in operation.get("parameters", []) if p.get("in") == "query"]
    if params:
        lines += ["Query parameters:", ""]
        for param in params:
            schema = param.get("schema", {})
            bits = []
            if "default" in schema:
                bits.append(f"default `{schema['default']}`")
            if "minimum" in schema or "maximum" in schema:
                bits.append(f"range {schema.get('minimum', '-')}–{schema.get('maximum', '-')}")
            suffix = f" ({', '.join(bits)})" if bits else ""
            required = " **required**" if param.get("required") else ""
            lines.append(f"- `{param['name']}`{required}{suffix}")
        lines.append("")

    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {})
    if body:
        lines += ["Request body:", "", "```json", block(resolve(body.get("schema", {}), spec)), "```", ""]

    ok = operation.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {})
    if ok:
        lines += ["Response `200`:", "", "```json", block(resolve(ok.get("schema", {}), spec)), "```", ""]

    return lines


def main() -> None:
    app = create_app(storage=InMemoryStorage())
    spec = app.openapi()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    (OUT_DIR / "openapi.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")

    documented: set[str] = set()
    doc: list[str] = [
        "# Code Coach — API Contract",
        "",
        "> Generated from the running service by `python -m app.dev_tools.export_api_contract`.",
        "> Every field below comes from the actual request/response models, so this file",
        "> cannot drift from the implementation. Regenerate after any route change.",
        "",
        "## Base URL",
        "",
        "| Environment | URL |",
        "|---|---|",
        "| Local development | `http://127.0.0.1:8000` |",
        "| Production (Cloud Run) | _added after deployment_ |",
        "",
        "Interactive docs (try any endpoint in a browser): `<base>/docs`",
        "",
        "## How to call this API",
        "",
        "1. **Sign the student in** with `POST /api/v1/auth/login`. Keep the returned",
        "   `access_token` (valid 1 hour) and `refresh_token`.",
        "2. **Send the access token** on every request:",
        "   `Authorization: Bearer <access_token>`.",
        "3. **On HTTP 401**, call `POST /api/v1/auth/refresh` with the refresh token,",
        "   then retry the original request once. Refresh tokens rotate: store the new",
        "   one and discard the old.",
        "4. **To validate a token your own service received**, forward it to",
        "   `GET /api/v1/auth/me`. A `200` returns the verified user; a `401` means",
        "   reject the request. Never ask students for their password in your own UI.",
        "",
        "## Conventions",
        "",
        "- All requests and responses are JSON; all timestamps are ISO-8601 UTC.",
        "- `me` in a path always means \"the user identified by the bearer token\" —",
        "  you cannot read another student's data, and no user id needs to be passed.",
        "- Errors return `{\"detail\": \"human readable reason\"}` with a standard status:",
        "  `400` bad request · `401` invalid/expired token · `403` inactive account ·",
        "  `404` not found or not yours · `409` conflict · `422` validation failed ·",
        "  `429` too many attempts (respect the `Retry-After` header).",
        "- Browser clients must be on the CORS allow-list — send your dev origin",
        "  (e.g. `http://localhost:3000`) to the Code Coach owner to have it added.",
        "  Server-to-server calls are unaffected.",
        "- The first request after an idle period may take a few seconds while the",
        "  deployed container starts. Do not set aggressive client timeouts.",
        "",
        "---",
        "",
    ]

    for title, description, paths in GROUPS:
        doc += [f"## {title}", "", description, ""]
        for path in paths:
            operations = spec["paths"].get(path)
            if not operations:
                continue
            documented.add(path)
            for method, operation in operations.items():
                doc += render_endpoint(path, method, operation, spec)
        doc.append("---")
        doc.append("")

    leftovers = [p for p in spec["paths"] if p not in documented and p not in SKIP_PATHS]
    if leftovers:
        doc += ["## Other endpoints", "", "Not yet grouped — ask before relying on these.", ""]
        for path in sorted(leftovers):
            for method, operation in spec["paths"][path].items():
                doc += render_endpoint(path, method, operation, spec)

    (OUT_DIR / "API_CONTRACT.md").write_text("\n".join(doc), encoding="utf-8")

    endpoint_count = sum(len(v) for p, v in spec["paths"].items() if p not in SKIP_PATHS)
    print(f"Wrote {OUT_DIR / 'API_CONTRACT.md'} ({endpoint_count} endpoints)")
    print(f"Wrote {OUT_DIR / 'openapi.json'}")
    if leftovers:
        print(f"NOTE: ungrouped endpoints listed under 'Other': {leftovers}")


if __name__ == "__main__":
    main()
