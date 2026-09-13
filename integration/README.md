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
> - [`prerequisite-graph.md`](prerequisite-graph.md) — what the concept
>   prerequisite graph is, how Code Coach derives one from real student
>   histories, and why it currently refuses to. Written for a reader who
>   has not seen it before.

---

## 1. Ports

Three services all defaulted to 8000. Use these:

| Service | Port |
|---|---|
| Code Coach backend | `8000` |
| **CodeGuru Portal** (the shared login UI) | `4200` |
| Study Guider — backend / frontend | `8010` / `5173` |
| PairPath — API / frontend / ml-service | `3001` / `3000` / `8020` |
| Gamification — API / frontend / ml-service | `3002` / `5174` / `8030` |

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

### Code Coach signs in the same way

Code Coach's UI is a VS Code extension, so it used to be the one service where
a student typed a password into the app itself. It now opens the portal in the
browser like everything else:

```
VS Code                    Portal (4200)              Code Coach (8000)
───────                    ─────────────              ─────────────────
Sign In
  listen on 127.0.0.1:53682
  open browser ──▶ /login?redirect_uri=http://127.0.0.1:53682/callback
                           student signs in
                           POST /api/v1/auth/handoff ──▶ { code }   (single use, 120s)
  ◀── http://127.0.0.1:53682/callback?code=… ──
  POST /api/v1/auth/handoff/redeem ──────────────────▶ { user, tokens }
```

Three things are different from the browser handoff, all for the same reason —
a loopback HTTP server never receives a URL fragment:

- **A code, not a token.** It is single-use, expires in 120 seconds, and grants
  nothing on its own, so putting it in a query string is safe in a way that
  putting an access token there would not be. No access token ever appears in a
  URL in this flow.
- **A fixed port (53682).** `redirect_uri` is checked by *exact origin*, so an
  ephemeral port could never be allowed. `http://127.0.0.1:53682` is in
  `VITE_ALLOWED_REDIRECTS`; the allow-list is not loosened to accommodate it.
  If the port is busy the extension says so and falls back to its prompts
  rather than silently picking another port the portal would reject.
- **Redeeming mints a NEW session** under `client_name: code-coach-vscode`
  rather than sharing the portal's. Two clients sharing one refresh token would
  fight over rotation, and signing out in the browser would silently sign the
  student out of their editor.

A `vscode://codeguru.code-coach-vscode/auth?code=…` handler is registered as a
second route. The original input-box prompts remain as the fallback for remote
/ SSH / WSL windows, where a loopback listener on the remote host is not the
loopback the local browser reaches.

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

The four frontends live in four separate repos, so there is no build-time way
to share code. One file is **copied** into each:

| Repo | Path |
|---|---|
| **code-coach** (master) | `portal/src/lib/codeguru-auth.js` |
| Study-Guider | `frontend/src/lib/codeguru-auth.js` |
| Pair_Path | `frontend/src/lib/codeguru-auth.js` |
| adaptive-gamification-engine | `frontend/src/lib/codeguru-auth.js` |

It holds the login/register/refresh/me/logout calls with the exact wire field
names, token storage, the 401-refresh-retry-once rule, the dev-login gate, and
both sides of the portal handoff.

**Change it in the master, then run `code-coach/sync-codeguru-auth.sh`** and
commit the result in each repo. The script keeps each copy's "do not edit"
header and verifies the bodies match. Editing a copy directly is how you get
`identifier` vs `email` mismatches — the exact bug this file prevents.

It takes its configuration as arguments (base URL, dev-login flag) precisely so
it can stay identical across three different bundlers. Keep it that way.

### The shared look: `codeguru-theme.css` and `CodeGuruBar`

Two more files are copied the same way, by
**`code-coach/sync-codeguru-shared.sh`**:

| File | Master | Copied to |
|---|---|---|
| `codeguru-theme.css` | `portal/src/styles/` | `<frontend>/src/styles/` in all three |
| `CodeGuruBar.jsx` | `portal/src/components/` | Study Guider, Gamification |
| `CodeGuruBar.tsx` | — | PairPath only, a hand-written TypeScript twin |

