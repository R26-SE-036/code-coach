# File & Method Reference

> Quick lookup: what every important file does, and what each function inside
> it is for. Organized bottom-up (foundation first), matching how the data
> flows. Backend first, then the extension.

---

## Backend — `backend/app/analysis/` (the detection pipeline)

### parser_utils.py — text → tree (the foundation)
Nothing here knows about ML, error types, or hints. Only: parse Java, walk
the tree.

| Function | Purpose |
|---|---|
| `parse_java_code_safe(code)` | THE entry point. Parses; returns `ParseResult` (tree, source_bytes, health, crashed). Callers bail if crashed or completeness < 0.35. |
| `parse_java_code(code)` | Bare parse without the safety wrapper (used by tools). |
| `collect_nodes_by_type(root, type)` | Walk the whole tree; return EVERY node of one type (all for-loops, all array accesses...). The workhorse. |
| `find_first_descendant_by_type(node, type)` | Depth-first; stop at the FIRST match ("any assignment inside this condition?"). |
| `get_node_text(node, source_bytes)` | Nodes store byte offsets only; slice the actual source text back out. |
| `node_to_span(node)` | Convert tree-sitter 0-based positions → 1-based editor Span. |
| `inspect_tree_health(root)` | Count ERROR/missing nodes in a half-typed parse → completeness score 0–1. Used to bail out AND to scale confidence. |

### feature_extractor.py — tree → 35 numbers (for the ML)
| Function | Purpose |
|---|---|
| `extract_features(code)` | THE entry point. Parses (independently), merges the four groups below + base counts into ONE flat dict. Keys must stay in sync with the models' training columns. |
| `_extract_general_ast_features` | File shape: class/method/loop/return counts, tree depth, node count. |
| `_extract_for_loop_features` | OFF_BY_ONE signals: `<=` in condition, `.length` in condition, both together, loop body size, array access in body. |
| `_extract_if_features` | INCORRECT_CONDITIONAL signals: assignment inside if-condition, equality ops, boolean literals, `&&`/`\|\|` counts. |
| `_extract_array_access_features` | ARRAY_LENGTH signals: `a[a.length]` counted directly, `.length` in any index, unique arrays touched. |

### ml_engine.py — 35 numbers → "probably present?" (the gate)
| Function | Purpose |
|---|---|
| `MLPrediction` (dataclass) | Returned per ml_gated type: error_type, probability, `predicted_positive` (the gate flag analyzer checks). |
| `_LOADED_MODELS` | Cache: each .joblib loaded from disk once, reused across requests. |
| `_get_model(spec)` | Lazy-load the model file named by the catalog spec from `backend/models/`. |
| `_build_feature_frame(model, feature_dict)` | CRITICAL: reorder features into the exact columns the model was trained on (`feature_names_in_`), missing → 0. |
| `predict_issue_types(feature_dict)` | THE entry point. For each `ml_gated_specs()` entry: `predict_proba` → probability; `>= spec.ml_threshold` → gate. Answers IF, never WHERE. |

### issue_locators.py — tree → exact line/column (the WHERE)
All 15 `locate_*` functions share one template: collect nodes of one type →
reach into field slots → check a pattern (crude text or precise structure) →
`_result(...)` → `_deduplicate(...)`. See Session 3 doc for the full table.

| Shared helper | Purpose |
|---|---|
| `_result(...)` | Build one DetectionResult: line/column from the pinpointing node, hand-set locator_confidence, message, code snippet. |
| `_deduplicate(results)` | Drop repeats keyed on (type, line, column, snippet) — never two underlines on one spot. |
| `_binary_operator(node)` | Read the operator symbol (`==`, `<=`, `/`, `\|\|`, `=`) out of a binary/assignment node. |
| `_unwrap_parentheses(node)` | Treat `((x != 1))` like `x != 1`. |
| `_collect_string_variable_names(root, sb)` | All variables declared as String (locals, params, fields) — for the `==`-on-strings check. |

### error_catalog.py — the single registry (the hub)
| Item | Purpose |
|---|---|
| `ErrorTypeSpec` (frozen dataclass) | One error type: `detection_mode` (`ml_gated`/`rule_only`), `locator` fn, and for ML: `target_column`, `model_file`, `ml_threshold`. |
| `ERROR_CATALOG` (dict) | All 15 entries. Adding error #16 = one entry here + a locator + a JSON hints entry. Thresholds/model files come from the calibration tool. |
| `ml_gated_specs()` / `rule_only_specs()` | Filtered views; ml_engine iterates the first. |
| `validate_catalog()` | Startup check (called from main.py): every entry's model file exists on disk AND has a hints entry in the knowledge base. Fails loudly instead of silently dropping diagnostics. |

