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

type LearningEventCreateResponse = {
  status: string;
  message: string;
  event_id: string;
};

type LearningEventRequest = {
  learning_session_id: string;
  component?: string;
  event_type: string;
  concept_tag?: string;
  occurred_at?: string;
  payload: Record<string, unknown>;
};

type AnalysisSnapshot = {
  diagnosticsCount: number;
  analysisDurationMs: number;
  analyzedAt: string;
  firstMessage?: string;
  firstLine?: number;
  learningSessionId?: string;
};

type CoachPanelState = {
  signedIn: boolean;
  userLabel?: string;
  fileLabel?: string;
  isSupportedFile: boolean;
  diagnostics: DiagnosticItem[];
  activeIndex: number;
  activeDiagnostic?: DiagnosticItem;
  snapshot?: AnalysisSnapshot;
  learningSessionId?: string;
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
  const analysisStatusBar = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    99,
  );
  analysisStatusBar.name = "Code Coach Analysis";
  analysisStatusBar.command = "code-coach-vscode.analyzeCurrentFile";

  const warningDecorationType = vscode.window.createTextEditorDecorationType({
    backgroundColor: "rgba(255, 215, 0, 0.18)",
    border: "1px solid rgba(255, 215, 0, 0.45)",
    borderRadius: "3px",
  });

  const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();
  const lastDiagnosticsByUri = new Map<string, DiagnosticItem[]>();
  const lastAnalysisSnapshotByUri = new Map<string, AnalysisSnapshot>();
  const activeHintIndexByUri = new Map<string, number>();
  const debounceDelayMs = 900;
  let activeAnalysisUriKey: string | undefined;
  let coachPanel: vscode.WebviewPanel | undefined;

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

  function escapeHtml(value: string): string {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatProbability(value?: number): string {
    if (value === undefined) {
      return "n/a";
    }

    return `${Math.round(value * 100)}%`;
  }

  function getCoachPanelState(): CoachPanelState {
    const editor = vscode.window.activeTextEditor;
    const isSupportedFile = !!editor && isSupportedDocument(editor.document);

    if (!editor || !isSupportedFile) {
      return {
        signedIn: !!currentUser,
        userLabel: currentUser?.full_name,
        isSupportedFile: false,
        diagnostics: [],
        activeIndex: 0,
      };
    }

    const uriKey = editor.document.uri.toString();
    const diagnostics = lastDiagnosticsByUri.get(uriKey) ?? [];
    const activeIndex = Math.min(
      activeHintIndexByUri.get(uriKey) ?? 0,
      Math.max(0, diagnostics.length - 1),
    );

    return {
      signedIn: !!currentUser,
      userLabel: currentUser?.full_name,
      fileLabel: vscode.workspace.asRelativePath(editor.document.uri, false),
      isSupportedFile: true,
      diagnostics,
      activeIndex,
      activeDiagnostic: diagnostics[activeIndex],
      snapshot: lastAnalysisSnapshotByUri.get(uriKey),
      learningSessionId: currentLearningSessionId,
    };
  }

  function buildCoachPanelHtml(): string {
    const state = getCoachPanelState();
    const active = state.activeDiagnostic;
    const issueCount = state.diagnostics.length;
    const hasIssues = issueCount > 0;
    const hintIndexLabel = hasIssues
      ? `${state.activeIndex + 1}/${issueCount}`
      : "0/0";
    const sessionLabel = state.learningSessionId ?? state.snapshot?.learningSessionId ?? "n/a";

    const issueCard = !state.signedIn
      ? `
        <div class="empty-state">
          <h2>Sign in to use Code Coach</h2>
          <p>Sign in to analyze Java files, save learning sessions, and keep your progress connected to the platform.</p>
          <div class="actions">
            <button data-command="signIn">Sign In</button>
            <button class="secondary" data-command="createAccount">Create Account</button>
          </div>
        </div>
      `
      : !state.isSupportedFile
        ? `
          <div class="empty-state">
            <h2>Open a Java file</h2>
            <p>Code Coach works on Java files. Open one to analyze it and see targeted hints here.</p>
          </div>
        `
        : !state.snapshot
          ? `
            <div class="empty-state">
              <h2>Analyze the current file</h2>
              <p>Run Code Coach to see the current issue summary, concept hint, guidance hint, and targeted hint.</p>
              <div class="actions">
                <button data-command="analyze">Analyze Current File</button>
              </div>
            </div>
          `
          : issueCount === 0
            ? `
              <div class="empty-state good">
                <h2>No target issues detected</h2>
                <p>Code Coach did not detect any of the current target beginner issues in this file.</p>
                <div class="meta-grid">
                  <div><span>Last analysis</span><strong>${escapeHtml(formatDuration(state.snapshot.analysisDurationMs))}</strong></div>
                  <div><span>Learning session</span><strong>${escapeHtml(sessionLabel)}</strong></div>
                </div>
                <div class="actions">
                  <button data-command="analyze">Analyze Again</button>
                  <button class="secondary" data-command="openOutput">Open Output</button>
                </div>
              </div>
            `
            : `
              <div class="issue-card">
                <div class="issue-header">
                  <div>
                    <div class="eyebrow">Current issue ${escapeHtml(hintIndexLabel)}</div>
                    <h2>${escapeHtml(active?.error_type ?? "Issue")}</h2>
                  </div>
                  <div class="pill">${escapeHtml(active?.severity ?? "warning")}</div>
                </div>
                <p class="message">${escapeHtml(active?.message ?? "")}</p>
                <div class="meta-grid">
                  <div><span>Line</span><strong>${escapeHtml(String(active?.line ?? "n/a"))}</strong></div>
                  <div><span>Concept</span><strong>${escapeHtml(active?.concept_tag ?? "n/a")}</strong></div>
                  <div><span>ML</span><strong>${escapeHtml(formatProbability(active?.ml_probability))}</strong></div>
                  <div><span>Locator</span><strong>${escapeHtml(formatProbability(active?.locator_confidence))}</strong></div>
                </div>
                <div class="hint-block">
                  <h3>Concept Hint</h3>
                  <p>${escapeHtml(active?.hints.concept ?? "")}</p>
                </div>
                <div class="hint-block">
                  <h3>Guidance Hint</h3>
                  <p>${escapeHtml(active?.hints.guidance ?? "")}</p>
                </div>
                <div class="hint-block">
                  <h3>Targeted Hint</h3>
                  <p>${escapeHtml(active?.hints.targeted ?? "")}</p>
                </div>
                <div class="actions">
                  <button data-command="previousHint">Previous</button>
                  <button data-command="nextHint">Next</button>
                  <button class="secondary" data-command="revealIssue">Reveal in Editor</button>
                  <button class="secondary" data-command="openOutput">Open Output</button>
                </div>
              </div>
            `;

    return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Code Coach Panel</title>
    <style>
      :root {
        color-scheme: light dark;
      }
      body {
        font-family: var(--vscode-font-family);
        color: var(--vscode-foreground);
        background: var(--vscode-editor-background);
        margin: 0;
        padding: 16px;
      }
      h1, h2, h3, p {
        margin: 0;
      }
      .page {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .summary {
        border: 1px solid var(--vscode-panel-border);
        border-radius: 8px;
        padding: 14px;
        background: color-mix(in srgb, var(--vscode-editor-background) 90%, var(--vscode-button-background) 10%);
      }
      .summary h1 {
        font-size: 16px;
        margin-bottom: 6px;
      }
      .summary p {
        font-size: 12px;
        color: var(--vscode-descriptionForeground);
      }
      .issue-card, .empty-state {
        border: 1px solid var(--vscode-panel-border);
        border-radius: 8px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .good {
        border-color: color-mix(in srgb, var(--vscode-terminal-ansiGreen) 50%, var(--vscode-panel-border) 50%);
      }
      .issue-header {
        display: flex;
        justify-content: space-between;
        gap: 12px;
      }
      .eyebrow {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--vscode-descriptionForeground);
        margin-bottom: 6px;
      }
      .message {
        line-height: 1.45;
      }
      .pill {
        align-self: flex-start;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 11px;
        background: color-mix(in srgb, var(--vscode-editorWarning-foreground) 16%, transparent);
        color: var(--vscode-foreground);
      }
      .meta-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .meta-grid div {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 10px;
        border-radius: 6px;
        background: color-mix(in srgb, var(--vscode-editor-background) 82%, var(--vscode-sideBar-background) 18%);
      }
      .meta-grid span {
        font-size: 11px;
        color: var(--vscode-descriptionForeground);
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }
      .meta-grid strong {
        font-size: 13px;
      }
      .hint-block {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 10px 12px;
        border-left: 3px solid var(--vscode-button-background);
        background: color-mix(in srgb, var(--vscode-editor-background) 88%, var(--vscode-button-background) 12%);
      }
      .hint-block h3 {
        font-size: 12px;
      }
      .hint-block p {
        line-height: 1.45;
        color: var(--vscode-foreground);
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      button {
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        background: var(--vscode-button-background);
        color: var(--vscode-button-foreground);
        cursor: pointer;
        font: inherit;
      }
      button:hover {
        background: var(--vscode-button-hoverBackground);
      }
      button.secondary {
        background: color-mix(in srgb, var(--vscode-button-background) 20%, transparent);
        color: var(--vscode-foreground);
        border: 1px solid var(--vscode-panel-border);
      }
      .footer-note {
        font-size: 11px;
        color: var(--vscode-descriptionForeground);
      }
    </style>
  </head>
  <body>
    <div class="page">
      <section class="summary">
        <h1>Code Coach</h1>
        <p>${escapeHtml(
          state.signedIn
            ? `Signed in as ${state.userLabel ?? "student"}`
            : "Not signed in",
        )}</p>
        <p>${escapeHtml(
          state.fileLabel
            ? `Current file: ${state.fileLabel}`
            : "Open a Java file to work with Code Coach.",
        )}</p>
      </section>
      ${issueCard}
      <div class="footer-note">
        Learning session: ${escapeHtml(sessionLabel)}
      </div>
    </div>
    <script>
      const vscode = acquireVsCodeApi();
      for (const element of document.querySelectorAll("[data-command]")) {
        element.addEventListener("click", () => {
          const command = element.getAttribute("data-command");
          if (command) {
            vscode.postMessage({ command });
          }
        });
      }
    </script>
  </body>
</html>`;
  }

  function updateCoachPanel() {
    if (!coachPanel) {
      return;
    }

    coachPanel.title = "Code Coach";
    coachPanel.webview.html = buildCoachPanelHtml();
  }

  function getSupportedActiveEditor(): vscode.TextEditor | undefined {
    const editor = vscode.window.activeTextEditor;
    return editor && isSupportedDocument(editor.document) ? editor : undefined;
  }

  function openCoachPanel() {
    if (coachPanel) {
      coachPanel.reveal(vscode.ViewColumn.Beside, true);
      updateCoachPanel();
      return;
    }

    coachPanel = vscode.window.createWebviewPanel(
      "codeCoachPanel",
      "Code Coach",
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      },
    );

    coachPanel.onDidDispose(() => {
      coachPanel = undefined;
    });

    coachPanel.webview.onDidReceiveMessage((message: { command?: string }) => {
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
          outputChannel.show(true);
          break;
        case "revealIssue": {
          const editor = getSupportedActiveEditor();
          if (!editor) {
            break;
          }
          const diagnostics =
            lastDiagnosticsByUri.get(editor.document.uri.toString()) ?? [];
          const currentIndex =
            activeHintIndexByUri.get(editor.document.uri.toString()) ?? 0;
          const diagnostic = diagnostics[currentIndex];
          if (diagnostic) {
            focusDiagnostic(editor, diagnostic);
          }
          break;
        }
        default:
          break;
      }
    });

    updateCoachPanel();
  }

  function formatDuration(durationMs: number): string {
    if (durationMs >= 1000) {
      return `${(durationMs / 1000).toFixed(2)} s`;
    }

    return `${Math.round(durationMs)} ms`;
  }

  function updateAnalysisStatusBar(
    editor: vscode.TextEditor | undefined = vscode.window.activeTextEditor,
  ) {
    if (!currentUser) {
      analysisStatusBar.text = "$(lock) Sign In for Code Coach";
      analysisStatusBar.tooltip =
        "Sign in to analyze Java files and save your progress.";
      analysisStatusBar.command = "code-coach-vscode.signIn";
      analysisStatusBar.show();
      updateCoachPanel();
      return;
    }

    if (!editor || !isSupportedDocument(editor.document)) {
      analysisStatusBar.text = "$(beaker) Code Coach Ready";
      analysisStatusBar.tooltip =
        "Open a Java file to analyze it with Code Coach.";
      analysisStatusBar.command = "code-coach-vscode.analyzeCurrentFile";
      analysisStatusBar.show();
      updateCoachPanel();
      return;
    }

    const uriKey = editor.document.uri.toString();
    const snapshot = lastAnalysisSnapshotByUri.get(uriKey);

    analysisStatusBar.command = "code-coach-vscode.analyzeCurrentFile";

    if (activeAnalysisUriKey === uriKey) {
      analysisStatusBar.text = "$(sync~spin) Code Coach Analyzing";
      analysisStatusBar.tooltip =
        "Code Coach is analyzing the current Java file.";
      analysisStatusBar.show();
      updateCoachPanel();
      return;
    }

    if (!snapshot) {
      analysisStatusBar.text = "$(search) Analyze Java File";
      analysisStatusBar.tooltip =
        "Run Code Coach on the current Java file.";
      analysisStatusBar.show();
      updateCoachPanel();
      return;
    }

    if (snapshot.diagnosticsCount === 0) {
      analysisStatusBar.text = "$(check) Code Coach Clean";
      analysisStatusBar.tooltip =
        `No target issues detected. Last analysis took ${formatDuration(snapshot.analysisDurationMs)}.`;
      analysisStatusBar.show();
      updateCoachPanel();
      return;
    }

    const issueLabel =
      snapshot.diagnosticsCount === 1 ? "issue" : "issues";
    analysisStatusBar.text =
      `$(warning) Code Coach ${snapshot.diagnosticsCount} ${issueLabel}`;
    analysisStatusBar.tooltip =
      `${snapshot.firstMessage ?? "Issues detected."} ` +
      `Line ${snapshot.firstLine ?? "n/a"}. ` +
      `Last analysis took ${formatDuration(snapshot.analysisDurationMs)}.`;
    analysisStatusBar.show();
    updateCoachPanel();
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
    updateAnalysisStatusBar(editor);
  }

  function clearFeedbackForDocument(
    document: vscode.TextDocument,
    options?: { preserveAnalysisSnapshot?: boolean },
  ) {
    clearTimerForUri(document.uri);
    diagnosticCollection.delete(document.uri);
    const uriKey = document.uri.toString();
    lastDiagnosticsByUri.delete(uriKey);
    activeHintIndexByUri.delete(uriKey);
    if (!options?.preserveAnalysisSnapshot) {
      lastAnalysisSnapshotByUri.delete(uriKey);
    }

    const activeEditor = vscode.window.activeTextEditor;
    if (
      activeEditor &&
      activeEditor.document.uri.toString() === uriKey
    ) {
      activeEditor.setDecorations(warningDecorationType, []);
      updateAnalysisStatusBar(activeEditor);
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
    lastAnalysisSnapshotByUri.clear();
    activeHintIndexByUri.clear();
    clearEditorFeedback(vscode.window.activeTextEditor);
    updateAuthStatusBar();
    updateAnalysisStatusBar();
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
    updateAnalysisStatusBar();
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
      updateAnalysisStatusBar();
      return false;
    }

    try {
      const me = await authorizedRequestJson<MeResponse>("/api/v1/auth/me", {
        method: "GET",
      });
      currentUser = me.user;
      await context.globalState.update(USER_STATE_KEY, me.user);
      updateAuthStatusBar();
      updateAnalysisStatusBar();
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

  async function createLearningEvent(
    event: LearningEventRequest,
  ): Promise<LearningEventCreateResponse> {
    return authorizedRequestJson<LearningEventCreateResponse>("/api/v1/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        learning_session_id: event.learning_session_id,
        component: event.component ?? "code_coach",
        event_type: event.event_type,
        concept_tag: event.concept_tag,
        occurred_at: event.occurred_at,
        payload: event.payload,
      }),
    });
  }

  function trackLearningEvent(event: LearningEventRequest) {
    if (!currentUser) {
      return;
    }

    void createLearningEvent(event).catch((error) => {
      console.error("Code Coach learning event tracking failed:", error);
    });
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
    updateAnalysisStatusBar(editor);
  }

  function focusDiagnostic(
    editor: vscode.TextEditor,
    diagnostic: DiagnosticItem,
  ): vscode.Range {
    const range = createRangeFromDiagnostic(editor.document, diagnostic);
    editor.selection = new vscode.Selection(range.start, range.start);
    editor.revealRange(
      range,
      vscode.TextEditorRevealType.InCenterIfOutsideViewport,
    );
    return range;
  }

  function hintTextForLevel(
    diagnostic: DiagnosticItem,
    level: "concept" | "guidance" | "targeted",
  ): string {
    switch (level) {
      case "guidance":
        return diagnostic.hints.guidance;
      case "targeted":
        return diagnostic.hints.targeted;
      default:
        return diagnostic.hints.concept;
    }
  }

  async function showHintAtIndex(
    editor: vscode.TextEditor,
    diagnostics: DiagnosticItem[],
    index: number,
    options: {
      level: "concept" | "guidance" | "targeted";
      navigationDirection?: "next" | "previous";
      sourceCommand: string;
    },
  ) {
    const diagnostic = diagnostics[index];
    if (!diagnostic) {
      return;
    }

    const uriKey = editor.document.uri.toString();
    activeHintIndexByUri.set(uriKey, index);
    focusDiagnostic(editor, diagnostic);
    updateCoachPanel();

    const hintText = hintTextForLevel(diagnostic, options.level);
    const levelLabel =
      options.level.charAt(0).toUpperCase() + options.level.slice(1);

    await vscode.window.showInformationMessage(
      `Code Coach ${levelLabel.toLowerCase()} hint ${index + 1}/${diagnostics.length}: ${hintText}`,
    );

    if (!currentLearningSessionId) {
      return;
    }

    const occurredAt = new Date().toISOString();

    if (options.navigationDirection) {
      trackLearningEvent({
        learning_session_id: currentLearningSessionId,
        event_type: "hint_navigation_used",
        concept_tag: diagnostic.concept_tag,
        occurred_at: occurredAt,
        payload: {
          diagnostic_id: diagnostic.diagnostic_id,
          error_type: diagnostic.error_type,
          explanation_key: diagnostic.explanation_key,
          hint_level: options.level,
          direction: options.navigationDirection,
          shown_index: index + 1,
          total_diagnostics: diagnostics.length,
          source_command: options.sourceCommand,
        },
      });
    }

    trackLearningEvent({
      learning_session_id: currentLearningSessionId,
      event_type: "hint_level_requested",
      concept_tag: diagnostic.concept_tag,
      occurred_at: occurredAt,
      payload: {
        diagnostic_id: diagnostic.diagnostic_id,
        error_type: diagnostic.error_type,
        explanation_key: diagnostic.explanation_key,
        hint_level: options.level,
        hint_text: hintText,
        surface: "info_message",
        source_command: options.sourceCommand,
      },
    });
  }

  function writeAnalysisOutput(result: AnalyzeResponse) {
    outputChannel.clear();
    outputChannel.appendLine("=== Code Coach Analysis Result ===");
    outputChannel.appendLine(`Status           : ${result.status}`);
    outputChannel.appendLine(`Message          : ${result.message}`);
    outputChannel.appendLine(`Timestamp        : ${result.timestamp}`);
    outputChannel.appendLine(
      `Analysis time    : ${formatDuration(result.analysis_duration_ms)}`,
    );
    outputChannel.appendLine(
      `Learning session : ${result.learning_session_id ?? "n/a"}`,
    );
    outputChannel.appendLine(`User             : ${currentUser?.email ?? "n/a"}`);
    outputChannel.appendLine(
      `Detected issues  : ${result.diagnostics.length}`,
    );
    outputChannel.appendLine("");

    if (result.diagnostics.length === 0) {
      outputChannel.appendLine("No target issues detected.");
      return;
    }

    result.diagnostics.forEach((diagnostic, index) => {
      outputChannel.appendLine(
        `Issue ${index + 1}: ${diagnostic.error_type} (Line ${diagnostic.line}, Column ${diagnostic.column})`,
      );
      outputChannel.appendLine(`  Message   : ${diagnostic.message}`);
      outputChannel.appendLine(`  Concept   : ${diagnostic.hints.concept}`);
      outputChannel.appendLine(`  Guidance  : ${diagnostic.hints.guidance}`);
      outputChannel.appendLine(`  Targeted  : ${diagnostic.hints.targeted}`);
      outputChannel.appendLine(
        `  Confidence: ${diagnostic.confidence} | ML: ${diagnostic.ml_probability ?? "n/a"} | Locator: ${diagnostic.locator_confidence ?? "n/a"}`,
      );
      outputChannel.appendLine("");
    });
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
          outputChannel.show(true);
          outputChannel.appendLine("The current file is empty.");
        }

      return;
    }

    try {
      activeAnalysisUriKey = document.uri.toString();
      updateAnalysisStatusBar(editor);

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

      lastAnalysisSnapshotByUri.set(document.uri.toString(), {
        diagnosticsCount: result.diagnostics.length,
        analysisDurationMs: result.analysis_duration_ms,
        analyzedAt: result.timestamp,
        firstMessage: result.diagnostics[0]?.message,
        firstLine: result.diagnostics[0]?.line,
        learningSessionId: result.learning_session_id ?? learningSessionId,
      });

      if (options.showOutput) {
        writeAnalysisOutput(result);
        outputChannel.show(true);
      }

      if (result.diagnostics.length === 0) {
        clearFeedbackForDocument(document, { preserveAnalysisSnapshot: true });

        if (options.showPopup) {
          void vscode.window
            .showInformationMessage(
              "Code Coach did not detect any of the current target issues in this file.",
              "Open Output",
              "Open Coach Panel",
            )
            .then((action) => {
              if (action === "Open Output") {
                outputChannel.show(true);
              } else if (action === "Open Coach Panel") {
                openCoachPanel();
              }
            });
        }

        return;
      }

      applyEditorFeedback(editor, result.diagnostics);

      if (options.showPopup) {
        const firstDiagnostic = result.diagnostics[0];

        trackLearningEvent({
          learning_session_id:
            result.learning_session_id ?? learningSessionId,
          event_type: "hint_shown",
          concept_tag: firstDiagnostic.concept_tag,
          occurred_at: new Date().toISOString(),
          payload: {
            diagnostic_id: firstDiagnostic.diagnostic_id,
            error_type: firstDiagnostic.error_type,
            explanation_key: firstDiagnostic.explanation_key,
            hint_level: "concept",
            hint_text: firstDiagnostic.hints.concept,
            surface: "warning_popup",
            trigger: "manual_analysis_results",
          },
        });

        void vscode.window
          .showWarningMessage(
            `Code Coach found ${result.diagnostics.length} issue(s). First issue on line ${firstDiagnostic.line}: ${firstDiagnostic.message}`,
            "Go to First Issue",
            "Show Guidance Hint",
            "Open Coach Panel",
            "Open Output",
          )
          .then((action) => {
            if (action === "Go to First Issue") {
              focusDiagnostic(editor, firstDiagnostic);
            } else if (action === "Show Guidance Hint") {
              void showHintAtIndex(editor, result.diagnostics, 0, {
                level: "guidance",
                sourceCommand: "analysis_popup",
              });
            } else if (action === "Open Coach Panel") {
              openCoachPanel();
            } else if (action === "Open Output") {
              outputChannel.show(true);
            }
          });
      }
    } catch (error) {
      clearFeedbackForDocument(document);

      const message =
        error instanceof Error ? error.message : "Unknown error occurred.";

      if (options.showPopup) {
        vscode.window.showErrorMessage(`Code Coach error: ${message}`);
      }

      console.error("Code Coach analyze error:", error);
    } finally {
      if (activeAnalysisUriKey === document.uri.toString()) {
        activeAnalysisUriKey = undefined;
      }
      updateAnalysisStatusBar(editor);
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
    void showHintAtIndex(editor, diagnostics, nextIndex, {
      level: "guidance",
      navigationDirection: direction === 1 ? "next" : "previous",
      sourceCommand: direction === 1 ? "next_hint" : "previous_hint",
    });
  }

  const startCommand = vscode.commands.registerCommand(
    "code-coach-vscode.start",
    () => {
      const action = currentUser
        ? "Analyze Current File"
        : "Sign In";
      void vscode.window
        .showInformationMessage(
          currentUser
            ? "Code Coach is ready. Use it on the current Java file."
            : "Code Coach is ready. Sign in to analyze code and save progress.",
          action,
          "Open Coach Panel",
        )
        .then((selected) => {
          if (selected === "Analyze Current File") {
            void vscode.commands.executeCommand(
              "code-coach-vscode.analyzeCurrentFile",
            );
          } else if (selected === "Sign In") {
            void vscode.commands.executeCommand("code-coach-vscode.signIn");
          } else if (selected === "Open Coach Panel") {
            openCoachPanel();
          }
        });
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
        vscode.window.showErrorMessage("Open a Java file to analyze it with Code Coach.");
        return;
      }

      clearTimerForUri(editor.document.uri);

      await runAnalysisForEditor(editor, {
        showPopup: true,
        showOutput: true,
      });
    },
  );

  const openCoachPanelCommand = vscode.commands.registerCommand(
    "code-coach-vscode.openCoachPanel",
    () => {
      openCoachPanel();
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
      updateAnalysisStatusBar(editor);
    },
  );

  const onDidCloseTextDocument = vscode.workspace.onDidCloseTextDocument(
    (document) => {
      clearFeedbackForDocument(document);
    },
  );

  updateAuthStatusBar();
  updateAnalysisStatusBar();
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
    openCoachPanelCommand,
    previousHintCommand,
    nextHintCommand,
    outputChannel,
    diagnosticCollection,
    warningDecorationType,
    authStatusBar,
    analysisStatusBar,
    onDidChangeTextDocument,
    onDidChangeActiveEditor,
    onDidCloseTextDocument,
  );
}

export function deactivate() {}
