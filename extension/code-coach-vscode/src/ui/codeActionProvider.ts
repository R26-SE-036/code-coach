import * as vscode from "vscode";
import { ExtensionState } from "../types";
import { createRangeFromDiagnostic } from "../analysis";
import { titleFor } from "../labels";

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
    context: vscode.CodeActionContext,
    _token: vscode.CancellationToken,
  ): vscode.CodeAction[] {
    const uriKey = document.uri.toString();
    const diagnostics = this.state.lastDiagnosticsByUri.get(uriKey) ?? [];
    const actions: vscode.CodeAction[] = [];

    // Compiler errors from the Java extension: a beginner gets the message
    // in plain words, for the line it points at.
    for (const problem of context.diagnostics) {
      if (problem.source === "Code Coach" || problem.severity !== vscode.DiagnosticSeverity.Error) { continue; }
      const explain = new vscode.CodeAction("💬 Code Coach: explain this error", vscode.CodeActionKind.QuickFix);
      explain.diagnostics = [problem];
      explain.command = {
        title: "Explain this error",
        command: "code-coach-vscode.explainCompilerError",
        arguments: [{ message: problem.message, line: problem.range.start.line + 1, source: problem.source }],
      };
      actions.push(explain);
      break;
    }

    if (diagnostics.length === 0) {
      return actions;
    }

    for (const diag of diagnostics) {
      const diagRange = createRangeFromDiagnostic(document, diag);

      // Only show actions if the cursor/selection intersects this diagnostic's range
      if (!range.intersection(diagRange)) {
        continue;
      }

      // Concept hint action
      const conceptAction = new vscode.CodeAction(
        `💡 ${titleFor(diag)}: ${truncate(diag.hints.concept, 80)}`,
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

      const explainAction = new vscode.CodeAction("✨ Code Coach: explain this in my code", vscode.CodeActionKind.QuickFix);
      explainAction.command = { title: "Explain in my code", command: "code-coach-vscode.explainInMyCode", arguments: [diag.diagnostic_id] };
      actions.push(explainAction);

      const exampleAction = new vscode.CodeAction("📘 Code Coach: show a similar example", vscode.CodeActionKind.QuickFix);
      exampleAction.command = { title: "Similar example", command: "code-coach-vscode.showSimilarExample", arguments: [diag.diagnostic_id] };
      actions.push(exampleAction);

      const learnAction = new vscode.CodeAction("🎓 Code Coach: learn this (free course)", vscode.CodeActionKind.QuickFix);
      learnAction.command = { title: "Learn this", command: "code-coach-vscode.openCourseUnit", arguments: [diag.diagnostic_id] };
      actions.push(learnAction);

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
