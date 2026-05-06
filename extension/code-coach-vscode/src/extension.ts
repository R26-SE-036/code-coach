import * as vscode from "vscode";
import { AuthUser, DiagnosticItem, ExtensionState } from "./types";
import { USER_STATE_KEY, LEARNING_SESSION_KEY } from "./constants";
import { signIn, signOut, createAccount, restoreAuthSession } from "./auth";
import {
  runAnalysisForEditor,
  scheduleAutoAnalysis,
  showHintForActiveEditor,
  clearTimerForUri,
  focusDiagnostic,
  clearFeedbackForDocument,
  navigatePanelHint,
} from "./analysis";
import { updateAuthStatusBar, updateAnalysisStatusBar, isSupportedDocument } from "./ui/statusBar";
import { updateCoachPanel, buildCoachPanelHtml } from "./ui/panelHtml";
import { createWarningDecorationType } from "./ui/decorations";
import { CoachSidebarProvider } from "./ui/sidebarProvider";
import { CoachCodeLensProvider } from "./ui/codeLensProvider";
import { CoachCodeActionProvider } from "./ui/codeActionProvider";

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
    codeLensProvider: undefined,
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

  // ── CodeLens provider ──
  const codeLensProvider = new CoachCodeLensProvider(state);
  state.codeLensProvider = codeLensProvider;
  const codeLensRegistration = vscode.languages.registerCodeLensProvider(
    { language: "java" },
    codeLensProvider,
  );

  // ── Code Action provider ──
  const codeActionRegistration = vscode.languages.registerCodeActionsProvider(
    { language: "java" },
    new CoachCodeActionProvider(state),
    { providedCodeActionKinds: CoachCodeActionProvider.providedCodeActionKinds },
  );

  // ── Coach panel helpers ──
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
        case "openOutput":
          state.outputChannel.show(true);
          break;
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

  const showCodeLensHintCommand = vscode.commands.registerCommand(
    "code-coach-vscode.showCodeLensHint",
    (index: number, level: "concept" | "guidance" | "targeted", diag: DiagnosticItem) => {
      const hintText = level === "guidance" ? diag.hints.guidance
        : level === "targeted" ? diag.hints.targeted
        : diag.hints.concept;
      const label = level.charAt(0).toUpperCase() + level.slice(1);
      void vscode.window.showInformationMessage(
        `Code Coach ${label} Hint (${diag.error_type}, line ${diag.line}): ${hintText}`,
      );
    },
  );

  const openWalkthroughCommand = vscode.commands.registerCommand(
    "code-coach-vscode.openWalkthrough", () => {
      void vscode.commands.executeCommand(
        "workbench.action.openWalkthrough",
        "code-coach-vscode.codeCoachWelcome",
        false,
      );
    },
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

  // On first activation, guide the user to move Code Coach to the right sidebar
  const shownTipKey = "codeCoach.shownRightSidebarTip";
  if (!context.globalState.get<boolean>(shownTipKey)) {
    void context.globalState.update(shownTipKey, true);
    setTimeout(() => {
      void vscode.window.showInformationMessage(
        "💡 Code Coach: Right-click the 🎓 icon in the activity bar and select \"Move to Secondary Side Bar\" to pin it on the right side.",
        "Open Code Coach",
      ).then((action) => {
        if (action === "Open Code Coach") {
          void vscode.commands.executeCommand("codeCoachSidebar.focus");
        }
      });
    }, 3000);
  }

  // ── Push disposables ──
  context.subscriptions.push(
    startCommand, signInCommand, createAccountCommand, signOutCommand,
    analyzeCommand, openCoachPanelCommand, previousHintCommand, nextHintCommand,
    showCodeLensHintCommand, openWalkthroughCommand,
    state.outputChannel, state.diagnosticCollection, state.warningDecorationType,
    state.authStatusBar, state.analysisStatusBar,
    sidebarRegistration, codeLensRegistration, codeLensProvider, codeActionRegistration,
    onDidChangeTextDocument, onDidChangeActiveEditor, onDidCloseTextDocument,
  );
}

export function deactivate() {}
