import * as vscode from "vscode";
import { AuthUser, ExtensionState } from "./types";
import { USER_STATE_KEY, LEARNING_SESSION_KEY } from "./constants";
import { signIn, signOut, createAccount, restoreAuthSession } from "./auth";
import {
  runAnalysisForEditor,
  scheduleAutoAnalysis,
  showHintForActiveEditor,
  clearTimerForUri,
  focusDiagnostic,
  clearFeedbackForDocument,
} from "./analysis";
import { updateAuthStatusBar, updateAnalysisStatusBar, isSupportedDocument } from "./ui/statusBar";
import { updateCoachPanel, buildCoachPanelHtml } from "./ui/panelHtml";
import { createWarningDecorationType } from "./ui/decorations";
import { CoachSidebarProvider } from "./ui/sidebarProvider";

export function activate(context: vscode.ExtensionContext) {
  console.log("Code Coach extension has been activated.");

  // ── Build shared state ──
  const state: ExtensionState = {
    currentUser:
      context.globalState.get<AuthUser | undefined>(USER_STATE_KEY) ?? undefined,
    currentLearningSessionId:
      context.workspaceState.get<string | undefined>(LEARNING_SESSION_KEY) ?? undefined,
    lastDiagnosticsByUri: new Map(),
    lastAnalysisSnapshotByUri: new Map(),
    activeHintIndexByUri: new Map(),
    debounceTimers: new Map(),
    activeAnalysisUriKey: undefined,
    coachPanel: undefined,
    sidebarProvider: undefined,
    outputChannel: vscode.window.createOutputChannel("Code Coach"),
    diagnosticCollection: vscode.languages.createDiagnosticCollection("code-coach"),
    warningDecorationType: createWarningDecorationType(),
    authStatusBar: vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100),
    analysisStatusBar: vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99),
    context,
  };

  state.authStatusBar.name = "Code Coach Auth";
  state.analysisStatusBar.name = "Code Coach Analysis";
  state.analysisStatusBar.command = "code-coach-vscode.analyzeCurrentFile";

  // ── Sidebar provider ──
  const sidebarProvider = new CoachSidebarProvider(state);
  state.sidebarProvider = sidebarProvider;
  const sidebarRegistration = vscode.window.registerWebviewViewProvider(
    CoachSidebarProvider.viewType,
    sidebarProvider,
    { webviewOptions: { retainContextWhenHidden: true } },
  );

  // ── Coach panel helpers ──
  function getSupportedActiveEditor(): vscode.TextEditor | undefined {
    const editor = vscode.window.activeTextEditor;
    return editor && isSupportedDocument(editor.document) ? editor : undefined;
  }

  function openCoachPanel() {
    if (state.coachPanel) {
      state.coachPanel.reveal(vscode.ViewColumn.Beside, true);
      updateCoachPanel(state);
      return;
    }

    state.coachPanel = vscode.window.createWebviewPanel(
      "codeCoachPanel",
      "Code Coach",
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true },
    );

    state.coachPanel.onDidDispose(() => { state.coachPanel = undefined; });

    state.coachPanel.webview.onDidReceiveMessage((message: { command?: string }) => {
      switch (message.command) {
        case "signIn":
          void vscode.commands.executeCommand("code-coach-vscode.signIn");
          break;
        case "createAccount":
          void vscode.commands.executeCommand("code-coach-vscode.createAccount");
          break;
        case "analyze":
          void vscode.commands.executeCommand("code-coach-vscode.analyzeCurrentFile");
          break;
        case "previousHint":
          void vscode.commands.executeCommand("code-coach-vscode.previousHint");
          break;
        case "nextHint":
          void vscode.commands.executeCommand("code-coach-vscode.nextHint");
          break;
        case "openOutput":
          state.outputChannel.show(true);
          break;
        case "revealIssue": {
          const editor = getSupportedActiveEditor();
          if (!editor) { break; }
          const diagnostics = state.lastDiagnosticsByUri.get(editor.document.uri.toString()) ?? [];
          const currentIndex = state.activeHintIndexByUri.get(editor.document.uri.toString()) ?? 0;
          const diagnostic = diagnostics[currentIndex];
          if (diagnostic) { focusDiagnostic(editor, diagnostic); }
          break;
        }
        default:
          break;
      }
    });

    updateCoachPanel(state);
  }

  // ── Register commands ──
  const startCommand = vscode.commands.registerCommand("code-coach-vscode.start", () => {
    const action = state.currentUser ? "Analyze Current File" : "Sign In";
    void vscode.window.showInformationMessage(
      state.currentUser
        ? "Code Coach is ready. Use it on the current Java file."
        : "Code Coach is ready. Sign in to analyze code and save progress.",
      action, "Open Coach Panel",
    ).then((selected) => {
      if (selected === "Analyze Current File") {
        void vscode.commands.executeCommand("code-coach-vscode.analyzeCurrentFile");
      } else if (selected === "Sign In") {
        void vscode.commands.executeCommand("code-coach-vscode.signIn");
      } else if (selected === "Open Coach Panel") {
        openCoachPanel();
      }
    });
    state.outputChannel.show(true);
    state.outputChannel.appendLine("Code Coach extension started.");
  });

  const signInCommand = vscode.commands.registerCommand(
    "code-coach-vscode.signIn", async () => { await signIn(state); },
  );

  const createAccountCommand = vscode.commands.registerCommand(
    "code-coach-vscode.createAccount", async () => { await createAccount(state); },
  );

  const signOutCommand = vscode.commands.registerCommand(
    "code-coach-vscode.signOut", async () => { await signOut(state); },
  );

  const analyzeCommand = vscode.commands.registerCommand(
    "code-coach-vscode.analyzeCurrentFile", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showErrorMessage("Open a Java file to analyze it with Code Coach.");
        return;
      }
      clearTimerForUri(state, editor.document.uri);
      await runAnalysisForEditor(state, editor, { showPopup: true, showOutput: true });
    },
  );

  const openCoachPanelCommand = vscode.commands.registerCommand(
    "code-coach-vscode.openCoachPanel", () => { openCoachPanel(); },
  );

  const previousHintCommand = vscode.commands.registerCommand(
    "code-coach-vscode.previousHint", () => { showHintForActiveEditor(state, -1); },
  );

  const nextHintCommand = vscode.commands.registerCommand(
    "code-coach-vscode.nextHint", () => { showHintForActiveEditor(state, 1); },
  );

  // ── Event listeners ──
  const onDidChangeTextDocument = vscode.workspace.onDidChangeTextDocument((event) => {
    if (event.contentChanges.length === 0) { return; }
    const activeEditor = vscode.window.activeTextEditor;
    if (!activeEditor) { return; }
    if (activeEditor.document.uri.toString() !== event.document.uri.toString()) { return; }
    scheduleAutoAnalysis(state, activeEditor);
  });

  const onDidChangeActiveEditor = vscode.window.onDidChangeActiveTextEditor((editor) => {
    if (!editor) { return; }
    scheduleAutoAnalysis(state, editor);
    updateAnalysisStatusBar(state, editor);
  });

  const onDidCloseTextDocument = vscode.workspace.onDidCloseTextDocument((document) => {
    clearFeedbackForDocument(state, document);
  });

  // ── Initialize ──
  updateAuthStatusBar(state);
  updateAnalysisStatusBar(state);
  void restoreAuthSession(state);

  const initialEditor = vscode.window.activeTextEditor;
  if (initialEditor) { scheduleAutoAnalysis(state, initialEditor); }

  // ── Push disposables ──
  context.subscriptions.push(
    startCommand, signInCommand, createAccountCommand, signOutCommand,
    analyzeCommand, openCoachPanelCommand, previousHintCommand, nextHintCommand,
    state.outputChannel, state.diagnosticCollection, state.warningDecorationType,
    state.authStatusBar, state.analysisStatusBar,
    sidebarRegistration,
    onDidChangeTextDocument, onDidChangeActiveEditor, onDidCloseTextDocument,
  );
}

export function deactivate() {}
