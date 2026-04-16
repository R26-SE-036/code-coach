import * as assert from "assert";
import * as fs from "fs/promises";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";

type TestAccount = {
  fullName: string;
  email: string;
  studentNumber: string;
  password: string;
};

const ARTIFACT_PATH = path.join(
  os.tmpdir(),
  "code-coach-extension-flow.json",
);

function uniqueAccount(): TestAccount {
  const suffix = `${Date.now()}${Math.floor(Math.random() * 1000)}`.slice(-10);
  return {
    fullName: "Code Coach Extension Test",
    email: `codecoach.extension.${suffix}@example.com`,
    studentNumber: `IT${suffix}`,
    password: "Password123",
  };
}

async function waitFor<T>(
  action: () => Promise<T | undefined> | T | undefined,
  timeoutMs: number,
  intervalMs = 250,
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

async function withPatchedWindow<T>(
  options: {
    inputQueue?: string[];
    infoResponder?: (...items: string[]) => string | undefined;
  },
  callback: () => Promise<T>,
): Promise<T> {
  const windowApi = vscode.window as unknown as {
    showInputBox: typeof vscode.window.showInputBox;
    showInformationMessage: typeof vscode.window.showInformationMessage;
    showWarningMessage: typeof vscode.window.showWarningMessage;
    showErrorMessage: typeof vscode.window.showErrorMessage;
  };

  const originalShowInputBox = windowApi.showInputBox;
  const originalShowInformationMessage = windowApi.showInformationMessage;
  const originalShowWarningMessage = windowApi.showWarningMessage;
  const originalShowErrorMessage = windowApi.showErrorMessage;

  const queuedInputs = [...(options.inputQueue ?? [])];
  const infoMessages: string[] = [];
  const warningMessages: string[] = [];
  const errorMessages: string[] = [];

  windowApi.showInputBox = (async () => queuedInputs.shift()) as typeof vscode.window.showInputBox;
  windowApi.showInformationMessage = (async <T extends string>(
    message: string,
    ...items: T[]
  ) => {
    infoMessages.push(message);
    const selected = options.infoResponder?.(...items);
    return selected as T | undefined;
  }) as typeof vscode.window.showInformationMessage;
  windowApi.showWarningMessage = (async <T extends string>(
    message: string,
  ) => {
    warningMessages.push(message);
    return undefined as T | undefined;
  }) as typeof vscode.window.showWarningMessage;
  windowApi.showErrorMessage = (async <T extends string>(
    message: string,
  ) => {
    errorMessages.push(message);
    return undefined as T | undefined;
  }) as typeof vscode.window.showErrorMessage;

  try {
    const result = await callback();
    assert.deepStrictEqual(errorMessages, [], `Unexpected error messages: ${errorMessages.join(" | ")}`);
    return result;
  } finally {
    windowApi.showInputBox = originalShowInputBox;
    windowApi.showInformationMessage = originalShowInformationMessage;
    windowApi.showWarningMessage = originalShowWarningMessage;
    windowApi.showErrorMessage = originalShowErrorMessage;
  }
}

suite("Code Coach Extension Flow", () => {
  suiteSetup(async function () {
    this.timeout(30000);

    await vscode.workspace
      .getConfiguration("codeCoach")
      .update(
        "backendUrl",
        "http://127.0.0.1:8000",
        vscode.ConfigurationTarget.Global,
      );
    await vscode.workspace
      .getConfiguration("codeCoach")
      .update(
        "enableEvaluationLogging",
        false,
        vscode.ConfigurationTarget.Global,
      );

    const healthResponse = await fetch("http://127.0.0.1:8000/health");
    assert.strictEqual(healthResponse.status, 200);

    const extension = vscode.extensions.all.find(
      (item) => item.packageJSON.name === "code-coach-vscode",
    );
    assert.ok(extension, "Code Coach extension should be discoverable.");
    await extension?.activate();

    await vscode.commands.executeCommand("workbench.action.closeAllEditors");
  });

  test("creates account, signs in, analyzes Java file, and records artifact", async function () {
    this.timeout(60000);

    const account = uniqueAccount();
    await fs.rm(ARTIFACT_PATH, { force: true });

    await withPatchedWindow(
      {
        inputQueue: [
          account.fullName,
          account.email,
          account.studentNumber,
          account.password,
          account.password,
        ],
      },
      async () => {
        await vscode.commands.executeCommand("code-coach-vscode.createAccount");
      },
    );

    await vscode.commands.executeCommand("code-coach-vscode.signOut");

    await withPatchedWindow(
      {
        inputQueue: [account.email, account.password],
      },
      async () => {
        await vscode.commands.executeCommand("code-coach-vscode.signIn");
      },
    );

    const javaFilePath = path.join(
      __dirname,
      "..",
      "..",
      "src",
      "sample-java",
      "Test2.java",
    );
    const document = await vscode.workspace.openTextDocument(javaFilePath);
    await vscode.window.showTextDocument(document);

    await vscode.commands.executeCommand("code-coach-vscode.analyzeCurrentFile");

    const diagnostics = await waitFor(async () => {
      const current = vscode.languages
        .getDiagnostics(document.uri)
        .filter((item) => item.source === "Code Coach");
      return current.length > 0 ? current : undefined;
    }, 15000);

    assert.ok(diagnostics.length > 0, "Expected Code Coach diagnostics.");
    assert.ok(
      diagnostics.some((item) =>
        String(item.code ?? "").includes("cc_"),
      ),
      "Expected a Code Coach diagnostic id.",
    );

    await fs.writeFile(
      ARTIFACT_PATH,
      JSON.stringify(
        {
          account,
          javaFilePath,
          diagnosticCount: diagnostics.length,
        },
        null,
        2,
      ),
      "utf-8",
    );
  });
});
