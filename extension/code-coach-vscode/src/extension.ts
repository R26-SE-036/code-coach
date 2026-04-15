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
  diagnostics: DiagnosticItem[];
};

export function activate(context: vscode.ExtensionContext) {
  console.log("Code Coach extension has been activated.");

  const outputChannel = vscode.window.createOutputChannel("Code Coach");
  const diagnosticCollection =
    vscode.languages.createDiagnosticCollection("code-coach");

  const warningDecorationType = vscode.window.createTextEditorDecorationType({
    backgroundColor: "rgba(255, 215, 0, 0.18)",
    border: "1px solid rgba(255, 215, 0, 0.45)",
    borderRadius: "3px",
  });

  const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();
  const lastDiagnosticsByUri = new Map<string, DiagnosticItem[]>();
  const activeHintIndexByUri = new Map<string, number>();
  const debounceDelayMs = 900;
  const sessionId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;

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
  }

  function clearFeedbackForDocument(document: vscode.TextDocument) {
    clearTimerForUri(document.uri);
    diagnosticCollection.delete(document.uri);
    lastDiagnosticsByUri.delete(document.uri.toString());
    activeHintIndexByUri.delete(document.uri.toString());

    const activeEditor = vscode.window.activeTextEditor;
    if (
      activeEditor &&
      activeEditor.document.uri.toString() === document.uri.toString()
    ) {
      activeEditor.setDecorations(warningDecorationType, []);
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
  }

  async function runAnalysisForEditor(
    editor: vscode.TextEditor,
    options: { showPopup: boolean; showOutput: boolean },
  ) {
    const document = editor.document;

    console.log("Code Coach auto-analysis running for:", document.fileName);

    if (!isSupportedDocument(document)) {
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
        outputChannel.clear();
        outputChannel.show(true);
        outputChannel.appendLine("=== Code Coach Analysis Result ===");
        outputChannel.appendLine("The current file is empty.");
      }

      return;
    }

    try {
      const payload = {
        language: "java",
        code,
        session_id: sessionId,
        enable_logging: isEvaluationLoggingEnabled(),
      };

      const response = await fetch(`${getBackendUrl()}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Backend request failed with status ${response.status}`);
      }

      const result = (await response.json()) as AnalyzeResponse;

      if (options.showOutput) {
        outputChannel.clear();
        outputChannel.show(true);
        outputChannel.appendLine("=== Code Coach Analysis Result ===");
        outputChannel.appendLine(`Status: ${result.status}`);
        outputChannel.appendLine(`Message: ${result.message}`);
        outputChannel.appendLine(`Timestamp: ${result.timestamp}`);
        outputChannel.appendLine(
          `Analysis time: ${result.analysis_duration_ms} ms`,
        );
        outputChannel.appendLine("");
      }

      if (result.diagnostics.length === 0) {
        clearFeedbackForDocument(document);

        if (options.showOutput) {
          outputChannel.appendLine("No issues detected.");
        }

        if (options.showPopup) {
          vscode.window.showInformationMessage("Code Coach: No issues detected.");
        }

        return;
      }

      if (options.showOutput) {
        for (const diagnostic of result.diagnostics) {
          outputChannel.appendLine(`Diagnostic : ${diagnostic.diagnostic_id}`);
          outputChannel.appendLine(`Error Type : ${diagnostic.error_type}`);
          outputChannel.appendLine(`Severity   : ${diagnostic.severity}`);
          outputChannel.appendLine(`Engine     : ${diagnostic.detection_engine}`);
          outputChannel.appendLine(`ML Prob.   : ${diagnostic.ml_probability ?? "n/a"}`);
          outputChannel.appendLine(
            `Locator   : ${diagnostic.locator_confidence ?? "n/a"}`,
          );
          outputChannel.appendLine(`Line       : ${diagnostic.line}`);
          outputChannel.appendLine(`Column     : ${diagnostic.column}`);
          outputChannel.appendLine(`Confidence : ${diagnostic.confidence}`);
          outputChannel.appendLine(`Message    : ${diagnostic.message}`);
          outputChannel.appendLine(`Context    : ${diagnostic.code_context}`);
          outputChannel.appendLine(`ConceptTag : ${diagnostic.concept_tag}`);
          outputChannel.appendLine(`ExplainKey : ${diagnostic.explanation_key}`);
          outputChannel.appendLine(`Concept    : ${diagnostic.hints.concept}`);
          outputChannel.appendLine(`Guidance   : ${diagnostic.hints.guidance}`);
          outputChannel.appendLine(`Targeted   : ${diagnostic.hints.targeted}`);
          outputChannel.appendLine("-----------------------------------");
        }
      }

      applyEditorFeedback(editor, result.diagnostics);

      if (options.showPopup) {
        const firstDiagnostic = result.diagnostics[0];

        vscode.window.showWarningMessage(
          `Code Coach: Found ${result.diagnostics.length} issue(s). First issue: ${firstDiagnostic.message} (Line ${firstDiagnostic.line}). Hint: ${firstDiagnostic.hints.concept}`,
        );
      }

      console.log("Analyze response:", result);
    } catch (error) {
      clearFeedbackForDocument(document);

      const message =
        error instanceof Error ? error.message : "Unknown error occurred.";

      if (options.showPopup) {
        vscode.window.showErrorMessage(`Code Coach error: ${message}`);
      }

      console.error("Code Coach analyze error:", error);
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

    console.log("Code Coach auto-analysis scheduled for:", document.fileName);

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

    activeHintIndexByUri.set(uriKey, nextIndex);
    editor.selection = new vscode.Selection(range.start, range.start);
    editor.revealRange(range, vscode.TextEditorRevealType.InCenterIfOutsideViewport);

    vscode.window.showInformationMessage(
      `Code Coach hint ${nextIndex + 1}/${diagnostics.length}: ${diagnostic.hints.guidance}`,
    );
  }

  const startCommand = vscode.commands.registerCommand(
    "code-coach-vscode.start",
    () => {
      vscode.window.showInformationMessage("Code Coach extension is running.");
      outputChannel.show(true);
      outputChannel.appendLine("Code Coach extension started.");
    },
  );

  const analyzeCommand = vscode.commands.registerCommand(
    "code-coach-vscode.analyzeCurrentFile",
    async () => {
      const editor = vscode.window.activeTextEditor;

      if (!editor) {
        vscode.window.showErrorMessage("No active editor found.");
        return;
      }

      clearTimerForUri(editor.document.uri);

      await runAnalysisForEditor(editor, {
        showPopup: true,
        showOutput: true,
      });
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
    },
  );

  const onDidCloseTextDocument = vscode.workspace.onDidCloseTextDocument(
    (document) => {
      clearFeedbackForDocument(document);
    },
  );

  const initialEditor = vscode.window.activeTextEditor;
  if (initialEditor) {
    scheduleAutoAnalysis(initialEditor);
  }

  context.subscriptions.push(
    startCommand,
    analyzeCommand,
    previousHintCommand,
    nextHintCommand,
    outputChannel,
    diagnosticCollection,
    warningDecorationType,
    onDidChangeTextDocument,
    onDidChangeActiveEditor,
    onDidCloseTextDocument,
  );
}

export function deactivate() { }
