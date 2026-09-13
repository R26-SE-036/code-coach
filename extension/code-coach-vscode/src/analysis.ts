/**
 * The client half of the analysis spine: editor text -> backend -> underlines.
 *
 * This is the VS Code mirror of the backend's analyzer.py. It takes the Java in
 * the active editor, sends it to POST /api/v1/code-coach/analyze, and renders
 * the diagnostics that come back as squiggly underlines, decorations, and hints.
 *
 * The full round trip (traced in Session 2):
 *   scheduleAutoAnalysis()  (debounce 900ms; also called from extension.ts events)
 *     -> runAnalysisForEditor()   (the main runner)
 *          -> ensureAuthenticated / ensureLearningSession   (auth.ts)
 *          -> requestAnalyze()  ->  authorizedRequestJson()  (api.ts)  -> BACKEND
 *          -> applyEditorFeedback()   (turn the JSON into VS Code Diagnostics)
 *
 * Who it depends on:
 *   - api.ts    -> authorizedRequestJson (the actual HTTP call, with auth token)
 *   - auth.ts   -> ensureAuthenticated, ensureLearningSession, trackLearningEvent
 *   - ui/*      -> decorations, status bar, coach panel rendering
 *
 * Note: it never builds URLs or attaches tokens itself — that is api.ts's job.
 * It only decides WHAT to send and WHAT to do with the response.
 */
import * as vscode from "vscode";
import {
  AnalyzeResponse,
  ApiError,
  DiagnosticItem,
  ExtensionState,
} from "./types";
import { DEBOUNCE_DELAY_MS } from "./constants";
import { authorizedRequestJson, clearLearningSession, isEvaluationLoggingEnabled } from "./api";
import { ensureAuthenticated, ensureLearningSession, trackLearningEvent } from "./auth";
import { isSupportedDocument, updateAnalysisStatusBar, formatDuration } from "./ui/statusBar";
import { updateCoachPanel, buildCoachPanelHtml } from "./ui/panelHtml";
import { buildDecorationOptions } from "./ui/decorations";
import { getPortalUrl } from "./browserAuth";

// ── Range & severity helpers ──

// Convert a backend diagnostic's 1-based line/column into a VS Code Range
// (0-based). This is the client-side counterpart to the +1 that parser_utils
// did on the backend: the backend counts from 1, VS Code counts from 0, so the
// two meet here. The Range is what tells VS Code exactly which text to underline.
export function createRangeFromDiagnostic(
  document: vscode.TextDocument,
  diagnostic: DiagnosticItem,
): vscode.Range {
  const lineIndex = Math.max(0, diagnostic.line - 1);
  if (lineIndex >= document.lineCount) {
    return new vscode.Range(0, 0, 0, 0);
  }
  const line = document.lineAt(lineIndex);
  if (line.text.length === 0) {
    return new vscode.Range(lineIndex, 0, lineIndex, 0);
  }
  const startChar = Math.max(0, Math.min(diagnostic.column - 1, line.text.length - 1));
  return new vscode.Range(lineIndex, startChar, lineIndex, line.text.length);
}

function severityFromDiagnostic(diagnostic: DiagnosticItem): vscode.DiagnosticSeverity {
  switch (diagnostic.severity) {
    case "error": return vscode.DiagnosticSeverity.Error;
    case "information": return vscode.DiagnosticSeverity.Information;
    case "hint": return vscode.DiagnosticSeverity.Hint;
    default: return vscode.DiagnosticSeverity.Warning;
  }
}

// ── Clear helpers ──

export function clearTimerForUri(state: ExtensionState, uri: vscode.Uri): void {
  const key = uri.toString();
  const existing = state.debounceTimers.get(key);
  if (existing) {
    clearTimeout(existing);
    state.debounceTimers.delete(key);
  }
}