### analyzer.py — the conductor
| Function | Purpose |
|---|---|
| `analyze_code(code)` | THE seam between HTTP and detection. parse → bail if unhealthy → extract features → ML predictions → for each catalog entry `_detect_for_spec` → `build_diagnostic` per finding → sort by confidence. |
| `_detect_for_spec(spec, ...)` | The mode switch: ml_gated → locator ONLY if `predicted_positive`; rule_only → locator directly. Stamps the engine label. |
| `_safe_predict_issue_types(...)` | try/except around ml_engine — broken model = no ML diagnostics, never a 500. |
| `_combine_confidence(...)` | ml_gated: 0.8·ml_probability + 0.2·locator_confidence; rule_only: locator alone; then × parse completeness; cap 0.99. |
| `_finalize_finding(...)` | Fill in the pipeline-level fields the locator didn't know (final confidence, engine, ml_probability). |

### hint_engine.py — finding → final Diagnostic (the teaching layer)
| Item | Purpose |
|---|---|
| `ERROR_KNOWLEDGE_BASE` | Loaded once from `knowledge_base/code_coach_errors.json` — THE source of truth for hints, keyed by error_type. |
| `get_error_knowledge(error_type)` | Lookup with a generic fallback (validate_catalog normally prevents the fallback ever firing). |
| `_diagnostic_id_for(finding)` | STABLE id `cc_<sha1[:12]>` hashed from type+line+column+snippet — same bug in same place = same id, enabling repeat-struggle tracking. |
| `build_diagnostic(finding)` | THE entry point: merge detection facts + knowledge-base content (concept_tag, explanation_key, 3-level hints) into the final `Diagnostic` sent to VS Code. |

---

## Backend — around the pipeline

| File | Purpose |
|---|---|
| `backend/app/main.py` | FastAPI app assembly; calls `validate_catalog()` at startup. |
| `backend/app/api/code_coach.py` | The `/api/v1/code-coach/analyze` route: validates `AnalyzeRequest`, auth-checks, hands off to the service. |
| `backend/app/services/code_coach_service.py` | Orchestration between route and analyzer (`run_analysis`, `build_diagnostic_records`): calls `analyze_code`, persists diagnostic records, logs learning events. |
| `backend/app/models.py` | ALL shared shapes: `AnalyzeRequest/Response`, `Diagnostic`, `HintSet`, `DetectionResult`, `ParseResult/ParseHealth/Span`, plus auth/session/event/dashboard models. The API contract lives here. |
| `backend/app/dev_tools/train_baselines.py` | OFFLINE: trains LR/RF/SVM per target on `data/ml/splits/train_v1.csv`, saves `.joblib` models + `baseline_metrics_v1.csv`. |
| `backend/app/dev_tools/calibrate_thresholds.py` | OFFLINE: picks best model (val F1, ties → latency) and threshold (margin midpoint, or F1 sweep on overlap); writes `calibration_v1.json`; human copies numbers into the catalog. |
| `backend/models/*.joblib` | The 9 trained models (3 types × 3 targets); catalog names which 3 are live. |
| `knowledge_base/code_coach_errors.json` | Hints (concept/guidance/targeted) per error type. |
| `knowledge_base/study_guider_lessons.json`, `gamification_catalog.json`, `collaboration_prompts.json` | Per-CONCEPT content for the downstream services (covered by `test_concept_content_coverage.py`). |
| `data/ml/splits/{train,val,test}_v1.csv` | The labeled feature rows: 147 / 28 / 35. |

---

## Extension — `extension/code-coach-vscode/src/`

### extension.ts — entry point / wiring (no logic of its own)
`activate()` does three things: builds the ONE shared `ExtensionState`
object; registers commands (signIn, analyzeCurrentFile, next/previousHint,
openCoachPanel...) pointing at auth.ts/analysis.ts; registers the event
listeners (`onDidChangeTextDocument`, `onDidChangeActiveTextEditor`) that
funnel into `scheduleAutoAnalysis`. Also creates `diagnosticCollection` and
the decoration type — the actual underline machinery.

