import * as vscode from "vscode";
import { ExtensionState } from "../types";
import { createRangeFromDiagnostic } from "../analysis";

/**
 * Code Action provider that shows a lightbulb (💡) on warning squiggles
 * with quick-fix options to view hints at each level.
 */
export class CoachCodeActionProvider implements vscode.CodeActionProvider {
  public static readonly providedCodeActionKinds = [
    vscode.CodeActionKind.QuickFix,
  ];

  constructor(private readonly state: ExtensionState) {}

  public provideCodeActions(
    document: vscode.TextDocument,
    range: vscode.Range | vscode.Selection,
    _context: vscode.CodeActionContext,
    _token: vscode.CancellationToken,
  ): vscode.CodeAction[] {
    const uriKey = document.uri.toString();
    const diagnostics = this.state.lastDiagnosticsByUri.get(uriKey);

    if (!diagnostics || diagnostics.length === 0) {
      return [];
    }

    const actions: vscode.CodeAction[] = [];

    for (const diag of diagnostics) {
      const diagRange = createRangeFromDiagnostic(document, diag);

      // Only show actions if the cursor/selection intersects this diagnostic's range
      if (!range.intersection(diagRange)) {
        continue;
      }

      // Concept hint action
      const conceptAction = new vscode.CodeAction(
        `💡 Code Coach: ${diag.hints.concept}`,
        vscode.CodeActionKind.QuickFix,
      );
      conceptAction.command = {
        title: "Show Concept Hint",
        command: "code-coach-vscode.showCodeLensHint",
        arguments: [0, "concept", diag],
      };
      conceptAction.isPreferred = true;
      actions.push(conceptAction);

      // Guidance hint action
      const guidanceAction = new vscode.CodeAction(
        `🧭 Guidance: ${truncate(diag.hints.guidance, 70)}`,
        vscode.CodeActionKind.QuickFix,
      );
      guidanceAction.command = {
        title: "Show Guidance Hint",
        command: "code-coach-vscode.showCodeLensHint",
        arguments: [0, "guidance", diag],
      };
      actions.push(guidanceAction);

      // Targeted hint action
      const targetedAction = new vscode.CodeAction(
        `🎯 Targeted: ${truncate(diag.hints.targeted, 70)}`,
        vscode.CodeActionKind.QuickFix,
      );
      targetedAction.command = {
        title: "Show Targeted Hint",
        command: "code-coach-vscode.showCodeLensHint",
        arguments: [0, "targeted", diag],
      };
      actions.push(targetedAction);

      // Open Coach Panel action
      const panelAction = new vscode.CodeAction(
        "📋 Open Coach Panel",
        vscode.CodeActionKind.QuickFix,
      );
      panelAction.command = {
        title: "Open Coach Panel",
        command: "code-coach-vscode.openCoachPanel",
      };
      actions.push(panelAction);
    }

    return actions;
  }
}

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) {
    return text;
  }
  return text.substring(0, maxLen - 1) + "…";
}
