import * as vscode from "vscode";
import { DiagnosticItem, ExtensionState } from "../types";

/**
 * Creates the enhanced warning decoration type for editor highlighting.
 * Upgraded with richer gradient glow, thicker left-accent border, and refined styling.
 */
export function createWarningDecorationType(): vscode.TextEditorDecorationType {
  return vscode.window.createTextEditorDecorationType({
    backgroundColor: "rgba(255, 191, 0, 0.10)",
    borderWidth: "0 0 0 3px",
    borderStyle: "solid",
    borderColor: "rgba(255, 191, 0, 0.7)",
    borderRadius: "0 4px 4px 0",
    overviewRulerColor: "rgba(255, 191, 0, 0.6)",
    overviewRulerLane: vscode.OverviewRulerLane.Right,
    after: {
      color: "rgba(180, 160, 100, 0.55)",
      fontStyle: "italic",
      margin: "0 0 0 16px",
    },
  });
}

/**
 * Builds a rich, structured hover MarkdownString for a diagnostic item.
 * Features: severity emoji, organized sections, code block, visual confidence bars.
 */
export function buildHoverMarkdown(item: DiagnosticItem): vscode.MarkdownString {
  const severityEmoji =
    item.severity === "error"
      ? "❌"
      : item.severity === "information"
        ? "ℹ️"
        : "⚠️";

  const confidenceBar = (value: number | undefined): string => {
    if (value === undefined) {
      return "n/a";
    }
    const pct = Math.round(value * 100);
    const filled = Math.round(value * 10);
    const empty = 10 - filled;
    return `\`[${"█".repeat(filled)}${"░".repeat(empty)}]\` ${pct}%`;
  };

  const md = new vscode.MarkdownString(undefined, true);
  md.isTrusted = true;
  md.supportHtml = true;

  md.appendMarkdown(
    `## ${severityEmoji} ${item.error_type}\n\n` +
    `${item.message}\n\n` +
    `---\n\n` +
    `### 📋 Issue Details\n\n` +
    `| | |\n` +
    `|:--|:--|\n` +
    `| **Severity** | \`${item.severity}\` |\n` +
    `| **Line : Column** | \`${item.line} : ${item.column}\` |\n` +
    `| **Concept** | \`${item.concept_tag}\` |\n` +
    `| **Engine** | \`${item.detection_engine}\` |\n` +
    `| **Diagnostic ID** | \`${item.diagnostic_id}\` |\n` +
    `| **Explanation key** | \`${item.explanation_key}\` |\n\n` +
    `---\n\n` +
    `### 🔬 Detection Confidence\n\n` +
    `**ML probability:** ${confidenceBar(item.ml_probability)}\n\n` +
    `**Locator confidence:** ${confidenceBar(item.locator_confidence)}\n\n` +
    `**Overall confidence:** \`${item.confidence}\`\n\n` +
    `---\n\n` +
    `### 📝 Code Context\n\n` +
    `\`\`\`java\n${item.code_context}\n\`\`\`\n\n` +
    `---\n\n` +
    `### 💡 Hints\n\n` +
    `**💡 Concept:**\n` +
    `> ${item.hints.concept}\n\n` +
    `**🧭 Guidance:**\n` +
    `> ${item.hints.guidance}\n\n` +
    `**🎯 Targeted:**\n` +
    `> ${item.hints.targeted}\n`,
  );

  return md;
}

/**
 * Builds decoration options array for a set of diagnostics.
 * Each decoration gets the enhanced hover tooltip.
 */
export function buildDecorationOptions(
  editor: vscode.TextEditor,
  diagnostics: DiagnosticItem[],
  createRange: (doc: vscode.TextDocument, d: DiagnosticItem) => vscode.Range,
): vscode.DecorationOptions[] {
  return diagnostics.map((item) => {
    const range = createRange(editor.document, item);
    return {
      range,
      hoverMessage: buildHoverMarkdown(item),
      renderOptions: {
        after: {
          contentText: `  ◆ ${item.concept_tag}`,
        },
      },
    };
  });
}
