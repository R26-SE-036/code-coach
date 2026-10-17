import * as vscode from "vscode";
import { conceptName, confidenceWords, titleFor } from "../labels";
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

/** The commands a hover link may run. Everything else in the hover is text. */
const HOVER_COMMANDS = [
  "code-coach-vscode.revealNextHint",
  "code-coach-vscode.explainInMyCode",
  "code-coach-vscode.showSimilarExample",
  "code-coach-vscode.openCourseUnit",
];

function commandLink(label: string, command: string, args: unknown[]): string {
  return `[${label}](command:${command}?${encodeURIComponent(JSON.stringify(args))})`;
}

/**
 * The hover card on a flagged line: what the mistake is called, how sure Code
 * Coach is in words, the hints opened so far, and the next steps as links.
 *
 * Hints are shown up to `revealed` only. The hover used to print all three
 * levels at once, so the targeted hint - the one that points at the fix - was
 * on screen before the student had asked for anything, which undid the
 * progressive hints everywhere else. The next level is a link that goes
 * through revealNextHint, so it is recorded like every other request.
 *
 * The technical table that used to lead the card (engine, ML and locator
 * percentages, the error id) is in the panel's "How Code Coach decided".
 */
export function buildHoverMarkdown(
  item: DiagnosticItem,
  revealed: HintLevel = "concept",
): vscode.MarkdownString {
  const md = new vscode.MarkdownString(undefined, true);
  // Trusted for the commands its links run, not for every command: the hint
  // and message text come from the backend and are rendered in here.
  md.isTrusted = { enabledCommands: HOVER_COMMANDS };
  md.supportHtml = true;

  const confidence = confidenceWords(item.confidence);
  md.appendMarkdown(
    `### $(lightbulb) ${titleFor(item)}\n\n` +
    `*${conceptName(item.concept_tag)} · ${confidence.label}*\n\n` +
    `${item.message}\n\n---\n\n` +
    `**💡 Concept** — ${item.hints.concept}\n\n`,
  );

  if (revealed !== "concept") {
    md.appendMarkdown(`**🧭 Guidance** — ${item.hints.guidance}\n\n`);
  }
  if (revealed === "targeted") {
    md.appendMarkdown(`**🎯 Targeted** — ${item.hints.targeted}\n\n`);
  }

  const links: string[] = [];
  if (revealed !== "targeted") {
    // The id only: the whole finding would put the unopened hints' text into
    // the link, and so into the hover's markdown.
    const next = revealed === "concept" ? "guidance" : "targeted";
    links.push(commandLink(`Show the ${next} hint`, "code-coach-vscode.revealNextHint", [item.diagnostic_id, "hover"]));
  }
  links.push(commandLink("✨ Explain in my code", "code-coach-vscode.explainInMyCode", [item.diagnostic_id]));
  links.push(commandLink("📘 Similar example", "code-coach-vscode.showSimilarExample", [item.diagnostic_id]));
  links.push(commandLink("🎓 Learn this", "code-coach-vscode.openCourseUnit", [item.diagnostic_id]));
  md.appendMarkdown(`---\n\n${links.join(" · ")}\n`);
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
    // The squiggle (a vscode.Diagnostic) sits under exactly the flagged code;
    // this highlight runs on to the end of the line, so the note after it
    // hangs off the line's end rather than in the middle of the code.
    const precise = createRange(editor.document, item);
    const lineEnd = editor.document.lineAt(precise.start.line).range.end;
    return {
      range: new vscode.Range(precise.start, lineEnd),
      hoverMessage: buildHoverMarkdown(item, revealedHintLevels?.get(item.diagnostic_id)),
      renderOptions: {
        after: {
          contentText: `  ◆ ${titleFor(item)}`,
        },
      },
    };
  });
}
