import * as vscode from "vscode";
import { cardKey, compilerKey, compilerProblemsFor, exampleKey, explainKey } from "../assistState";
import { conceptName, confidenceWords, engineWords, inlineCodeHtml, titleFor } from "../labels";
import { AssistEntry, CoachPanelState, DiagnosticItem, ExtensionState, HiddenFinding, ModelCard } from "../types";
import { isSupportedDocument, formatDuration } from "./statusBar";

const HINT_ORDER = ["concept", "guidance", "targeted"];

function hintReached(revealed: string, level: string): boolean {
  return HINT_ORDER.indexOf(revealed) >= HINT_ORDER.indexOf(level);
}

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

function formatTime(iso: string): string {
  const parsed = new Date(iso);
  return isNaN(parsed.getTime()) ? "" : parsed.toLocaleTimeString();
}

// One horizontal confidence bar; renders nothing when the value is absent
// (rule_only diagnostics have no ML probability).
function confidenceBar(label: string, value: number | undefined): string {
  if (value === undefined) { return ""; }
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return `
    <div class="conf-row">
      <span class="conf-label">${escapeHtml(label)}</span>
      <div class="conf-bar"><div class="conf-fill" style="width:${pct}%"></div></div>
      <span class="conf-val">${pct}%</span>
    </div>`;
}

export function getCoachPanelState(state: ExtensionState): CoachPanelState {
  // Prefer the active editor; when the webview itself has focus (the user just
  // clicked a panel button) activeTextEditor is undefined, so fall back to the
  // last Java file the user worked in instead of blanking the panel.
  const editor = vscode.window.activeTextEditor;
  let fileUri: vscode.Uri | undefined;
  if (editor && isSupportedDocument(editor.document)) {
    fileUri = editor.document.uri;
  } else if (state.lastSupportedUriKey) {
    fileUri = vscode.Uri.parse(state.lastSupportedUriKey);
  }

  if (!fileUri) {
    return { signedIn: !!state.currentUser, userLabel: state.currentUser?.full_name, isSupportedFile: false, diagnostics: [], activeIndex: 0 };
  }

  const uriKey = fileUri.toString();
  const diagnostics = state.lastDiagnosticsByUri.get(uriKey) ?? [];
  const activeIndex = Math.min(state.activeHintIndexByUri.get(uriKey) ?? 0, Math.max(0, diagnostics.length - 1));
  return {
    signedIn: !!state.currentUser, userLabel: state.currentUser?.full_name,
    fileLabel: vscode.workspace.asRelativePath(fileUri, false),
    isSupportedFile: true, diagnostics, activeIndex,
    activeDiagnostic: diagnostics[activeIndex],
    snapshot: state.lastAnalysisSnapshotByUri.get(uriKey),
    learningSessionId: state.currentLearningSessionId,
    fileUriKey: uriKey,
  };
}

function paragraphs(text: string): string {
  return text
    .split(/\n\s*\n/)
    .map((block) => `<p>${inlineCodeHtml(block.trim(), escapeHtml).replace(/\n/g, "<br/>")}</p>`)
    .join("");
}

function sourceNote(entry: AssistEntry): string {
  const left = entry.remaining !== undefined && entry.limit !== undefined
    ? ` · ${entry.remaining} of ${entry.limit} left today`
    : "";
  if (entry.source === "llm") { return `Written for your code${left}`; }
  if (entry.source === "cache") { return `Written for this code earlier${left}`; }
  if (entry.limitReached) { return "Today's explanations are used up - here are the hints instead. More tomorrow."; }
  return "From Code Coach's hint library";
}

function explanationCard(entry: AssistEntry | undefined, title: string): string {
  if (!entry) { return ""; }
  if (entry.loading) {
    return `<div class="assist-card"><div class="assist-title">${escapeHtml(title)}</div><p class="muted"><span class="spinner"></span> Reading your code…</p></div>`;
  }
  if (entry.error) {
    return `<div class="assist-card assist-error"><div class="assist-title">${escapeHtml(title)}</div><p>${escapeHtml(entry.error)}</p></div>`;
  }
  return `<div class="assist-card"><div class="assist-title">${escapeHtml(title)}</div>${paragraphs(entry.text ?? "")}<div class="assist-meta">${escapeHtml(sourceNote(entry))}</div></div>`;
}

