import * as vscode from "vscode";
import { CoachPanelState, ExtensionState } from "../types";
import { isSupportedDocument, formatDuration } from "./statusBar";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatProbability(value?: number): string {
  if (value === undefined) { return "n/a"; }
  return `${Math.round(value * 100)}%`;
}

export function getCoachPanelState(state: ExtensionState): CoachPanelState {
  const editor = vscode.window.activeTextEditor;
  const isSupported = !!editor && isSupportedDocument(editor.document);
  if (!editor || !isSupported) {
    return { signedIn: !!state.currentUser, userLabel: state.currentUser?.full_name, isSupportedFile: false, diagnostics: [], activeIndex: 0 };
  }
  const uriKey = editor.document.uri.toString();
  const diagnostics = state.lastDiagnosticsByUri.get(uriKey) ?? [];
  const activeIndex = Math.min(state.activeHintIndexByUri.get(uriKey) ?? 0, Math.max(0, diagnostics.length - 1));
  return {
    signedIn: !!state.currentUser, userLabel: state.currentUser?.full_name,
    fileLabel: vscode.workspace.asRelativePath(editor.document.uri, false),
    isSupportedFile: true, diagnostics, activeIndex,
    activeDiagnostic: diagnostics[activeIndex],
    snapshot: state.lastAnalysisSnapshotByUri.get(uriKey),
    learningSessionId: state.currentLearningSessionId,
  };
}

