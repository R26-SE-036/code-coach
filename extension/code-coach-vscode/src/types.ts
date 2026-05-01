import * as vscode from "vscode";

export type HintSet = {
  concept: string;
  guidance: string;
  targeted: string;
};

export type DiagnosticItem = {
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

export type AnalyzeResponse = {
  status: string;
  message: string;
  timestamp: string;
  analysis_duration_ms: number;
  learning_session_id?: string;
  diagnostics: DiagnosticItem[];
};

export type AuthUser = {
  user_id: string;
  full_name: string;
  email: string;
  student_number: string;
  role: string;
  status: string;
  created_at: string;
};

export type AuthSession = {
  auth_session_id: string;
  client_name: string;
  status: string;
  created_at: string;
  last_seen_at: string;
  expires_at: string;
};

export type TokenBundle = {
  token_type: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
};

export type AuthResponse = {
  status: string;
  message: string;
  user: AuthUser;
  auth_session: AuthSession;
  tokens: TokenBundle;
};

export type MeResponse = {
  status: string;
  user: AuthUser;
  auth_session: AuthSession;
};

export type LearningSessionResponse = {
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

export type LearningEventCreateResponse = {
  status: string;
  message: string;
  event_id: string;
};

export type LearningEventRequest = {
  learning_session_id: string;
  component?: string;
  event_type: string;
  concept_tag?: string;
  occurred_at?: string;
  payload: Record<string, unknown>;
};

export type AnalysisSnapshot = {
  diagnosticsCount: number;
  analysisDurationMs: number;
  analyzedAt: string;
  firstMessage?: string;
  firstLine?: number;
  learningSessionId?: string;
};

export type CoachPanelState = {
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

export class ApiError extends Error {
  readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

/**
 * Shared mutable state passed by reference across all modules.
 * Replaces the closure-captured locals from the original monolithic activate().
 */
export type ExtensionState = {
  currentUser: AuthUser | undefined;
  currentLearningSessionId: string | undefined;
  lastDiagnosticsByUri: Map<string, DiagnosticItem[]>;
  lastAnalysisSnapshotByUri: Map<string, AnalysisSnapshot>;
  activeHintIndexByUri: Map<string, number>;
  debounceTimers: Map<string, ReturnType<typeof setTimeout>>;
  activeAnalysisUriKey: string | undefined;
  coachPanel: vscode.WebviewPanel | undefined;
  outputChannel: vscode.OutputChannel;
  diagnosticCollection: vscode.DiagnosticCollection;
  warningDecorationType: vscode.TextEditorDecorationType;
  authStatusBar: vscode.StatusBarItem;
  analysisStatusBar: vscode.StatusBarItem;
  context: vscode.ExtensionContext;
};
