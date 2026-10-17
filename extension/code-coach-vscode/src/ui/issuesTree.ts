/**
 * The "Issues" view: every finding in the current Java file, grouped by the
 * concept it belongs to, in VS Code's own tree - so the list looks and behaves
 * like the Problems view (keyboard, screen readers, collapse) rather than like
 * a web page. Compiler errors from the Java extension get their own group,
 * each with "explain" as its inline action.
 */
import * as vscode from "vscode";
import { compilerProblemsFor, mutedErrorTypes } from "../assistState";
import { conceptName, titleFor } from "../labels";
import { CompilerProblem, DiagnosticItem, ExtensionState } from "../types";

type Node =
  | { kind: "concept"; tag: string; items: DiagnosticItem[] }
  | { kind: "issue"; item: DiagnosticItem }
  | { kind: "compilerGroup"; problems: CompilerProblem[] }
  | { kind: "compiler"; problem: CompilerProblem };

export class IssuesTreeProvider implements vscode.TreeDataProvider<Node> {
  public static readonly viewType = "codeCoachIssues";
  private readonly changed = new vscode.EventEmitter<Node | undefined>();
  public readonly onDidChangeTreeData = this.changed.event;

  constructor(private readonly state: ExtensionState) {}

  refresh(): void {
    this.changed.fire(undefined);
  }

  private currentUri(): vscode.Uri | undefined {
    const editor = vscode.window.activeTextEditor;
    if (editor && editor.document.languageId === "java") { return editor.document.uri; }
    return this.state.lastSupportedUriKey ? vscode.Uri.parse(this.state.lastSupportedUriKey) : undefined;
  }

  getChildren(node?: Node): Node[] {
    const uri = this.currentUri();
    if (!uri) { return []; }
    if (!node) {
      const muted = new Set(mutedErrorTypes());
      const items = (this.state.lastDiagnosticsByUri.get(uri.toString()) ?? []).filter((d) => !muted.has(d.error_type));
      const groups = new Map<string, DiagnosticItem[]>();
      for (const item of items) {
        groups.set(item.concept_tag, [...(groups.get(item.concept_tag) ?? []), item]);
      }
      const nodes: Node[] = [...groups.entries()]
        .sort((a, b) => conceptName(a[0]).localeCompare(conceptName(b[0])))
        .map(([tag, list]) => ({ kind: "concept", tag, items: list.sort((x, y) => x.line - y.line) }));
      const problems = compilerProblemsFor(uri);
      if (problems.length) { nodes.unshift({ kind: "compilerGroup", problems }); }
      return nodes;
    }
    if (node.kind === "concept") { return node.items.map((item) => ({ kind: "issue", item })); }
    if (node.kind === "compilerGroup") { return node.problems.map((problem) => ({ kind: "compiler", problem })); }
    return [];
  }

  getTreeItem(node: Node): vscode.TreeItem {
    if (node.kind === "concept") {
      const item = new vscode.TreeItem(conceptName(node.tag), vscode.TreeItemCollapsibleState.Expanded);
      item.description = `${node.items.length}`;
      item.iconPath = new vscode.ThemeIcon("symbol-namespace");
      item.contextValue = "codeCoachConcept";
      return item;
    }
    if (node.kind === "compilerGroup") {
      const item = new vscode.TreeItem("Does not compile yet", vscode.TreeItemCollapsibleState.Expanded);
      item.description = `${node.problems.length}`;
      item.iconPath = new vscode.ThemeIcon("error", new vscode.ThemeColor("errorForeground"));
      item.tooltip = "Errors from the Java compiler. Code Coach can explain them in plain words.";
      return item;
    }
    if (node.kind === "compiler") {
      const item = new vscode.TreeItem(node.problem.message, vscode.TreeItemCollapsibleState.None);
      item.description = `line ${node.problem.line}`;
      item.iconPath = new vscode.ThemeIcon("circle-filled", new vscode.ThemeColor("errorForeground"));
      item.contextValue = "codeCoachCompilerError";
      item.command = { command: "code-coach-vscode.explainCompilerError", title: "Explain this error", arguments: [node.problem] };
      return item;
    }
    const diagnostic = node.item;
    const item = new vscode.TreeItem(titleFor(diagnostic), vscode.TreeItemCollapsibleState.None);
    item.description = `line ${diagnostic.line}`;
    item.tooltip = new vscode.MarkdownString(`**${titleFor(diagnostic)}** — line ${diagnostic.line}\n\n${diagnostic.message}\n\n💡 ${diagnostic.hints.concept}`);
    item.iconPath = new vscode.ThemeIcon("warning", new vscode.ThemeColor("editorWarning.foreground"));
    item.contextValue = "codeCoachIssue";
    item.command = { command: "code-coach-vscode.revealDiagnostic", title: "Go to the issue", arguments: [diagnostic.diagnostic_id] };
    return item;
  }

  dispose(): void {
    this.changed.dispose();
  }
}
