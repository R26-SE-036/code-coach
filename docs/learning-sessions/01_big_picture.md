# Session 1 — The Big Picture

> **Goal of this session:** be able to say what Code Coach *is*, what the two
> halves do, and what the two detection modes mean — without opening any code.

## What Code Coach is, in one paragraph

Code Coach is a learning tool for beginner Java programmers. It watches the
Java file a student is editing in VS Code, sends the code to a backend server,
and the server looks for **logical errors** — code that compiles and runs but
does the wrong thing (infinite loops, off-by-one indexing, comparing strings
with `==`). Each error comes back with three levels of hints (concept →
guidance → targeted) so the student is *taught*, not just corrected. The
system also records what the student struggles with, so downstream services
(Study Guider, Gamification, Collaboration) can recommend lessons, quizzes,
and pair-programming prompts.

**Plain English:** it's a spell-checker for *logic* instead of spelling, that
also remembers what kind of mistakes you keep making.

## The two halves (client-server architecture)

```
┌──────────────────────────┐        HTTP + JSON        ┌──────────────────────────┐
│  VS Code EXTENSION       │  ───────────────────────► │  FastAPI BACKEND         │
│  (TypeScript)            │   POST /api/v1/...        │  (Python)                │
│                          │  ◄───────────────────────  │                          │
│  - watches your typing   │      JSON responses       │  - parses the Java       │
│  - sends code to backend │                           │  - detects the errors    │
│  - paints underlines     │                           │  - builds the hints      │
│  - shows hints/panel     │                           │  - stores users/progress │
└──────────────────────────┘                           └──────────────────────────┘
   extension/code-coach-vscode/src/                        backend/app/
```

Why split it? The extension can only do lightweight UI work; the heavy
machinery (a real parser, trained ML models, a database) lives on the server.
They speak plain HTTP with JSON bodies — the same way any web app talks to
its API. Neither half knows the other's internals; they only agree on the
JSON shapes (defined in `backend/app/models.py` and mirrored in
`extension/.../src/types.ts`).

## The backend's three jobs

1. **Analyze code** — the pipeline in `backend/app/analysis/` (Sessions 2–5
   are all about this).
2. **Manage identity** — accounts, login, JWT tokens, learning sessions
   (`/api/v1/auth/*`, `/api/v1/learning-sessions`).
3. **Track learning signals** — every diagnostic and every hint interaction
   is stored as events, so repeated struggle on a concept can be detected and
   sent to the Study Guider / Gamification / Collaboration services.

## The 15 error types and the two detection modes

All 15 error types live in ONE registry: `ERROR_CATALOG` in
[backend/app/analysis/error_catalog.py](../../backend/app/analysis/error_catalog.py).
Each entry says *how* that type is detected — its `detection_mode`:

### rule_only (12 types)
A deterministic AST pattern-matcher (a "locator") runs directly on the parse
tree. No machine learning involved. If the pattern is there, it's flagged.
Works because these bugs have unmistakable shapes: `x = x` is always
self-assignment, `x / 0` is always division by zero.

### ml_gated (3 types)
Two steps, in order:
1. A trained ML model looks at file-level features and asks: *"does this file
   probably contain this kind of bug?"* → a probability.
2. **Only if** the probability clears that type's calibrated threshold does
   the AST locator run to find the exact line.

The ML is a **gate** in front of the locator, not a replacement for it.
These three types (off-by-one loop boundary, incorrect conditional operator,
array length index misuse) got the gate because their text patterns are
ambiguous enough that the locator alone over-fires (proved in Session 3).

| Mode | Types | Engine label in diagnostics |
|------|-------|------------------------------|
| ml_gated | OFF_BY_ONE_LOOP_BOUNDARY, INCORRECT_CONDITIONAL_OPERATOR, ARRAY_LENGTH_INDEX_MISUSE | `ml_gated_ast_locator` |
| rule_only | the other 12 | `ast_locator_rule` |

## The three-level hint system

Every diagnostic ships with a `HintSet` from
`knowledge_base/code_coach_errors.json`:

- **concept** — the gentlest nudge: what idea to think about.
- **guidance** — a stronger push: what to check in this code.
- **targeted** — nearly the answer: what exactly is wrong here.

Escalating hints exist because the goal is learning: give the student a
chance to find it themselves before spelling it out. Hint usage is itself
tracked — a student who always jumps to "targeted" is flagged as
hint-dependent for the Study Guider.

## What you should be able to say out loud

- "Code Coach is a VS Code extension talking to a FastAPI backend over
  HTTP/JSON; the extension is the face, the backend is the brain."
- "It detects 15 logical error types, all registered in one catalog; 12 are
  pure AST rules, 3 are ML-gated — the model decides IF the bug is likely in
  the file, the AST locator decides WHERE."
- "Every finding carries three escalating hints, and every interaction is
  logged as a learning signal for the downstream services."

**Next:** [Session 2](02_request_journey.md) — follow one keystroke through
every file until it becomes a yellow underline.
