# Code Guru — Integration Guide

> **Audience:** everyone building a Code Guru service — Study Guider, PairPath,
> the Gamification Engine, and anything added later.
>
> Code Coach is the platform's **identity provider** and the owner of every
> struggle signal. You never touch its database; this API is the contract.
>
> - [`API_CONTRACT.md`](API_CONTRACT.md) — every endpoint, generated from the
>   running service (`python -m app.dev_tools.export_api_contract`), so it
>   cannot drift from the code.
> - [`openapi.json`](openapi.json) — the same thing for Postman / client
>   generators.
> - [`inter-service-events.md`](inter-service-events.md) — the async half.

---

## 1. Ports

Three services all defaulted to 8000. Use these:

| Service | Port |
|---|---|
| Code Coach backend | `8000` |
| **CodeGuru Portal** (the shared login UI) | `4200` |
| Study Guider — backend / frontend | `8010` / `5173` |
| PairPath — API / frontend / ml-service | `3001` / `3000` / `8020` |

Every service's CORS allow-list must include the portal origin. Code Coach
already allows 3000, 5173 and 4200 out of the box
(`backend/app/core/config.py`, `CORS_ALLOWED_ORIGINS`).

---

## 2. One login for the whole platform

There is **one** login and registration UI: the **CodeGuru Portal**
(`code-coach/portal`, port 4200). Your service does not have a login page.

### The handoff

```
Your app                          Portal (4200)                  Code Coach (8000)
────────                          ─────────────                  ─────────────────
no session?
  redirect ────────▶ /login?redirect_uri=<your url>
                                  student signs in
                                       │  POST /api/v1/auth/login
                                       ▼
                                                    ◀── { user, tokens } ──
  ◀── <your url>#access_token=…&refresh_token=…&expires_in=…&user_id=… ──

  store the tokens, scrub the fragment, carry on
```

Both halves are already written for you in **`codeguru-auth.js`** (see §4):

```js
// On load, in every app:
consumeHandoffFragment();          // adopts a session from the fragment, clears the URL
if (!isSignedIn()) redirectToPortal(PORTAL_URL);
```

**Why the fragment and not a query string:** a fragment is never sent to a
server, so the token stays out of access logs and `Referer` headers. It does
land in browser history, which is why `consumeHandoffFragment` replaces the URL
the moment it has read it.

