/**
 * Help the student asks for: an explanation written for their own code, a
 * similar worked example, a plain-words reading of a compiler error, the free
 * course unit for the mistake, and muting a kind of finding.
 *
 * None of this runs on a keystroke - each is a button. The backend writes the
 * explanations with a language model under a daily allowance and falls back to
 * the hint templates, so a button always answers. Results are kept in
 * state.assistByKey so the panel can show them while analysis re-runs.
 *
 * Asking for an explanation is recorded as an `explanation_requested` learning
 * event. The learning signals (hint dependency, struggle) count only the hint
 * event types, so this adds research data without changing anyone's scores.
 */
import * as vscode from "vscode";
import { authorizedRequestJson } from "./api";
import { trackLearningEvent } from "./auth";
import { getPortalUrl } from "./browserAuth";
import { compilerKey, exampleKey, explainKey, mutedErrorTypes, MUTED_SETTING } from "./assistState";
import { titleFor } from "./labels";
import {
  CompilerProblem,
  DiagnosticItem,
  ExplanationResponse,
  ExtensionState,
  SimilarExampleResponse,
} from "./types";
import { updateCoachPanel } from "./ui/panelHtml";

function documentFor(state: ExtensionState): vscode.TextDocument | undefined {
  const editor = vscode.window.activeTextEditor;
  if (editor && editor.document.languageId === "java") { return editor.document; }
  const key = state.lastSupportedUriKey;
  return vscode.workspace.textDocuments.find((doc) => doc.uri.toString() === key);
}

function failureText(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (/fetch failed|ECONNREFUSED|ENOTFOUND|network/i.test(message)) {
    return "Code Coach could not reach its server. Check your connection and try again.";
  }
  return message;
}

function record(state: ExtensionState, diagnostic: DiagnosticItem | undefined, kind: string, extra: Record<string, unknown>): void {
  if (!state.currentLearningSessionId) { return; }
  trackLearningEvent(state, {
    learning_session_id: state.currentLearningSessionId,
    event_type: "explanation_requested",
    concept_tag: diagnostic?.concept_tag,
    occurred_at: new Date().toISOString(),
    payload: {
      kind,
      diagnostic_id: diagnostic?.diagnostic_id,
      error_type: diagnostic?.error_type,
      ...extra,
    },
  });
}

/** "Explain in my code": why THIS line is a problem, without the fix. */
export async function explainInMyCode(state: ExtensionState, diagnostic: DiagnosticItem): Promise<void> {
  const document = documentFor(state);
  if (!document) { return; }
  const key = explainKey(diagnostic);
  state.assistByKey.set(key, { kind: "explanation", loading: true });
  updateCoachPanel(state);
  try {
    const result = await authorizedRequestJson<ExplanationResponse>(state, "/api/v1/code-coach/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        error_type: diagnostic.error_type,
        code: document.getText(),
        line: diagnostic.line,
        message: diagnostic.message,
        diagnostic_id: diagnostic.diagnostic_id,
      }),
    });
    state.assistByKey.set(key, {
      kind: "explanation", text: result.explanation, source: result.source,
      remaining: result.remaining_today, limit: result.daily_limit, limitReached: result.limit_reached,
    });
    record(state, diagnostic, "explain_in_my_code", { source: result.source });
  } catch (error) {
    state.assistByKey.set(key, { kind: "explanation", error: failureText(error) });
  }
  updateCoachPanel(state);
}

/** The closest worked example from the free course, for the same mistake. */
export async function showSimilarExample(state: ExtensionState, diagnostic: DiagnosticItem): Promise<void> {
  const document = documentFor(state);
  const key = exampleKey(diagnostic);
  state.assistByKey.set(key, { kind: "example", loading: true });
  updateCoachPanel(state);
  try {
    const result = await authorizedRequestJson<SimilarExampleResponse>(state, "/api/v1/code-coach/similar-example", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        error_type: diagnostic.error_type,
        code: document?.getText() ?? "",
        line: diagnostic.line,
      }),
    });
    state.assistByKey.set(key, { kind: "example", example: result });
    record(state, diagnostic, "similar_example", { source: result.source });
  } catch (error) {
    state.assistByKey.set(key, { kind: "example", error: failureText(error) });
  }
  updateCoachPanel(state);
}

/** A compiler error, read out for a beginner. */
export async function explainCompilerError(state: ExtensionState, problem: CompilerProblem): Promise<void> {
  const document = documentFor(state);
  if (!document) { return; }
  const key = compilerKey(problem);
  state.assistByKey.set(key, { kind: "compiler", loading: true, message: problem.message, line: problem.line });
  updateCoachPanel(state);
  try {
    const result = await authorizedRequestJson<ExplanationResponse>(state, "/api/v1/code-coach/explain-compiler-error", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: problem.message, code: document.getText(), line: problem.line }),
    });
    state.assistByKey.set(key, {
      kind: "compiler", message: problem.message, line: problem.line, text: result.explanation,
      source: result.source, remaining: result.remaining_today, limit: result.daily_limit,
      limitReached: result.limit_reached,
    });
    record(state, undefined, "compiler_error", { source: result.source, message: problem.message.slice(0, 160) });
  } catch (error) {
    state.assistByKey.set(key, { kind: "compiler", message: problem.message, line: problem.line, error: failureText(error) });
  }
  updateCoachPanel(state);
}

/** The free course unit for this mistake, in the browser. */
export function openCourseUnit(state: ExtensionState, diagnostic: DiagnosticItem): void {
  const target = new URL(`/study/course/${encodeURIComponent(diagnostic.error_type)}`, `${getPortalUrl()}/`);
  state.outputChannel.appendLine(`Opening course unit: ${target.toString()}`);
  void vscode.env.openExternal(vscode.Uri.parse(target.toString()));
  record(state, diagnostic, "course_unit_opened", {});
}

/** Stop showing one kind of finding in the editor (it can be undone in settings). */
export async function muteErrorType(state: ExtensionState, diagnostic: DiagnosticItem): Promise<void> {
  const title = titleFor(diagnostic);
  const choice = await vscode.window.showInformationMessage(
    `Stop showing "${title}" in the editor? You can turn it back on in Settings → Code Coach → Muted Error Types.`,
    { modal: false }, "Mute", "Cancel",
  );
  if (choice !== "Mute") { return; }
  const muted = new Set(mutedErrorTypes());
  muted.add(diagnostic.error_type);
  await vscode.workspace.getConfiguration("codeCoach").update(
    MUTED_SETTING, [...muted], vscode.ConfigurationTarget.Global,
  );
  record(state, diagnostic, "error_type_muted", {});
  void vscode.commands.executeCommand("code-coach-vscode.analyzeCurrentFile");
}
