/**
 * Auth workflows + learning-session lifecycle + learning-event tracking.
 *
 * This file owns the "who is the user and what session are they in" side of the
 * extension. Three groups of functions:
 *   1. Identity   — createAccount / signIn / signOut / restoreAuthSession /
 *                   ensureAuthenticated. These drive the input-box prompts and
 *                   then call the /api/v1/auth/* endpoints.
 *   2. Session    — ensureLearningSession lazily creates a learning session so
 *                   the backend can group a student's diagnostics over time.
 *   3. Telemetry  — trackLearningEvent / createLearningEvent fire /api/v1/events
 *                   whenever the student sees or navigates a hint.
 *
 * How it splits work with api.ts:
 *   - api.ts does the actual HTTP + token storage (requestJson,
 *     authorizedRequestJson, storeAuthResponse, clearStoredAuthState).
 *   - auth.ts orchestrates WHEN to call them and what to prompt the user for.
 *
 * Callers: extension.ts commands (Sign In / Create Account / Sign Out) and
 * analysis.ts (ensureAuthenticated + ensureLearningSession before an analyze,
 * trackLearningEvent after a hint). The scheduleAutoAnalysis import re-kicks
 * analysis right after a successful login so feedback appears immediately.
 */
import * as vscode from "vscode";
import {
  AuthResponse,
  ExtensionState,
  LearningEventCreateResponse,
  LearningEventRequest,
  LearningSessionResponse,
  MeResponse,
} from "./types";
import { CLIENT_NAME, USER_STATE_KEY } from "./constants";
import {
  authorizedRequestJson,
  clearLearningSession,
  clearStoredAuthState,
  requestJson,
  storeAuthResponse,
} from "./api";
import { signInThroughBrowser } from "./browserAuth";
import { updateAuthStatusBar, updateAnalysisStatusBar } from "./ui/statusBar";
import { scheduleAutoAnalysis } from "./analysis";

// ── Prompt helper ──

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

// ── Browser sign-in ──

// What happens when the student runs Sign In or Create Account.
//
// Code Coach was the only service in the platform where a password was typed
// into the app itself; the other three sign in on the web through the Code Guru
// portal. This routes the extension to the same place, and only falls back to
// the old prompts when the browser round trip genuinely cannot be used.
type BrowserOutcome = "signed-in" | "cancelled" | "fallback";

async function tryBrowserSignIn(
  state: ExtensionState,
  mode: "login" | "register",
): Promise<BrowserOutcome> {
  // A remote/SSH/WSL window runs the extension host on the other machine, so a
  // loopback listener there is not the loopback the local browser would reach.
  // Rather than half-work, hand straight back to the prompts.
  if (vscode.env.remoteName) {
    return "fallback";
  }

  try {
    const response = await signInThroughBrowser(state, mode);
    if (!response) {
      // Cancelled or timed out. The student made a choice; do not immediately
      // ask them for a password instead.
      return "cancelled";
    }

    vscode.window.showInformationMessage(
      mode === "register"
        ? `Welcome to Code Coach, ${response.user.full_name}.`
        : `Signed in to Code Coach as ${response.user.full_name}.`,
    );

    if (vscode.window.activeTextEditor) {
      scheduleAutoAnalysis(state, vscode.window.activeTextEditor);
    }
    return "signed-in";
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Browser sign-in failed.";
    state.outputChannel.appendLine(`Browser sign-in failed: ${message}`);
    vscode.window.showWarningMessage(
      `${message} Falling back to signing in here.`,
    );
    return "fallback";
  }
}

// ── Account creation ──

// Prompt for name/email/password, POST /api/v1/auth/register (via requestJson —
// no token exists yet), then hand the response to storeAuthResponse (api.ts) to
// persist tokens and set currentUser. Ends by kicking scheduleAutoAnalysis so
// the open file gets analyzed right away.
export async function createAccount(state: ExtensionState): Promise<void> {
  const outcome = await tryBrowserSignIn(state, "register");
  if (outcome !== "fallback") {
    return;
  }
  await createAccountWithPrompts(state);
}

// The original input-box flow, kept as the fallback for remote windows and for
// the case where the browser round trip cannot start at all.
async function createAccountWithPrompts(state: ExtensionState): Promise<void> {
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

    const password = await promptValue(
      {
        prompt: "Create a password (minimum 8 characters)",
        password: true,
      },
      { trim: false },
    );
    if (!password) {
      return;
    }

    const confirmPassword = await promptValue(
      {
        prompt: "Confirm your password",
        password: true,
      },
      { trim: false },
    );
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
        password,
        client_name: CLIENT_NAME,
      }),
    });

    await storeAuthResponse(state, response, { resetLearningSession: true });
    state.outputChannel.appendLine(`Signed in as ${response.user.email}`);
    vscode.window.showInformationMessage(
      `Welcome to Code Coach, ${response.user.full_name}.`,
    );

    if (vscode.window.activeTextEditor) {
      scheduleAutoAnalysis(state, vscode.window.activeTextEditor);
    }
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Account creation failed.";
    vscode.window.showErrorMessage(`Code Coach error: ${message}`);
  }
}

// ── Sign in ──

// Same shape as createAccount but hits /api/v1/auth/login with an existing
// identifier + password. storeAuthResponse then saves the returned tokens.
export async function signIn(state: ExtensionState): Promise<void> {
  const outcome = await tryBrowserSignIn(state, "login");
  if (outcome !== "fallback") {
    return;
  }
  await signInWithPrompts(state);
}

