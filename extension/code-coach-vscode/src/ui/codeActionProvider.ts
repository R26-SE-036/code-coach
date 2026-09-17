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

      // The next hint level, by name only. These titles used to carry the
      // guidance and targeted text itself, so opening the lightbulb showed
      // the most specific hint before the student had asked for any - see
      // "Hint levels, in order" in analysis.ts.
      const revealed = this.state.revealedHintLevels.get(diag.diagnostic_id) ?? "concept";
      if (revealed === "concept" || revealed === "guidance") {
        const next = revealed === "concept" ? "guidance" : "targeted";
        const nextAction = new vscode.CodeAction(
          next === "guidance" ? "🧭 Code Coach: show the guidance hint" : "🎯 Code Coach: show the targeted hint",
          vscode.CodeActionKind.QuickFix,
        );
        nextAction.command = {
          title: "Show Next Hint",
          command: "code-coach-vscode.revealNextHint",
          arguments: [diag],
        };
        actions.push(nextAction);
      } else {
        // Already opened, so it may be read again from here.
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
      }

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

      // False-positive feedback — the labeled data that measures and
      // improves detection accuracy.
      const disputeAction = new vscode.CodeAction(
        "🚩 Report false positive (this warning is wrong)",
        vscode.CodeActionKind.QuickFix,
      );
      disputeAction.command = {
        title: "Report False Positive",
        command: "code-coach-vscode.reportFalsePositive",
        arguments: [diag],
      };
      actions.push(disputeAction);
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
