# Code Coach API — Integration Guide for CodeGuru Teams

> **Audience:** Study Guider, Gamification Engine, Pair Review Studio, and the
> CodeGuru website. This is everything you need to sign users in, read Code
> Coach's data, and test against a real running instance. You never touch Code
> Coach's database — this API **is** the contract.

## Base URLs

| Environment | Base URL |
|---|---|
| Local development | `http://127.0.0.1:8000` (run: `uvicorn app.main:app` from `backend/`) |
| Production (Cloud Run) | `https://code-coach-backend-<hash>-el.a.run.app` — shared after deployment |

Interactive docs (try every endpoint in the browser): `<base>/docs` (Swagger UI).

**CORS:** browser frontends must be on the allow-list. Local dev ports 3000,
5173, 4200 are pre-allowed; ask for your origin to be added to
`CORS_ALLOWED_ORIGINS` if you use another. Server-to-server calls are never
blocked by CORS.

## 1. Identity — one account for the whole platform

Code Coach is CodeGuru's **identity provider**. Students register once and the
same credentials work in the extension, the website, and every service.

### Sign in (website login form → these two calls)

```bash
curl -X POST <base>/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"student@example.com","password":"...","client_name":"codeguru-web"}'
```

Response (the parts you need):

```json
{
  "user": { "user_id": "user_c94da...", "full_name": "Ravindu Nethmina", "role": "student" },
  "tokens": {
    "access_token":  "<JWT — send on every request>",
    "refresh_token": "<opaque — store securely, use only for /refresh>",
    "expires_in": 3600
  }
}
```

- Send `Authorization: Bearer <access_token>` on **every** API call.
- Access tokens live **1 hour**. On a `401`, call `POST /api/v1/auth/refresh`
  with `{"refresh_token": "..."}` — you get a fresh pair (the old refresh
  token is invalidated: rotation). Retry the original request once.
- `POST /api/v1/auth/register` has the same response shape
  (`full_name`, `email`, `password`, `client_name`).
- `POST /api/v1/auth/logout` (bearer) revokes the session server-side.

### How YOUR service validates a user (token introspection)

Your microservice receives requests carrying the student's bearer token. You
cannot verify it yourself (you don't share Code Coach's secret, and tokens are
revocable server-side) — so you ask Code Coach:

```
Browser ──(Bearer T)──▶ Your service ──GET /api/v1/auth/me (Bearer T)──▶ Code Coach
                                        ◀── 200 {user_id, name, role}      valid ✓
                                        ◀── 401                            reject ✗
```

One call, and you get the verified identity + profile. Cache the result for a
minute or two per token if you care about latency. **Never** ask students for
their password in your own UI — always send them through these auth endpoints.

## 2. Student data — what each team needs

`me` in a path always means *"the student identified by the bearer token"*.
Your service forwards the student's own token; authorization is automatic
(nobody can read anyone else's data).

### Study Guider

| Endpoint | Returns |
|---|---|
| `GET /api/v1/students/me/struggling-concepts` | concepts the student repeatedly fails, with struggle scores — your lesson-picker input |
| `GET /api/v1/students/me/diagnostics/summary` | aggregated top error types + hint usage |
| `GET /api/v1/remediation/me/recommendations` | active remediation triggers shaped as lesson recommendations |
| `POST /api/v1/remediation/me/triggers/{id}/lesson-opened` | report the student opened your micro-lesson |
| `POST /api/v1/remediation/me/triggers/{id}/quiz-completed` | report quiz result `{quiz_id, score_percent}` — ≥70% marks the trigger completed |

### Gamification Engine

| Endpoint | Returns |
|---|---|
| `GET /api/v1/students/me/concept-mastery` | per-concept mastery scores (your XP/levels input) |
| `GET /api/v1/students/me/diagnostics?status=resolved` | fixed bugs (award points) |
| `GET /api/v1/events/me?event_type=hint_level_requested` | hint usage (dependency scoring) |
| `GET /api/v1/gamification/me/*` | recommendation/adaptation endpoints (this logic will migrate to your service) |

### Pair Review Studio

| Endpoint | Returns |
|---|---|
| `GET /api/v1/collaboration/me/prompts` | pairing prompts derived from struggles |
| `POST /api/v1/collaboration/me/pair-sessions` | record a pairing session |
| `POST /api/v1/collaboration/me/peer-reviews` | record a peer review |

### Website dashboard

| Endpoint | Returns |
|---|---|
| `GET /api/v1/dashboard/me/overview` | headline stats for the student home page |
| `GET /api/v1/dashboard/me/timeline` | activity timeline |
| `GET /api/v1/students/me/diagnostics` | full error history (filters: `learning_session_id`, `error_type`, `status`, `limit`) |

### Renamed July 2026 (old → new — old paths are GONE)

```
GET /api/v1/users/me/concept-struggles   → GET /api/v1/students/me/struggling-concepts
GET /api/v1/users/me/diagnostic-summary  → GET /api/v1/students/me/diagnostics/summary
GET /api/v1/users/me/mastery             → GET /api/v1/students/me/concept-mastery
GET /api/v1/diagnostics/me               → GET /api/v1/students/me/diagnostics
```

## 3. Errors, conventions, gotchas

- Errors are `{"detail": "human-readable reason"}` with proper status codes:
  `401` bad/expired token → refresh and retry once; `404` not yours/absent;
  `409` conflict (e.g. email already registered); `422` invalid body.
- All timestamps are ISO-8601 UTC. All bodies are JSON.
- List endpoints accept `limit` (see `/docs` for per-endpoint ranges).
- First request after idle may take a few extra seconds on Cloud Run
  (scale-from-zero cold start) — not a bug, don't add aggressive timeouts.

## 4. Events (async) — see inter-service-events.md

Everything above is request/response. For *reacting* to things Code Coach
detects (e.g. "student is struggling → Study Guider shows a lesson"), we use
published events instead of polling — topics and JSON schemas are specified in
[inter-service-events.md](inter-service-events.md).
