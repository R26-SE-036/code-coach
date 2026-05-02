import * as vscode from "vscode";
import { ExtensionState } from "../types";
import { buildCoachPanelHtml } from "./panelHtml";
import { isSupportedDocument } from "./statusBar";
import { navigatePanelHint } from "../analysis";

/**
 * WebviewViewProvider that renders the Coach Panel inside the
 * activity-bar sidebar. This makes Code Coach always accessible
 * without needing Ctrl+Shift+P.
 */
export class CoachSidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "codeCoachSidebar";

  private _view: vscode.WebviewView | undefined;

  constructor(private readonly state: ExtensionState) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
    };

    webviewView.webview.html = buildCoachPanelHtml(this.state);

    webviewView.webview.onDidReceiveMessage((message: { command?: string }) => {
      switch (message.command) {
        case "signIn":
          void vscode.commands.executeCommand("code-coach-vscode.signIn");
          break;
        case "createAccount":
          void vscode.commands.executeCommand("code-coach-vscode.createAccount");
          break;
        case "signOut":
          void vscode.commands.executeCommand("code-coach-vscode.signOut");
          break;
        case "analyze":
          void vscode.commands.executeCommand("code-coach-vscode.analyzeCurrentFile");
          break;
        case "panelPrevious":
          navigatePanelHint(this.state, -1);
          break;
        case "panelNext":
          navigatePanelHint(this.state, 1);
          break;
        case "openOutput":
          this.state.outputChannel.show(true);
          break;
        default:
          break;
      }
    });

    webviewView.onDidDispose(() => {
      this._view = undefined;
    });
  }

  /** Refresh the sidebar HTML. Called by updateCoachPanel. */
  public refresh(): void {
    if (!this._view) { return; }
    this._view.webview.html = buildCoachPanelHtml(this.state);
  }

  /** Whether the sidebar webview is currently active. */
  public get isActive(): boolean {
    return this._view !== undefined;
  }
}
