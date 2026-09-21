/**
 * The extension inside a real VS Code.
 *
 *     npm test
 *
 * Three suites, from no dependencies to the whole platform:
 *
 *   Settings            The addresses default to the platform's edge. They
 *                       defaulted to dev-server ports, so sign-in against the
 *                       compose stack opened a page nothing served.
 *   Browser sign-in     The whole loopback round trip - open the portal, receive
 *                       the code, redeem it - against a fake Code Coach started
 *                       by the test. Needs nothing running.
 *   Live platform       The prompt fallback and a real analysis, against the
 *                       running stack at CODE_COACH_TEST_URL (default: the local
 *                       compose stack, not the extension's default - that is the
 *                       deployed platform, and a local test run should not create
 *                       accounts there unasked). CI sets it to the deployed URL
 *                       on purpose. Skipped, and says so, when nothing answers.
 */
import * as assert from "assert";
import * as fs from "fs/promises";
import * as http from "http";
import { AddressInfo } from "net";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";

import { getBackendUrl } from "../api";
import { LOOPBACK_PORT, getPortalUrl } from "../browserAuth";
import { DEFAULT_PLATFORM_URL, LOCAL_STACK_URL } from "../constants";

type TestAccount = {
  fullName: string;
  email: string;
  password: string;
};

type Messages = { info: string[]; warning: string[]; error: string[] };

const ARTIFACT_PATH = path.join(os.tmpdir(), "code-coach-extension-flow.json");
const LIVE_URL = (process.env.CODE_COACH_TEST_URL ?? LOCAL_STACK_URL).replace(/\/$/, "");

function uniqueAccount(): TestAccount {
  const suffix = `${Date.now()}${Math.floor(Math.random() * 1000)}`.slice(-10);
  return {
    fullName: "Code Coach Extension Test",
    email: `codecoach.extension.${suffix}@example.com`,
    password: "Password123",
  };
}

const settings = () => vscode.workspace.getConfiguration("codeCoach");

async function setSetting(key: string, value: unknown): Promise<void> {
  await settings().update(key, value, vscode.ConfigurationTarget.Global);
}

async function activateExtension(): Promise<void> {
  const extension = vscode.extensions.all.find(
    (item) => item.packageJSON.name === "code-coach-vscode",
  );
  assert.ok(extension, "Code Coach extension should be discoverable.");
  await extension.activate();
}

