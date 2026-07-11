# Session 2 — One Request, End to End

> **Goal of this session:** trace a single keystroke through every file and
> function until it becomes a yellow underline. This chain is the SPINE of
> the whole project — everything else is a zoom-in on one of its nodes.

## The full chain (memorize this shape)

```
VS Code (you edit a Java file)
  │  onDidChangeTextDocument fires (extension.ts)
  ▼
scheduleAutoAnalysis()                      analysis.ts
  │  debounce: (re)starts a 900ms timer per document.
  │  Typing again resets the timer — a burst of keystrokes = ONE request.
  ▼
runAnalysisForEditor()                      analysis.ts   ← the main runner
  │  1. isSupportedDocument? (Java only)
  │  2. ensureAuthenticated()              auth.ts  (signed in? silent restore?)
  │  3. ensureLearningSession()            auth.ts  (get-or-create session id)
  ▼
requestAnalyze()                            analysis.ts
  │  builds POST body: { language:"java", code, learning_session_id, enable_logging }
  ▼
authorizedRequestJson()                     api.ts   ← the ONLY file that fetches
  │  reads access token from secret storage, adds "Authorization: Bearer ..."
  │  on 401: refreshAuthSession() once, then retry
  ▼
════════ HTTP: POST http://127.0.0.1:8000/api/v1/code-coach/analyze ════════
  ▼
route handler                               backend/app/api/code_coach.py
  │  validates the JSON into AnalyzeRequest (models.py), checks the token
  ▼
run_analysis() / build_diagnostic_records() backend/app/services/code_coach_service.py
  │  orchestrates: calls the analyzer, persists diagnostics, logs events
  ▼
analyze_code(code)                          backend/app/analysis/analyzer.py
  │  parse → features → ML predictions → per-catalog-entry detection → hints
  │  (Sessions 3–5 zoom into this box)
  ▼
list of Diagnostic objects → AnalyzeResponse JSON travels back up
  ▼
════════ HTTP response ════════
  ▼
runAnalysisForEditor() receives AnalyzeResponse
  ▼
applyEditorFeedback()                       analysis.ts
  │  each backend diagnostic → vscode.Diagnostic (range, message, severity)
  ▼
state.diagnosticCollection.set(...)         (created once in extension.ts via
  │                                          vscode.languages.createDiagnosticCollection)
  ▼
YELLOW UNDERLINES appear. Hovering shows the message + concept hint.
```

## The key ideas at each hop

### Debounce (why 900ms?)
Sending a request on every keystroke would hammer the backend and analyze
half-typed garbage. `scheduleAutoAnalysis` starts a 900ms timer
(`DEBOUNCE_DELAY_MS` in `constants.ts`) and **cancels the previous timer**
each time you type. Only when you pause does the request fire.
**Plain English:** the extension waits until you stop typing for about a
second, then analyzes once.

### The request body
```json
POST /api/v1/code-coach/analyze
{
  "language": "java",
  "code": "<the entire file text>",
  "learning_session_id": "ls_...",
  "enable_logging": false
}
```
The **whole file** is sent, not a diff. `learning_session_id` ties this
analysis to the student's ongoing session so diagnostics are attributed to
them over time.

### Auth on the way out (api.ts)
`analysis.ts` never builds URLs or touches tokens. `api.ts` owns all HTTP:
it prefixes the backend URL, attaches the Bearer access token, and if the
server answers 401 (token expired) it silently trades the refresh token for
a new access token and retries **once** (`allowRefresh=false` on the retry so
a dead session can't loop forever).

### Session-retry on the way in (analysis.ts)
If the backend answers 404/409 for the learning session (stale id), the
runner clears it, calls `ensureLearningSession()` again, and retries the
analysis once. The student never notices.

### The response
```json
{
  "status": "ok", "message": "...", "timestamp": "...",
  "analysis_duration_ms": 42.5,
  "learning_session_id": "ls_...",
  "diagnostics": [
    {
      "diagnostic_id": "cc_ab12cd34ef56",
      "error_type": "WHILE_VARIABLE_NOT_UPDATED",
      "severity": "warning",
      "line": 26, "column": 12,
      "confidence": 0.86,
      "message": "...",
      "code_context": "while (emailsSent < 3) {",
      "concept_tag": "loop_termination",
      "detection_engine": "ast_locator_rule",
      "ml_probability": null,
      "locator_confidence": 0.86,
      "hints": { "concept": "...", "guidance": "...", "targeted": "..." }
    }
  ]
}
```

### Rendering (applyEditorFeedback)
- Backend lines/columns are **1-based**; VS Code is **0-based**. The
  conversion happens in `createRangeFromDiagnostic()`.
- Diagnostics go into `state.diagnosticCollection` → the underline.
- The raw list is also cached in `state.lastDiagnosticsByUri` so hint
  navigation and the coach panel work **without** re-calling the backend.

### Manual vs automatic runs
The same `runAnalysisForEditor` serves both paths, told apart by options:
- **auto** (typing): `{ showPopup: false, showOutput: false }` — silent.
- **manual** (command/button): `{ showPopup: true, showOutput: true }` —
  progress notification, popup with "Go to First Issue", output channel dump.

## ExtensionState — the client's shared spine

One object, created once in `extension.ts` `activate()`, passed by reference
into nearly every function. When `auth.ts` sets `currentUser`, or
`analysis.ts` caches diagnostics, they write into THIS object:

- `currentUser`, `currentLearningSessionId` — who and which session
- `diagnosticCollection`, `warningDecorationType` — the VS Code handles
- `lastDiagnosticsByUri`, `activeHintIndexByUri` — caches per file
- `debounceTimers` — the 900ms timers per document

The backend has **no equivalent** — each HTTP request is stateless; identity
comes from the Bearer token every time. (A good viva point about
client-vs-server state.)

## What you should be able to say out loud

- "A keystroke fires a listener in extension.ts, which debounces 900ms into
  scheduleAutoAnalysis, which calls runAnalysisForEditor."
- "The extension POSTs the whole file to /api/v1/code-coach/analyze via
  authorizedRequestJson in api.ts, which attaches the Bearer token and
  handles 401-refresh."
- "The backend route hands off to the service, which calls
  analyzer.analyze_code — the seam where detection happens."
- "The diagnostics come back as JSON; applyEditorFeedback converts them to
  vscode.Diagnostic objects in a DiagnosticCollection — that's the yellow
  underline."

**Next:** [Session 3](03_ast_and_locators.md) — inside `analyze_code`: how
text becomes a tree and how locators find the exact line.