// The original input-box flow. See createAccountWithPrompts.
async function signInWithPrompts(state: ExtensionState): Promise<void> {
  try {
    const identifier = await promptValue({
      prompt: "Enter your email",
      placeHolder: "student@example.com",
    });
    if (!identifier) {
      return;
    }

    const password = await promptValue(
      {
        prompt: "Enter your password",
        password: true,
      },
      { trim: false },
    );
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

    await storeAuthResponse(state, response, { resetLearningSession: true });
    state.outputChannel.appendLine(`Signed in as ${response.user.email}`);
    vscode.window.showInformationMessage(
      `Signed in to Code Coach as ${response.user.full_name}.`,
    );

    if (vscode.window.activeTextEditor) {
      scheduleAutoAnalysis(state, vscode.window.activeTextEditor);
    }
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Sign in failed.";
    vscode.window.showErrorMessage(`Code Coach error: ${message}`);
  }
}

// ── Sign out ──

export async function signOut(state: ExtensionState): Promise<void> {
  try {
    if (state.currentUser) {
      await authorizedRequestJson<{ status: string; message: string }>(
        state,
        "/api/v1/auth/logout",
        {
          method: "POST",
        },
      );
    }
  } catch (error) {
    console.error("Code Coach logout error:", error);
  } finally {
    await clearStoredAuthState(state);
    vscode.window.showInformationMessage("Signed out from Code Coach.");
  }
}

// ── Session restore ──

// Silent re-login on startup: if tokens are already in secret storage, call
// /api/v1/auth/me to confirm they're still valid and rehydrate currentUser.
// Called once from extension.ts activate(), and again as a fallback inside
// ensureAuthenticated. authorizedRequestJson handles a stale access token by
// refreshing it under the hood, so a returning user usually skips the prompts.
export async function restoreAuthSession(
  state: ExtensionState,
): Promise<boolean> {
  const accessToken = await state.context.secrets.get("codeCoach.accessToken");
  const refreshToken = await state.context.secrets.get(
    "codeCoach.refreshToken",
  );

  if (!accessToken && !refreshToken) {
    state.currentUser = undefined;
    updateAuthStatusBar(state);
    updateAnalysisStatusBar(state);
    return false;
  }

  try {
    const me = await authorizedRequestJson<MeResponse>(
      state,
      "/api/v1/auth/me",
      {
        method: "GET",
      },
    );
    state.currentUser = me.user;
    await state.context.globalState.update(USER_STATE_KEY, me.user);
    updateAuthStatusBar(state);
    updateAnalysisStatusBar(state);
    return true;
  } catch (error) {
    console.error("Code Coach session restore failed:", error);
    await clearStoredAuthState(state);
    return false;
  }
}

// ── Ensure authenticated ──

// The gate analysis.ts calls before every analyze. Fast path: currentUser is
// already set. Otherwise try a silent restoreAuthSession; only if that fails
// AND showPrompt is true does it interrupt the user with a Sign In / Create
// Account choice. Auto-analysis passes showPrompt=false so typing never nags.
export async function ensureAuthenticated(
  state: ExtensionState,
  showPrompt: boolean,
): Promise<boolean> {
  if (state.currentUser) {
    return true;
  }

  if (await restoreAuthSession(state)) {
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
    await signIn(state);
  } else if (action === "Create Account") {
    await createAccount(state);
  }

  return state.currentUser !== undefined;
}

// ── Learning session management ──

// Lazily get-or-create the learning session id that ties a run of analyses
// together on the backend. Returns the cached id if present; otherwise POSTs
// /api/v1/learning-sessions and caches the new id on state + workspaceState.
// analysis.ts calls this right before requestAnalyze and passes the id along,
// so every diagnostic the backend stores is attributed to this session.
export async function ensureLearningSession(
  state: ExtensionState,
): Promise<string | undefined> {
  if (state.currentLearningSessionId) {
    return state.currentLearningSessionId;
  }

  if (!(await ensureAuthenticated(state, false))) {
    return undefined;
  }

  const response = await authorizedRequestJson<LearningSessionResponse>(
    state,
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

  state.currentLearningSessionId = response.learning_session_id;
  await state.context.workspaceState.update(
    "codeCoach.learningSessionId",
    state.currentLearningSessionId,
  );
  return state.currentLearningSessionId;
}

// ── Learning event tracking ──

export async function createLearningEvent(
  state: ExtensionState,
  event: LearningEventRequest,
): Promise<LearningEventCreateResponse> {
  return authorizedRequestJson<LearningEventCreateResponse>(
    state,
    "/api/v1/events",
    {
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
    },
  );
}

// Fire-and-forget wrapper around createLearningEvent: analysis.ts calls this
// each time a hint is shown or navigated. It returns void (doesn't block the UI)
// and swallows errors — telemetry must never break the analysis flow. These
// events are the raw material the backend turns into struggle/hint-dependence
// signals for the downstream Study Guider.
export function trackLearningEvent(
  state: ExtensionState,
  event: LearningEventRequest,
): void {
  if (!state.currentUser) {
    return;
  }

  void createLearningEvent(state, event).catch((error) => {
    console.error("Code Coach learning event tracking failed:", error);
  });
}
