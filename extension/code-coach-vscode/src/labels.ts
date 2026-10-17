/**
 * Words for the student, not identifiers.
 *
 * The panel and the hover used to show `OFF_BY_ONE_LOOP_BOUNDARY`,
 * `loop_boundaries`, `candidate_gated_ast_locator` and a raw percentage - the
 * names the backend files things under. A beginner reading "ml_gated_ast_locator"
 * learns nothing about their loop. These turn each one into plain words; the
 * raw values stay available behind "How Code Coach decided".
 */
import { DiagnosticItem } from "./types";

const CONCEPT_NAMES: Record<string, string> = {
  arithmetic_operations: "Arithmetic",
  array_indexing: "Array indexing",
  assignment_logic: "Variables and assignment",
  boolean_logic: "Boolean logic",
  conditional_logic: "If and else",
  control_flow: "Control flow",
  immutable_strings: "Strings that never change",
  loop_boundaries: "Loop boundaries",
  loop_control: "Loop counters",
  loop_initialization: "Starting a loop",
  loop_termination: "Ending a loop",
  statement_structure: "Statement structure",
  string_comparison: "Comparing Strings",
  switch_statements: "Switch statements",
};

/** The mistake's name. The backend sends one; older backends do not. */
export function titleFor(diagnostic: Pick<DiagnosticItem, "title" | "error_type">): string {
  if (diagnostic.title) { return diagnostic.title; }
  const words = diagnostic.error_type.toLowerCase().split("_").join(" ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export function conceptName(tag: string | undefined): string {
  if (!tag) { return "General"; }
  return CONCEPT_NAMES[tag] ?? tag.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

/** How sure Code Coach is, in words. */
export function confidenceWords(confidence: number): { label: string; tone: "high" | "medium" | "low" } {
  if (confidence >= 0.85) { return { label: "Very likely", tone: "high" }; }
  if (confidence >= 0.65) { return { label: "Likely", tone: "medium" }; }
  return { label: "Worth a look", tone: "low" };
}

/** Which part of Code Coach made the call. */
export function engineWords(engine: string): string {
  switch (engine) {
    case "candidate_ml": return "A model trained on running code judged this exact spot";
    case "candidate_gated_ast_locator": return "A model judged this loop, then the tree pinpointed it";
    case "ml_gated_ast_locator": return "A model flagged the file, then the tree pinpointed the line";
    case "ast_locator_rule": return "A rule that is always true for this pattern";
    default: return engine;
  }
}

/** `code` in hint text as <code>, everything else escaped. */
export function inlineCodeHtml(text: string, escape: (value: string) => string): string {
  return text
    .split(/(`[^`]+`)/g)
    .map((part) => (part.startsWith("`") && part.endsWith("`") && part.length > 2
      ? `<code>${escape(part.slice(1, -1))}</code>`
      : escape(part)))
    .join("");
}
