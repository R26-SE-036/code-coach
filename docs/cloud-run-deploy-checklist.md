# Cloud Run Deployment Checklist — Code Coach

> Decision made: the Code Coach backend deploys to **Google Cloud Run**
> (project `code-guru-1b5d9`, region `asia-south1`). This is the do-it-together
> checklist for the team meeting; the reasoning lives in
> [deployment.md](deployment.md). Tick boxes in order — each phase depends on
> the previous one.

## Phase 0 — Decisions the team must make first (5 min)

- [ ] **Whose card goes on the Blaze plan?** Cloud Run requires upgrading the
      Firebase project from Spark to Blaze (pay-as-you-go). Usage at our
      scale sits inside the free tier (2M requests + 360k GiB-seconds/month),
      so the expected bill is **$0** — but a card must be on file and its
      owner should be the one clicking in Phase 1.
- [ ] **Agree the cost guardrail**: budget alert at **$1**, alert email = the
      card owner.

## Phase 1 — One-time setup (card owner, ~10 min)

- [ ] Upgrade to Blaze: Firebase console → bottom-left **Upgrade** → follow
      the flow.
- [ ] Set the budget alert: [console.cloud.google.com/billing](https://console.cloud.google.com/billing)
      → Budgets & alerts → Create budget → amount $1 → alert at 50/90/100%.
- [ ] Install the gcloud CLI: <https://cloud.google.com/sdk/docs/install>
- [ ] Authenticate and select the project:

  ```bash
  gcloud auth login
  gcloud config set project code-guru-1b5d9
  ```

## Phase 2 — Deploy (any teammate with repo access, ~10 min)

- [ ] Generate a NEW production JWT secret (never reuse the dev one from
      `backend/.env`). In PowerShell:

  ```powershell
  -join ((65..90)+(97..122)+(48..57) | Get-Random -Count 48 | % {[char]$_})
  ```

- [ ] From the **repo root** (where the Dockerfile is):

  ```bash
  gcloud run deploy code-coach-backend \
    --source . \
    --region asia-south1 \
    --allow-unauthenticated \
    --set-env-vars FIREBASE_PROJECT_ID=code-guru-1b5d9,JWT_SECRET=<paste-the-new-secret>
  ```

  Notes: `--source .` sends the repo to Cloud Build, which uses our
  Dockerfile; first build takes ~5–8 min. `--allow-unauthenticated` is
  correct — our own JWT auth guards every data endpoint. **No Firestore key
  file is needed anywhere**: the service authenticates as its runtime
  service account (ADC).

- [ ] If the deploy warns about Firestore permissions: grant the service
      account the **Cloud Datastore User** role when prompted (or in IAM).
- [ ] Record the printed URL here: `https://code-coach-backend-________-el.a.run.app`

## Phase 3 — Verify the deployment (~5 min)

- [ ] `curl https://<url>/health` → `{"status":"ok"}`
- [ ] Startup log says the right backend: Cloud console → Cloud Run →
      code-coach-backend → **Logs** → look for
      `Storage backend: Firestore (project=code-guru-1b5d9)`.
- [ ] Register a throwaway account against the deployed URL and confirm the
      user document appears in Firestore console → Data.

## Phase 4 — Point the extension at production (~5 min)

- [ ] VS Code → Settings → `codeCoach.backendUrl` → the Cloud Run URL
      (for the Marketplace build: change the setting's **default** in the
      extension's package.json before packaging).
- [ ] Full smoke from a real editor: sign in → open
      `TotalMarksPrinter.java` → yellow underline appears → fix the bug →
      underline clears → diagnostic flips to `resolved` in Firestore.
- [ ] Cold-start check (expected behavior, not a bug): after ~15 idle
      minutes the first request takes a few extra seconds while a container
      spins up. Every request after that is fast (analysis itself is ~4 ms).

## Phase 5 — Redeploy & rollback (know before you need it)

- **Redeploy** (after any backend change): rerun the same
  `gcloud run deploy` command. Cloud Run shifts traffic to the new revision
  only when it passes startup.
- **Rollback**: Cloud console → Cloud Run → Revisions → select the previous
  revision → **Manage traffic** → 100% to it. (Or:
  `gcloud run services update-traffic code-coach-backend --to-revisions <rev>=100`)
- **Delete everything** (end of semester): `gcloud run services delete
  code-coach-backend --region asia-south1` — billing stops with it.

## What we deliberately did NOT set up (and why)

- **No key file on Cloud Run** — ADC replaces it; the key file stays a
  local-development-only artifact in `backend/secrets/`.
- **No min-instances** — scale-to-zero keeps cost at $0; the cold start is
  acceptable for a student tool. Revisit only if demo latency matters.
- **No custom domain / no VPC / no load balancer** — the default
  `*.run.app` HTTPS URL is all the extension needs.