**`codeguru-theme.css`** is the whole palette, plus radius, shadow, easing and
typeface. Two layers, because three consumers need different formats:

- `--cg-rgb-*` — raw `R G B` triplets. PairPath's `tailwind.config.js`
  interpolates them with `<alpha-value>`, which is what keeps
  `bg-surface-800/50` working.
- `--cg-*` — ready-made `rgb()` values, for stylesheets and for inline
  `style={{}}` props. Inline styles beat every stylesheet, so they can only be
  re-themed by holding a `var()` themselves.

Two places where `var()` does **not** work, and both bit us:

- **SVG presentation attributes.** `stroke="var(--cg-accent)"` on a Recharts
  series or a lucide icon renders with no colour at all — attributes are not CSS
  declarations. Resolve the token first (Study Guider's `lib/theme.js`) or set
  CSS `color` and let `currentColor` do it.
- **Libraries that render their own SVG**, like Mermaid and Monaco. They need
  their own theme configured from resolved token values.

**`CodeGuruBar`** is the platform bar. Its service links point at
`{portal}/go?to=<key>`, which resolves the key against the portal's registry and
reuses the allow-listed handoff — so your service never needs to know where its
siblings live, and it carries the session across the origin boundary. Mount it
with your service key, `PORTAL_URL`, the user, and a sign-out handler. All its
styling lives in the theme file, so the copies cannot drift apart visually.

Dark mode is deliberately not built yet: `:root[data-theme='dark']` in the theme
file is empty. Because every service reaches colour through these tokens, adding
it is a values-only change there plus a toggle in the bar — no component needs
to be touched.

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

Built and integrated. It has no accounts of its own: it verifies every request
against Code Coach and reads struggle data from there rather than keeping a
local copy.

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

## 7. One account, several clients

Code Coach is the identity provider; the portal is the one *web* login. The VS
Code extension signs in inside the IDE, and that is not an exception to the
single-login rule — it is the same account reached from a different client.

Every surface calls the same `/api/v1/auth/*` endpoints with the same fields.
The only thing that differs is `client_name`, which is recorded on the auth
session so you can tell where a login came from:

| Surface | `client_name` |
|---|---|
| VS Code extension | `code-coach-vscode` |
| CodeGuru Portal (web) | `codeguru-portal` |
| Study Guider | `codeguru-study-guider` |
| PairPath | `pair-review-studio` |

Same email and password, same `user_id`, same diagnostics and triggers. A
student who registers at the portal can sign into the extension with those
credentials, and the errors the extension finds drive the lessons the portal
sends them to. This is the shape GitHub uses: one account, reached from the
web, a CLI, or an IDE.

The extension cannot use the portal handoff because a redirect back into VS
Code needs a `vscode://` URI handler — doable, but a separate piece of work.
Until then the IDE keeps its own sign-in prompt against the same endpoints.

---

## 8. Testing the integration before anything is deployed

Nothing is on Cloud Run yet, so "the platform" is a set of processes on one or
more laptops. Three ways to run it, depending on what you are doing.

### Mode 1 — working on your own service (most of the time)

You need Code Coach and your service. **You do not need the portal.**

```bash
# terminal 1
cd code-coach/backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# terminal 2 — your own service, with CODE_COACH_URL pointing at 8000
```

Set `VITE_ENABLE_DEV_LOGIN=true` (or `NEXT_PUBLIC_ENABLE_DEV_LOGIN=true`) and
sign in at your own `/dev-login`. This is exactly what that page is for: same
Code Coach calls, same fields, no portal round trip.

### Mode 2 — the whole platform on one machine

Five processes. Ports are in §1.

```bash
cd code-coach/backend  && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
cd code-coach/portal   && npm run dev                    # 4200
cd Study-Guider/backend && python -m uvicorn app.main:app --port 8010
cd Study-Guider/frontend && npm run dev                  # 5173
cd Pair_Path/api && npm run start:dev                    # 3001
cd Pair_Path/frontend && npm run dev                     # 3000
```

Sign in at `http://localhost:4200` and follow the hub links — the session
travels with you.

### Mode 3 — the team, on different laptops

**Only Code Coach needs to be shared.** Everything else each person runs
locally against it. One person (whoever owns Code Coach) exposes it:

```bash
cloudflared tunnel --url http://localhost:8000
```

That prints a URL like `https://random-words-1234.trycloudflare.com`. Share it.
Everyone else sets it as their `CODE_COACH_URL` / `VITE_CODE_COACH_URL` /
`NEXT_PUBLIC_CODE_COACH_URL` and otherwise runs exactly as in Mode 1.

The hostname **changes every time the tunnel restarts**, which is why every
service reads it from the environment and none of them hardcode it.

Two things the Code Coach owner must do:

1. **Run on MongoDB, not in-memory.** Code Coach falls back to in-memory
   storage when no credentials are configured, and then every account, session
   and trigger is lost on restart — teammates cannot see each other's data, and
   an already-signed-in VS Code extension gets silently logged out (its stored
   session no longer exists, the 401 clears its tokens, and auto-analysis fails
   quietly with no prompt). Check the startup line says
   `Storage backend: MongoDB`.
2. **Add teammates' origins to CORS.** Browsers calling the tunnel from
   `http://localhost:5173` etc. are blocked otherwise:

   ```
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:4200
   ```

   Server-to-server calls (Study Guider's backend, PairPath's API) are never
   affected by CORS — only browsers are.

If someone wants the full portal flow across machines, they run their own copy
of the portal locally pointing at the shared Code Coach; the portal holds no
state of its own. Its `VITE_ALLOWED_REDIRECTS` must list whatever origin it is
handing the token back to.

### Seeding a trigger to test against

Study Guider shows "nothing to work on" until Code Coach has actually raised a
remediation trigger, which needs the *same* concept to fail repeatedly. Either:

- **Through the extension** — open one of the sample programs in
  `extension/code-coach-vscode/src/sample-java/` and let it analyze. Each of the
  six has planted errors; three repeats of one concept crosses the threshold.
- **By hand**, which is faster for backend work:

  ```bash
  # 1. register (or login) -> keep tokens.access_token
  curl -X POST $CC/api/v1/auth/register -H 'Content-Type: application/json'     -d '{"full_name":"Test Student","email":"t@example.com","password":"test-1234","client_name":"codeguru-portal"}'

  # 2. create a learning session -> keep learning_session_id
  curl -X POST $CC/api/v1/learning-sessions -H "Authorization: Bearer $AT"     -H 'Content-Type: application/json' -d '{"source_component":"code_coach","language":"java"}'

  # 3. analyze Java with the SAME mistake three times over
  #    (e.g. three `arr[arr.length]` lines) -> raises a high-struggle trigger
  curl -X POST $CC/api/v1/code-coach/analyze -H "Authorization: Bearer $AT"     -H 'Content-Type: application/json' -d '{"language":"java","code":"...","learningSessionId":"ls_..."}'

  # 4. confirm
  curl $CC/api/v1/remediation/me/recommendations -H "Authorization: Bearer $AT"
  ```

Triggers are created by a background task after the analysis response is sent,
so allow a second or two before step 4.

### What "working" looks like end to end

1. Register at the portal → land on the hub.
2. Sign into the VS Code extension with those same credentials → yellow
   underlines on a sample program.
3. Repeat one mistake three times → `GET /api/v1/remediation/me/recommendations`
   returns a trigger.
4. Open Study Guider from the hub → that trigger is on screen, with the real
   concept and repeat count.
5. Open the lesson → the trigger's `intervention_status` becomes
   `lesson_opened`.
6. Pass the quiz (≥70%) → the trigger completes, drops off the list, and
   `GET /api/v1/students/me/concept-mastery` shows the concept updated.
