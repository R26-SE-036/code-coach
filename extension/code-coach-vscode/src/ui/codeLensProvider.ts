import * as vscode from "vscode";
import { DiagnosticItem, ExtensionState } from "../types";

/**
 * CodeLens provider that shows clickable hint actions directly
 * above lines with detected issues in the editor.
 *
 * Each problem line gets up to 3 lenses:
 *   💡 Concept Hint  ·  🧭 Guidance Hint  ·  🎯 Targeted Hint
 */
export class CoachCodeLensProvider implements vscode.CodeLensProvider {
  private readonly _onDidChangeCodeLenses = new vscode.EventEmitter<void>();
  public readonly onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;

  constructor(private readonly state: ExtensionState) {}

  /** Signal VS Code to re-request lenses (called after analysis completes). */
  public refresh(): void {
    this._onDidChangeCodeLenses.fire();
  }

  public provideCodeLenses(
    document: vscode.TextDocument,
    _token: vscode.CancellationToken,
  ): vscode.CodeLens[] {
    const uriKey = document.uri.toString();
    const diagnostics = this.state.lastDiagnosticsByUri.get(uriKey);

    if (!diagnostics || diagnostics.length === 0) {
      return [];
    }

    const lenses: vscode.CodeLens[] = [];

    for (let i = 0; i < diagnostics.length; i++) {
      const diag = diagnostics[i];
      const lineIndex = Math.max(0, diag.line - 1);

      if (lineIndex >= document.lineCount) {
        continue;
      }

      const range = new vscode.Range(lineIndex, 0, lineIndex, 0);

      // 💡 Concept hint lens — single lens per issue
      lenses.push(
        new vscode.CodeLens(range, {
          title: `💡 ${diag.error_type}: ${truncate(diag.hints.concept, 80)}`,
          command: "code-coach-vscode.showCodeLensHint",
          arguments: [i, "concept", diag],
          tooltip: "Click to see the full concept hint for this issue",
        }),
      );
    }

    return lenses;
  }

  public dispose(): void {
    this._onDidChangeCodeLenses.dispose();
  }
}

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) {
    return text;
  }
  return text.substring(0, maxLen - 1) + "…";
}
