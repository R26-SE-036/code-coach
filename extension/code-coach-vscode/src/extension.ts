import * as vscode from "vscode";

type HintSet = {
  concept: string;
  guidance: string;
  targeted: string;
};

type DiagnosticItem = {
  diagnostic_id: string;
  error_type: string;
  severity: string;
  line: number;
  column: number;
  confidence: number;
  message: string;
  code_context: string;
  concept_tag: string;
  explanation_key: string;
  status: string;
  detection_engine: string;
  ml_probability?: number;
  locator_confidence?: number;
  hints: HintSet;
};

type AnalyzeResponse = {
  status: string;
  message: string;
  timestamp: string;
  analysis_duration_ms: number;
  learning_session_id?: string;
  diagnostics: DiagnosticItem[];
};

type AuthUser = {
  user_id: string;
  full_name: string;
  email: string;
  student_number: string;
  role: string;
  status: string;
  created_at: string;
};

type AuthSession = {
  auth_session_id: string;
  client_name: string;
  status: string;
  created_at: string;
  last_seen_at: string;
  expires_at: string;
};

type TokenBundle = {
  token_type: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
};

type AuthResponse = {
  status: string;
  message: string;
  user: AuthUser;
  auth_session: AuthSession;
  tokens: TokenBundle;
};

type MeResponse = {
  status: string;
  user: AuthUser;
  auth_session: AuthSession;
};

type LearningSessionResponse = {
  status: string;
  message: string;
  learning_session_id: string;
  user_id: string;
  source_component: string;
  language: string;
  task_id?: string;
  learning_session_status: string;
  started_at: string;
  last_analysis_at?: string;
  reused_existing: boolean;
};

class ApiError extends Error {
  readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

const ACCESS_TOKEN_SECRET = "codeCoach.accessToken";
const REFRESH_TOKEN_SECRET = "codeCoach.refreshToken";
const USER_STATE_KEY = "codeCoach.user";
const LEARNING_SESSION_KEY = "codeCoach.learningSessionId";
const CLIENT_NAME = "code-coach-vscode";

export function activate(context: vscode.ExtensionContext) {
  console.log("Code Coach extension has been activated.");

  const outputChannel = vscode.window.createOutputChannel("Code Coach");
  const diagnosticCollection =
    vscode.languages.createDiagnosticCollection("code-coach");
  const authStatusBar = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    100,
  );
  authStatusBar.name = "Code Coach Auth";

  const warningDecorationType = vscode.window.createTextEditorDecorationType({
    backgroundColor: "rgba(255, 215, 0, 0.18)",
    border: "1px solid rgba(255, 215, 0, 0.45)",
    borderRadius: "3px",
  });

  const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();
  const lastDiagnosticsByUri = new Map<string, DiagnosticItem[]>();
  const activeHintIndexByUri = new Map<string, number>();
  const debounceDelayMs = 900;

  let currentUser =
    context.globalState.get<AuthUser | undefined>(USER_STATE_KEY) ?? undefined;
  let currentLearningSessionId =
    context.workspaceState.get<string | undefined>(LEARNING_SESSION_KEY) ??
    undefined;

  function getBackendUrl(): string {
    return vscode.workspace
      .getConfiguration("codeCoach")
      .get<string>("backendUrl", "http://127.0.0.1:8000")
      .replace(/\/$/, "");
  }

  function isEvaluationLoggingEnabled(): boolean {
    return vscode.workspace
      .getConfiguration("codeCoach")
      .get<boolean>("enableEvaluationLogging", false);
  }

  function updateAuthStatusBar() {
    if (currentUser) {
      authStatusBar.text = `$(account) ${currentUser.full_name}`;
      authStatusBar.tooltip = `Signed in to Code Coach as ${currentUser.email}`;
      authStatusBar.command = "code-coach-vscode.signOut";
      authStatusBar.show();
      return;
    }

    authStatusBar.text = "$(account) Code Coach Sign In";
    authStatusBar.tooltip = "Sign in to Code Coach";
    authStatusBar.command = "code-coach-vscode.signIn";
    authStatusBar.show();
  }

  function isSupportedDocument(document: vscode.TextDocument): boolean {
    return document.languageId === "java";
  }

  function clearTimerForUri(uri: vscode.Uri) {
    const key = uri.toString();
    const existingTimer = debounceTimers.get(key);

    if (existingTimer) {
      clearTimeout(existingTimer);
      debounceTimers.delete(key);
    }
  }

