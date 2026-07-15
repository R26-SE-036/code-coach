# Code Coach — Development Log (AI-Assisted Phase, July 4–12, 2026)

> Everything added to Code Coach since the AI-assisted development phase began,
> grouped by area, each item tied to its commit. The baseline before this
> phase (March–May): the VS Code extension, the FastAPI backend with custom
> auth, 3 ML-gated error types, and the initial hand-authored dataset.
> Use this log for progress reports, the team meeting, and the viva demo plan.

## Headline results produced in this phase (all measured, not estimated)

| Result | Value |
|---|---|
| Error types detected | 3 → **15** (10 rule-only + 5 ML-gated) |
| Test F1 on human-written holdout | **0.973 – 1.0** (all 5 gated targets) |
| Training corpus | **2,010 verified synthetic files** (+ 210 manual as held-out test) |
| Gate distinguishes intent | real missing break **0.996** vs intentional fall-through **0.024** |
| Out-of-distribution failure | **fixed**: big-file probability 0.033 → **0.999** |
| Full analysis latency | **3.9 ms** (behind a 900 ms debounce) |
| Data persistence | in-memory (lost on restart) → **Cloud Firestore** |
| Container image | **527 MB**, verified end-to-end against real Firestore |

## 1. Error Detection & Machine Learning

- **Single error catalog** — consolidated scattered error-type registries into
  one `ERROR_CATALOG` that owns each type's detection mode, locator, model
  file, and threshold (`6db9e536`)
- **15 error types** — expanded detection from 3 to 15 beginner Java error
  types with AST locators (`57fc7ef6`) + hint content for the 11 new concept
  tags (`3d7f1278`)
- **Per-target threshold calibration** — margin-midpoint rule with best-F1
  sweep fallback; model selection by validation F1, ties broken by latency
  (`a48f5103`)
- **Two new ML-gated types** — MISSING_BREAK_IN_SWITCH and
  WHILE_VARIABLE_NOT_UPDATED promoted from rule-only: 16 new switch/while
  features, pipeline extended to 5 binary targets (`a8d4a019`)
- **All 5 targets retrained & promoted** — plus one structural feature
  (`loop_condition_leq_bare_length_count`) that reopened the off-by-one
  margin from 0.0 to 0.94 after intentional negatives exposed crude text
  features; feature vector now 52 (`53772422`)
- **Gate scoring hardening** — feature frame built once per request
  (5.2 → 3.2 ms), positive class read from `model.classes_`, ML failures
  logged instead of silently swallowed (`8885c6af`)

## 2. Training Data & Pipeline

- **Snippet index automation** — `build_snippet_index.py` regenerates the
  dataset index from the folder structure, byte-identical to the manual CSV
  (`8c781596`), later multi-root with provenance columns (`53772422`)
- **Verified synthetic data generator** — `generate_snippets.py`: minimal
  pairs (bug at random position in 1–9-method classes), intentional
  negatives, distractor library; every file auto-verified at generation
  (must parse + fire exactly the planted locators); deterministic from a
  seed (`53772422`)
- **Manual-holdout split** — when synthetic data exists, all 210 hand-written
  snippets go to the test set, so reported F1 measures synthetic-to-human
  transfer (`53772422`)
- **CI** — backend test suite runs on every PR and push (`437a2979`)

## 3. Backend Platform

- **Cloud Firestore persistence** — `FirestoreStorage` adapter behind the
  existing storage seam (natural keys as document IDs, no composite indexes);
  fixed accounts dying on every backend restart; ADC support for keyless
  auth on Google Cloud (`0c3e545e`, `65e72726`)
- **CORS middleware** — configurable allow-list; required for teammates'
  browser frontends (`ce390dd1`)
- **Meaningful API URLs** — all current-student reads under
  `/api/v1/students/me/...` (diagnostics, diagnostics/summary,
  struggling-concepts, concept-mastery) (`ce390dd1`)
- **Brute-force protection** — sliding-window rate limiting on
  register/login/refresh (10/min per IP per endpoint, X-Forwarded-For
  aware, HTTP 429 + Retry-After), with dedicated tests (`aa410274`)
- Backend test suite: **30 tests + 15 subtests**, all passing

## 4. VS Code Extension

- **Coach panel hint navigation fixed** — buttons were never rendered and
  webview focus cleared `activeTextEditor`; both root causes fixed
  (`c603e4c9`)
- **Panel professionalized** — nav bar with position + dot indicators,
  all-issues list (click to select, editor follows), ML/locator confidence
  bars, detection-engine badge, jump-to-line, arrow-key navigation,
  analysis metadata footer (`c603e4c9`)
- **UI performance** — webview HTML reassigned only on real change (was:
  full DOM teardown on every editor event); unchanged tab switches reuse
  cached results instead of re-analyzing; hint position preserved across
  auto re-analysis (`c603e4c9`)
- **False-positive feedback loop** — "🚩 Not a real bug?" in panel +
  lightbulb quick action; emits `diagnostic_disputed` learning events =
  labeled false-positive data for evaluation and retraining (`aa410274`)
- **Viva demo programs** — 6 sample Java files covering all 15 error types
  (`cb92b321`, `c0761033`)

## 5. Deployment & Architecture

- **Production Docker image** — python:3.12-slim, 527 MB, secrets excluded,
  PORT-aware; verified in-container against real Firestore
  (register → login → analyze) (`65e72726`)
- **Deployment runbooks** — Cloud Run path (chosen; asia-south1) with team
  checklist incl. Blaze/budget guidance + Render fallback (`65e72726`,
  `22ec1571`)
- **Architecture diagram** — UML deployment/component diagram (PNG + PDF +
  editable Mermaid + regenerable renderer script) showing Marketplace,
  Cloud Run, Firestore, and planned sibling services (`3305cc10`,
  `22ec1571`)
- **Integration contracts for teammates** — per-team endpoint catalog with
  auth/introspection guide, and Pub/Sub event contract v1
  (`remediation.triggered`, `learning-event.created`) (`ce390dd1`)

## 6. Documentation & Research Assets

- **Pipeline annotation** — every analysis module documented with its role
  in the request spine (`26d5a4d5`)
- **Study-guide series (docs 00–10)** — big picture, request journey, AST &
  locators, ML engine, training & calibration, file reference, glossary +
  quiz, promotion runbook, probability deep-dive, candidate-level
  limitation chapter — all with real measured numbers (`3cdee032`,
  `700f22a1`, `74dd86d5`, `d9a791b2`)
- **Backend viva guide** (`871c6a99`)
- **Research paper draft** — IEEE-style, Code-Coach-only, with merge guide
  for the combined Code Guru paper (outside repo:
  `Academic/.../Research_Paper/`)

## Still open (decided, not yet executed)

- Cloud Run deployment (awaiting team decision on Blaze billing)
- VS Code Marketplace publishing (needs the deployed backend URL)
- User study with real students (instrumentation ready, incl. dispute events)
- Candidate-level scoring (documented migration path, ~2–4 days, optional)
