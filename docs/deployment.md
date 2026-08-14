# Deploying the Code Coach Backend

> Goal: a public HTTPS URL for the backend, so the VS Code extension works
> from anywhere — the prerequisite for publishing to the Marketplace.
> The container is built once ([Dockerfile](../Dockerfile)); where you run it
> is a choice between two paths below.

## What the container contains (and what it never contains)

- `backend/app` (source), `backend/models` (the 5 trained .joblib models,
  validated at startup), `knowledge_base/` (hints/lessons) — the same layout
  the code expects locally.
- **Never**: `backend/secrets/`, `.env`, `data/`, tests, dev_tools — enforced
  by [.dockerignore](../.dockerignore). All configuration enters as
  environment variables at run time.

Required environment variables in production:

| Variable | Value | Why |
|---|---|---|
| `JWT_SECRET` | a long random string (NOT the dev one) | signs access tokens |
| `FIREBASE_PROJECT_ID` | `code-guru-1b5d9` | Firestore project (ADC — no key file on GCP) |
| `FIREBASE_CREDENTIALS_PATH` | only OUTSIDE Google Cloud | key-file auth for non-GCP hosts |

## Local verification (already scripted)

```powershell
docker build -t code-coach-backend .
docker run --rm -p 8000:8080 `
  -v ${PWD}/backend/secrets:/app/backend/secrets:ro `
  -e FIREBASE_CREDENTIALS_PATH=secrets/firebase-service-account.json `
  -e JWT_SECRET=local-container-test `
  code-coach-backend
# then: curl http://127.0.0.1:8000/health
```

## Path A — Google Cloud Run (recommended)

**Why:** scales to zero (no cost while idle), automatic HTTPS, same Google
project as your Firestore, and Firestore auth needs no key file (the service
authenticates as itself).

**⚠️ The one catch:** Cloud Run requires the project to be upgraded from the
Spark (free) plan to **Blaze** — pay-as-you-go with a credit/debit card on
file. The free tier is generous (2M requests/month, 360k GiB-seconds — a
student project stays at $0 in practice), but the card is mandatory. Decide
this consciously; set a budget alert (e.g. $1) in Google Cloud Billing when
you upgrade. If you don't want a card involved, use Path B.

Steps (one time):

1. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install),
   then `gcloud auth login` and `gcloud config set project code-guru-1b5d9`.
2. Upgrade the Firebase project to Blaze (Firebase console, bottom-left
   "Upgrade") and set a billing budget alert.
3. Deploy — from the repo root:

   ```bash
   gcloud run deploy code-coach-backend \
     --source . \
     --region asia-south1 \
     --allow-unauthenticated \
     --set-env-vars FIREBASE_PROJECT_ID=code-guru-1b5d9,JWT_SECRET=<GENERATE-A-NEW-LONG-RANDOM-ONE>
   ```

   (`--source .` makes Cloud Build use the Dockerfile; `asia-south1` =
   Mumbai, closest region to Sri Lanka. `--allow-unauthenticated` is correct
   here — your own JWT auth protects the API endpoints.)
4. Grant Firestore access to the service account if prompted (Cloud Run's
   default compute service account usually already has it via the
   `Editor`/`Datastore User` role).
5. The command prints your public URL, e.g.
   `https://code-coach-backend-xxxxx-el.a.run.app`. Verify:
   `curl <url>/health` → `{"status":"ok"}`.

## Path B — Render.com free tier (no card needed)

**Why:** free web services without a credit card. **Trade-offs:** the free
instance sleeps after ~15 min idle (first request after that takes ~1 min —
fine for demos, feels slow in daily use), and you must upload the service
account key as a Secret File because Render is outside Google Cloud.

1. Push the repo to GitHub (Render deploys from your repo).
2. render.com → New → Web Service → connect the repo. Render auto-detects
   the Dockerfile.
3. Environment: add `JWT_SECRET` (new random value) and
   `FIREBASE_CREDENTIALS_PATH=/etc/secrets/firebase-service-account.json`.
4. Secret Files: add `firebase-service-account.json` with the key file's
   contents (Render mounts secret files under `/etc/secrets/`).
5. Deploy; verify `<url>/health`.

## After either path: point the extension at it

1. In the extension, set `codeCoach.backendUrl` to the deployed URL (user
   setting), or change the default in the extension's configuration so the
   Marketplace build ships pointing at production.
2. Full smoke: sign in from VS Code, analyze `TotalMarksPrinter.java`, watch
   the diagnostic appear in the Firestore console.

## Marketplace note (the step after this)

Publishing needs: a free publisher account on the VS Code Marketplace
(via Azure DevOps), `npm i -g @vscode/vsce`, a `publisher` field + icon in
package.json, then `vsce publish`. Do it only after the backend URL is
stable — the shipped default must point somewhere that exists.
