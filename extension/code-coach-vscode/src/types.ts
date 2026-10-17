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
  /** Plain-words name of the mistake (backends from 0.3 on). */
  title?: string;
  /** Where the flagged code ends, 1-based, when the backend knows it. */
  end_line?: number;
  end_column?: number;
};

/** The answer to "Explain in my code" or "Explain this error". */
export type ExplanationResponse = {
  status: string;
  explanation: string;
  /** "llm" (written for this code), "cache" (written earlier) or "template". */
  source: string;
  remaining_today: number;
  daily_limit: number;
  limit_reached: boolean;
};

export type WorkedExample = {
  title: string;
  buggy?: string;
  fixed?: string;
  code?: string;
  note?: string;
};

export type SimilarExampleResponse = {
  error_type: string;
  title: string;
  examples: WorkedExample[];
  course_path: string;
  source: string;
};

type CardMetrics = { precision: number; recall: number; f1: number; average_precision?: number };

/** How one error type's model was trained and tested (GET /model-cards/{type}). */
export type ModelCard = {
  error_type: string;
  title: string;
  detects: string;
  considers: string;
  example: { mistake: string; lookalike: string };
  model: { family_name: string; threshold: number; threshold_rule: string; feature_count: number; top_features: string[] };
  training_data: {
    description: string;
    split: string;
    training_sites: number;
    training_mistakes: number;
    test_sites: number;
    test_mistakes: number;
  };
  performance: {
    test: CardMetrics;
    previous: Partial<CardMetrics> & { name: string };
    codebert: CardMetrics | null;
    human_code: { flags: number; real: number; plausible: number; wrong: number };
    curated: { snippets: number; mistakes: number; precision: number; recall: number; false_alarms: number } | null;
  };
  unreliable_when: string[];
  limitations: string[];
  general_limitations: string[];
  in_use: boolean;
};

/** What the panel shows under a finding after the student asks for it. */
export type AssistEntry = {
  kind: "explanation" | "example" | "compiler" | "card";
  loading?: boolean;
  text?: string;
  source?: string;
  remaining?: number;
  limit?: number;
  limitReached?: boolean;
  example?: SimilarExampleResponse;
  card?: ModelCard;
  /** For a compiler error: its message and line. */
  message?: string;
  line?: number;
  error?: string;
};

/** A compiler error VS Code's Java extension reported for the open file. */
export type CompilerProblem = {
  message: string;
  line: number;
  source?: string;
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
  /** document.version at analysis time — lets tab switches reuse cached results. */
  documentVersion?: number;
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
  /** The file the panel is about, for its compiler errors. */
  fileUriKey?: string;
};

export class ApiError extends Error {
  readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

import { CoachSidebarProvider } from "./ui/sidebarProvider";
import { CoachCodeLensProvider } from "./ui/codeLensProvider";

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
  /**
   * The furthest hint level the student has opened, per diagnostic_id. The
   * concept hint is always shown; guidance and targeted wait until asked for,
   * one at a time. Keyed by the finding's id, which stays the same while the
   * rest of the file is edited, so re-analysis does not hide what was opened.
   */
  revealedHintLevels: Map<string, "concept" | "guidance" | "targeted">;
  debounceTimers: Map<string, ReturnType<typeof setTimeout>>;
  activeAnalysisUriKey: string | undefined;
  /**
   * Last Java file the user worked in. Webview clicks steal focus and make
   * vscode.window.activeTextEditor undefined, so panel state and hint
   * navigation fall back to this instead of going blank / no-op.
   */
  lastSupportedUriKey: string | undefined;
  /** Cache of the last HTML pushed to the coach panel — skip identical reassigns. */
  lastPanelHtml: string | undefined;
  /**
   * diagnostic_ids the user reported as false positives this session — used
   * to flip the report button to "Reported ✓" and avoid duplicate events.
   */
  disputedDiagnosticIds: Set<string>;
  /**
   * Explanations and worked examples the student asked for, keyed by
   * "explain:<diagnostic_id>", "example:<diagnostic_id>" or
   * "compiler:<line>:<message>", so re-analysis while the student reads does
   * not throw them away.
   */
  assistByKey: Map<string, AssistEntry>;
  /** Findings that went away after an edit, this session - "Fixed it!". */
  fixedThisSession: number;
  lastFix?: { title: string; at: number };
  /** Set when the backend could not be reached, cleared on the next success. */
  backendOffline: boolean;
  issuesTreeProvider: { refresh(): void } | undefined;
  coachPanel: vscode.WebviewPanel | undefined;
  sidebarProvider: CoachSidebarProvider | undefined;
  codeLensProvider: CoachCodeLensProvider | undefined;
  outputChannel: vscode.OutputChannel;
  diagnosticCollection: vscode.DiagnosticCollection;
  warningDecorationType: vscode.TextEditorDecorationType;
  authStatusBar: vscode.StatusBarItem;
  analysisStatusBar: vscode.StatusBarItem;
  context: vscode.ExtensionContext;
};
