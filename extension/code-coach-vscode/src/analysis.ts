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

// ── Range & severity helpers ──

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
}

// ── Apply editor feedback ──

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
  state.activeHintIndexByUri.set(uriKey, 0);
  state.diagnosticCollection.set(editor.document.uri, vscodeDiagnostics);
  editor.setDecorations(state.warningDecorationType, decorationOptions);
  updateAnalysisStatusBar(state, editor);
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

  await vscode.window.showInformationMessage(
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

  const code = document.getText();

  if (!code.trim()) {
    clearFeedbackForDocument(state, document);
    if (options.showPopup) { vscode.window.showWarningMessage("The current file is empty."); }
    if (options.showOutput) { state.outputChannel.show(true); state.outputChannel.appendLine("The current file is empty."); }
    return;
  }

  try {
    state.activeAnalysisUriKey = document.uri.toString();
    updateAnalysisStatusBar(state, editor);

    let learningSessionId = await ensureLearningSession(state);
    if (!learningSessionId) { throw new Error("Unable to start a learning session."); }

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

    state.lastAnalysisSnapshotByUri.set(document.uri.toString(), {
      diagnosticsCount: result.diagnostics.length,
      analysisDurationMs: result.analysis_duration_ms,
      analyzedAt: result.timestamp,
      firstMessage: result.diagnostics[0]?.message,
      firstLine: result.diagnostics[0]?.line,
      learningSessionId: result.learning_session_id ?? learningSessionId,
    });

    if (options.showOutput) { writeAnalysisOutput(state, result); state.outputChannel.show(true); }

    if (result.diagnostics.length === 0) {
      clearFeedbackForDocument(state, document, { preserveAnalysisSnapshot: true });
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
}

// ── Auto analysis ──

export function scheduleAutoAnalysis(state: ExtensionState, editor: vscode.TextEditor | undefined): void {
  if (!editor) { return; }
  const document = editor.document;
  if (!isSupportedDocument(document)) { clearFeedbackForDocument(state, document); return; }
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

// ── Coach panel opener (used internally) ──

export function openCoachPanelFromState(state: ExtensionState): void {
  // Delegated to openCoachPanel in extension.ts to avoid circular dep on panel creation logic
  void vscode.commands.executeCommand("code-coach-vscode.openCoachPanel");
}