function exampleCard(entry: AssistEntry | undefined): string {
  if (!entry) { return ""; }
  if (entry.loading) {
    return `<div class="assist-card"><div class="assist-title">📘 A similar example</div><p class="muted"><span class="spinner"></span> Finding one…</p></div>`;
  }
  if (entry.error) {
    return `<div class="assist-card assist-error"><div class="assist-title">📘 A similar example</div><p>${escapeHtml(entry.error)}</p></div>`;
  }
  const example = entry.example?.examples?.[0];
  if (!example) {
    return `<div class="assist-card"><div class="assist-title">📘 A similar example</div><p class="muted">No worked example for this one yet - the course unit explains it in full.</p>
      <button class="btn btn-ghost" data-command="panelLearn">🎓 Open the course unit</button></div>`;
  }
  const code = (label: string, body: string | undefined, tone: string) => body
    ? `<div class="code-label ${tone}">${label}</div><pre class="code ${tone}">${escapeHtml(body)}</pre>`
    : "";
  return `<div class="assist-card">
      <div class="assist-title">📘 ${escapeHtml(example.title || "A similar example")}</div>
      ${code("The mistake", example.buggy ?? example.code, "bad")}
      ${code("Fixed", example.fixed, "good")}
      ${example.note ? paragraphs(example.note) : ""}
      <button class="btn btn-ghost" data-command="panelLearn">🎓 Read the whole unit</button>
    </div>`;
}

function compilerCard(state: ExtensionState, uriKey: string | undefined): string {
  const problems = compilerProblemsFor(uriKey ? vscode.Uri.parse(uriKey) : undefined);
  if (problems.length === 0) { return ""; }
  const rows = problems.slice(0, 3).map((problem, index) => {
    const entry = state.assistByKey.get(compilerKey(problem));
    return `<div class="compiler-row">
        <div class="compiler-msg"><span class="row-line">L${problem.line}</span> ${escapeHtml(problem.message)}</div>
        ${entry ? explanationCard(entry, "What this means") : `<button class="btn btn-secondary" data-command="panelExplainCompiler" data-index="${index}">💬 Explain this error</button>`}
      </div>`;
  }).join("");
  return `<div class="card compiler-card">
      <div class="list-title">⛔ Does not compile yet (${problems.length})</div>
      <p class="muted">Logic checks need code that compiles. Fix these first - Code Coach can explain them.</p>
      ${rows}
    </div>`;
}

/**
 * The findings this analysis left out because the student reported them as
 * not a real bug. Without this the panel said "All clear!" over a mistake that
 * was still there, and the student had no way to get it back.
 */
function hiddenCard(hidden: HiddenFinding[]): string {
  if (hidden.length === 0) { return ""; }
  const rows = hidden.slice(0, 5).map((finding, index) => `<div class="hidden-row">
        <span class="row-line">L${finding.line}</span>
        <span class="hidden-title">${escapeHtml(titleFor({ title: finding.title ?? undefined, error_type: finding.error_type }))}</span>
        <button class="btn btn-secondary btn-undo" data-command="undoReport" data-index="${index}" title="Show and count this finding again">Undo report</button>
      </div>`).join("");
  const what = hidden.length === 1 ? "1 finding hidden" : `${hidden.length} findings hidden`;
  return `<div class="card hidden-card">
      <div class="list-title">🚩 ${what} because you reported ${hidden.length === 1 ? "it" : "them"}</div>
      <p class="muted">You marked ${hidden.length === 1 ? "it" : "them"} as not a real bug, so Code Coach does not show or count ${hidden.length === 1 ? "it" : "them"} here. Changed your mind? Undo the report.</p>
      ${rows}
    </div>`;
}

function percent(value: number | undefined): string {
  return value === undefined || value === null ? "—" : `${Math.round(value * 100)}%`;
}

function cardList(items: string[]): string {
  return `<ul class="card-list">${items.map((item) => `<li>${inlineCodeHtml(item, escapeHtml)}</li>`).join("")}</ul>`;
}

