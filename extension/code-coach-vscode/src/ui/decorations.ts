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

type HintLevel = "concept" | "guidance" | "targeted";

/**
 * Builds a rich, structured hover MarkdownString for a diagnostic item.
 * Features: severity emoji, organized sections, code block, visual confidence bars.
 *
 * Hints are shown up to `revealed` only. The hover used to print all three
 * levels at once, so the targeted hint - the one that points at the fix - was
 * on screen before the student had asked for anything, which undid the
 * progressive hints everywhere else. The next level is a link that goes
 * through revealNextHint, so it is recorded like every other request.
 */
export function buildHoverMarkdown(
  item: DiagnosticItem,
  revealed: HintLevel = "concept",
): vscode.MarkdownString {
  const severityEmoji =
    item.severity === "error"
      ? "❌"
      : item.severity === "information"
        ? "ℹ️"
        : "⚠️";

  const pctLabel = (value: number | undefined): string => {
    if (value === undefined) { return "n/a"; }
    return `\`${Math.round(value * 100)}%\``;
  };

  const md = new vscode.MarkdownString(undefined, true);
  // Trusted for the one command its link runs, not for every command: the
  // hint and message text come from the backend and are rendered in here.
  md.isTrusted = { enabledCommands: ["code-coach-vscode.revealNextHint"] };
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
    `| **Confidence** | \`${item.confidence}\` — ML ${pctLabel(item.ml_probability)} · Locator ${pctLabel(item.locator_confidence)} |\n\n` +
    `---\n\n` +
    `### 📝 Code Context\n\n` +
    `\`\`\`java\n${item.code_context}\n\`\`\`\n\n` +
    `---\n\n` +
    `### 💡 Hints\n\n` +
    `**💡 Concept:**\n` +
    `> ${item.hints.concept}\n\n`,
  );

  if (revealed !== "concept") {
    md.appendMarkdown(`**🧭 Guidance:**\n> ${item.hints.guidance}\n\n`);
  }
  if (revealed === "targeted") {
    md.appendMarkdown(`**🎯 Targeted:**\n> ${item.hints.targeted}\n`);
  } else {
    const next = revealed === "concept" ? "guidance" : "targeted";
    // The id only: the whole finding would put the unopened hints' text into
    // the link, and so into the hover's markdown.
    const args = encodeURIComponent(JSON.stringify([item.diagnostic_id, "hover"]));
    md.appendMarkdown(
      `[Show the ${next} hint](command:code-coach-vscode.revealNextHint?${args})\n`,
    );
  }

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
  revealedHintLevels?: ExtensionState["revealedHintLevels"],
): vscode.DecorationOptions[] {
  return diagnostics.map((item) => {
    const range = createRange(editor.document, item);
    return {
      range,
      hoverMessage: buildHoverMarkdown(item, revealedHintLevels?.get(item.diagnostic_id)),
      renderOptions: {
        after: {
          contentText: `  ◆ ${item.concept_tag}`,
        },
      },
    };
  });
}
