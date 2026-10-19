# Code Guru — Integration Guide

> **Audience:** anyone working on a Code Guru service — Code Coach, Study
> Guider, PairPath, the Gamification Engine, or the web app.
>
> Code Coach is the platform's **identity provider** and the owner of every
> struggle signal. No other service touches its database; this API is the
> contract.
>
> - [`API_CONTRACT.md`](API_CONTRACT.md) — every endpoint, generated from the
>   running service (`python -m app.dev_tools.export_api_contract` in
>   `backend/`), so it cannot drift from the code.
> - [`openapi.json`](openapi.json) — the same thing for Postman and client
>   generators.
> - [`inter-service-events.md`](inter-service-events.md) — the learning events
>   each component emits.

---

## 1. The pieces

| Service | Repository | Local port | Database |
|---|---|---|---|
| Web app (the only UI) | `codeguru-web` | `4200` | none - an encrypted session cookie |
| Code Coach API | `code-coach/backend` | `8000` | MongoDB Atlas |
| Study Guider API | `Study-Guider/backend` | `8010` | Neo4j AuraDB |
| PairPath API (+ Socket.IO) | `Pair_Path/backend` | `3001` | PostgreSQL (Neon), Redis optional |
| PairPath ML service | `Pair_Path/backend/ml` | `8020` | none |
| Gamification API | `adaptive-gamification-engine/backend` | `3002` | MongoDB Atlas (its own cluster) |
| Gamification ML service | `adaptive-gamification-engine/backend/ml` | `5000` | none |
| VS Code extension | `code-coach/extension/code-coach-vscode` | - | - |