/** The model card, in words a student can follow: what it looks for, how it learned, how it did, where it fails. */
export function modelCardHtml(card: ModelCard): string {
  const p = card.performance;
  const row = (label: string, m: { precision?: number; recall?: number; f1?: number } | null | undefined) => m
    ? `<tr><td>${escapeHtml(label)}</td><td>${percent(m.precision)}</td><td>${percent(m.recall)}</td><td>${m.f1 === undefined ? "—" : m.f1.toFixed(2)}</td></tr>`
    : "";
  const human = p.human_code.flags
    ? `On code written by people it raised ${p.human_code.flags} flag${p.human_code.flags === 1 ? "" : "s"}: ${p.human_code.real} real, ${p.human_code.plausible} plausible, ${p.human_code.wrong} wrong.`
    : "It raised no flags on the code written by people that it was checked on.";
  const curated = p.curated
    ? ` On ${p.curated.snippets} hand-labelled snippets it found ${Math.round(p.curated.recall * p.curated.mistakes)} of ${p.curated.mistakes} mistakes with ${p.curated.false_alarms} false alarm${p.curated.false_alarms === 1 ? "" : "s"}.`
    : "";
  return `<div class="model-card">
      <div class="assist-title">📄 Model card: ${escapeHtml(card.title)}</div>
      ${card.in_use ? "" : `<p class="muted">This model is switched off at the moment; the older detector is deciding this kind of finding.</p>`}
      <p>${inlineCodeHtml(card.detects, escapeHtml)}</p>
      <p class="muted">${inlineCodeHtml(card.considers, escapeHtml)}</p>
      <div class="code-label bad">The mistake</div><pre class="code bad">${escapeHtml(card.example.mistake)}</pre>
      <div class="code-label good">Looks similar, but correct</div><pre class="code good">${escapeHtml(card.example.lookalike)}</pre>
      <h4>Model</h4>
      <p>${escapeHtml(card.model.family_name)} over ${card.model.feature_count} facts about each place. It flags a place when its score reaches ${card.model.threshold.toFixed(2)}: ${escapeHtml(card.model.threshold_rule)}.</p>
      <h4>Trained on</h4>
      <p>${escapeHtml(card.training_data.description)}</p>
      <p class="muted">${card.training_data.training_sites.toLocaleString()} places to learn from (${card.training_data.training_mistakes.toLocaleString()} mistakes); tested on ${card.training_data.test_sites.toLocaleString()} it never saw (${card.training_data.test_mistakes.toLocaleString()} mistakes). ${escapeHtml(card.training_data.split)}</p>
      <h4>How well it does</h4>
      <table class="card-table"><tr><th></th><th>Precision</th><th>Recall</th><th>F1</th></tr>
        ${row("This model", p.test)}${row(p.previous.name.startsWith("the detector") ? "Before" : "A simple rule", p.previous)}${row("CodeBERT (offline)", p.codebert)}
      </table>
      <p class="muted">Precision: of the places it flags, how many are real mistakes. Recall: of the real mistakes, how many it flags.</p>
      <p>${escapeHtml(human + curated)}</p>
      <h4>When not to trust it</h4>
      ${cardList(card.unreliable_when)}
      <h4>Known limitations</h4>
      ${cardList([...card.limitations, ...(card.general_limitations ?? [])])}
    </div>`;
}

function modelCardBlock(entry: AssistEntry | undefined): string {
  if (!entry) {
    return `<button class="btn btn-ghost" data-command="panelModelCard" title="What this model looks for, what it learned from, how it was tested and where it can be wrong">📄 How this model was tested</button>`;
  }
  if (entry.loading) { return `<p class="muted"><span class="spinner"></span> Loading the model card…</p>`; }
  if (entry.error || !entry.card) {
    return `<div class="assist-card assist-error"><p>${escapeHtml(entry.error ?? "No model card for this one.")}</p></div>`;
  }
  return modelCardHtml(entry.card);
}

function decidedBlock(state: ExtensionState, active: DiagnosticItem | undefined): string {
  if (!active) { return ""; }
  const bars = [
    confidenceBar(active.detection_engine === "candidate_ml" ? "Model" : "ML gate", active.ml_probability),
    confidenceBar("Rule", active.locator_confidence),
  ].join("");
  // Only a model has a card. Kept open once a card is asked for, because
  // the panel is redrawn when it arrives.
  const hasModel = active.detection_engine === "candidate_ml";
  const card = hasModel ? state.assistByKey.get(cardKey(active)) : undefined;
  return `<details class="decided"${card ? " open" : ""}>
      <summary>How Code Coach decided</summary>
      <p class="muted">${escapeHtml(engineWords(active.detection_engine))}.</p>
      ${bars.trim() ? `<div class="conf-block">${bars}</div>` : ""}
      <p class="mono muted">${escapeHtml(active.error_type)} · ${escapeHtml(active.concept_tag)} · ${escapeHtml(active.detection_engine)}</p>
      ${hasModel ? modelCardBlock(card) : ""}
    </details>`;
}