export function clearEditorFeedback(state: ExtensionState, editor: vscode.TextEditor | undefined): void {
  if (!editor) { return; }
  clearTimerForUri(state, editor.document.uri);
  state.diagnosticCollection.delete(editor.document.uri);
  editor.setDecorations(state.warningDecorationType, []);
  updateAnalysisStatusBar(state, editor);
}

export function clearFeedbackForDocument(
  state: ExtensionState,
  document: vscode.TextDocument,
  options?: { preserveAnalysisSnapshot?: boolean },
): void {
  clearTimerForUri(state, document.uri);
  state.diagnosticCollection.delete(document.uri);
  const uriKey = document.uri.toString();
  state.lastDiagnosticsByUri.delete(uriKey);
  state.activeHintIndexByUri.delete(uriKey);
  if (!options?.preserveAnalysisSnapshot) {
    state.lastAnalysisSnapshotByUri.delete(uriKey);
  }
  const activeEditor = vscode.window.activeTextEditor;
  if (activeEditor && activeEditor.document.uri.toString() === uriKey) {
    activeEditor.setDecorations(state.warningDecorationType, []);
    updateAnalysisStatusBar(state, activeEditor);
  }

  // Refresh CodeLens so lenses disappear when feedback is cleared
  if (state.codeLensProvider) { state.codeLensProvider.refresh(); }
}

// ── Apply editor feedback ──

// THE rendering step: turn the backend's DiagnosticItem[] into what the user
// actually sees. For each item it builds a vscode.Diagnostic (the underline +
// the "message. Hint: ..." on hover) and pushes it into state.diagnosticCollection
// — the collection created once in extension.ts. It also caches the raw items in
// state.lastDiagnosticsByUri so hint navigation and the coach panel can reuse
// them without re-calling the backend.
function applyEditorFeedback(
  state: ExtensionState,
  editor: vscode.TextEditor,
  backendDiagnostics: DiagnosticItem[],
): void {
  const uriKey = editor.document.uri.toString();
  const vscodeDiagnostics: vscode.Diagnostic[] = [];

  for (const item of backendDiagnostics) {
    const range = createRangeFromDiagnostic(editor.document, item);
    const diagnostic = new vscode.Diagnostic(
      range,
      `${item.message} Hint: ${item.hints.concept}`,
      severityFromDiagnostic(item),
    );
    diagnostic.source = "Code Coach";
    diagnostic.code = item.diagnostic_id;
    vscodeDiagnostics.push(diagnostic);
  }

  const decorationOptions = buildDecorationOptions(editor, backendDiagnostics, createRangeFromDiagnostic);

  state.lastDiagnosticsByUri.set(uriKey, backendDiagnostics);
  state.lastSupportedUriKey = uriKey;
  // Preserve the user's position in the hint list across auto re-analysis
  // (only clamp if the new result has fewer diagnostics).
  const previousIndex = state.activeHintIndexByUri.get(uriKey) ?? 0;
  state.activeHintIndexByUri.set(uriKey, Math.min(previousIndex, backendDiagnostics.length - 1));
  state.diagnosticCollection.set(editor.document.uri, vscodeDiagnostics);
  editor.setDecorations(state.warningDecorationType, decorationOptions);
  updateAnalysisStatusBar(state, editor);

  // Refresh CodeLens so inline hint actions appear above problem lines
  if (state.codeLensProvider) { state.codeLensProvider.refresh(); }
}

// ── Focus & hint helpers ──

export function focusDiagnostic(editor: vscode.TextEditor, diagnostic: DiagnosticItem): vscode.Range {
  const range = createRangeFromDiagnostic(editor.document, diagnostic);
  editor.selection = new vscode.Selection(range.start, range.start);
  editor.revealRange(range, vscode.TextEditorRevealType.InCenterIfOutsideViewport);
  return range;
}