  function clearEditorFeedback(editor: vscode.TextEditor | undefined) {
    if (!editor) {
      return;
    }

    clearTimerForUri(editor.document.uri);
    diagnosticCollection.delete(editor.document.uri);
    editor.setDecorations(warningDecorationType, []);
  }

  function clearFeedbackForDocument(document: vscode.TextDocument) {
    clearTimerForUri(document.uri);
    diagnosticCollection.delete(document.uri);
    lastDiagnosticsByUri.delete(document.uri.toString());
    activeHintIndexByUri.delete(document.uri.toString());

    const activeEditor = vscode.window.activeTextEditor;
    if (
      activeEditor &&
      activeEditor.document.uri.toString() === document.uri.toString()
    ) {
      activeEditor.setDecorations(warningDecorationType, []);
    }
  }

  async function clearLearningSession() {
    currentLearningSessionId = undefined;
    await context.workspaceState.update(LEARNING_SESSION_KEY, undefined);
  }

  async function clearStoredAuthState() {
    await context.secrets.delete(ACCESS_TOKEN_SECRET);
    await context.secrets.delete(REFRESH_TOKEN_SECRET);
    await context.globalState.update(USER_STATE_KEY, undefined);
    currentUser = undefined;
    await clearLearningSession();
    diagnosticCollection.clear();
    lastDiagnosticsByUri.clear();
    activeHintIndexByUri.clear();
    clearEditorFeedback(vscode.window.activeTextEditor);
    updateAuthStatusBar();
  }

  async function storeAuthResponse(
    payload: AuthResponse,
    options: { resetLearningSession: boolean },
  ) {
    await context.secrets.store(
      ACCESS_TOKEN_SECRET,
      payload.tokens.access_token,
    );
    await context.secrets.store(
      REFRESH_TOKEN_SECRET,
      payload.tokens.refresh_token,
    );
    currentUser = payload.user;
    await context.globalState.update(USER_STATE_KEY, payload.user);

    if (options.resetLearningSession) {
      await clearLearningSession();
    }

    updateAuthStatusBar();
  }

  function headersToRecord(
    headers?: RequestInit["headers"],
  ): Record<string, string> {
    const normalized: Record<string, string> = {};

    if (!headers) {
      return normalized;
    }

    if (headers instanceof Headers) {
      for (const [key, value] of headers.entries()) {
        normalized[key] = value;
      }
      return normalized;
    }

    if (Array.isArray(headers)) {
      for (const [key, value] of headers) {
        normalized[key] = String(value);
      }
      return normalized;
    }

    for (const [key, value] of Object.entries(headers)) {
      normalized[key] = Array.isArray(value) ? value.join(", ") : String(value);
    }

    return normalized;
  }

  async function extractErrorMessage(response: Response): Promise<string> {
    const rawText = await response.text();

    if (!rawText) {
      return `Backend request failed with status ${response.status}.`;
    }

    try {
      const parsed = JSON.parse(rawText) as {
        detail?: string;
        message?: string;
      };
      return (
        parsed.detail ??
        parsed.message ??
        `Backend request failed with status ${response.status}.`
      );
    } catch {
      return rawText;
    }
  }

  async function requestJson<T>(
    path: string,
    init: RequestInit,
  ): Promise<T> {
    const response = await fetch(`${getBackendUrl()}${path}`, init);

    if (!response.ok) {
      throw new ApiError(await extractErrorMessage(response), response.status);
    }

    return (await response.json()) as T;
  }

