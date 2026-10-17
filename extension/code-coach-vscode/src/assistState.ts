/**
 * Keys and lookups shared by the assist actions (assist.ts) and the panel
 * that shows their results (ui/panelHtml.ts). Kept apart so neither imports
 * the other.
 */
import * as vscode from "vscode";
import { CompilerProblem, DiagnosticItem } from "./types";

export const MUTED_SETTING = "mutedErrorTypes";

export function explainKey(diagnostic: DiagnosticItem): string {
  return `explain:${diagnostic.diagnostic_id}`;
}

export function exampleKey(diagnostic: DiagnosticItem): string {
  return `example:${diagnostic.diagnostic_id}`;
}

/** One per error type: every finding of a type shares its model's card. */
export function cardKey(diagnostic: DiagnosticItem): string {
  return `card:${diagnostic.error_type}`;
}

export function compilerKey(problem: CompilerProblem): string {
  return `compiler:${problem.line}:${problem.message}`;
}

/** Errors other tools (the Java extension, javac) report for this file. */
export function compilerProblemsFor(uri: vscode.Uri | undefined): CompilerProblem[] {
  if (!uri) { return []; }
  return vscode.languages.getDiagnostics(uri)
    .filter((d) => d.severity === vscode.DiagnosticSeverity.Error && d.source !== "Code Coach")
    .map((d) => ({ message: d.message, line: d.range.start.line + 1, source: d.source }))
    .slice(0, 5);
}

/** Error types the student has chosen not to see in the editor. */
export function mutedErrorTypes(): string[] {
  return vscode.workspace.getConfiguration("codeCoach").get<string[]>(MUTED_SETTING, []) ?? [];
}