function hintTextForLevel(diagnostic: DiagnosticItem, level: "concept" | "guidance" | "targeted"): string {
  switch (level) {
    case "guidance": return diagnostic.hints.guidance;
    case "targeted": return diagnostic.hints.targeted;
    default: return diagnostic.hints.concept;
  }
}

// Show one hint (concept/guidance/targeted) for the diagnostic at `index`, move
// the cursor to it, and refresh the coach panel. Crucially, it also reports the
// interaction to the backend via trackLearningEvent (auth.ts): every hint the
// student opens becomes a learning event, which is how the downstream Study
// Guider later detects hint-dependence and repeated struggle.
async function showHintAtIndex(
  state: ExtensionState,
  editor: vscode.TextEditor,
  diagnostics: DiagnosticItem[],
  index: number,
  options: { level: "concept" | "guidance" | "targeted"; navigationDirection?: "next" | "previous"; sourceCommand: string },
): Promise<void> {
  const diagnostic = diagnostics[index];
  if (!diagnostic) { return; }

  const uriKey = editor.document.uri.toString();
  state.activeHintIndexByUri.set(uriKey, index);
  focusDiagnostic(editor, diagnostic);
  updateCoachPanel(state);

  const hintText = hintTextForLevel(diagnostic, options.level);
  const levelLabel = options.level.charAt(0).toUpperCase() + options.level.slice(1);

  // Fire-and-forget: awaiting an info message blocks until the user dismisses
  // it, which used to delay the learning-event tracking below by seconds.
  void vscode.window.showInformationMessage(
    `Code Coach ${levelLabel.toLowerCase()} hint ${index + 1}/${diagnostics.length}: ${hintText}`,
  );

  if (!state.currentLearningSessionId) { return; }

  const occurredAt = new Date().toISOString();

  if (options.navigationDirection) {
    trackLearningEvent(state, {
      learning_session_id: state.currentLearningSessionId,
      event_type: "hint_navigation_used",
      concept_tag: diagnostic.concept_tag,
      occurred_at: occurredAt,
      payload: {
        diagnostic_id: diagnostic.diagnostic_id, error_type: diagnostic.error_type,
        explanation_key: diagnostic.explanation_key, hint_level: options.level,
        direction: options.navigationDirection, shown_index: index + 1,
        total_diagnostics: diagnostics.length, source_command: options.sourceCommand,
      },
    });
  }

  trackLearningEvent(state, {
    learning_session_id: state.currentLearningSessionId,
    event_type: "hint_level_requested",
    concept_tag: diagnostic.concept_tag,
    occurred_at: occurredAt,
    payload: {
      diagnostic_id: diagnostic.diagnostic_id, error_type: diagnostic.error_type,
      explanation_key: diagnostic.explanation_key, hint_level: options.level,
      hint_text: hintText, surface: "info_message", source_command: options.sourceCommand,
    },
  });
}

// ── Output writer ──

function writeAnalysisOutput(state: ExtensionState, result: AnalyzeResponse): void {
  state.outputChannel.clear();
  state.outputChannel.appendLine("=== Code Coach Analysis Result ===");
  state.outputChannel.appendLine(`Status           : ${result.status}`);
  state.outputChannel.appendLine(`Message          : ${result.message}`);
  state.outputChannel.appendLine(`Timestamp        : ${result.timestamp}`);
  state.outputChannel.appendLine(`Analysis time    : ${formatDuration(result.analysis_duration_ms)}`);
  state.outputChannel.appendLine(`Learning session : ${result.learning_session_id ?? "n/a"}`);
  state.outputChannel.appendLine(`User             : ${state.currentUser?.email ?? "n/a"}`);
  state.outputChannel.appendLine(`Detected issues  : ${result.diagnostics.length}`);
  state.outputChannel.appendLine("");

  if (result.diagnostics.length === 0) {
    state.outputChannel.appendLine("No target issues detected.");
    return;
  }

  result.diagnostics.forEach((diagnostic, index) => {
    state.outputChannel.appendLine(`Issue ${index + 1}: ${diagnostic.error_type} (Line ${diagnostic.line}, Column ${diagnostic.column})`);
    state.outputChannel.appendLine(`  Message   : ${diagnostic.message}`);
    state.outputChannel.appendLine(`  Concept   : ${diagnostic.hints.concept}`);
    state.outputChannel.appendLine(`  Guidance  : ${diagnostic.hints.guidance}`);
    state.outputChannel.appendLine(`  Targeted  : ${diagnostic.hints.targeted}`);
    state.outputChannel.appendLine(`  Confidence: ${diagnostic.confidence} | ML: ${diagnostic.ml_probability ?? "n/a"} | Locator: ${diagnostic.locator_confidence ?? "n/a"}`);
    state.outputChannel.appendLine("");
  });
}

