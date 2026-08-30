/**
 * Sign in through the Code Guru portal instead of through input boxes.
 *
 * Code Coach used to be the one service where you typed a password into a
 * VS Code prompt while every other service signed in on the web. This module
 * moves it onto the same surface: the extension opens the portal in the
 * student's browser, and the resulting session comes back to the editor
 * automatically.
 *
 * ---------------------------------------------------------------------------
 * How the token gets back
 * ---------------------------------------------------------------------------
 * Two routes, tried in that order:
 *
 *   1. A loopback HTTP server on 127.0.0.1:53682. This is the primary route
 *      because it works in the Extension Development Host with no publisher id
 *      and no marketplace listing - which matters, since this extension is run
 *      with F5 rather than installed.
 *   2. A vscode:// URI handler, registered in extension.ts. Useful if the
 *      browser cannot reach the loopback server, but it needs the extension to
 *      be properly identified, and a vscode:// link can surface in a different
 *      window than the one that asked for it.
 *
 * If both fail, or the student cancels, or the window is remote, auth.ts falls
 * back to the original prompts. Nothing is lost.
 *
 * ---------------------------------------------------------------------------
 * Why a fixed port
 * ---------------------------------------------------------------------------
 * The portal validates redirect_uri against an exact-origin allow-list. An
 * ephemeral port could never be on that list, so the flow uses one fixed port
 * that is listed in VITE_ALLOWED_REDIRECTS. If the port is busy we fail with a
 * clear message rather than silently picking another one the portal would
 * reject.
 *
 * ---------------------------------------------------------------------------
 * Why a code and not a token
 * ---------------------------------------------------------------------------
 * The portal's normal handoff puts tokens in the URL fragment, which a browser
 * never transmits - so a loopback server would receive nothing at all. What
 * arrives here instead is a single-use code, valid for two minutes, which the
 * extension trades for its own session. No access token is ever put in a URL.
 */
import * as http from "http";
import * as vscode from "vscode";

import { requestJson, storeAuthResponse } from "./api";
import { ApiError, AuthResponse, ExtensionState } from "./types";

/** Must match VSCODE_LOOPBACK_PORT in the portal, and its allow-list entry. */
export const LOOPBACK_PORT = 53682;
const LOOPBACK_REDIRECT_URI = `http://127.0.0.1:${LOOPBACK_PORT}/callback`;

/** How long to wait for the student to finish signing in. */
const SIGN_IN_TIMEOUT_MS = 3 * 60 * 1000;

export function getPortalUrl(): string {
  return vscode.workspace
    .getConfiguration("codeCoach")
    .get<string>("portalUrl", "http://localhost:4200")
    .replace(/\/$/, "");
}

/** The page the browser is left on. Plain, self-contained, no assets. */
function resultPage(heading: string, detail: string): string {
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Code Guru</title>
<style>
  body { margin:0; min-height:100vh; display:flex; align-items:center;
         justify-content:center; background:#f4f7fc; color:#2d3c58;
         font-family:'Segoe UI',system-ui,sans-serif; }
  .card { background:#fff; border:1px solid #dae3f1; border-radius:14px;
          padding:36px 40px; text-align:center; max-width:380px;
          box-shadow:0 20px 44px -16px rgba(15,27,51,.18); }
  h1 { margin:0 0 8px; font-size:1.2rem; color:#0f1b33; }
  p  { margin:0; font-size:.9rem; color:#64748b; line-height:1.55; }
</style></head>
<body><div class="card"><h1>${heading}</h1><p>${detail}</p></div></body></html>`;
}

/** Turn a one-time code into a real session stored in VS Code's secret storage. */
export async function redeemHandoffCode(
  state: ExtensionState,
  code: string,
): Promise<AuthResponse> {
  const response = await requestJson<AuthResponse>("/api/v1/auth/handoff/redeem", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });

  await storeAuthResponse(state, response, { resetLearningSession: true });
  return response;
}

/**
 * Wait for the browser to come back with a code.
 *
 * Resolves with the code, or null if the student cancelled or it timed out.
 * Rejects only if the listener itself could not start.
 */
function waitForCode(token: vscode.CancellationToken): Promise<string | null> {
  return new Promise((resolve, reject) => {
    let settled = false;

    const server = http.createServer((request, response) => {
      const url = new URL(request.url || "/", `http://127.0.0.1:${LOOPBACK_PORT}`);

      // Browsers ask for this unprompted; answering 404 keeps it out of the log.
      if (url.pathname === "/favicon.ico") {
        response.writeHead(404).end();
        return;
      }

      const code = url.searchParams.get("code");
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      response.end(
        code
          ? resultPage("You are signed in", "You can close this tab and return to VS Code.")
          : resultPage("Something went wrong", "No sign-in code arrived. Try again from VS Code."),
      );

      finish(code);
    });

    function finish(value: string | null) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      // close() waits for open connections; the browser tab may still be one.
      server.close();
      resolve(value);
    }

    const timer = setTimeout(() => finish(null), SIGN_IN_TIMEOUT_MS);
    token.onCancellationRequested(() => finish(null));

    server.on("error", (error: NodeJS.ErrnoException) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (error.code === "EADDRINUSE") {
        // Deliberately not falling back to another port: the portal validates
        // the return address by exact origin, so a different port would be
        // rejected and the student would see a confusing "not allowed" page
        // instead of this.
        reject(
          new Error(
            `Port ${LOOPBACK_PORT} is already in use, so browser sign-in cannot ` +
              `start. Close whatever is using it, or sign in with your email and ` +
              `password instead.`,
          ),
        );
        return;
      }
      reject(error);
    });

    server.listen(LOOPBACK_PORT, "127.0.0.1");
  });
}

/**
 * Run the whole browser sign-in.
 *
 * Returns the signed-in user, or null if it did not complete — in which case
 * the caller should fall back to the prompts. Throws only for a genuine
 * failure worth showing the student.
 */
export async function signInThroughBrowser(
  state: ExtensionState,
  mode: "login" | "register",
): Promise<AuthResponse | null> {
  const portal = getPortalUrl();
  const target = new URL(portal + (mode === "register" ? "/register" : "/login"));
  target.searchParams.set("redirect_uri", LOOPBACK_REDIRECT_URI);

  return vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "Waiting for you to sign in to Code Guru in your browser…",
      cancellable: true,
    },
    async (_progress, token) => {
      const codePromise = waitForCode(token);

      // Opened after the listener is up, so a very fast sign-in cannot arrive
      // before there is anything to receive it.
      const opened = await vscode.env.openExternal(vscode.Uri.parse(target.toString()));
      if (!opened) {
        throw new Error("VS Code could not open a browser window.");
      }

      state.outputChannel.appendLine(`Browser sign-in started: ${target.toString()}`);

      const code = await codePromise;
      if (!code) return null;

      try {
        const response = await redeemHandoffCode(state, code);
        state.outputChannel.appendLine(`Signed in as ${response.user.email} (browser)`);
        return response;
      } catch (error) {
        if (error instanceof ApiError && error.statusCode === 400) {
          // Single-use and short-lived: this is what a replayed or stale code
          // looks like, and it is worth saying so plainly.
          throw new Error("That sign-in link had already been used. Please try again.");
        }
        throw error;
      }
    },
  );
}
