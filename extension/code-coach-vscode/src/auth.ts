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

// ── Account creation ──

export async function createAccount(state: ExtensionState): Promise<void> {
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

export async function signIn(state: ExtensionState): Promise<void> {
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
