import * as vscode from "vscode";
import { ExtensionState } from "../types";
import { updateCoachPanel } from "./panelHtml";

export function formatDuration(durationMs: number): string {
  if (durationMs >= 1000) {
    return `${(durationMs / 1000).toFixed(2)} s`;
  }

  return `${Math.round(durationMs)} ms`;
}

export function isSupportedDocument(document: vscode.TextDocument): boolean {
  return document.languageId === "java";
}

export function updateAuthStatusBar(state: ExtensionState): void {
  if (state.currentUser) {
    state.authStatusBar.text = `$(account) ${state.currentUser.full_name}`;
    state.authStatusBar.tooltip = `Signed in to Code Coach as ${state.currentUser.email}`;
    state.authStatusBar.command = "code-coach-vscode.signOut";
    state.authStatusBar.show();
    return;
  }

  state.authStatusBar.text = "$(account) Code Coach Sign In";
  state.authStatusBar.tooltip = "Sign in to Code Coach";
  state.authStatusBar.command = "code-coach-vscode.signIn";
  state.authStatusBar.show();
}

export function updateAnalysisStatusBar(
  state: ExtensionState,
  editor: vscode.TextEditor | undefined = vscode.window.activeTextEditor,
): void {
  if (!state.currentUser) {
    state.analysisStatusBar.text = "$(lock) Sign In for Code Coach";
    state.analysisStatusBar.tooltip =
      "Sign in to analyze Java files and save your progress.";
    state.analysisStatusBar.command = "code-coach-vscode.signIn";
    state.analysisStatusBar.show();
    updateCoachPanel(state);
    return;
  }

  if (!editor || !isSupportedDocument(editor.document)) {
    state.analysisStatusBar.text = "$(beaker) Code Coach Ready";
    state.analysisStatusBar.tooltip =
      "Open a Java file to analyze it with Code Coach.";
    state.analysisStatusBar.command = "code-coach-vscode.analyzeCurrentFile";
    state.analysisStatusBar.show();
    updateCoachPanel(state);
    return;
  }

  const uriKey = editor.document.uri.toString();
  const snapshot = state.lastAnalysisSnapshotByUri.get(uriKey);

  state.analysisStatusBar.command = "code-coach-vscode.analyzeCurrentFile";

  if (state.activeAnalysisUriKey === uriKey) {
    state.analysisStatusBar.text = "$(sync~spin) Code Coach Analyzing";
    state.analysisStatusBar.tooltip =
      "Code Coach is analyzing the current Java file.";
    state.analysisStatusBar.show();
    updateCoachPanel(state);
    return;
  }

  if (!snapshot) {
    state.analysisStatusBar.text = "$(search) Analyze Java File";
    state.analysisStatusBar.tooltip =
      "Run Code Coach on the current Java file.";
    state.analysisStatusBar.show();
    updateCoachPanel(state);
    return;
  }

  if (snapshot.diagnosticsCount === 0) {
    state.analysisStatusBar.text = "$(check) Code Coach Clean";
    state.analysisStatusBar.tooltip = `No target issues detected. Last analysis took ${formatDuration(snapshot.analysisDurationMs)}.`;
    state.analysisStatusBar.show();
    updateCoachPanel(state);
    return;
  }

  const issueLabel = snapshot.diagnosticsCount === 1 ? "issue" : "issues";
  state.analysisStatusBar.text = `$(warning) Code Coach ${snapshot.diagnosticsCount} ${issueLabel}`;
  state.analysisStatusBar.tooltip =
    `${snapshot.firstMessage ?? "Issues detected."} ` +
    `Line ${snapshot.firstLine ?? "n/a"}. ` +
    `Last analysis took ${formatDuration(snapshot.analysisDurationMs)}.`;
  state.analysisStatusBar.show();
  updateCoachPanel(state);
}
