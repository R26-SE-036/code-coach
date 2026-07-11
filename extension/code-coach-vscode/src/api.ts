/**
 * The HTTP plumbing layer: the only file that actually talks to the backend.
 *
 * Everything that reaches the FastAPI server goes through here. It owns three
 * concerns nobody else should duplicate:
 *   1. Building the request  — getBackendUrl() + fetch in requestJson().
 *   2. Authentication        — authorizedRequestJson() attaches the Bearer
 *                              access token and, on a 401, transparently
 *                              refreshes it (refreshAuthSession) and retries once.
 *   3. Token / auth state    — storeAuthResponse / clearStoredAuthState keep the
 *                              access+refresh tokens in VS Code's secret storage
 *                              and currentUser on the shared ExtensionState.
 *
 * Who calls in:
 *   - analysis.ts -> authorizedRequestJson (the analyze request)
 *   - auth.ts     -> requestJson (login/register, no token yet) and
 *                    authorizedRequestJson (me/logout/sessions/events)
 *
 * The auth-state helpers live in THIS file (not auth.ts) on purpose — see the
 * note near storeAuthResponse — to avoid an import cycle between api and auth.
 */
import * as vscode from "vscode";
import {
  ApiError,
  AuthResponse,
  ExtensionState,
} from "./types";
import { ACCESS_TOKEN_SECRET, REFRESH_TOKEN_SECRET } from "./constants";

export function getBackendUrl(): string {
  return vscode.workspace
    .getConfiguration("codeCoach")
    .get<string>("backendUrl", "http://127.0.0.1:8000")
    .replace(/\/$/, "");
}

export function isEvaluationLoggingEnabled(): boolean {
  return vscode.workspace
    .getConfiguration("codeCoach")
    .get<boolean>("enableEvaluationLogging", false);
}

export function headersToRecord(
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

export async function extractErrorMessage(response: Response): Promise<string> {
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

// The lowest-level call: prefix the path with the backend URL, fetch, and either
// return the parsed JSON as type T or throw an ApiError carrying the status code.
// Used directly ONLY for endpoints that need no token yet (login, register,
// refresh). Everything else goes through authorizedRequestJson below.
export async function requestJson<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const response = await fetch(`${getBackendUrl()}${path}`, init);

  if (!response.ok) {
    throw new ApiError(await extractErrorMessage(response), response.status);
  }

  return (await response.json()) as T;
}

// Trade the stored refresh token for a fresh access token (when the old one
// expired). On success it re-stores the new tokens; on failure it wipes auth
// state so the user is treated as signed out. Called automatically by
// authorizedRequestJson on a 401 — the student never sees the expiry.
export async function refreshAuthSession(
  state: ExtensionState,
): Promise<boolean> {
  const refreshToken = await state.context.secrets.get(REFRESH_TOKEN_SECRET);

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

    await storeAuthResponse(state, response, { resetLearningSession: false });
    return true;
  } catch (error) {
    console.error("Code Coach token refresh failed:", error);
    await clearStoredAuthState(state);
    return false;
  }
}

// THE workhorse used for every authenticated call (analyze, me, logout,
// sessions, events). It reads the access token from secret storage, adds the
// Authorization: Bearer header, and delegates to requestJson. If the server
// says 401, it refreshes the token once (refreshAuthSession) and retries with
// allowRefresh=false so a genuinely-dead session can't loop forever.
export async function authorizedRequestJson<T>(
  state: ExtensionState,
  path: string,
  init: RequestInit,
  allowRefresh = true,
): Promise<T> {
  const accessToken = await state.context.secrets.get(ACCESS_TOKEN_SECRET);
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
      (await refreshAuthSession(state))
    ) {
      return authorizedRequestJson<T>(state, path, init, false);
    }

    throw error;
  }
}

// ── Auth state helpers (imported by auth.ts too, kept here to avoid circular deps) ──

import { updateAuthStatusBar, updateAnalysisStatusBar } from "./ui/statusBar";
import { LEARNING_SESSION_KEY, USER_STATE_KEY } from "./constants";

export async function clearLearningSession(
  state: ExtensionState,
): Promise<void> {
  state.currentLearningSessionId = undefined;
  await state.context.workspaceState.update(LEARNING_SESSION_KEY, undefined);
}

// The "sign everything out" reset: delete both tokens from secret storage, drop
// currentUser, and clear every cached diagnostic/decoration off the screen.
// Called on explicit sign-out (auth.ts) and whenever a refresh fails.
export async function clearStoredAuthState(
  state: ExtensionState,
): Promise<void> {
  await state.context.secrets.delete(ACCESS_TOKEN_SECRET);
  await state.context.secrets.delete(REFRESH_TOKEN_SECRET);
  await state.context.globalState.update(USER_STATE_KEY, undefined);
  state.currentUser = undefined;
  await clearLearningSession(state);
  state.diagnosticCollection.clear();
  state.lastDiagnosticsByUri.clear();
  state.lastAnalysisSnapshotByUri.clear();
  state.activeHintIndexByUri.clear();

  const activeEditor = vscode.window.activeTextEditor;
  if (activeEditor) {
    activeEditor.setDecorations(state.warningDecorationType, []);
  }

  updateAuthStatusBar(state);
  updateAnalysisStatusBar(state);
}

// The "sign in succeeded" counterpart: persist the access + refresh tokens into
// secret storage and set currentUser. Called by auth.ts after login, register,
// and refresh. This is the single place tokens are written, which is why it
// lives in api.ts alongside the code that reads them.
export async function storeAuthResponse(
  state: ExtensionState,
  payload: AuthResponse,
  options: { resetLearningSession: boolean },
): Promise<void> {
  await state.context.secrets.store(
    ACCESS_TOKEN_SECRET,
    payload.tokens.access_token,
  );
  await state.context.secrets.store(
    REFRESH_TOKEN_SECRET,
    payload.tokens.refresh_token,
  );
  state.currentUser = payload.user;
  await state.context.globalState.update(USER_STATE_KEY, payload.user);

  if (options.resetLearningSession) {
    await clearLearningSession(state);
  }

  updateAuthStatusBar(state);
  updateAnalysisStatusBar(state);
}