**The browser talks to the web app and nothing else** (plus PairPath's socket).
`codeguru-web` is a backend-for-frontend: it holds the student's tokens in an
encrypted cookie and forwards each call server-side through
`/api/bff/<service>/...`, so no backend URL or token reaches the browser and no
backend needs CORS for it. The VS Code extension is the one other client: it
calls Code Coach's `/api/v1` directly with its own tokens.

---

## 2. Signing in

There is one account for the whole platform, held by Code Coach.

- **Web:** the web app's own login and register pages call Code Coach's
  `/api/v1/auth/*`, then keep the tokens in its session cookie.
- **VS Code extension:** "Sign in" opens the web app, which asks Code Coach for
  a one-time code (`POST /api/v1/auth/handoff`) and passes it back to the
  extension over a loopback address; the extension redeems it
  (`POST /api/v1/auth/handoff/redeem`) for its own tokens.
- **PairPath** issues its own JWT, because its Socket.IO handshake verifies its
  own signature and every foreign key points at its local `users.id`. The web
  app trades the Code Coach token for one at `POST /auth/exchange`, which
  verifies it with Code Coach and finds or creates the local user.

`client_name` on login records where a session came from:

| Client | `client_name` |
|---|---|
| Web app | `codeguru-web` |
| VS Code extension (own sign-in) | `code-coach-vscode` |
| VS Code extension (handoff from the web) | `codeguru-vscode` |
| PairPath's exchange | `pair-review-studio` |

---

## 3. Verifying a token in your backend

Your service receives requests carrying the student's Code Coach access token.
You cannot verify it yourself — you have no share of Code Coach's signing
secret, and sessions are revocable server-side. So ask:

```
Web app BFF ──(Bearer T)──▶ Your service ──GET /api/v1/auth/me (Bearer T)──▶ Code Coach
                                           ◀── 200 {user_id, full_name, role}   valid
                                           ◀── 401                              reject
```

**Cache the result for ~60 seconds per token.** The trade is that a revoked
token stays usable for at most the TTL. References:
`Study-Guider/backend/app/core/auth.py`,
`adaptive-gamification-engine/backend/middleware/auth.js`.

1. **`me` means the token's owner.** Forward the student's token rather than
   using a service account, and authorization comes free.
2. **Never take a `user_id` from a request body.** Anyone can type a different id.
3. **Distinguish "rejected" from "could not check".** A `401` from `/auth/me`
   means reject. A timeout or connection error means Code Coach is down —
   answer `503`, not `401`, and never let the request through.

**Server to server** calls that are not made for one student (PairPath asking
which concepts and mistakes are in a pair's code) use `/api/v1/internal/*` with
the shared `X-Internal-Key` header, set as `INTERNAL_SERVICE_KEY` on both
sides. PairPath asks Study Guider for the review after a session the same way
(`/api/session-review`), because that request carries the exercise's model
solution.

---

## 4. What each service reads

`me` always means "the student identified by the bearer token".

### Study Guider — remediation

Code Coach raises a **remediation trigger** when a student repeatedly fails the
same concept.

| Call | Purpose |
|---|---|
| `GET /api/v1/remediation/me/recommendations` | active triggers, already shaped into a lesson + quiz recommendation |
| `GET /api/v1/remediation/me/triggers` | the raw triggers — `repeat_count`, `struggle_score`, hint dependence |
| `POST /api/v1/remediation/me/triggers/{id}/lesson-opened` | student opened the lesson → moves the trigger off `pending` |
| `POST /api/v1/remediation/me/triggers/{id}/quiz-completed` | `{quiz_id, score_percent}` → **≥70% completes the trigger** |
| `GET /api/v1/students/me/struggling-concepts` | struggle scores, to pick lessons yourself |

Send only the score and let Code Coach apply the pass mark. **A trigger carries
no student code** — only a hash of the code around a diagnostic — so teach from
the concept, and label any snippet you show as an example.

### Gamification Engine

| Call | Purpose |
|---|---|
| `GET /api/v1/students/me/concept-mastery` | per-concept mastery scores |
| `GET /api/v1/gamification/me/recommendations` | adaptive practice recommendations |
| `POST /api/v1/gamification/me/adaptation-decisions` | record a difficulty/support decision |
| `POST /api/v1/gamification/me/session-results` | record a game result → updates mastery |

### PairPath — collaboration

| Call | Purpose |
|---|---|
| `GET /api/v1/collaboration/me/prompts` | pairing prompts derived from struggle signals |
| `POST /api/v1/collaboration/me/pair-sessions` | record a pairing session |
| `POST /api/v1/collaboration/me/peer-reviews` | record a peer review |
| `POST /api/v1/collaboration/me/pair-session-results` | one student's outcome for a finished session |
| `POST /api/v1/internal/concepts` | (server to server) concepts and error types in a pair's code, for hints and suggested exercises |

### Web app

Everything above through the BFF, plus account, subscription (`/billing/me/*`),
dashboard (`/dashboard/me/*`), diagnostics (`/students/me/*`) and the error
catalogue (`/code-coach/catalog`).

### Any service — sessions and events

| Call | Purpose |
|---|---|
| `POST /api/v1/learning-sessions` | create or resume the session that groups a student's activity |
| `POST /api/v1/events` | emit a learning event from your component |
| `GET /api/v1/events/me` | read them back |

---

## 5. Conventions

- JSON in, JSON out. All timestamps ISO-8601 UTC.
- Errors are `{"detail": "human readable reason"}`, written to be shown to a
  student — surface it rather than inventing your own wording.
- Statuses: `400` bad request · `401` invalid/expired token · `402` needs Pro ·
  `403` inactive account · `404` not found or not yours · `409` conflict ·
  `422` validation failed · `429` too many attempts (respect `Retry-After`).
- **Access tokens live 1 hour.** On `401`, refresh at `/api/v1/auth/refresh`,
  store the new pair (refresh tokens **rotate** — the old one is dead), and
  retry **once**. The web app's BFF already does this.
- Concept tags are the platform's shared vocabulary: the fourteen in
  `knowledge_base/code_coach_errors.json`. Use them as they are.

---

## 6. Running it locally

**The whole platform, one command** — from `codeguru-web/deploy`:

```bash
docker compose build
docker compose up -d        # http://localhost:8080, or HTTP_PORT if set
```

Each service's settings come from its own `.env`, as that compose file
describes. On machines where Windows reserves 8080, set `HTTP_PORT` (for
example `8200`).

**One service at a time**, against a running Code Coach:

```bash
cd code-coach/backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
cd codeguru-web && npm run dev                                     # 4200
cd Study-Guider/backend && .venv/Scripts/python -m uvicorn app.main:app --port 8010
cd Pair_Path/backend && npm run start:dev                          # 3001
cd Pair_Path/backend/ml && .venv/Scripts/python -m app.main        # 8020
cd adaptive-gamification-engine/backend && npm start               # 3002
cd adaptive-gamification-engine/backend/ml && python app.py        # 5000
```

Sign in at `http://localhost:4200`. Code Coach must run on MongoDB, not its
in-memory fallback, or every account is lost on restart — check that the
startup line says `Storage backend: MongoDB`.

To get a student with remediation triggers to test against, run
`python -m app.dev_tools.seed_student` in `code-coach/backend` (read it first:
it creates the account and triggers through the running API).

## 7. Deployment

Each repository deploys itself: a push to `main` runs its tests, builds its
images, pushes them to ECR and rolls them out on the AWS server
(`.github/workflows/`). The server's compose file, Caddy configuration and
deploy scripts are in `codeguru-web/deploy/aws`.
