# Firebase / Firestore Setup — Code Coach

> Follow this once. At the end, every account, learning session, diagnostic
> and event survives backend restarts, stored in your Firestore database
> (project **CodeGuru / code-guru-1b5d9**), visible live in the Firebase console.

## What was decided and why (for the report)

- **Firestore replaces MongoDB/in-memory as the database.** The backend
  already had a storage-adapter seam (`build_storage()` in
  `backend/app/db/storage.py`), so this added ONE new file
  (`firestore_storage.py`) and changed zero routes or services.
- **Custom auth stays** (Argon2 password hashing + JWT with refresh-token
  rotation). Firebase *Authentication* was considered and deferred: it would
  centralize identity across all four microservices, but replacing a working,
  well-built auth layer before the viva is risk without functional gain.
- Document IDs are the natural keys (`userId`, `authSessionId`, ...), and
  queries use at most one equality filter with filtering/sorting in Python —
  so **no composite indexes ever need to be created or managed**. At student
  scale this is the right trade; the file documents when to revisit it.

## One-time setup (about 3 minutes)

### Step 1 — Generate the service account key

The backend authenticates to Firestore as a *service account* (a robot
identity), not as your Google account.

1. Open the [Firebase console](https://console.firebase.google.com/) →
   project **CodeGuru**.
2. Click the **gear icon** next to "Project Overview" (top-left) →
   **Project settings**.
3. Go to the **Service accounts** tab.
4. Keep **Python** selected, click **Generate new private key** → **Generate
   key**. A `.json` file downloads.
5. Move and rename it to exactly:

   ```
   backend/secrets/firebase-service-account.json
   ```

   The `backend/secrets/` folder already exists and is **gitignored** — this
   file is a password-equivalent secret. Never commit it, never paste its
   contents in chat, never share it. If it ever leaks: same console tab →
   "Manage service account permissions" → delete the key and generate a new
   one.

### Step 2 — Point the backend at it

In `backend/.env`, uncomment the line that is already there:

```env
FIREBASE_CREDENTIALS_PATH=secrets/firebase-service-account.json
```

(The path is relative to the `backend/` folder you run the server from.
`MONGODB_URI` stays commented out — Firestore wins when both are set.)

### Step 3 — Verify

From `backend/`:

```bash
python -m app.dev_tools.check_firestore
```

This exercises EVERY storage operation against the real database — user
creation, refresh-token rotation, the diagnostic active→resolved lifecycle,
remediation dedupe — printing `OK` per check, then deletes everything it
created. Expected ending: `ALL CHECKS PASSED`.

### Step 4 — Run the app for real

Start the backend as usual (it will print `Storage backend: Firestore
(project=code-guru-1b5d9)` on startup), launch the extension in debug mode,
**create your account again** (the old one lived in memory and is gone),
and analyze a demo file. Then open the Firebase console → **Firestore
Database → Data**: you'll see `users`, `authSessions`, `learningSessions`,
`codeDiagnostics`, `learningEvents` collections filling up as you type.
Restart the backend and sign in again — your account now survives.

## How the pieces map

| Mongo concept (old) | Firestore concept (new) |
|---|---|
| database `code-guru` | your project's `(default)` database |
| collection (e.g. `users`) | collection (same names kept) |
| document with `userId` field | document whose **ID is** the `userId` |
| `find_one({"userId": ...})` | direct document read (no query at all) |
| compound query + sort + index | one equality filter, then Python filter/sort |

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `FileNotFoundError: ... service account key not found` | Key not at `backend/secrets/firebase-service-account.json`, or you ran from the wrong folder — run from `backend/`. |
| `403 PERMISSION_DENIED` / `Cloud Firestore API has not been used` | Open the printed link and enable the Firestore API, or confirm the key belongs to project `code-guru-1b5d9`. |
| `DefaultCredentialsError` | `.env` line still commented out. |
| Old account can't log in | Expected — in-memory data died with the old process. Register again once; from now on it persists. |