// ── Request analyze ──

// The one function that actually calls the analysis endpoint. It assembles the
// POST body {language, code, learning_session_id, enable_logging} and hands it
// to authorizedRequestJson (api.ts), which adds the base URL + Bearer token and
// does the fetch. The <AnalyzeResponse> generic is the client's mirror of the
// backend AnalyzeResponse model (status, timings, diagnostics[]).
async function requestAnalyze(state: ExtensionState, code: string, learningSessionId: string): Promise<AnalyzeResponse> {
  return authorizedRequestJson<AnalyzeResponse>(state, "/api/v1/code-coach/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      language: "java", code, learning_session_id: learningSessionId,
      enable_logging: isEvaluationLoggingEnabled(),
    }),
  });
}

// ── Main analysis runner ──

// THE main runner — the client-side equivalent of backend analyze_code(). Order:
//   1. bail out if the file isn't Java (isSupportedDocument) or is empty,
//   2. make sure the user is signed in (ensureAuthenticated, auth.ts),
//   3. make sure a learning session exists (ensureLearningSession, auth.ts),
//   4. requestAnalyze() -> backend,   (with a retry if the session 404/409'd),
//   5. applyEditorFeedback() to render, or clear feedback if nothing was found.
// The `options` flag distinguishes manual runs (showPopup: progress + popups)
// from the silent auto-analysis triggered by typing.
export async function runAnalysisForEditor(
  state: ExtensionState,
  editor: vscode.TextEditor,
  options: { showPopup: boolean; showOutput: boolean },
): Promise<void> {
  const document = editor.document;

  if (!isSupportedDocument(document)) {
    clearFeedbackForDocument(state, document);
    return;
  }

  if (!(await ensureAuthenticated(state, options.showPopup))) {
    clearFeedbackForDocument(state, document);
    return;
  }

  state.lastSupportedUriKey = document.uri.toString();
  const code = document.getText();
  const documentVersion = document.version;

  if (!code.trim()) {
    clearFeedbackForDocument(state, document);
    if (options.showPopup) { vscode.window.showWarningMessage("The current file is empty."); }
    if (options.showOutput) { state.outputChannel.show(true); state.outputChannel.appendLine("The current file is empty."); }
    return;
  }

  const doAnalysis = async (
    progress?: vscode.Progress<{ message?: string; increment?: number }>,
  ) => {
    try {
      state.activeAnalysisUriKey = document.uri.toString();
      updateAnalysisStatusBar(state, editor);

      progress?.report({ message: "Initializing session…", increment: 10 });

      let learningSessionId = await ensureLearningSession(state);
      if (!learningSessionId) { throw new Error("Unable to start a learning session."); }

      progress?.report({ message: "Analyzing code…", increment: 30 });

      let result: AnalyzeResponse;

      try {
        result = await requestAnalyze(state, code, learningSessionId);
      } catch (error) {
        if (error instanceof ApiError && (error.statusCode === 404 || error.statusCode === 409)) {
          await clearLearningSession(state);
          learningSessionId = await ensureLearningSession(state);
          if (!learningSessionId) { throw error; }
          result = await requestAnalyze(state, code, learningSessionId);
        } else {
          throw error;
        }
      }

      progress?.report({ message: "Processing results…", increment: 40 });

      state.lastAnalysisSnapshotByUri.set(document.uri.toString(), {
        diagnosticsCount: result.diagnostics.length,
        analysisDurationMs: result.analysis_duration_ms,
        analyzedAt: result.timestamp,
        firstMessage: result.diagnostics[0]?.message,
        firstLine: result.diagnostics[0]?.line,
        learningSessionId: result.learning_session_id ?? learningSessionId,
        documentVersion,
      });

      if (options.showOutput) { writeAnalysisOutput(state, result); state.outputChannel.show(true); }

      if (result.diagnostics.length === 0) {
        clearFeedbackForDocument(state, document, { preserveAnalysisSnapshot: true });
        progress?.report({ message: "No issues found ✓", increment: 20 });
        if (options.showPopup) {
          void vscode.window.showInformationMessage(
            "Code Coach did not detect any of the current target issues in this file.",
            "Open Output", "Open Coach Panel",
          ).then((action) => {
            if (action === "Open Output") { state.outputChannel.show(true); }
            else if (action === "Open Coach Panel") { openCoachPanelFromState(state); }
          });
        }
        return;
      }

      applyEditorFeedback(state, editor, result.diagnostics);

      progress?.report({ message: `Found ${result.diagnostics.length} issue(s)`, increment: 20 });

      if (options.showPopup) {
        const first = result.diagnostics[0];
        trackLearningEvent(state, {
          learning_session_id: result.learning_session_id ?? learningSessionId,
          event_type: "hint_shown", concept_tag: first.concept_tag,
          occurred_at: new Date().toISOString(),
          payload: {
            diagnostic_id: first.diagnostic_id, error_type: first.error_type,
            explanation_key: first.explanation_key, hint_level: "concept",
            hint_text: first.hints.concept, surface: "warning_popup", trigger: "manual_analysis_results",
          },
        });

        void vscode.window.showWarningMessage(
          `Code Coach found ${result.diagnostics.length} issue(s). First issue on line ${first.line}: ${first.message}`,
          "Go to First Issue", "Show Guidance Hint", "Open Coach Panel", "Open Output",
        ).then((action) => {
          if (action === "Go to First Issue") { focusDiagnostic(editor, first); }
          else if (action === "Show Guidance Hint") { void showHintAtIndex(state, editor, result.diagnostics, 0, { level: "guidance", sourceCommand: "analysis_popup" }); }
          else if (action === "Open Coach Panel") { openCoachPanelFromState(state); }
          else if (action === "Open Output") { state.outputChannel.show(true); }
        });
      }
    } catch (error) {
      clearFeedbackForDocument(state, document);
      const message = error instanceof Error ? error.message : "Unknown error occurred.";
      if (options.showPopup) { vscode.window.showErrorMessage(`Code Coach error: ${message}`); }
      console.error("Code Coach analyze error:", error);
    } finally {
      if (state.activeAnalysisUriKey === document.uri.toString()) { state.activeAnalysisUriKey = undefined; }
      updateAnalysisStatusBar(state, editor);
    }
  };

  // Show progress notification for manual analysis, run silently for auto-analysis
  if (options.showPopup) {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "Code Coach",
        cancellable: false,
      },
      async (progress) => { await doAnalysis(progress); },
    );
  } else {
    await doAnalysis();
  }
}