async function waitFor<T>(
  action: () => Promise<T | undefined> | T | undefined,
  timeoutMs: number,
  intervalMs = 100,
): Promise<T> {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    const result = await action();
    if (result !== undefined) {
      return result;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error(`Timed out after ${timeoutMs} ms.`);
}

/** Answer prompts from a queue and record every message shown. */
async function withPatchedWindow<T>(
  options: { inputQueue?: string[]; allowErrors?: boolean },
  callback: (messages: Messages) => Promise<T>,
): Promise<T> {
  const windowApi = vscode.window as unknown as {
    showInputBox: typeof vscode.window.showInputBox;
    showInformationMessage: typeof vscode.window.showInformationMessage;
    showWarningMessage: typeof vscode.window.showWarningMessage;
    showErrorMessage: typeof vscode.window.showErrorMessage;
  };

  const original = {
    showInputBox: windowApi.showInputBox,
    showInformationMessage: windowApi.showInformationMessage,
    showWarningMessage: windowApi.showWarningMessage,
    showErrorMessage: windowApi.showErrorMessage,
  };

  const queuedInputs = [...(options.inputQueue ?? [])];
  const messages: Messages = { info: [], warning: [], error: [] };
  const record = (bucket: string[]) =>
    (async (message: string) => {
      bucket.push(message);
      return undefined;
    }) as never;

  windowApi.showInputBox = (async () => queuedInputs.shift()) as typeof vscode.window.showInputBox;
  windowApi.showInformationMessage = record(messages.info);
  windowApi.showWarningMessage = record(messages.warning);
  windowApi.showErrorMessage = record(messages.error);

  try {
    const result = await callback(messages);
    if (!options.allowErrors) {
      assert.deepStrictEqual(messages.error, [], `Unexpected error messages: ${messages.error.join(" | ")}`);
    }
    return result;
  } finally {
    Object.assign(windowApi, original);
  }
}

/**
 * Capture what the extension asks the OS to open, instead of opening it.
 *
 * `answer` is what openExternal reports: true as if a browser opened, false as
 * if none could - which is what sends sign-in to the prompt fallback.
 */
async function withOpenExternal<T>(
  answer: boolean,
  callback: (opened: vscode.Uri[]) => Promise<T>,
): Promise<T> {
  const env = vscode.env as unknown as { openExternal: typeof vscode.env.openExternal };
  const original = env.openExternal;
  const opened: vscode.Uri[] = [];

  try {
    env.openExternal = (async (uri: vscode.Uri) => {
      opened.push(uri);
      return answer;
    }) as typeof vscode.env.openExternal;
  } catch (error) {
    throw new Error(
      `vscode.env.openExternal cannot be replaced in this VS Code build, so the ` +
        `browser sign-in cannot be driven from a test: ${String(error)}`,
    );
  }

  try {
    return await callback(opened);
  } finally {
    env.openExternal = original;
  }
}

type Recorded = { method: string; url: string; body: unknown };

/** Just enough of Code Coach's auth API to sign an editor in. */
async function startFakeCodeCoach() {
  const requests: Recorded[] = [];
  const user = {
    user_id: "user_fake",
    full_name: "Fake Student",
    email: "fake.student@example.com",
    status: "active",
  };
  const authSession = { auth_session_id: "as_fake", client_name: "codeguru-vscode", status: "active" };

  const server = http.createServer((request, response) => {
    let raw = "";
    request.on("data", (chunk) => (raw += chunk));
    request.on("end", () => {
      let body: unknown = null;
      try {
        body = raw ? JSON.parse(raw) : null;
      } catch {
        body = raw;
      }
      requests.push({ method: request.method ?? "", url: request.url ?? "", body });

      const send = (status: number, payload: unknown) => {
        response.writeHead(status, { "Content-Type": "application/json" });
        response.end(JSON.stringify(payload));
      };

      if (request.method === "POST" && request.url === "/api/v1/auth/handoff/redeem") {
        const code = (body as { code?: string } | null)?.code;
        if (code === GOOD_CODE) {
          send(200, {
            status: "ok",
            message: "Sign-in successful.",
            user,
            auth_session: authSession,
            tokens: {
              token_type: "bearer",
              access_token: "fake-access",
              refresh_token: "fake-refresh",
              expires_in: 3600,
            },
          });
        } else {
          send(400, { detail: "That sign-in code has already been used or has expired." });
        }
        return;
      }
      if (request.method === "POST" && request.url === "/api/v1/auth/logout") {
        send(200, { status: "ok", message: "Signed out." });
        return;
      }
      if (request.url === "/api/v1/auth/me") {
        send(200, { status: "ok", user, auth_session: authSession });
        return;
      }
      send(404, { detail: "Not Found" });
    });
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const { port } = server.address() as AddressInfo;

  return {
    url: `http://127.0.0.1:${port}`,
    requests,
    close: () => new Promise<void>((resolve) => server.close(() => resolve())),
  };
}

const GOOD_CODE = "good-code-0123456789";
const callback = (query = "") => fetch(`http://127.0.0.1:${LOOPBACK_PORT}/callback${query}`);

// ── Settings ────────────────────────────────────────────────────────────────

suite("Settings", () => {
  test("both addresses default to the deployed platform's edge", () => {
    // One origin for both, over HTTPS: an installed copy has no local stack.
    assert.match(DEFAULT_PLATFORM_URL, /^https:\/\/[^/]+$/);
    for (const key of ["portalUrl", "backendUrl"]) {
      assert.strictEqual(
        settings().inspect<string>(key)?.defaultValue,
        DEFAULT_PLATFORM_URL,
        `package.json's default for codeCoach.${key} disagrees with constants.ts`,
      );
    }
  });

  test("a trailing slash in a setting does not double up in request paths", async () => {
    await setSetting("portalUrl", "http://localhost:4200/");
    await setSetting("backendUrl", "http://127.0.0.1:8000/");
    try {
      assert.strictEqual(getPortalUrl(), "http://localhost:4200");
      assert.strictEqual(getBackendUrl(), "http://127.0.0.1:8000");
    } finally {
      await setSetting("portalUrl", undefined);
      await setSetting("backendUrl", undefined);
    }
  });
});

// ── Browser sign-in, against a fake Code Coach ──────────────────────────────

suite("Browser sign-in", () => {
  let fake: Awaited<ReturnType<typeof startFakeCodeCoach>>;

  suiteSetup(async function () {
    this.timeout(30000);
    fake = await startFakeCodeCoach();
    await setSetting("backendUrl", fake.url);
    await setSetting("portalUrl", undefined);
    await activateExtension();
    await vscode.commands.executeCommand("workbench.action.closeAllEditors");
  });

  suiteTeardown(async () => {
    await setSetting("backendUrl", undefined);
    await fake?.close();
  });

  test("opens the portal's sign-in page and redeems the code that comes back", async function () {
    this.timeout(60000);

    await withOpenExternal(true, (opened) =>
      withPatchedWindow({}, async (messages) => {
        const signingIn = vscode.commands.executeCommand("code-coach-vscode.signIn");

        const target = new URL((await waitFor(() => opened[0], 10000)).toString(true));
        assert.strictEqual(target.origin, DEFAULT_PLATFORM_URL);
        assert.strictEqual(target.pathname, "/login");
        assert.strictEqual(
          target.searchParams.get("redirect_uri"),
          `http://127.0.0.1:${LOOPBACK_PORT}/callback`,
        );

        const page = await callback(`?code=${GOOD_CODE}`);
        assert.match(await page.text(), /You are signed in/);
        await signingIn;

        assert.deepStrictEqual(
          fake.requests.filter((item) => item.url === "/api/v1/auth/handoff/redeem").map((item) => item.body),
          [{ code: GOOD_CODE }],
        );
        assert.ok(
          messages.info.some((message) => message.includes("Signed in to Code Coach as Fake Student")),
          `no sign-in confirmation among: ${messages.info.join(" | ")}`,
        );
      }),
    );

    await withPatchedWindow({}, async () => {
      await vscode.commands.executeCommand("code-coach-vscode.signOut");
    });
  });

  test("Create Account opens the register page, and a browser that returns no code cancels quietly", async function () {
    this.timeout(60000);

    await withOpenExternal(true, (opened) =>
      withPatchedWindow({}, async (messages) => {
        const registering = vscode.commands.executeCommand("code-coach-vscode.createAccount");

        const target = new URL((await waitFor(() => opened[0], 10000)).toString(true));
        assert.strictEqual(target.pathname, "/register");

        const page = await callback();
        assert.match(await page.text(), /No sign-in code arrived/);
        await registering;

        assert.deepStrictEqual(messages.warning, [], "a cancelled sign-in should not fall back to prompts");
      }),
    );
  });

  test("a browser that will not open releases the port, so the next sign-in can start", async function () {
    this.timeout(60000);

    await withOpenExternal(false, () =>
      withPatchedWindow({ inputQueue: [] }, async (messages) => {
        await vscode.commands.executeCommand("code-coach-vscode.signIn");
        assert.ok(
          messages.warning.some((message) => message.includes("could not open a browser")),
          `no explanation among: ${messages.warning.join(" | ")}`,
        );
      }),
    );

    // Straight away, well inside the three-minute timeout the listener used to
    // hold the port for.
    await withOpenExternal(true, (opened) =>
      withPatchedWindow({}, async (messages) => {
        const signingIn = vscode.commands.executeCommand("code-coach-vscode.signIn");
        await waitFor(() => opened[0], 10000);

        await callback();
        await signingIn;

        assert.deepStrictEqual(
          messages.warning.filter((message) => message.includes("already in use")),
          [],
          "the earlier attempt was still holding the loopback port",
        );
      }),
    );
  });

  test("a code that was already used is explained, then the prompts take over", async function () {
    this.timeout(60000);

    await withOpenExternal(true, (opened) =>
      withPatchedWindow({ inputQueue: [] }, async (messages) => {
        const signingIn = vscode.commands.executeCommand("code-coach-vscode.signIn");
        await waitFor(() => opened[0], 10000);

        await callback("?code=stale-code-0123456789");
        await signingIn;

        assert.ok(
          messages.warning.some((message) => message.includes("already been used")),
          `no explanation among: ${messages.warning.join(" | ")}`,
        );
      }),
    );
  });
});

// ── The live platform ───────────────────────────────────────────────────────

suite("Live platform", () => {
  suiteSetup(async function () {
    this.timeout(30000);

    let reachable = true;
    try {
      await fetch(`${LIVE_URL}/api/v1/auth/me`, { signal: AbortSignal.timeout(3000) });
    } catch {
      reachable = false;
    }
    if (!reachable) {
      console.log(`Skipping the live platform suite: nothing is answering at ${LIVE_URL}.`);
      this.skip();
    }

    await setSetting("backendUrl", LIVE_URL);
    await setSetting("enableEvaluationLogging", false);
    await activateExtension();
    await vscode.commands.executeCommand("workbench.action.closeAllEditors");
  });

  suiteTeardown(async () => {
    await setSetting("backendUrl", undefined);
  });

  test("creates an account and signs in through the prompts, then analyses a Java file", async function () {
    this.timeout(120000);

    const account = uniqueAccount();
    await fs.rm(ARTIFACT_PATH, { force: true });

    // No browser: sign-in falls back to the prompts, which is the path a remote
    // window always takes.
    await withOpenExternal(false, async () => {
      await withPatchedWindow(
        { inputQueue: [account.fullName, account.email, account.password, account.password] },
        async () => {
          await vscode.commands.executeCommand("code-coach-vscode.createAccount");
        },
      );

      await withPatchedWindow({}, async () => {
        await vscode.commands.executeCommand("code-coach-vscode.signOut");
      });

      await withPatchedWindow({ inputQueue: [account.email, account.password] }, async () => {
        await vscode.commands.executeCommand("code-coach-vscode.signIn");
      });
    });

    const javaFilePath = path.join(__dirname, "..", "..", "src", "sample-java", "BankAccountSimulator.java");
    const document = await vscode.workspace.openTextDocument(javaFilePath);
    await vscode.window.showTextDocument(document);

    await vscode.commands.executeCommand("code-coach-vscode.analyzeCurrentFile");

    const diagnostics = await waitFor(async () => {
      const current = vscode.languages
        .getDiagnostics(document.uri)
        .filter((item) => item.source === "Code Coach");
      return current.length > 0 ? current : undefined;
    }, 30000, 250);

    assert.ok(diagnostics.length > 0, "Expected Code Coach diagnostics.");
    assert.ok(
      diagnostics.some((item) => String(item.code ?? "").includes("cc_")),
      "Expected a Code Coach diagnostic id.",
    );

    await fs.writeFile(
      ARTIFACT_PATH,
      JSON.stringify({ account: account.email, javaFilePath, diagnosticCount: diagnostics.length }, null, 2),
      "utf-8",
    );

    await withPatchedWindow({}, async () => {
      await vscode.commands.executeCommand("code-coach-vscode.signOut");
    });
  });
});