export function buildCoachPanelHtml(state: ExtensionState): string {
  const s = getCoachPanelState(state);
  const active = s.activeDiagnostic;
  const count = s.diagnostics.length;
  const has = count > 0;
  const idx = has ? `${s.activeIndex + 1} / ${count}` : "0 / 0";
  const sess = s.learningSessionId ?? s.snapshot?.learningSessionId ?? "—";

  let content: string;

  if (!s.signedIn) {
    content = `
      <div class="card empty-card">
        <div class="empty-icon">🔐</div>
        <h2>Sign in to Code Coach</h2>
        <p class="muted">Analyze Java files, save learning sessions, and track your progress across the platform.</p>
        <div class="btn-row">
          <button class="btn btn-primary" data-command="signIn">Sign In</button>
          <button class="btn btn-ghost" data-command="createAccount">Create Account</button>
        </div>
      </div>`;
  } else if (!s.isSupportedFile) {
    content = `
      <div class="card empty-card">
        <div class="empty-icon">☕</div>
        <h2>Open a Java file</h2>
        <p class="muted">Code Coach analyzes Java source files. Open one to get targeted hints and feedback.</p>
      </div>`;
  } else if (!s.snapshot) {
    content = `
      <div class="card empty-card">
        <div class="empty-icon">🔍</div>
        <h2>Ready to analyze</h2>
        <p class="muted">Run Code Coach to detect issues and receive concept hints, guidance, and targeted feedback.</p>
        <div class="btn-row">
          <button class="btn btn-primary" data-command="analyze">
            <span class="btn-icon">▶</span> Analyze Current File
          </button>
        </div>
      </div>`;
  } else if (count === 0) {
    content = `
      <div class="card clean-card">
        <div class="clean-badge">✓</div>
        <h2>All clear!</h2>
        <p class="muted">No target beginner issues detected in this file.</p>
        <div class="stat-row">
          <div class="stat"><span class="stat-label">Duration</span><span class="stat-value">${escapeHtml(formatDuration(s.snapshot.analysisDurationMs))}</span></div>
          <div class="stat"><span class="stat-label">Session</span><span class="stat-value mono">${escapeHtml(sess.substring(0, 8))}</span></div>
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" data-command="analyze">Analyze Again</button>
          <button class="btn btn-ghost" data-command="openOutput">Open Output</button>
        </div>
      </div>`;
  } else {
    const sevClass = active?.severity === "error" ? "sev-error" : active?.severity === "information" ? "sev-info" : "sev-warning";
    content = `
      <div class="card issue-card">
        <div class="issue-top">
          <div class="issue-title-group">
            <span class="eyebrow">Issue ${escapeHtml(idx)}</span>
            <h2>${escapeHtml(active?.error_type ?? "Issue")}</h2>
          </div>
          <span class="sev-pill ${sevClass}">${escapeHtml(active?.severity ?? "warning")}</span>
        </div>
        <p class="issue-msg">${escapeHtml(active?.message ?? "")}</p>

        <div class="stat-row">
          <div class="stat"><span class="stat-label">Line</span><span class="stat-value">${escapeHtml(String(active?.line ?? "—"))}</span></div>
          <div class="stat"><span class="stat-label">Concept</span><span class="stat-value">${escapeHtml(active?.concept_tag ?? "—")}</span></div>
          <div class="stat"><span class="stat-label">ML</span><span class="stat-value">${escapeHtml(formatProbability(active?.ml_probability))}</span></div>
          <div class="stat"><span class="stat-label">Locator</span><span class="stat-value">${escapeHtml(formatProbability(active?.locator_confidence))}</span></div>
        </div>

        <div class="hint-block hint-concept">
          <div class="hint-header"><span class="hint-icon">💡</span><h3>Concept Hint</h3></div>
          <p>${escapeHtml(active?.hints.concept ?? "")}</p>
        </div>
        <div class="hint-block hint-guidance">
          <div class="hint-header"><span class="hint-icon">🧭</span><h3>Guidance Hint</h3></div>
          <p>${escapeHtml(active?.hints.guidance ?? "")}</p>
        </div>
        <div class="hint-block hint-targeted">
          <div class="hint-header"><span class="hint-icon">🎯</span><h3>Targeted Hint</h3></div>
          <p>${escapeHtml(active?.hints.targeted ?? "")}</p>
        </div>

        <div class="btn-row nav-row">
          <button class="btn btn-nav" data-command="panelPrevious">← Previous</button>
          <button class="btn btn-nav" data-command="panelNext">Next →</button>
        </div>
        <div class="btn-row">
          <button class="btn btn-ghost" data-command="openOutput">Open Output</button>
        </div>
      </div>`;
  }

  const userLine = s.signedIn ? `Signed in as <strong>${escapeHtml(s.userLabel ?? "student")}</strong>` : "Not signed in";
  const logoutBtn = s.signedIn ? `<button class="btn btn-logout" data-command="signOut" title="Sign out">Sign Out</button>` : "";
  const fileLine = s.fileLabel ? escapeHtml(s.fileLabel) : "No Java file open";

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Code Coach</title>
<style>
:root{color-scheme:light dark}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

body{
  font-family:var(--vscode-font-family);
  color:var(--vscode-foreground);
  background:var(--vscode-editor-background);
  padding:0;margin:0;
  overflow-x:hidden;
}

/* ── Accent bar ── */
.accent-bar{
  height:3px;
  background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa,#6366f1);
  background-size:200% 100%;
  animation:shimmer 3s linear infinite;
}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* ── Page ── */
.page{display:flex;flex-direction:column;gap:14px;padding:16px 18px 24px}

/* ── Header ── */
.header{
  display:flex;flex-direction:column;gap:6px;
  padding:14px 16px;
  border-radius:10px;
  background:color-mix(in srgb,var(--vscode-editor-background) 85%,var(--vscode-button-background) 15%);
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 60%,transparent);
}
.header-title{
  display:flex;align-items:center;gap:8px;
  font-size:15px;font-weight:700;
  background:linear-gradient(135deg,#818cf8,#a78bfa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}
.header-title .logo{font-size:18px;-webkit-text-fill-color:initial}
.header-meta{font-size:12px;color:var(--vscode-descriptionForeground);line-height:1.4}
.header-meta strong{color:var(--vscode-foreground);font-weight:600}
.header-file{
  font-size:11px;color:var(--vscode-descriptionForeground);
  padding:4px 8px;border-radius:6px;
  background:color-mix(in srgb,var(--vscode-editor-background) 70%,var(--vscode-sideBar-background) 30%);
  font-family:var(--vscode-editor-font-family);word-break:break-all;
}

/* ── Cards ── */
.card{
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 50%,transparent);
  border-radius:10px;padding:16px;
  display:flex;flex-direction:column;gap:12px;
  background:color-mix(in srgb,var(--vscode-editor-background) 92%,var(--vscode-sideBar-background) 8%);
  animation:fadeUp .3s ease;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

.empty-card{align-items:center;text-align:center;padding:28px 20px}
.empty-icon{font-size:36px;margin-bottom:4px}
.empty-card h2{font-size:16px;font-weight:700}

/* ── Clean state ── */
.clean-card{align-items:center;text-align:center;padding:28px 20px;border-color:color-mix(in srgb,var(--vscode-terminal-ansiGreen) 40%,var(--vscode-panel-border) 60%)}
.clean-badge{
  width:48px;height:48px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:22px;font-weight:700;
  background:color-mix(in srgb,var(--vscode-terminal-ansiGreen) 14%,transparent);
  color:var(--vscode-terminal-ansiGreen);
  animation:pulse 2s ease-in-out infinite;
}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(74,222,128,.25)}50%{box-shadow:0 0 0 8px rgba(74,222,128,0)}}