// ── Auto analysis ──
// The debounced entry point called by extension.ts on every keystroke / editor
// switch. Instead of analyzing immediately, it (re)starts a 900ms timer per
// document (DEBOUNCE_DELAY_MS, from constants.ts); only when typing pauses does
// the timer fire runAnalysisForEditor() in silent mode. Clearing the previous
// timer on each call is what collapses a burst of keystrokes into one request.
export function scheduleAutoAnalysis(state: ExtensionState, editor: vscode.TextEditor | undefined): void {
  if (!editor) { return; }
  const document = editor.document;
  if (!isSupportedDocument(document)) { clearFeedbackForDocument(state, document); return; }
  state.lastSupportedUriKey = document.uri.toString();

  // FAST PATH: switching back to a tab whose text has not changed since its
  // last analysis. The results are already known — reapply the cached
  // decorations (they are per-editor and vanish on tab switch) and skip the
  // debounce + backend round trip entirely. document.version bumps on every
  // edit, so any real change still goes through full analysis below.
  const uriKey = document.uri.toString();
  const snapshot = state.lastAnalysisSnapshotByUri.get(uriKey);
  if (snapshot?.documentVersion === document.version) {
    const cached = state.lastDiagnosticsByUri.get(uriKey);
    if (cached && cached.length > 0) {
      editor.setDecorations(
        state.warningDecorationType,
        buildDecorationOptions(editor, cached, createRangeFromDiagnostic),
      );
    }
    updateAnalysisStatusBar(state, editor);
    return;
  }

  clearTimerForUri(state, document.uri);
  const timer = setTimeout(() => {
    void runAnalysisForEditor(state, editor, { showPopup: false, showOutput: false });
    state.debounceTimers.delete(document.uri.toString());
  }, DEBOUNCE_DELAY_MS);
  state.debounceTimers.set(document.uri.toString(), timer);
}