  async function refreshAuthSession(): Promise<boolean> {
    const refreshToken = await context.secrets.get(REFRESH_TOKEN_SECRET);

    if (!refreshToken) {
      return false;
    }

    try {
      const response = await requestJson<AuthResponse>("/api/v1/auth/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      await storeAuthResponse(response, { resetLearningSession: false });
      return true;
    } catch (error) {
      console.error("Code Coach token refresh failed:", error);
      await clearStoredAuthState();
      return false;
    }
  }

  async function authorizedRequestJson<T>(
    path: string,
    init: RequestInit,
    allowRefresh = true,
  ): Promise<T> {
    const accessToken = await context.secrets.get(ACCESS_TOKEN_SECRET);
    if (!accessToken) {
      throw new Error("Please sign in to Code Coach first.");
    }

    const headers = headersToRecord(init.headers);
    headers.Authorization = `Bearer ${accessToken}`;

    try {
      return await requestJson<T>(path, {
        ...init,
        headers,
      });
    } catch (error) {
      if (
        error instanceof ApiError &&
        error.statusCode === 401 &&
        allowRefresh &&
        (await refreshAuthSession())
      ) {
        return authorizedRequestJson<T>(path, init, false);
      }

      throw error;
    }
  }

  async function restoreAuthSession(): Promise<boolean> {
    const accessToken = await context.secrets.get(ACCESS_TOKEN_SECRET);
    const refreshToken = await context.secrets.get(REFRESH_TOKEN_SECRET);

    if (!accessToken && !refreshToken) {
      currentUser = undefined;
      updateAuthStatusBar();
      return false;
    }

    try {
      const me = await authorizedRequestJson<MeResponse>("/api/v1/auth/me", {
        method: "GET",
      });
      currentUser = me.user;
      await context.globalState.update(USER_STATE_KEY, me.user);
      updateAuthStatusBar();
      return true;
    } catch (error) {
      console.error("Code Coach session restore failed:", error);
      await clearStoredAuthState();
      return false;
    }
  }

  async function ensureAuthenticated(showPrompt: boolean): Promise<boolean> {
    if (currentUser) {
      return true;
    }

    if (await restoreAuthSession()) {
      return true;
    }

    if (!showPrompt) {
      return false;
    }

    const action = await vscode.window.showInformationMessage(
      "Sign in to Code Coach to analyze code and save progress.",
      "Sign In",
      "Create Account",
    );

    if (action === "Sign In") {
      await signIn();
    } else if (action === "Create Account") {
      await createAccount();
    }

    return currentUser !== undefined;
  }

  async function ensureLearningSession(): Promise<string | undefined> {
    if (currentLearningSessionId) {
      return currentLearningSessionId;
    }

    if (!(await ensureAuthenticated(false))) {
      return undefined;
    }

    const response = await authorizedRequestJson<LearningSessionResponse>(
      "/api/v1/learning-sessions",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source_component: "code_coach",
          language: "java",
        }),
      },
    );

    currentLearningSessionId = response.learning_session_id;
    await context.workspaceState.update(
      LEARNING_SESSION_KEY,
      currentLearningSessionId,
    );
    return currentLearningSessionId;
  }

  async function promptValue(
    options: vscode.InputBoxOptions,
    settings?: { trim?: boolean },
  ): Promise<string | undefined> {
    const value = await vscode.window.showInputBox({
      ignoreFocusOut: true,
      ...options,
    });

    if (value === undefined) {
      return undefined;
    }

    if (settings?.trim === false) {
      return value.length > 0 ? value : undefined;
    }

    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : undefined;
  }

  async function createAccount() {
    try {
      const fullName = await promptValue({
        prompt: "Enter your full name",
        placeHolder: "Jane Student",
      });
      if (!fullName) {
        return;
      }

      const email = await promptValue({
        prompt: "Enter your email address",
        placeHolder: "student@example.com",
      });
      if (!email) {
        return;
      }

      const studentNumber = await promptValue({
        prompt: "Enter your student number",
        placeHolder: "IT22203380",
      });
      if (!studentNumber) {
        return;
      }

      const password = await promptValue({
        prompt: "Create a password (minimum 8 characters)",
        password: true,
      }, { trim: false });
      if (!password) {
        return;
      }

      const confirmPassword = await promptValue({
        prompt: "Confirm your password",
        password: true,
      }, { trim: false });
      if (!confirmPassword) {
        return;
      }

      if (password !== confirmPassword) {
        vscode.window.showErrorMessage("The passwords do not match.");
        return;
      }

      const response = await requestJson<AuthResponse>("/api/v1/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_name: fullName,
          email,
          student_number: studentNumber,
          password,
          client_name: CLIENT_NAME,
        }),
      });

      await storeAuthResponse(response, { resetLearningSession: true });
      outputChannel.appendLine(`Signed in as ${response.user.email}`);
      vscode.window.showInformationMessage(
        `Welcome to Code Coach, ${response.user.full_name}.`,
      );

      if (vscode.window.activeTextEditor) {
        scheduleAutoAnalysis(vscode.window.activeTextEditor);
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Account creation failed.";
      vscode.window.showErrorMessage(`Code Coach error: ${message}`);
    }
  }

  async function signIn() {
    try {
      const identifier = await promptValue({
        prompt: "Enter your email or student number",
        placeHolder: "student@example.com or IT22203380",
      });
      if (!identifier) {
        return;
      }

      const password = await promptValue({
        prompt: "Enter your password",
        password: true,
      }, { trim: false });
      if (!password) {
        return;
      }

      const response = await requestJson<AuthResponse>("/api/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          identifier,
          password,
          client_name: CLIENT_NAME,
        }),
      });

      await storeAuthResponse(response, { resetLearningSession: true });
      outputChannel.appendLine(`Signed in as ${response.user.email}`);
      vscode.window.showInformationMessage(
        `Signed in to Code Coach as ${response.user.full_name}.`,
      );

      if (vscode.window.activeTextEditor) {
        scheduleAutoAnalysis(vscode.window.activeTextEditor);
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Sign in failed.";
      vscode.window.showErrorMessage(`Code Coach error: ${message}`);
    }
  }

  async function signOut() {
    try {
      if (currentUser) {
        await authorizedRequestJson<{ status: string; message: string }>(
          "/api/v1/auth/logout",
          {
            method: "POST",
          },
        );
      }
    } catch (error) {
      console.error("Code Coach logout error:", error);
    } finally {
      await clearStoredAuthState();
      vscode.window.showInformationMessage("Signed out from Code Coach.");
    }
  }

  function createRangeFromDiagnostic(
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

    const startChar = Math.max(
      0,
      Math.min(diagnostic.column - 1, line.text.length - 1),
    );

    return new vscode.Range(lineIndex, startChar, lineIndex, line.text.length);
  }

  function severityFromDiagnostic(
    diagnostic: DiagnosticItem,
  ): vscode.DiagnosticSeverity {
    switch (diagnostic.severity) {
      case "error":
        return vscode.DiagnosticSeverity.Error;
      case "information":
        return vscode.DiagnosticSeverity.Information;
      case "hint":
        return vscode.DiagnosticSeverity.Hint;
      default:
        return vscode.DiagnosticSeverity.Warning;
    }
  }

  function applyEditorFeedback(
    editor: vscode.TextEditor,
    backendDiagnostics: DiagnosticItem[],
  ) {
    const uriKey = editor.document.uri.toString();
    const vscodeDiagnostics: vscode.Diagnostic[] = [];
    const decorationOptions: vscode.DecorationOptions[] = [];

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

      decorationOptions.push({
        range,
        hoverMessage: new vscode.MarkdownString(
          `**${item.error_type}**\n\n` +
            `${item.message}\n\n` +
            `**Diagnostic ID:** ${item.diagnostic_id}\n\n` +
            `**Severity:** ${item.severity}\n\n` +
            `**Engine:** ${item.detection_engine}\n\n` +
            `**ML probability:** ${item.ml_probability ?? "n/a"}\n\n` +
            `**Locator confidence:** ${item.locator_confidence ?? "n/a"}\n\n` +
            `**Concept tag:** ${item.concept_tag}\n\n` +
            `**Explanation key:** ${item.explanation_key}\n\n` +
            `**Code context:** \`${item.code_context}\`\n\n` +
            `**Concept hint:** ${item.hints.concept}\n\n` +
            `**Guidance hint:** ${item.hints.guidance}\n\n` +
            `**Targeted hint:** ${item.hints.targeted}\n\n` +
            `Confidence: ${item.confidence}`,
        ),
      });
    }

    lastDiagnosticsByUri.set(uriKey, backendDiagnostics);
    activeHintIndexByUri.set(uriKey, 0);
    diagnosticCollection.set(editor.document.uri, vscodeDiagnostics);
    editor.setDecorations(warningDecorationType, decorationOptions);
  }

  async function requestAnalyze(
    code: string,
    learningSessionId: string,
  ): Promise<AnalyzeResponse> {
    return authorizedRequestJson<AnalyzeResponse>("/api/v1/code-coach/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        language: "java",
        code,
        learning_session_id: learningSessionId,
        enable_logging: isEvaluationLoggingEnabled(),
      }),
    });
  }

  async function runAnalysisForEditor(
    editor: vscode.TextEditor,
    options: { showPopup: boolean; showOutput: boolean },
  ) {
    const document = editor.document;

    if (!isSupportedDocument(document)) {
      clearFeedbackForDocument(document);
      return;
    }

    if (!(await ensureAuthenticated(options.showPopup))) {
      clearFeedbackForDocument(document);
      return;
    }

    const code = document.getText();

    if (!code.trim()) {
      clearFeedbackForDocument(document);

      if (options.showPopup) {
        vscode.window.showWarningMessage("The current file is empty.");
      }

      if (options.showOutput) {
        outputChannel.clear();
        outputChannel.show(true);
        outputChannel.appendLine("=== Code Coach Analysis Result ===");
        outputChannel.appendLine("The current file is empty.");
      }

      return;
    }

    try {
      let learningSessionId = await ensureLearningSession();
      if (!learningSessionId) {
        throw new Error("Unable to start a learning session.");
      }

      let result: AnalyzeResponse;

      try {
        result = await requestAnalyze(code, learningSessionId);
      } catch (error) {
        if (
          error instanceof ApiError &&
          (error.statusCode === 404 || error.statusCode === 409)
        ) {
          await clearLearningSession();
          learningSessionId = await ensureLearningSession();

          if (!learningSessionId) {
            throw error;
          }

          result = await requestAnalyze(code, learningSessionId);
        } else {
          throw error;
        }
      }

      if (options.showOutput) {
        outputChannel.clear();
        outputChannel.show(true);
        outputChannel.appendLine("=== Code Coach Analysis Result ===");
        outputChannel.appendLine(`Status: ${result.status}`);
        outputChannel.appendLine(`Message: ${result.message}`);
        outputChannel.appendLine(`Timestamp: ${result.timestamp}`);
        outputChannel.appendLine(
          `Analysis time: ${result.analysis_duration_ms} ms`,
        );
        outputChannel.appendLine(
          `Learning session: ${result.learning_session_id ?? "n/a"}`,
        );
        outputChannel.appendLine(`User: ${currentUser?.email ?? "n/a"}`);
        outputChannel.appendLine("");
      }

      if (result.diagnostics.length === 0) {
        clearFeedbackForDocument(document);

        if (options.showOutput) {
          outputChannel.appendLine("No issues detected.");
        }

        if (options.showPopup) {
          vscode.window.showInformationMessage("Code Coach: No issues detected.");
        }

        return;
      }

      if (options.showOutput) {
        for (const diagnostic of result.diagnostics) {
          outputChannel.appendLine(`Diagnostic : ${diagnostic.diagnostic_id}`);
          outputChannel.appendLine(`Error Type : ${diagnostic.error_type}`);
          outputChannel.appendLine(`Severity   : ${diagnostic.severity}`);
          outputChannel.appendLine(
            `Engine     : ${diagnostic.detection_engine}`,
          );
          outputChannel.appendLine(
            `ML Prob.   : ${diagnostic.ml_probability ?? "n/a"}`,
          );
          outputChannel.appendLine(
            `Locator    : ${diagnostic.locator_confidence ?? "n/a"}`,
          );
          outputChannel.appendLine(`Line       : ${diagnostic.line}`);
          outputChannel.appendLine(`Column     : ${diagnostic.column}`);
          outputChannel.appendLine(`Confidence : ${diagnostic.confidence}`);
          outputChannel.appendLine(`Message    : ${diagnostic.message}`);
          outputChannel.appendLine(`Context    : ${diagnostic.code_context}`);
          outputChannel.appendLine(`ConceptTag : ${diagnostic.concept_tag}`);
          outputChannel.appendLine(`ExplainKey : ${diagnostic.explanation_key}`);
          outputChannel.appendLine(`Concept    : ${diagnostic.hints.concept}`);
          outputChannel.appendLine(`Guidance   : ${diagnostic.hints.guidance}`);
          outputChannel.appendLine(`Targeted   : ${diagnostic.hints.targeted}`);
          outputChannel.appendLine("-----------------------------------");
        }
      }

      applyEditorFeedback(editor, result.diagnostics);

      if (options.showPopup) {
        const firstDiagnostic = result.diagnostics[0];

        vscode.window.showWarningMessage(
          `Code Coach: Found ${result.diagnostics.length} issue(s). First issue: ${firstDiagnostic.message} (Line ${firstDiagnostic.line}). Hint: ${firstDiagnostic.hints.concept}`,
        );
      }
    } catch (error) {
      clearFeedbackForDocument(document);

      const message =
        error instanceof Error ? error.message : "Unknown error occurred.";

      if (options.showPopup) {
        vscode.window.showErrorMessage(`Code Coach error: ${message}`);
      }

      console.error("Code Coach analyze error:", error);
    }
  }

  function scheduleAutoAnalysis(editor: vscode.TextEditor | undefined) {
    if (!editor) {
      return;
    }

    const document = editor.document;

    if (!isSupportedDocument(document)) {
      clearFeedbackForDocument(document);
      return;
    }

    clearTimerForUri(document.uri);

    const timer = setTimeout(() => {
      void runAnalysisForEditor(editor, {
        showPopup: false,
        showOutput: false,
      });
      debounceTimers.delete(document.uri.toString());
    }, debounceDelayMs);

    debounceTimers.set(document.uri.toString(), timer);
  }

  function showHintForActiveEditor(direction: 1 | -1) {
    const editor = vscode.window.activeTextEditor;

    if (!editor || !isSupportedDocument(editor.document)) {
      vscode.window.showInformationMessage("Code Coach: Open a Java file first.");
      return;
    }

    const uriKey = editor.document.uri.toString();
    const diagnostics = lastDiagnosticsByUri.get(uriKey) ?? [];

    if (diagnostics.length === 0) {
      vscode.window.showInformationMessage("Code Coach: No active hints.");
      return;
    }

    const currentIndex = activeHintIndexByUri.get(uriKey) ?? 0;
    const nextIndex =
      (currentIndex + direction + diagnostics.length) % diagnostics.length;
    const diagnostic = diagnostics[nextIndex];
    const range = createRangeFromDiagnostic(editor.document, diagnostic);

    activeHintIndexByUri.set(uriKey, nextIndex);
    editor.selection = new vscode.Selection(range.start, range.start);
    editor.revealRange(
      range,
      vscode.TextEditorRevealType.InCenterIfOutsideViewport,
    );

    vscode.window.showInformationMessage(
      `Code Coach hint ${nextIndex + 1}/${diagnostics.length}: ${diagnostic.hints.guidance}`,
    );
  }

  const startCommand = vscode.commands.registerCommand(
    "code-coach-vscode.start",
    () => {
      vscode.window.showInformationMessage("Code Coach extension is running.");
      outputChannel.show(true);
      outputChannel.appendLine("Code Coach extension started.");
    },
  );

  const signInCommand = vscode.commands.registerCommand(
    "code-coach-vscode.signIn",
    async () => {
      await signIn();
    },
  );

  const createAccountCommand = vscode.commands.registerCommand(
    "code-coach-vscode.createAccount",
    async () => {
      await createAccount();
    },
  );

  const signOutCommand = vscode.commands.registerCommand(
    "code-coach-vscode.signOut",
    async () => {
      await signOut();
    },
  );

  const analyzeCommand = vscode.commands.registerCommand(
    "code-coach-vscode.analyzeCurrentFile",
    async () => {
      const editor = vscode.window.activeTextEditor;

      if (!editor) {
        vscode.window.showErrorMessage("No active editor found.");
        return;
      }

      clearTimerForUri(editor.document.uri);

      await runAnalysisForEditor(editor, {
        showPopup: true,
        showOutput: true,
      });
    },
  );

  const previousHintCommand = vscode.commands.registerCommand(
    "code-coach-vscode.previousHint",
    () => {
      showHintForActiveEditor(-1);
    },
  );

  const nextHintCommand = vscode.commands.registerCommand(
    "code-coach-vscode.nextHint",
    () => {
      showHintForActiveEditor(1);
    },
  );

  const onDidChangeTextDocument = vscode.workspace.onDidChangeTextDocument(
    (event) => {
      if (event.contentChanges.length === 0) {
        return;
      }

      const activeEditor = vscode.window.activeTextEditor;
      if (!activeEditor) {
        return;
      }

      if (
        activeEditor.document.uri.toString() !== event.document.uri.toString()
      ) {
        return;
      }

      scheduleAutoAnalysis(activeEditor);
    },
  );

  const onDidChangeActiveEditor = vscode.window.onDidChangeActiveTextEditor(
    (editor) => {
      if (!editor) {
        return;
      }

      scheduleAutoAnalysis(editor);
    },
  );

  const onDidCloseTextDocument = vscode.workspace.onDidCloseTextDocument(
    (document) => {
      clearFeedbackForDocument(document);
    },
  );

  updateAuthStatusBar();
  void restoreAuthSession();

  const initialEditor = vscode.window.activeTextEditor;
  if (initialEditor) {
    scheduleAutoAnalysis(initialEditor);
  }

  context.subscriptions.push(
    startCommand,
    signInCommand,
    createAccountCommand,
    signOutCommand,
    analyzeCommand,
    previousHintCommand,
    nextHintCommand,
    outputChannel,
    diagnosticCollection,
    warningDecorationType,
    authStatusBar,
    onDidChangeTextDocument,
    onDidChangeActiveEditor,
    onDidCloseTextDocument,
  );
}

export function deactivate() {}
