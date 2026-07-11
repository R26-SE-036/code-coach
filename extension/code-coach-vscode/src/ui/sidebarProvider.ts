import * as vscode from "vscode";
import { ExtensionState } from "../types";
import { buildCoachPanelHtml } from "./panelHtml";
import { handleCoachPanelMessage } from "../analysis";

/**
 * WebviewViewProvider that renders the Coach Panel inside the
 * activity-bar sidebar. This makes Code Coach always accessible
 * without needing Ctrl+Shift+P.
 *
 * Message handling is shared with the standalone coach panel via
 * handleCoachPanelMessage (analysis.ts), so the two surfaces always
 * support exactly the same actions.
 */
export class CoachSidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "codeCoachSidebar";

  private _view: vscode.WebviewView | undefined;
  private _lastHtml: string | undefined;

  constructor(private readonly state: ExtensionState) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this._view = webviewView;
    this._lastHtml = undefined;

    webviewView.webview.options = {
      enableScripts: true,
    };

    webviewView.webview.onDidReceiveMessage(
      (message: { command?: string; index?: number }) => {
        handleCoachPanelMessage(this.state, message);
      },
    );

    webviewView.onDidDispose(() => {
      this._view = undefined;
      this._lastHtml = undefined;
    });

    this.refresh();
  }

  /**
   * Refresh the sidebar HTML. Called by updateCoachPanel with a prebuilt
   * HTML string (so panel + sidebar share one render). Skips the assignment
   * when the HTML is unchanged — reassigning webview.html tears down the
   * whole DOM, causing flicker and lost scroll position.
   */
  public refresh(html?: string): void {
    if (!this._view) { return; }
    const next = html ?? buildCoachPanelHtml(this.state);
    if (next === this._lastHtml) { return; }
    this._view.webview.html = next;
    this._lastHtml = next;
  }

  /** Whether the sidebar webview is currently active. */
  public get isActive(): boolean {
    return this._view !== undefined;
  }
}