// ── Hint navigation ──

export function showHintForActiveEditor(state: ExtensionState, direction: 1 | -1): void {
  const editor = vscode.window.activeTextEditor;
  if (!editor || !isSupportedDocument(editor.document)) {
    vscode.window.showInformationMessage("Code Coach: Open a Java file first.");
    return;
  }
  const uriKey = editor.document.uri.toString();
  const diagnostics = state.lastDiagnosticsByUri.get(uriKey) ?? [];
  if (diagnostics.length === 0) {
    vscode.window.showInformationMessage("Code Coach: No active hints.");
    return;
  }
  const currentIndex = state.activeHintIndexByUri.get(uriKey) ?? 0;
  const nextIndex = (currentIndex + direction + diagnostics.length) % diagnostics.length;
  void showHintAtIndex(state, editor, diagnostics, nextIndex, {
    level: "guidance",
    navigationDirection: direction === 1 ? "next" : "previous",
    sourceCommand: direction === 1 ? "next_hint" : "previous_hint",
  });
}

/**
 * Resolve which file panel actions should operate on. When a webview button
 * is clicked the webview takes focus and activeTextEditor is often undefined,
 * so fall back to the last supported file the user worked in.
 */
export function resolvePanelUriKey(state: ExtensionState): string | undefined {
  const editor = vscode.window.activeTextEditor;
  if (editor && isSupportedDocument(editor.document)) {
    return editor.document.uri.toString();
  }
  return state.lastSupportedUriKey;
}

function findVisibleEditorForUri(uriKey: string): vscode.TextEditor | undefined {
  return vscode.window.visibleTextEditors.find(
    (editor) => editor.document.uri.toString() === uriKey,
  );
}

