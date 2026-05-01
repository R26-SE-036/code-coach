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