export function buildCoachPanelHtml(state: ExtensionState): string {
  const s = getCoachPanelState(state);
  const active = s.activeDiagnostic;
  const count = s.diagnostics.length;
  const has = count > 0;
  const idx = has ? `${s.activeIndex + 1} / ${count}` : "0 / 0";
  const sess = s.learningSessionId ?? s.snapshot?.learningSessionId ?? "—";
  const hidden = s.signedIn && s.isSupportedFile ? s.snapshot?.hiddenByReport ?? [] : [];

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
      <div class="card clean-card${hidden.length ? " clean-partial" : ""}">
        <div class="clean-badge">✓</div>
        <h2>${hidden.length ? "Nothing else found" : "All clear!"}</h2>
        <p class="muted">${hidden.length
          ? `Apart from what you reported (below), none of the 30 logic mistakes Code Coach looks for were found in this file.`
          : "None of the 30 logic mistakes Code Coach looks for were found in this file."}</p>
        <div class="stat-row">
          <div class="stat"><span class="stat-label">Checked in</span><span class="stat-value">${escapeHtml(formatDuration(s.snapshot.analysisDurationMs))}</span></div>
          <div class="stat"><span class="stat-label">Fixed this session</span><span class="stat-value">${state.fixedThisSession}</span></div>
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" data-command="analyze">Analyze Again</button>
          <button class="btn btn-ghost" data-command="openOutput">Open Output</button>
        </div>
      </div>`;
  } else {
    const sevClass = active?.severity === "error" ? "sev-error" : active?.severity === "information" ? "sev-info" : "sev-warning";
    const navDisabled = count < 2 ? " disabled" : "";

    // Dot indicators (hidden for large counts where they would overflow).
    const dots = count > 1 && count <= 12
      ? `<div class="nav-dots">${s.diagnostics.map((_, k) =>
          `<button class="dot-nav${k === s.activeIndex ? " active" : ""}" data-command="panelSelect" data-index="${k}" title="Issue ${k + 1}" aria-label="Go to issue ${k + 1}"></button>`,
        ).join("")}</div>`
      : "";

    const confidence = confidenceWords(active?.confidence ?? 0);
    const revealed = active ? state.revealedHintLevels.get(active.diagnostic_id) ?? "concept" : "concept";

    content = `
      <div class="card issue-card">
        <div class="nav-bar">
          <button class="icon-btn" data-command="panelPrevious" title="Previous issue (←)" aria-label="Previous issue"${navDisabled}>‹</button>
          <div class="nav-center">
            <span class="nav-pos">Issue ${escapeHtml(idx)}</span>
            ${dots}
          </div>
          <button class="icon-btn" data-command="panelNext" title="Next issue (→)" aria-label="Next issue"${navDisabled}>›</button>
        </div>

        <div class="issue-top">
          <div class="issue-title-group">
            <span class="eyebrow">${escapeHtml(conceptName(active?.concept_tag))} · line ${escapeHtml(String(active?.line ?? "—"))}</span>
            <h2>${escapeHtml(active ? titleFor(active) : "Issue")}</h2>
          </div>
          <span class="conf-pill conf-${confidence.tone}" title="How sure Code Coach is">${escapeHtml(confidence.label)}</span>
        </div>
        <p class="issue-msg">${escapeHtml(active?.message ?? "")}</p>

        <div class="hint-block hint-concept">
          <div class="hint-header"><span class="hint-icon">💡</span><h3>Concept Hint</h3></div>
          <p>${inlineCodeHtml(active?.hints.concept ?? "", escapeHtml)}</p>
        </div>
        ${/*
          Guidance and targeted wait to be asked for, one at a time - see
          "Hint levels, in order" in analysis.ts. All three used to be printed
          at once, so the hint that nearly gives the fix away was on screen
          before the student had read the first one.
        */""}
        ${hintReached(revealed, "guidance")
          ? `<div class="hint-block hint-guidance">
          <div class="hint-header"><span class="hint-icon">🧭</span><h3>Guidance Hint</h3></div>
          <p>${inlineCodeHtml(active?.hints.guidance ?? "", escapeHtml)}</p>
        </div>`
          : `<button class="btn btn-secondary hint-reveal" data-command="panelRevealHint" title="Still stuck after the concept hint? This one narrows it down.">🧭 Show the guidance hint</button>`}
        ${hintReached(revealed, "targeted")
          ? `<div class="hint-block hint-targeted">
          <div class="hint-header"><span class="hint-icon">🎯</span><h3>Targeted Hint</h3></div>
          <p>${inlineCodeHtml(active?.hints.targeted ?? "", escapeHtml)}</p>
        </div>`
          : hintReached(revealed, "guidance")
            ? `<button class="btn btn-secondary hint-reveal" data-command="panelRevealHint" title="The last hint looks at this exact line of your code.">🎯 Show the targeted hint</button>`
            : ""}

        <div class="assist-row">
          <button class="btn btn-primary" data-command="panelExplain" title="An explanation written for your code - never the answer">✨ Explain in my code</button>
          <button class="btn btn-secondary" data-command="panelExample" title="A worked example of the same mistake">📘 Similar example</button>
          <button class="btn btn-secondary" data-command="panelLearn" title="The free course unit on this mistake, in your browser">🎓 Learn this</button>
        </div>
        ${active ? explanationCard(state.assistByKey.get(explainKey(active)), "✨ In your code") : ""}
        ${active ? exampleCard(state.assistByKey.get(exampleKey(active))) : ""}

        <div class="btn-row">
          <button class="btn btn-secondary" data-command="panelGoto"><span class="btn-icon">↪</span> Jump to Line ${escapeHtml(String(active?.line ?? ""))}</button>
          ${/*
            FR-09's second half: the card navigates to the web dashboard.
            The panel had no link to it at all - portalUrl was used only by the
            sign-in flow - so the IDE and the dashboard were two surfaces with
            nothing joining them.

            Hidden when there is no concept tag, because without one the link
            can only reach the generic list, and a button that sometimes lands
            somewhere useful and sometimes does not is worse than no button.
          */""}
          ${active?.concept_tag
            ? `<button class="btn btn-ghost" data-command="openStudy" title="Open the full micro-lesson and your progress in the browser">📖 Study this concept</button>`
            : ""}
          ${active && state.disputedDiagnosticIds.has(active.diagnostic_id)
            ? `<button class="btn btn-ghost btn-disputed" disabled>✓ Reported — thanks</button>`
            : `<button class="btn btn-ghost" data-command="panelDispute" title="Tell us this warning is wrong — it improves detection">🚩 Not a real bug?</button>`}
          <button class="btn btn-ghost" data-command="panelMute" title="Stop showing this kind of finding">🔕 Mute this kind</button>
        </div>
        ${decidedBlock(state, active)}
      </div>
      ${count > 1 ? `
      <div class="card list-card">
        <div class="list-title">All issues in this file (${count})</div>
        ${s.diagnostics.map((d, k) => `
        <button class="issue-row${k === s.activeIndex ? " active" : ""}" data-command="panelSelect" data-index="${k}">
          <span class="row-idx">${k + 1}</span>
          <span class="row-line">L${d.line}</span>
          <span class="row-type">${escapeHtml(titleFor(d))}</span>
        </button>`).join("")}
      </div>` : ""}`;
  }

  const fixedBanner = state.lastFix && Date.now() - state.lastFix.at < 12_000
    ? `<div class="fixed-banner" role="status"><span class="fixed-icon">✓</span><div><strong>Fixed it!</strong><span>${escapeHtml(state.lastFix.title)}</span></div></div>`
    : "";
  void sess;

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
  background:linear-gradient(90deg,#2563eb,#3b82f6,#60a5fa,#2563eb);
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
  background:linear-gradient(135deg,#3b82f6,#60a5fa);
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
.hint-reveal{width:100%;justify-content:center;margin:2px 0 4px}
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

.hint-concept{border-left-color:#3b82f6;background:rgba(59,130,246,.06)}
.hint-concept:hover{background:rgba(59,130,246,.1)}
.hint-guidance{border-left-color:#64748b;background:rgba(100,116,139,.06)}
.hint-guidance:hover{background:rgba(100,116,139,.1)}
.hint-targeted{border-left-color:#60a5fa;background:rgba(96,165,250,.06)}
.hint-targeted:hover{background:rgba(96,165,250,.1)}

/* ── Buttons ── */
.btn-row{display:flex;flex-wrap:wrap;gap:8px}
.btn{
  border:none;border-radius:8px;padding:8px 14px;cursor:pointer;font:inherit;
  font-size:12px;font-weight:600;transition:all .15s ease;display:inline-flex;align-items:center;gap:6px;
}
.btn:active{transform:scale(.97)}
.btn-icon{font-size:11px}

.btn-primary{
  background:linear-gradient(135deg,#2563eb,#3b82f6);color:#fff;
  box-shadow:0 2px 8px rgba(37,99,235,.25);
}
.btn-primary:hover{box-shadow:0 4px 16px rgba(37,99,235,.35);transform:translateY(-1px)}

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
.btn-disputed{color:var(--vscode-terminal-ansiGreen);border-color:color-mix(in srgb,var(--vscode-terminal-ansiGreen) 40%,transparent);cursor:default}

/* ── Issue navigation bar ── */
.nav-bar{
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:6px 8px;border-radius:8px;
  background:color-mix(in srgb,var(--vscode-editor-background) 78%,var(--vscode-sideBar-background) 22%);
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 30%,transparent);
}
.icon-btn{
  width:28px;height:28px;border-radius:6px;border:1px solid color-mix(in srgb,var(--vscode-panel-border) 50%,transparent);
  background:transparent;color:var(--vscode-foreground);cursor:pointer;
  font-size:16px;line-height:1;font-weight:700;display:flex;align-items:center;justify-content:center;
  transition:all .15s ease;flex-shrink:0;
}
.icon-btn:hover:not([disabled]){background:color-mix(in srgb,var(--vscode-button-background) 25%,transparent);transform:scale(1.06)}
.icon-btn[disabled]{opacity:.35;cursor:default}
.nav-center{display:flex;flex-direction:column;align-items:center;gap:5px;min-width:0}
.nav-pos{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--vscode-descriptionForeground)}
.nav-dots{display:flex;gap:5px;flex-wrap:wrap;justify-content:center}
.dot-nav{
  width:8px;height:8px;border-radius:50%;border:none;padding:0;cursor:pointer;
  background:color-mix(in srgb,var(--vscode-descriptionForeground) 40%,transparent);
  transition:all .15s ease;
}
.dot-nav:hover{background:var(--vscode-descriptionForeground);transform:scale(1.25)}
.dot-nav.active{background:#3b82f6;transform:scale(1.3)}

/* ── Confidence bars ── */
.conf-block{display:flex;flex-direction:column;gap:6px;padding:10px 12px;border-radius:8px;
  background:color-mix(in srgb,var(--vscode-editor-background) 78%,var(--vscode-sideBar-background) 22%);
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 30%,transparent);
}
.conf-title{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--vscode-descriptionForeground);font-weight:600}
.conf-row{display:flex;align-items:center;gap:8px}
.conf-label{font-size:11px;color:var(--vscode-descriptionForeground);width:56px;flex-shrink:0}
.conf-bar{flex:1;height:6px;border-radius:3px;overflow:hidden;
  background:color-mix(in srgb,var(--vscode-descriptionForeground) 18%,transparent)}
.conf-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,#2563eb,#60a5fa);transition:width .3s ease}
.conf-val{font-size:11px;font-weight:600;width:34px;text-align:right;flex-shrink:0}

/* ── Issue list ── */
.list-card{gap:6px;padding:12px}
.list-title{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--vscode-descriptionForeground);font-weight:700;padding:0 2px 4px}
.issue-row{
  display:flex;align-items:center;gap:8px;width:100%;text-align:left;
  padding:7px 10px;border-radius:6px;cursor:pointer;font:inherit;font-size:12px;
  background:transparent;color:var(--vscode-foreground);
  border:1px solid transparent;transition:all .12s ease;
}
.issue-row:hover{background:color-mix(in srgb,var(--vscode-button-background) 15%,transparent)}
.issue-row.active{
  background:color-mix(in srgb,var(--vscode-button-background) 22%,transparent);
  border-color:color-mix(in srgb,#3b82f6 45%,transparent);
}
.row-idx{
  width:18px;height:18px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:700;
  background:color-mix(in srgb,var(--vscode-descriptionForeground) 20%,transparent);
}
.issue-row.active .row-idx{background:#3b82f6;color:#fff}
.row-line{font-family:var(--vscode-editor-font-family);font-size:11px;color:var(--vscode-descriptionForeground);flex-shrink:0;width:34px}
.row-type{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}

/* ── Confidence pill (words, not a percentage) ── */
.conf-pill{flex-shrink:0;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.02em}
.conf-high{background:rgba(248,113,113,.14);color:#f87171;border:1px solid rgba(248,113,113,.3)}
.conf-medium{background:rgba(251,191,36,.14);color:#fbbf24;border:1px solid rgba(251,191,36,.3)}
.conf-low{background:rgba(96,165,250,.14);color:#60a5fa;border:1px solid rgba(96,165,250,.3)}

/* ── Help on demand ── */
.assist-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
.assist-row .btn{justify-content:center;padding:8px 6px}
.assist-card{
  display:flex;flex-direction:column;gap:8px;padding:12px 14px;border-radius:8px;
  border:1px solid color-mix(in srgb,#8b5cf6 35%,transparent);
  background:color-mix(in srgb,#8b5cf6 7%,transparent);
  animation:fadeUp .25s ease;
}
.assist-error{border-color:color-mix(in srgb,var(--vscode-errorForeground) 40%,transparent);background:color-mix(in srgb,var(--vscode-errorForeground) 6%,transparent)}
.assist-title{font-size:12px;font-weight:700;letter-spacing:.02em}
.assist-card p{font-size:13px;line-height:1.55}
.assist-card code,.hint-block code{font-family:var(--vscode-editor-font-family);font-size:12px;padding:1px 5px;border-radius:4px;
  background:color-mix(in srgb,var(--vscode-textCodeBlock-background) 80%,transparent)}
.assist-meta{font-size:11px;color:var(--vscode-descriptionForeground)}
.code-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.code-label.bad{color:#f87171}.code-label.good{color:var(--vscode-terminal-ansiGreen)}
pre.code{font-family:var(--vscode-editor-font-family);font-size:12px;line-height:1.5;padding:8px 10px;border-radius:6px;overflow-x:auto;white-space:pre;
  background:var(--vscode-textCodeBlock-background);border-left:3px solid transparent}
pre.code.bad{border-left-color:#f87171}pre.code.good{border-left-color:var(--vscode-terminal-ansiGreen)}
.spinner{display:inline-block;width:10px;height:10px;border-radius:50%;border:2px solid currentColor;border-right-color:transparent;animation:spin .8s linear infinite;vertical-align:-1px;margin-right:4px}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── How Code Coach decided ── */
.decided{border-top:1px solid color-mix(in srgb,var(--vscode-panel-border) 35%,transparent);padding-top:8px}
.decided summary{cursor:pointer;font-size:11px;font-weight:600;color:var(--vscode-descriptionForeground)}
.decided[open] summary{margin-bottom:8px}
.decided p{margin:4px 0}
.model-card{display:flex;flex-direction:column;gap:4px;margin-top:8px;padding:10px 12px;border-radius:8px;
  border:1px solid color-mix(in srgb,var(--vscode-panel-border) 45%,transparent);font-size:12px;line-height:1.45}
.model-card h4{margin:8px 0 2px;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--vscode-descriptionForeground)}
.card-table{border-collapse:collapse;font-size:11.5px;margin:2px 0}
.card-table th,.card-table td{padding:3px 8px 3px 0;text-align:left}
.card-table th{font-weight:600;color:var(--vscode-descriptionForeground)}
.card-table tr:nth-child(2) td{font-weight:600}
.card-list{margin:2px 0;padding-left:18px}
.card-list li{margin:2px 0}

/* ── Fixed it! ── */
.fixed-banner{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:10px;
  background:color-mix(in srgb,var(--vscode-terminal-ansiGreen) 14%,transparent);
  border:1px solid color-mix(in srgb,var(--vscode-terminal-ansiGreen) 40%,transparent);
  animation:pop .45s cubic-bezier(.2,1.4,.4,1)}
.fixed-banner div{display:flex;flex-direction:column;font-size:12px}
.fixed-banner strong{font-size:13px;color:var(--vscode-terminal-ansiGreen)}
.fixed-icon{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font-weight:800;
  background:var(--vscode-terminal-ansiGreen);color:var(--vscode-editor-background)}
@keyframes pop{0%{transform:scale(.85);opacity:0}100%{transform:scale(1);opacity:1}}

/* ── Compiler errors ── */
.clean-partial{border-color:var(--vscode-panel-border)}
.clean-partial .clean-badge{display:none}
.hidden-card{border-color:color-mix(in srgb,var(--vscode-editorWarning-foreground) 30%,var(--vscode-panel-border) 70%)}
.hidden-row{display:flex;align-items:center;gap:8px;padding:8px 0;border-top:1px solid color-mix(in srgb,var(--vscode-panel-border) 25%,transparent)}
.hidden-title{flex:1;font-size:12px;min-width:0}
.btn-undo{padding:4px 10px;font-size:11px;flex-shrink:0}
.compiler-card{border-color:color-mix(in srgb,var(--vscode-errorForeground) 35%,var(--vscode-panel-border) 65%)}
.compiler-row{display:flex;flex-direction:column;gap:6px;padding:8px 0;border-top:1px solid color-mix(in srgb,var(--vscode-panel-border) 25%,transparent)}
.compiler-msg{font-size:12px;line-height:1.45;font-family:var(--vscode-editor-font-family)}

/* ── Footer ── */
.footer{
  font-size:10px;color:var(--vscode-descriptionForeground);
  padding:0 4px;display:flex;align-items:center;gap:6px;
  border-top:1px solid color-mix(in srgb,var(--vscode-panel-border) 30%,transparent);
  padding-top:10px;
}
.footer .dot{width:6px;height:6px;border-radius:50%;background:var(--vscode-terminal-ansiGreen);flex-shrink:0}
.footer .dot.offline{background:var(--vscode-errorForeground)}

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
@media(max-width:340px){
  .assist-row{grid-template-columns:1fr}
}
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
    ${fixedBanner}
    ${s.signedIn && s.isSupportedFile ? compilerCard(state, s.fileUriKey) : ""}
    ${content}
    ${hiddenCard(hidden)}
    <div class="footer">
      <span class="dot${state.backendOffline ? " offline" : ""}"></span>
      <span>${state.backendOffline ? "Offline - Code Coach could not reach its server" : s.snapshot ? `Checked ${escapeHtml(formatTime(s.snapshot.analyzedAt))} in ${escapeHtml(formatDuration(s.snapshot.analysisDurationMs))}` : "Ready"}${state.fixedThisSession ? ` · ${state.fixedThisSession} fixed this session` : ""}</span>
    </div>
  </div>
  <script>
    const vscode=acquireVsCodeApi();
    function send(command,index){
      vscode.postMessage(index===undefined?{command:command}:{command:command,index:index});
    }
    for(const el of document.querySelectorAll("[data-command]")){
      el.addEventListener("click",()=>{
        const cmd=el.getAttribute("data-command");
        if(!cmd)return;
        const idx=el.getAttribute("data-index");
        send(cmd,idx===null?undefined:Number(idx));
      });
    }
    // Keyboard navigation while the panel has focus
    window.addEventListener("keydown",(e)=>{
      if(e.key==="ArrowLeft"){send("panelPrevious");}
      else if(e.key==="ArrowRight"){send("panelNext");}
    });
  </script>
</body>
</html>`;
}

export function updateCoachPanel(state: ExtensionState): void {
  // Build ONCE and share between panel and sidebar; reassigning webview.html
  // tears down the whole DOM (flicker + lost scroll), so both surfaces skip
  // the assignment when nothing actually changed. updateAnalysisStatusBar
  // calls this on every editor event, so the skip path is the common path.
  const html = buildCoachPanelHtml(state);

  if (state.coachPanel && state.lastPanelHtml !== html) {
    state.coachPanel.webview.html = html;
    state.lastPanelHtml = html;
  }

  if (state.sidebarProvider) {
    state.sidebarProvider.refresh(html);
  }
}
