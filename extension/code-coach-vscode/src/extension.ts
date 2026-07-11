/**
 * Entry point / composition root of the extension.
 *
 * VS Code calls activate() once when the extension wakes up. This file does the
 * wiring only — it holds almost no logic of its own. Its three jobs:
 *   1. Build the single shared ExtensionState object that every other file reads
 *      and mutates (current user, learning session, caches, VS Code handles).
 *   2. Register the commands (Sign In, Analyze, Next Hint, ...) and point each at
 *      a function in auth.ts or analysis.ts.
 *   3. Register the event listeners that fire analysis automatically (typing,
 *      switching editors) by calling scheduleAutoAnalysis() in analysis.ts.
 *
 * Who it talks to:
 *   - auth.ts      -> signIn / signOut / createAccount / restoreAuthSession
 *   - analysis.ts  -> runAnalysisForEditor / scheduleAutoAnalysis / hint nav
 *   - ui/*         -> status bars, decorations, panel, sidebar, code lens
 *
 * Nothing here calls the backend directly; that happens downstream in analysis.ts
 * and api.ts. This file is where user/editor events ENTER the system.
 */
import * as vscode from "vscode";
import { AuthUser, DiagnosticItem, ExtensionState } from "./types";
import { USER_STATE_KEY, LEARNING_SESSION_KEY } from "./constants";
import { signIn, signOut, createAccount, restoreAuthSession } from "./auth";
import {
  runAnalysisForEditor,
  scheduleAutoAnalysis,
  showHintForActiveEditor,
  clearTimerForUri,
  clearFeedbackForDocument,
  handleCoachPanelMessage,
} from "./analysis";
import { updateAuthStatusBar, updateAnalysisStatusBar, isSupportedDocument } from "./ui/statusBar";
import { updateCoachPanel, buildCoachPanelHtml } from "./ui/panelHtml";
import { createWarningDecorationType } from "./ui/decorations";
import { CoachSidebarProvider } from "./ui/sidebarProvider";
import { CoachCodeLensProvider } from "./ui/codeLensProvider";
import { CoachCodeActionProvider } from "./ui/codeActionProvider";

export function activate(context: vscode.ExtensionContext) {

  // ── Build shared state ──
  // THE single source of runtime truth for the whole extension. One instance is
  // created here and threaded (by reference) into every command, listener, and
  // helper. When analysis.ts caches diagnostics or auth.ts sets currentUser,
  // they are writing into THIS object. Note the two VS Code handles that matter
  // most downstream: diagnosticCollection (the yellow underlines) and
  // warningDecorationType (the highlight styling) — both defined once, here.
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
    lastSupportedUriKey: undefined,
    lastPanelHtml: undefined,
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

    // A fresh webview starts blank — invalidate the HTML cache so the first
    // updateCoachPanel below always assigns, even if the state is unchanged
    // since a previous panel instance was disposed.
    state.lastPanelHtml = undefined;
    state.coachPanel.onDidDispose(() => {
      state.coachPanel = undefined;
      state.lastPanelHtml = undefined;
    });

    state.coachPanel.webview.onDidReceiveMessage(
      (message: { command?: string; index?: number }) => {
        handleCoachPanelMessage(state, message);
      },
    );

    updateCoachPanel(state);
  }

  // ── Register commands ──
  // Each command id (declared in package.json, invoked from the palette, panel
  // buttons, or keybindings) is bound to a handler here. The handlers are thin:
  // they mostly just call into auth.ts (signIn/createAccount/signOut) or
  // analysis.ts (runAnalysisForEditor / showHintForActiveEditor), passing `state`.
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
      let editor = vscode.window.activeTextEditor;
      if ((!editor || !isSupportedDocument(editor.document)) && state.lastSupportedUriKey) {
        // Clicking the panel's Analyze button focuses the webview and clears
        // activeTextEditor — fall back to the last Java file still visible.
        editor = vscode.window.visibleTextEditors.find(
          (candidate) => candidate.document.uri.toString() === state.lastSupportedUriKey,
        );
      }
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
  // This is the automatic (non-command) trigger path. Every keystroke fires
  // onDidChangeTextDocument; switching files fires onDidChangeActiveTextEditor.
  // Both funnel into scheduleAutoAnalysis() in analysis.ts, which debounces
  // 900ms before actually analyzing. This is the start of the request spine you
  // traced in Session 2.
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