/* ── Issue card ── */
.issue-top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
.issue-title-group{display:flex;flex-direction:column;gap:4px}
.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--vscode-descriptionForeground);font-weight:600}
.issue-card h2{font-size:15px;font-weight:700}
.issue-msg{line-height:1.5;font-size:13px;color:var(--vscode-foreground)}

/* Severity pills */
.sev-pill{
  flex-shrink:0;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;
  text-transform:uppercase;letter-spacing:.04em;
}
.sev-warning{background:rgba(251,191,36,.15);color:#fbbf24;border:1px solid rgba(251,191,36,.3)}
.sev-error{background:rgba(248,113,113,.15);color:#f87171;border:1px solid rgba(248,113,113,.3);animation:sevPulse 2s ease-in-out infinite}
.sev-info{background:rgba(96,165,250,.15);color:#60a5fa;border:1px solid rgba(96,165,250,.3)}
@keyframes sevPulse{0%,100%{box-shadow:0 0 0 0 rgba(248,113,113,.2)}50%{box-shadow:0 0 0 6px rgba(248,113,113,0)}}

/* ── Stat row ── */
.stat-row{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}
.stat{
  display:flex;flex-direction:column;gap:3px;padding:10px 12px;border-radius:8px;
  background:color-mix(in srgb,var(--vscode-editor-background) 78%,var(--vscode-sideBar-background) 22%);
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 30%,transparent);
}
.stat-label{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--vscode-descriptionForeground);font-weight:600}
.stat-value{font-size:13px;font-weight:600}
.mono{font-family:var(--vscode-editor-font-family);font-size:12px}

/* ── Hint blocks ── */
.hint-block{
  display:flex;flex-direction:column;gap:6px;
  padding:12px 14px;border-radius:8px;
  border-left:3px solid transparent;
  transition:background .2s,transform .15s;
}
.hint-block:hover{transform:translateX(3px)}
.hint-header{display:flex;align-items:center;gap:6px}
.hint-icon{font-size:14px;flex-shrink:0}
.hint-block h3{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.hint-block p{font-size:13px;line-height:1.5;color:var(--vscode-foreground)}

.hint-concept{border-left-color:#60a5fa;background:rgba(96,165,250,.06)}
.hint-concept:hover{background:rgba(96,165,250,.1)}
.hint-guidance{border-left-color:#2dd4bf;background:rgba(45,212,191,.06)}
.hint-guidance:hover{background:rgba(45,212,191,.1)}
.hint-targeted{border-left-color:#a78bfa;background:rgba(167,139,250,.06)}
.hint-targeted:hover{background:rgba(167,139,250,.1)}

/* ── Buttons ── */
.btn-row{display:flex;flex-wrap:wrap;gap:8px}
.btn{
  border:none;border-radius:8px;padding:8px 14px;cursor:pointer;font:inherit;
  font-size:12px;font-weight:600;transition:all .15s ease;display:inline-flex;align-items:center;gap:6px;
}
.btn:active{transform:scale(.97)}
.btn-icon{font-size:11px}

.btn-primary{
  background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;
  box-shadow:0 2px 8px rgba(99,102,241,.25);
}
.btn-primary:hover{box-shadow:0 4px 16px rgba(99,102,241,.35);transform:translateY(-1px)}

.btn-secondary{
  background:color-mix(in srgb,var(--vscode-button-background) 18%,transparent);
  color:var(--vscode-foreground);border:1px solid color-mix(in srgb,var(--vscode-panel-border) 60%,transparent);
}
.btn-secondary:hover{background:color-mix(in srgb,var(--vscode-button-background) 28%,transparent)}

.btn-ghost{
  background:transparent;color:var(--vscode-descriptionForeground);
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 40%,transparent);
}
.btn-ghost:hover{color:var(--vscode-foreground);border-color:var(--vscode-panel-border)}

.btn-nav{
  flex:1;justify-content:center;
  background:color-mix(in srgb,var(--vscode-editor-background) 70%,var(--vscode-button-background) 30%);
  color:var(--vscode-foreground);border:1px solid color-mix(in srgb,var(--vscode-panel-border) 50%,transparent);
}
.btn-nav:hover{background:color-mix(in srgb,var(--vscode-editor-background) 55%,var(--vscode-button-background) 45%)}

.nav-row{gap:6px}

/* ── Footer ── */
.footer{
  font-size:10px;color:var(--vscode-descriptionForeground);
  padding:0 4px;display:flex;align-items:center;gap:6px;
  border-top:1px solid color-mix(in srgb,var(--vscode-panel-border) 30%,transparent);
  padding-top:10px;
}
.footer .dot{width:4px;height:4px;border-radius:50%;background:var(--vscode-terminal-ansiGreen);flex-shrink:0}

.muted{font-size:13px;color:var(--vscode-descriptionForeground);line-height:1.5}

/* ── Logout button ── */
.btn-logout{
  padding:4px 10px;font-size:11px;
  background:transparent;color:var(--vscode-descriptionForeground);
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 50%,transparent);
  border-radius:6px;cursor:pointer;font:inherit;font-weight:600;
  transition:all .15s ease;
}
.btn-logout:hover{color:var(--vscode-errorForeground);border-color:var(--vscode-errorForeground)}

/* ── Header row ── */
.header-row{display:flex;justify-content:space-between;align-items:center;gap:8px}

/* ── Responsive ── */
@media(max-width:220px){
  .stat-row{grid-template-columns:1fr}
  .btn-row{flex-direction:column}
  .btn-nav{flex:unset}
  .header-title{font-size:13px}
  .hint-block{padding:8px 10px}
  .empty-icon{font-size:28px}
}
@media(max-width:300px){
  .page{padding:10px 12px 16px}
  .header{padding:10px 12px}
  .card{padding:12px}
  .issue-top{flex-direction:column;gap:6px}
  .sev-pill{align-self:flex-start}
}
</style>
</head>
<body>
  <div class="accent-bar"></div>
  <div class="page">
    <section class="header">
      <div class="header-row">
        <div class="header-title"><span class="logo">🎓</span> Code Coach</div>
        ${logoutBtn}
      </div>
      <div class="header-meta">${userLine}</div>
      <div class="header-file">📄 ${fileLine}</div>
    </section>
    ${content}
    <div class="footer">
      <span class="dot"></span>
      <span>Session: ${escapeHtml(sess.substring(0, 12))}${sess.length > 12 ? "…" : ""}</span>
    </div>
  </div>
  <script>
    const vscode=acquireVsCodeApi();
    for(const el of document.querySelectorAll("[data-command]")){
      el.addEventListener("click",()=>{
        const cmd=el.getAttribute("data-command");
        if(cmd)vscode.postMessage({command:cmd});
      });
    }
  </script>
</body>
</html>`;
}

export function updateCoachPanel(state: ExtensionState): void {
  if (state.coachPanel) {
    state.coachPanel.title = "Code Coach";
    state.coachPanel.webview.html = buildCoachPanelHtml(state);
  }

  // Also refresh the sidebar if it exists
  if (state.sidebarProvider) {
    state.sidebarProvider.refresh();
  }
}