**`redirect_uri` is validated against an allow-list** (`VITE_ALLOWED_REDIRECTS`
in the portal's env). Without that check the portal would be an open redirect
handing students' access tokens to any URL that asked. **Add your origin to
that list** or the portal will refuse to return to you — which is the intended
behaviour, not a bug.

### Working on localhost

You should not need the portal running to develop your own service. Each
frontend carries a **localhost-only** login form:

- It renders only when `devLoginEnabled(flag)` passes: the page must be served
  from `localhost`/`127.0.0.1` **and** the build flag must be set
  (`VITE_ENABLE_DEV_LOGIN` / `NEXT_PUBLIC_ENABLE_DEV_LOGIN`). Two independent
  guards, so a flag left on in a deployed build cannot ship a second login page.
- It is **not a second implementation**. It calls the same Code Coach endpoints
  with the same field names through the same `codeguru-auth.js`. Only the
  hosting differs, so the localhost path exercises the production one.

Deployed builds leave the flag unset and redirect to the portal instead.

---

## 3. Verifying a token in YOUR backend

Your service receives requests carrying the student's Code Coach access token.
You cannot verify it yourself — you have no share of Code Coach's signing
secret, and sessions are revocable server-side. So ask:

```
Browser ──(Bearer T)──▶ Your service ──GET /api/v1/auth/me (Bearer T)──▶ Code Coach
                                        ◀── 200 {user_id, full_name, role}   valid ✓
                                        ◀── 401                              reject ✗
```

**Cache the result for ~60 seconds per token.** Without it every page load pays
a network round trip before it can render. The trade is that a revoked token
stays usable for at most the TTL. Study Guider's implementation is a good
reference: `Study-Guider/backend/app/core/auth.py`.

Three rules worth stating outright:

1. **`me` means the token's owner.** Every `/me` endpoint resolves to the user
   the token belongs to. Forward the *student's* token rather than using a
   service account and authorization comes free — you cannot read another
   student's data even by accident.
2. **Never take a `user_id` from a request body.** That is not authentication;
   anyone can type a different id. Study Guider did this before integration and
   every student's progress was readable by anyone who guessed an id.
3. **Distinguish "rejected" from "could not check".** A `401` from `/auth/me`
   means reject. A timeout or connection error means Code Coach is down — answer
   `503`, not `401`. Returning a user in that case turns an outage into an
   authentication bypass. See `Pair_Path/api/src/modules/auth/code-coach.service.ts`
   (`me` fails closed; `login` deliberately fails soft).

### If your service issues its own tokens

PairPath does, because its Socket.IO handshake verifies its own signature and
every foreign key points at its local `users.id`. It exposes
`POST /auth/exchange`, which takes a Code Coach access token, verifies it via
`/auth/me`, finds-or-creates the local user, and returns a PairPath JWT. Do the
same rather than adopting a foreign token into a schema that cannot key on it.

---

## 4. `codeguru-auth.js` — copy it, do not rewrite it

The three frontends live in three separate repos, so there is no build-time way
to share code. One file is **copied** into each:

| Repo | Path |
|---|---|
| **code-coach** (master) | `portal/src/lib/codeguru-auth.js` |
| Study-Guider | `frontend/src/lib/codeguru-auth.js` |
| Pair_Path | `frontend/src/lib/codeguru-auth.js` |

It holds the login/register/refresh/me/logout calls with the exact wire field
names, token storage, the 401-refresh-retry-once rule, the dev-login gate, and
both sides of the portal handoff.

**Change it in the master, then run `code-coach/sync-codeguru-auth.sh`** and
commit the result in each repo. The script keeps each copy's "do not edit"
header and verifies the bodies match. Editing a copy directly is how you get
`identifier` vs `email` mismatches — the exact bug this file prevents.

It takes its configuration as arguments (base URL, dev-login flag) precisely so
it can stay identical across three different bundlers. Keep it that way.

---

## 5. What each service reads

`me` always means "the student identified by the bearer token".

### Study Guider — remediation

Code Coach raises a **remediation trigger** when a student repeatedly fails the
same concept. This is the loop:

| Call | Purpose |
|---|---|
| `GET /api/v1/remediation/me/recommendations` | active triggers, already shaped into a lesson + quiz recommendation |
| `GET /api/v1/remediation/me/triggers` | the raw triggers — `repeat_count`, `struggle_score`, hint dependence |
| `POST /api/v1/remediation/me/triggers/{id}/lesson-opened` | student opened the lesson → moves the trigger off `pending` |
| `POST /api/v1/remediation/me/triggers/{id}/quiz-completed` | `{quiz_id, score_percent}` → **≥70% completes the trigger** |
| `GET /api/v1/students/me/struggling-concepts` | struggle scores, if you want to pick lessons yourself |

Triggers appear on their own: `sync_code_coach_remediation_triggers` runs in the
background after every analysis the VS Code extension submits.

**Send only the score and let Code Coach apply the pass mark.** `passed` is
optional; deciding it yourself lets your service disagree with the rest of the
platform about what passing means.

**A trigger carries no student code.** Code Coach stores only a hash of the code
around a diagnostic (`codeContextHash`), never the source — deliberate, and not
something to work around. Teach from the concept, and if you show an example
snippet, label it as an example rather than implying it is the student's own.

### Gamification Engine

Nothing is built yet, but the endpoints are and are documented in
[`API_CONTRACT.md`](API_CONTRACT.md), so you can code against a real contract
from day one.

| Call | Purpose |
|---|---|
| `GET /api/v1/students/me/concept-mastery` | per-concept mastery scores (XP / levels input) |
| `GET /api/v1/gamification/me/recommendations` | adaptive practice recommendations |
| `POST /api/v1/gamification/me/adaptation-decisions` | record a difficulty/support decision |
| `POST /api/v1/gamification/me/session-results` | record a game result → updates mastery |
| `GET /api/v1/events/me?event_type=hint_level_requested` | hint usage |

### PairPath — collaboration

| Call | Purpose |
|---|---|
| `GET /api/v1/collaboration/me/prompts` | pairing prompts derived from struggle signals |
| `POST /api/v1/collaboration/me/pair-sessions` | record a pairing session |
| `POST /api/v1/collaboration/me/peer-reviews` | record a peer review |

### Any service — sessions and events

| Call | Purpose |
|---|---|
| `POST /api/v1/learning-sessions` | create or resume the session that groups a student's activity |
| `POST /api/v1/events` | emit a learning event from your component |
| `GET /api/v1/events/me` | read them back |
| `GET /api/v1/dashboard/me/overview` | pre-aggregated student home page stats |

---

## 6. Conventions and gotchas

- JSON in, JSON out. All timestamps ISO-8601 UTC.
- Errors are `{"detail": "human readable reason"}`. That text is written to be
  shown to a student — surface it rather than inventing your own wording.
- Statuses: `400` bad request · `401` invalid/expired token · `403` inactive
  account · `404` not found or not yours · `409` conflict · `422` validation
  failed · `429` too many attempts (respect `Retry-After`).
- **Access tokens live 1 hour.** On `401`, call `/api/v1/auth/refresh`, store the
  new pair (refresh tokens **rotate** — the old one is dead), retry **once**.
  `codeguru-auth.js` already does this; do not reimplement it.
- Rate limiting on register/login/refresh is 10 attempts per IP per minute.
- Server-to-server calls are never blocked by CORS. Browsers are.
- The first request after an idle period on Cloud Run pays a cold start. Do not
  set aggressive client timeouts.

---

## 7. Running the whole platform locally

```bash
# 1. Code Coach (identity + data hub)
cd code-coach/backend && uvicorn app.main:app --port 8000

# 2. The portal (login UI)
cd code-coach/portal && cp .env.example .env && npm install && npm run dev   # 4200

# 3. Your service, with CODE_COACH_URL pointing at 8000
```

Sign in at `http://localhost:4200`, then follow the hub links — the session
travels with you.

Code Coach falls back to **in-memory storage** when no Firestore or MongoDB
credentials are configured. That is the easiest way to develop against it
without touching shared cloud data; it prints `Storage backend: in-memory` at
startup and forgets everything on restart.