/** Set the active hint index, sync the editor cursor to it, refresh the panel. */
function setPanelHintIndex(state: ExtensionState, uriKey: string, index: number): void {
  const diagnostics = state.lastDiagnosticsByUri.get(uriKey) ?? [];
  if (diagnostics.length === 0) { return; }
  const bounded = Math.max(0, Math.min(index, diagnostics.length - 1));
  state.activeHintIndexByUri.set(uriKey, bounded);

  // Keep the code and the panel in sync: reveal the selected issue in the
  // editor (without stealing focus from the panel the user is clicking in).
  const editor = findVisibleEditorForUri(uriKey);
  if (editor) { focusDiagnostic(editor, diagnostics[bounded]); }

  updateCoachPanel(state);

  if (state.currentLearningSessionId) {
    const diagnostic = diagnostics[bounded];
    trackLearningEvent(state, {
      learning_session_id: state.currentLearningSessionId,
      event_type: "hint_navigation_used",
      concept_tag: diagnostic.concept_tag,
      occurred_at: new Date().toISOString(),
      payload: {
        diagnostic_id: diagnostic.diagnostic_id, error_type: diagnostic.error_type,
        explanation_key: diagnostic.explanation_key, hint_level: "concept",
        direction: "panel_select", shown_index: bounded + 1,
        total_diagnostics: diagnostics.length, source_command: "coach_panel",
      },
    });
  }
}

/**
 * Silent hint navigation for the panel/sidebar buttons.
 * Updates the active index and refreshes the panel without showing a popup.
 */
export function navigatePanelHint(state: ExtensionState, direction: 1 | -1): void {
  const uriKey = resolvePanelUriKey(state);
  if (!uriKey) { return; }
  const diagnostics = state.lastDiagnosticsByUri.get(uriKey) ?? [];
  if (diagnostics.length === 0) { return; }
  const currentIndex = state.activeHintIndexByUri.get(uriKey) ?? 0;
  const nextIndex = (currentIndex + direction + diagnostics.length) % diagnostics.length;
  setPanelHintIndex(state, uriKey, nextIndex);
}

/** Jump directly to issue `index` (issue list rows / dot indicators). */
export function selectPanelHint(state: ExtensionState, index: number): void {
  const uriKey = resolvePanelUriKey(state);
  if (!uriKey) { return; }
  setPanelHintIndex(state, uriKey, index);
}

/** Reveal the active diagnostic's line in the editor ("Jump to line" button). */
export function gotoActiveDiagnostic(state: ExtensionState): void {
  const uriKey = resolvePanelUriKey(state);
  if (!uriKey) { return; }
  const diagnostics = state.lastDiagnosticsByUri.get(uriKey) ?? [];
  if (diagnostics.length === 0) { return; }
  const index = Math.min(state.activeHintIndexByUri.get(uriKey) ?? 0, diagnostics.length - 1);
  const editor = findVisibleEditorForUri(uriKey);
  if (editor) {
    focusDiagnostic(editor, diagnostics[index]);
  } else {
    // File not visible (user closed the split) — reopen it at the issue.
    void vscode.window.showTextDocument(vscode.Uri.parse(uriKey), { preview: false })
      .then((opened) => { focusDiagnostic(opened, diagnostics[index]); });
  }
}

/**
 * Report the diagnostic as a false positive. The event lands in
 * learningEvents (event_type: diagnostic_disputed) — the labeled data that
 * measures the detector's real false-positive rate and feeds retraining.
 */
export function reportFalsePositive(
  state: ExtensionState,
  diagnostic: DiagnosticItem,
  surface: "coach_panel" | "code_action",
): void {
  if (state.disputedDiagnosticIds.has(diagnostic.diagnostic_id)) {
    void vscode.window.showInformationMessage(
      "Code Coach: already recorded — thanks again.",
    );
    return;
  }
  state.disputedDiagnosticIds.add(diagnostic.diagnostic_id);

  if (state.currentLearningSessionId) {
    trackLearningEvent(state, {
      learning_session_id: state.currentLearningSessionId,
      event_type: "diagnostic_disputed",
      concept_tag: diagnostic.concept_tag,
      occurred_at: new Date().toISOString(),
      payload: {
        diagnostic_id: diagnostic.diagnostic_id, error_type: diagnostic.error_type,
        explanation_key: diagnostic.explanation_key, line: diagnostic.line,
        detection_engine: diagnostic.detection_engine,
        ml_probability: diagnostic.ml_probability,
        dispute_reason: "false_positive", surface,
      },
    });
  }

  void vscode.window.showInformationMessage(
    "Code Coach: thanks — your report helps improve detection accuracy.",
  );
  updateCoachPanel(state);
}