### analysis.ts — the client half of the spine
| Function | Purpose |
|---|---|
| `scheduleAutoAnalysis(state, editor)` | The 900ms debounce (`DEBOUNCE_DELAY_MS`). Resets per keystroke; fires `runAnalysisForEditor` silently. |
| `runAnalysisForEditor(state, editor, opts)` | THE runner: supported doc? → ensureAuthenticated → ensureLearningSession → requestAnalyze (with one 404/409 session retry) → applyEditorFeedback or clear. `opts` distinguishes manual (popups/progress) from auto (silent). |
| `requestAnalyze(state, code, sessionId)` | Builds the POST body for `/api/v1/code-coach/analyze`; delegates HTTP to api.ts. |
| `applyEditorFeedback(state, editor, diags)` | Backend diagnostics → `vscode.Diagnostic[]` → diagnosticCollection (underlines) + decorations; caches raw list for hint navigation. |
| `createRangeFromDiagnostic(doc, diag)` | 1-based backend line/col → 0-based VS Code Range (clamped to the line). |
| `showHintAtIndex / showHintForActiveEditor / navigatePanelHint` | Hint display + cycling; every hint shown/navigated is reported via `trackLearningEvent`. |
| `writeAnalysisOutput(state, result)` | Dumps the full result (incl. ml_probability / locator_confidence) to the Output channel. |
| `clearTimerForUri / clearEditorFeedback / clearFeedbackForDocument` | Cancel timers, remove underlines/decorations/caches. |

### api.ts — the ONLY file that talks HTTP / stores tokens
| Function | Purpose |
|---|---|
| `getBackendUrl()` | From settings (`codeCoach.backendUrl`, default `http://127.0.0.1:8000`). |
| `requestJson(path, init)` | Base fetch → typed JSON or `ApiError(status)`. Used directly only pre-token (login/register/refresh). |
| `authorizedRequestJson(state, path, init)` | THE workhorse: attach `Authorization: Bearer <access token>`; on 401 → `refreshAuthSession()` once → retry with `allowRefresh=false`. |
| `refreshAuthSession(state)` | Trade the stored refresh token for new tokens; on failure wipe auth state. |
| `storeAuthResponse(state, payload, opts)` | The ONLY writer of tokens (VS Code secret storage) + currentUser. Lives here (not auth.ts) to avoid an import cycle. |
| `clearStoredAuthState(state)` | Full sign-out reset: tokens, user, caches, underlines. |
| `clearLearningSession(state)` | Drop the cached learning-session id. |

### auth.ts — identity workflows + learning sessions + telemetry
| Function | Purpose |
|---|---|
| `createAccount / signIn` | Input-box prompts → POST `/auth/register` / `/auth/login` → `storeAuthResponse` → kick `scheduleAutoAnalysis`. |
| `signOut` | POST `/auth/logout`, then `clearStoredAuthState` regardless. |
| `restoreAuthSession(state)` | Silent startup re-login: tokens in storage? → GET `/auth/me` → rehydrate currentUser. |
| `ensureAuthenticated(state, showPrompt)` | The gate before every analyze: fast path → silent restore → (only if showPrompt) Sign In / Create Account dialog. Auto-analysis passes false, so typing never nags. |
| `ensureLearningSession(state)` | Get-or-create the learning session id (POST `/api/v1/learning-sessions`); cached on state + workspaceState. |
| `trackLearningEvent(state, event)` | Fire-and-forget POST `/api/v1/events` (hint shown/navigated...); errors swallowed — telemetry must never break analysis. |

### Supporting
| File | Purpose |
|---|---|
| `types.ts` | Client mirrors of the backend JSON shapes + `ExtensionState` + `ApiError`. |
| `constants.ts` | `DEBOUNCE_DELAY_MS` (900), secret-storage keys, client name. |
| `ui/statusBar.ts`, `ui/decorations.ts`, `ui/panelHtml.ts`, `ui/sidebarProvider.ts`, `ui/codeLensProvider.ts`, `ui/codeActionProvider.ts` | Status bars, underline styling, coach panel HTML, sidebar webview, per-line CodeLens hints, quick-action hooks. |
| `src/sample-java/` | The six viva demo programs + `DEMO_GUIDE.md` (all 15 error types planted and verified). |
