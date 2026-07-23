"""Render the Code Coach deployment/component architecture diagram (PNG + PDF)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT_DIR = Path(r"C:\Hello\University_Projects\code-coach\docs\diagrams")
OUT_DIR.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(17, 10.5))
ax.set_xlim(0, 170)
ax.set_ylim(0, 105)
ax.axis("off")

C = {
    "client":  "#E8F0FE", "client_edge":  "#1A56DB",
    "aws":     "#E7F3EF", "aws_edge":     "#0B7285",
    "fb":      "#FEF9E7", "fb_edge":      "#B7950B",
    "inner":   "#FFFFFF", "inner_edge":   "#64748B",
    "pipe":    "#EEF6EE", "pipe_edge":    "#2F855A",
    "reg":     "#F3E8FF", "reg_edge":     "#7E22CE",
    "art":     "#F1F5F9", "art_edge":     "#94A3B8",
    "future":  "#FAFAFA", "future_edge":  "#9CA3AF",
}

def box(x, y, w, h, fill, edge, lw=1.4, style="round,pad=0.6", ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, linewidth=lw,
                       edgecolor=edge, facecolor=fill, linestyle=ls, zorder=2)
    ax.add_patch(p)
    return p

def text(x, y, s, size=8, weight="normal", ha="left", va="top", color="#111827", family="sans-serif", style="normal"):
    ax.text(x, y, s, fontsize=size, fontweight=weight, ha=ha, va=va,
            color=color, family=family, style=style, zorder=5)

def arrow(x1, y1, x2, y2, label=None, lx=None, ly=None, color="#374151",
          ls="-", lw=1.6, size=10, connectionstyle="arc3,rad=0.0", labelsize=7.2):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=size,
                        linewidth=lw, color=color, linestyle=ls, zorder=4,
                        connectionstyle=connectionstyle)
    ax.add_patch(a)
    if label:
        text(lx if lx is not None else (x1 + x2) / 2,
             ly if ly is not None else (y1 + y2) / 2,
             label, size=labelsize, color=color, ha="center", va="center", weight="bold")

# ------------------------------------------------------------------- title
text(85, 104, "CodeGuru — Code Coach Component: Deployment & Component Architecture",
     size=15, weight="bold", ha="center")
text(85, 100.4, "as implemented, July 2026  ·  UML deployment/component hybrid  ·  "
     "solid = implemented & verified, dashed = planned", size=8.5, ha="center", color="#6B7280")

# ============================================================ CLIENT NODE
box(2, 26, 46, 70, C["client"], C["client_edge"], lw=2)
text(4, 94.5, "«device»  Student's Machine", size=10.5, weight="bold", color=C["client_edge"])
text(4, 91.3, "Visual Studio Code", size=9, weight="bold")

# marketplace
box(4, 82, 42, 6.5, C["inner"], C["client_edge"], ls="--")
text(25, 86.9, "«distribution»  VS Code Marketplace", size=8.5, weight="bold", ha="center", color=C["client_edge"])
text(25, 84.2, "publishes the packaged extension (vsce)", size=7.2, ha="center", color="#6B7280")

# extension container
box(4, 29, 42, 49, C["inner"], C["client_edge"])
text(25, 76.2, "«component»  Code Coach Extension  (TypeScript)", size=9, weight="bold", ha="center", color=C["client_edge"])

def ext_box(y, title, desc):
    box(6, y, 38, 7.6, "#F8FAFF", C["inner_edge"], lw=1)
    text(8, y + 6.7, title, size=8, weight="bold")
    text(8, y + 3.6, desc, size=7.1, color="#4B5563")

ext_box(66.5, "extension.ts — activation & wiring", "builds shared ExtensionState, registers commands,\nlisteners funnel edits into the debounce")
ext_box(57.5, "analysis.ts — analysis runner", "900 ms debounce → runAnalysisForEditor →\nrenders diagnostics as squiggles + 3-level hints")
ext_box(48.5, "auth.ts — identity workflows", "register / sign-in / silent restore,\nlearning-session bootstrap, event telemetry")
ext_box(39.5, "api.ts — the ONLY HTTP layer", "Bearer token attach, 401 → one refresh retry,\ntokens in VS Code SecretStorage")
ext_box(30.5, "ui/* — presentation", "status bar, decorations, coach panel,\nsidebar, CodeLens hints")

arrow(25, 82, 25, 78.6, color=C["client_edge"], ls="--")
text(26.8, 80.0, "installs / updates", size=7.2, color=C["client_edge"], weight="bold", va="center")

# ============================================================ AWS NODE
box(56, 26, 84, 70, C["aws"], C["aws_edge"], lw=2)
text(58, 94.5, "«execution environment»  Google Cloud — Cloud Run  (region: asia-south1)", size=10.5, weight="bold", color=C["aws_edge"])
text(58, 91.3, "Docker container (python:3.12-slim, 527 MB) · scales to zero · automatic HTTPS · env vars: JWT_SECRET, FIREBASE_PROJECT_ID", size=8)

# FastAPI app container
box(58, 29, 80, 59, C["inner"], C["aws_edge"])
text(98, 86.4, "«component»  Code Coach Backend  (FastAPI, Python)", size=9, weight="bold", ha="center", color=C["aws_edge"])

# API layer
box(60, 76.5, 76, 7, "#FFF8F0", C["inner_edge"], lw=1)
text(62, 82.6, "API routes  (/api/v1)   —   Bearer JWT: 1 h access token, rotating refresh token", size=8, weight="bold")
text(62, 79.7, "auth (register/login/refresh/logout/me) · learning-sessions · code-coach/analyze · diagnostics · events · dashboard",
     size=7.1, color="#4B5563")

# core + services row
box(60, 67.5, 37, 7.5, "#FFF8F0", C["inner_edge"], lw=1)
text(62, 74, "core — security & auth context", size=8, weight="bold")
text(62, 71.2, "Argon2id password hashing · JWT (HS256)\nrefresh-token rotation · session revocation", size=7.1, color="#4B5563")

box(99, 67.5, 37, 7.5, "#FFF8F0", C["inner_edge"], lw=1)
text(101, 74, "services — orchestration", size=8, weight="bold")
text(101, 71.2, "code_coach_service (persist + respond)\nlearning signals · evaluation logging", size=7.1, color="#4B5563")

# analysis pipeline
box(60, 47, 76, 18.5, C["pipe"], C["pipe_edge"], lw=1.4)
text(62, 64.2, "analysis pipeline  (analyzer.py orchestrates)", size=8.2, weight="bold", color=C["pipe_edge"])

stages = [
    ("parser_utils", "tree-sitter\nJava → AST\n+ parse health"),
    ("feature_extractor", "AST → 52\nwhole-file\nfeatures"),
    ("ml_engine", "5 LR gates\np = σ(w·x+b)\nvs thresholds"),
    ("issue_locators", "15 locators\nAST → exact\nline / column"),
    ("hint_engine", "3-level hints\nconcept →\ntargeted"),
]
sx = 61.5
for i, (name, desc) in enumerate(stages):
    box(sx, 48.5, 13.2, 12, "#FFFFFF", C["pipe_edge"], lw=1)
    text(sx + 6.6, 59.4, name, size=7.4, weight="bold", ha="center")
    text(sx + 6.6, 56.3, desc, size=6.6, ha="center", color="#4B5563")
    if i < 4:
        arrow(sx + 13.6, 54.5, sx + 15.0, 54.5, color=C["pipe_edge"], size=8, lw=1.3)
    sx += 15.1

# registry + artifacts row
box(60, 37.5, 37, 7.5, C["reg"], C["reg_edge"], lw=1.3)
text(62, 44, "error_catalog — single registry", size=8, weight="bold", color=C["reg_edge"])
text(62, 41.2, "15 error types: 5 ml_gated / 10 rule_only\nmodel files + calibrated thresholds per target", size=7.1, color="#4B5563")

box(99, 37.5, 37, 7.5, C["art"], C["art_edge"], lw=1.3)
text(101, 44, "«artifacts»  baked into the image", size=8, weight="bold", color="#475569")
text(101, 41.2, "models/*.joblib (5 trained LR models)\nknowledge_base/*.json (hints & lessons)", size=7.1, color="#4B5563")

# storage seam
box(60, 30, 76, 6, "#FFF8F0", C["inner_edge"], lw=1)
text(62, 35.1, "db — storage seam (repository pattern)", size=8, weight="bold")
text(62, 32.4, "build_storage(): FirestoreStorage (active)  |  MongoStorage  |  InMemoryStorage — swappable, zero route changes",
     size=7.1, color="#4B5563")

arrow(78.5, 44.9, 78.5, 46.8, color=C["reg_edge"], size=8, lw=1.2)

# ============================================================ FIREBASE NODE
box(56, 3, 84, 17.5, C["fb"], C["fb_edge"], lw=2)
text(58, 19, "«cloud service»  Firebase — Cloud Firestore  (project: code-guru-1b5d9)", size=10, weight="bold", color=C["fb_edge"])
rows = [
    ["users", "authSessions", "learningSessions", "codeDiagnostics"],
    ["learningEvents", "remediationTriggers", "conceptMastery", "collaborationSessions"],
]
for r, names in enumerate(rows):
    cx = 58.5
    cy = 12.2 - r * 5.4
    for name in names:
        w = 2.0 + len(name) * 0.72
        box(cx, cy, w, 4.4, "#FFFFFF", C["fb_edge"], lw=1)
        text(cx + w / 2, cy + 3.3, name, size=6.9, ha="center", family="monospace")
        cx += w + 1.8
text(58, 5.6, "document IDs = natural keys · single-equality queries + in-memory filter (no composite indexes)", size=7, color="#6B7280")

# ============================================================ FUTURE NODE
box(2, 3, 46, 17.5, C["future"], C["future_edge"], lw=1.4, ls="--")
text(4, 19, "«planned»  Other CodeGuru microservices", size=9.5, weight="bold", color="#6B7280")
text(4, 16, "Study Guider · Gamification Engine · Pair Review Studio\nseparate repos · separate Firebase projects (DB-per-service)",
     size=7.4, color="#6B7280")
text(4, 10.2, "inter-service events over Google Pub/Sub (or RabbitMQ)\n(contract: remediation.triggered, learning events)", size=7.4, color="#6B7280", style="italic")

# ============================================================ CROSS-NODE ARROWS
arrow(48.6, 62, 55.4, 62, color="#1F2937", lw=2.2, size=14)
text(52, 65.7, "HTTPS", size=7, ha="center", color="#1F2937", weight="bold")
text(52, 63.6, "JSON REST", size=7, ha="center", color="#1F2937", weight="bold")
text(52, 60.2, "Bearer JWT", size=7, ha="center", color="#1F2937", weight="bold")

arrow(98, 29, 98, 21.2, color=C["fb_edge"], lw=2.0, size=12)
text(100.3, 24.3, "google-cloud-firestore\nADC — same project, no key file", size=7.2, color=C["fb_edge"], weight="bold")

arrow(48.6, 12, 55.4, 12, color="#9CA3AF", lw=1.6, size=10, ls="--")
text(52, 14.6, "planned\nevents", size=6.8, ha="center", color="#9CA3AF")

fig.savefig(OUT_DIR / "code_coach_architecture.png", dpi=220, bbox_inches="tight", facecolor="white")
fig.savefig(OUT_DIR / "code_coach_architecture.pdf", bbox_inches="tight", facecolor="white")
print("written:", OUT_DIR / "code_coach_architecture.png")
print("written:", OUT_DIR / "code_coach_architecture.pdf")