function disputeActiveDiagnostic(state: ExtensionState): void {
  const uriKey = resolvePanelUriKey(state);
  if (!uriKey) { return; }
  const diagnostics = state.lastDiagnosticsByUri.get(uriKey) ?? [];
  if (diagnostics.length === 0) { return; }
  const index = Math.min(state.activeHintIndexByUri.get(uriKey) ?? 0, diagnostics.length - 1);
  reportFalsePositive(state, diagnostics[index], "coach_panel");
}

/**
 * ONE message handler shared by the coach panel and the sidebar webviews, so
 * the two surfaces can never drift apart in what their buttons do.
 */
/**
 * Open the web dashboard on the concept the student is currently stuck on.
 *
 * This is the second half of FR-09 - "an IDE summary card that navigates to a
 * detailed web dashboard for the full lesson". The card existed and the
 * dashboard existed; nothing joined them. `portalUrl` was configured and read
 * in exactly one place, the loopback sign-in flow, so the setting looked like
 * it powered this and did not.
 *
 * The concept tag travels as a query parameter rather than a trigger id.
 * The extension does not have a trigger id: Code Coach raises triggers on its
 * own schedule, from repeat counts the editor never sees, so a diagnostic on
 * screen may have no trigger behind it yet. Sending the concept lets the
 * Study page highlight the matching lesson when one exists and simply list
 * everything when it does not - which degrades honestly either way.
 */
export function openStudyDashboard(state: ExtensionState): void {
  const uriKey = resolvePanelUriKey(state);
  const diagnostics = uriKey ? state.lastDiagnosticsByUri.get(uriKey) ?? [] : [];

  let conceptTag: string | undefined;
  if (diagnostics.length > 0) {
    const index = Math.min(
      state.activeHintIndexByUri.get(uriKey as string) ?? 0,
      diagnostics.length - 1,
    );
    conceptTag = diagnostics[index]?.concept_tag;
  }

  const target = new URL("/study", `${getPortalUrl()}/`);
  if (conceptTag) {
    target.searchParams.set("concept", conceptTag);
  }

  state.outputChannel.appendLine(`Opening study dashboard: ${target.toString()}`);
  void vscode.env.openExternal(vscode.Uri.parse(target.toString()));
}

export function handleCoachPanelMessage(
  state: ExtensionState,
  message: { command?: string; index?: number },
): void {
  switch (message.command) {
    case "signIn":
      void vscode.commands.executeCommand("code-coach-vscode.signIn");
      break;
    case "createAccount":
      void vscode.commands.executeCommand("code-coach-vscode.createAccount");
      break;
    case "signOut":
      void vscode.commands.executeCommand("code-coach-vscode.signOut");
      break;
    case "analyze":
      void vscode.commands.executeCommand("code-coach-vscode.analyzeCurrentFile");
      break;
    case "panelPrevious":
      navigatePanelHint(state, -1);
      break;
    case "panelNext":
      navigatePanelHint(state, 1);
      break;
    case "panelSelect":
      if (typeof message.index === "number" && Number.isFinite(message.index)) {
        selectPanelHint(state, message.index);
      }
      break;
    case "panelGoto":
      gotoActiveDiagnostic(state);
      break;
    case "panelDispute":
      disputeActiveDiagnostic(state);
      break;
    case "openStudy":
      openStudyDashboard(state);
      break;
    case "openOutput":
      state.outputChannel.show(true);
      break;
    default:
      break;
  }
}

// ── Coach panel opener (used internally) ──

export function openCoachPanelFromState(state: ExtensionState): void {
  // Delegated to openCoachPanel in extension.ts to avoid circular dep on panel creation logic
  void vscode.commands.executeCommand("code-coach-vscode.openCoachPanel");
}
