"""Render the Code Guru PLATFORM architecture figure (all four components).

Two-column IEEE figure (7.16 in wide) and grayscale-safe: boxes are
distinguished by border weight and label rather than colour. Each
student-facing surface sits directly above the service it talks to, so no
connector crosses another. Vertical space is kept tight so the figure does
not dominate a page.

Outputs: codeguru_platform_architecture.png (600 dpi) and .pdf (vector)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT = Path(r"C:\Hello\University_Projects\code-coach\docs\diagrams")
OUT.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7.16, 3.55))
ax.set_xlim(0, 100); ax.set_ylim(0, 52); ax.axis("off")

INK, GREY = "#141414", "#565656"
F_MID, F_LIGHT, F_WHITE = "#e9e9e9", "#f6f6f6", "#ffffff"

def box(x, y, w, h, fill=F_WHITE, edge=INK, lw=1.0, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.2,rounding_size=0.4",
                 linewidth=lw, edgecolor=edge, facecolor=fill,
                 linestyle=ls, zorder=2))

def txt(x, y, s, size=6.2, weight="normal", ha="center", va="center",
        color=INK, style="normal"):
    ax.text(x, y, s, fontsize=size, fontweight=weight, ha=ha, va=va,
            color=color, style=style, zorder=5, linespacing=1.35)

def band(y, label):
    ax.text(4.2, y, label, fontsize=5.6, fontweight="bold", color=GREY,
            ha="center", va="center", rotation=90, zorder=5)

def arrow(x1, y1, x2, y2, lw=1.0, ms=7, color=INK, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=ms, linewidth=lw, color=color, linestyle=ls,
                 zorder=4, connectionstyle="arc3,rad=0"))

COLS = [(11, 21), (33.3, 21), (55.6, 21), (77.9, 20.1)]
CTR = [x + w / 2 for x, w in COLS]

# ── student-facing surfaces
band(46.8, "SURFACES")
box(11, 43.6, 21, 6.2, F_MID, INK, lw=1.2)
txt(21.5, 47.9, "VS Code extension", size=6.6, weight="bold")
txt(21.5, 45.5, "inline hints, navigation", size=5.4, color=GREY)
box(33.3, 43.6, 43.3, 6.2, F_MID, INK, lw=1.2)
txt(55, 47.9, "Web dashboard", size=6.6, weight="bold")
txt(55, 45.5, "micro-lessons \u00b7 quizzes \u00b7 mastery \u00b7 practice", size=5.4, color=GREY)
box(77.9, 43.6, 20.1, 6.2, F_MID, INK, lw=1.2)
txt(88, 47.9, "Shared editor", size=6.6, weight="bold")
txt(88, 45.5, "instrumented pairing", size=5.4, color=GREY)

# ── microservices
band(29.5, "MICROSERVICES")
SVC_Y, SVC_H = 20.5, 17.6
SERVICES = [
    ("CODE COACH", "detection + hints",
     "Tree-sitter AST\n52 whole-file features\n"
     "15 error types, 5 ML-gated\n3-level scaffolded hints",
     "also: identity provider", 1.7),
    ("STUDY GUIDER", "adaptive remediation",
     "struggle classifier\n(Random Forest)\n"
     "Graph RAG micro-lessons\nauto-generated quizzes",
     "trigger: 3 repeats per concept", 1.0),
    ("GAMIFICATION", "adaptive practice",
     "mastery-matched practice\nprogress on resolved bugs\n"
     "frustration-aware pacing",
     "consumes shared signals", 1.0),
    ("PAIRPATH", "collaboration support",
     "behavioural events\ncollaboration-state\n"
     "classifier (XGBoost)\nnon-solution nudges",
     "5 states \u00b7 cooldown policy", 1.0),
]
for (x, w), (title, sub, bodytext, foot, lw) in zip(COLS, SERVICES):
    box(x, SVC_Y, w, SVC_H, F_WHITE, INK, lw=lw)
    cx = x + w / 2
    txt(cx, 35.4, title, size=7.0, weight="bold")
    txt(cx, 33.2, sub, size=5.8, style="italic", color=GREY)
    txt(cx, 28.2, bodytext, size=5.6)
    txt(cx, 22.4, foot, size=5.2, color=GREY, style="italic")

for cx in CTR:
    arrow(cx, 43.3, cx, 38.5, lw=1.1)

# ── per-service databases
band(14.0, "DATA")
STORES = [
    "Cloud Firestore\nusers \u00b7 diagnostics \u00b7 events",
    "document store + Neo4j\nlessons \u00b7 mastery graph",
    "progress store\npoints \u00b7 levels \u00b7 streaks",
    "PostgreSQL\nsessions \u00b7 interventions",
]
for (x, w), label in zip(COLS, STORES):
    box(x, 11.4, w, 5.2, F_LIGHT, GREY, lw=0.8)
    txt(x + w / 2, 14.0, label, size=5.5)
for cx in CTR:
    arrow(cx, 20.2, cx, 16.8, lw=0.8, ms=6, color=GREY)

# ── shared contracts
box(11, 1.6, 87, 7.4, F_MID, INK, lw=1.1, ls="--")
txt(54.5, 7.6, "SHARED CONTRACTS", size=5.6, weight="bold", color=GREY)
txt(32.5, 4.4,
    "Identity \u2014 one account, issued by Code Coach\n"
    "(Argon2id + rotating JWT); sibling services verify\n"
    "a bearer token via GET /auth/me introspection", size=5.4)
txt(76.5, 4.4,
    "Learning events \u2014 typed envelope emitted on struggle,\n"
    "hint use and resolution; consumed asynchronously\n"
    "through Pub/Sub push subscriptions", size=5.4)
ax.plot([54.5, 54.5], [2.3, 6.9], color=GREY, lw=0.7, ls=":", zorder=3)
for cx in CTR:
    ax.plot([cx, cx], [11.1, 9.3], color=GREY, lw=0.7, ls=":", zorder=3)

fig.savefig(OUT / "codeguru_platform_architecture.png", dpi=600,
            bbox_inches="tight", facecolor="white", pad_inches=0.03)
fig.savefig(OUT / "codeguru_platform_architecture.pdf",
            bbox_inches="tight", facecolor="white", pad_inches=0.03)
print("written PNG + PDF")
