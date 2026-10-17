"""A two-page PDF of the CodeBERT comparison, for showing to a panel.

Reads only result files - backend/models/pretrained_comparison_v1.json, the
calibration record, curated_comparison_v1.csv and logic_human_review_v1.csv -
and the titles from error_catalog.py's source, so it runs in the research
environment (it needs reportlab, which the service does not):

    research-venv/Scripts/python -m app.dev_tools.mutation.comparison_report --out ../../CodeBERT_Comparison.pdf
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.dev_tools.mutation.java_runner import PROJECT_ROOT

# Arrows and "≈" are not in the built-in PDF fonts; Arial has them.
_FONTS = Path("C:/Windows/Fonts")
if (_FONTS / "arial.ttf").exists():
    pdfmetrics.registerFont(TTFont("Body", str(_FONTS / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(_FONTS / "arialbd.ttf")))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")
    REGULAR, BOLD = "Body", "Body-Bold"
else:
    REGULAR, BOLD = "Helvetica", BOLD

MODELS = PROJECT_ROOT / "backend" / "models"
TIE = 0.01
INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#616e7c")
WIN = colors.HexColor("#d9f2e3")
LOSS = colors.HexColor("#fde2e1")
EVEN = colors.HexColor("#eef1f4")
HEAD = colors.HexColor("#243b53")
RULE = colors.HexColor("#cbd2d9")


def _titles() -> dict:
    source = (PROJECT_ROOT / "backend" / "app" / "analysis" / "error_catalog.py").read_text(encoding="utf-8")
    titles = dict(re.findall(r'error_type="([A-Z_]+)",\s*title="([^"]+)"', source))
    titles.update(re.findall(r'^\s*"([A-Z_]+)": "([^"]+)",$', source, re.M))
    return titles


def _f(value, digits: int = 2) -> str:
    return "–" if value is None or value == "" else f"{float(value):.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(PROJECT_ROOT.parent / "CodeBERT_Comparison.pdf"))
    args = parser.parse_args()

    titles = _titles()
    comparison = json.loads((MODELS / "pretrained_comparison_v1.json").read_text(encoding="utf-8"))
    calibration = json.loads((MODELS / "logic_calibration_v1.json").read_text(encoding="utf-8"))["results"]
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName=REGULAR, fontSize=8.6, leading=11.2, textColor=INK, alignment=TA_LEFT)
    small = ParagraphStyle("small", parent=body, fontSize=7.4, leading=9.4, textColor=MUTED)
    cell = ParagraphStyle("cell", parent=body, fontSize=7.6, leading=9.2)
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontName=BOLD, fontSize=16, leading=19, textColor=HEAD, alignment=TA_LEFT, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=BOLD, fontSize=11, leading=14, textColor=HEAD, spaceBefore=6, spaceAfter=3)

    # ── page 1: the comparison ──
    header = ["Error type", "Test sites\n(bugs)", "Before\nF1", "Our model\nP / R / F1", "Our\nAP",
              "CodeBERT\nP / R / F1", "CodeBERT\nAP", "CodeBERT +\nours F1", "Result"]
    rows, fills = [header], []
    wins = ties = losses = 0
    sums = {"ours_f1": 0.0, "bert_f1": 0.0, "ours_ap": 0.0, "bert_ap": 0.0, "both_f1": 0.0}
    order = sorted(comparison["results"], key=lambda t: titles.get(t, t))
    for index, error_type in enumerate(order, start=1):
        record = comparison["results"][error_type]
        ours = calibration[error_type]["test"]["model"]
        before = calibration[error_type]["test"]["rule_baseline"]
        previous = str(calibration[error_type].get("rule_baseline_is", "")).startswith("the detector")
        bert, both = record["variants"][0]["test"], record["variants"][1]["test"]
        diff = ours["f1"] - bert["f1"]
        if abs(diff) < TIE:
            result, fill, ties = "Tie", EVEN, ties + 1
        elif diff > 0:
            result, fill, wins = "Ours", WIN, wins + 1
        else:
            result, fill, losses = "CodeBERT", LOSS, losses + 1
        for key, value in (("ours_f1", ours["f1"]), ("bert_f1", bert["f1"]), ("ours_ap", ours.get("average_precision", 0)),
                           ("bert_ap", bert.get("average_precision", 0)), ("both_f1", both["f1"])):
            sums[key] += float(value or 0)
        rows.append([
            Paragraph(titles.get(error_type, error_type), cell),
            f"{record['test_rows']} ({record['test_positives']})",
            f"{_f(before['f1'])}{'†' if previous else '‡'}",
            f"{_f(ours['precision'])} / {_f(ours['recall'])} / {_f(ours['f1'])}",
            _f(ours.get("average_precision")),
            f"{_f(bert['precision'])} / {_f(bert['recall'])} / {_f(bert['f1'])}",
            _f(bert.get("average_precision")),
            _f(both["f1"]),
            result,
        ])
        fills.append((index, fill))
    n = len(order)
    rows.append([Paragraph("<b>Mean over the %d types</b>" % n, cell), "", "", f"F1 {sums['ours_f1'] / n:.3f}", f"{sums['ours_ap'] / n:.3f}",
                 f"F1 {sums['bert_f1'] / n:.3f}", f"{sums['bert_ap'] / n:.3f}", f"{sums['both_f1'] / n:.3f}", f"{wins} / {ties} / {losses}"])

    widths = [62 * mm, 20 * mm, 15 * mm, 34 * mm, 14 * mm, 34 * mm, 17 * mm, 20 * mm, 19 * mm]
    table = Table(rows, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), BOLD), ("FONTNAME", (0, 1), (-1, -1), REGULAR), ("FONTSIZE", (0, 0), (-1, -1), 7.6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE), ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("FONTNAME", (0, -1), (-1, -1), BOLD), ("BACKGROUND", (0, -1), (-1, -1), EVEN),
    ]
    for row_index, fill in fills:
        style.append(("BACKGROUND", (8, row_index), (8, row_index), fill))
    table.setStyle(TableStyle(style))

    doc = SimpleDocTemplate(args.out, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm, topMargin=10 * mm, bottomMargin=9 * mm,
                            title="Code Coach: our per-site models vs CodeBERT", author="Code Coach")
    story = [
        Paragraph("Code Coach — our per-site models vs CodeBERT", h1),
        Paragraph(
            "Each row is one kind of beginner mistake. Every candidate site (one loop, one <font face='Courier'>a == b</font>, one division) "
            "was scored by our model, which reads a few dozen numbers describing that site, and by "
            "<b>CodeBERT</b> (microsoft/codebert-base, 125 M parameters, frozen), which reads the whole program with the site marked "
            "and feeds its 1,536-number representation to a logistic regression. Same sites, same split (by base program, so no program is "
            "in both training and test), same threshold rule, same held-out test sites scored once. "
            f"<b>Result: ours better on {wins}, tie on {ties} (F1 within {TIE}), CodeBERT better on {losses}.</b>", body),
        Spacer(1, 4),
        table,
        Spacer(1, 3),
        Paragraph("P = precision (of the sites flagged, how many were real bugs), R = recall (of the real bugs, how many were flagged), "
                  "F1 = their balance, AP = average precision (threshold-free). Before: † the detector this type had before "
                  "(rule, behind its file-level gate where it had one); ‡ a hand-written rule over the same features (new type). "
                  "Labels come from running each mutant against its original program, except where a mistake is wrong in what the code says "
                  "whatever the inputs (String ==, decimal ==, ignored String result, misleading indentation, a return ending a loop body).", small),
        PageBreak(),
    ]

    # ── page 2: cost, human-written code, limits ──
    ours_size = sum(p.stat().st_size for p in MODELS.glob("logic__*.joblib")) / 1048576
    latency = [r["selected"]["latency_ms_per_candidate"] for r in calibration.values() if "selected" in r]
    bert_ms = comparison.get("ms_per_site")
    cost = Table([
        ["", "Our 24 models", "CodeBERT"],
        ["Size", f"{ours_size:.0f} MB in total", "≈ 480 MB, plus a classifier per type"],
        ["Time per site (CPU)", f"≈ {sum(latency) / len(latency):.2f} ms", f"≈ {bert_ms:.0f} ms" if bert_ms else "≈ 100–300 ms"],
        ["Runs on the 2 GB server", "Yes — live now", "No (memory and latency)"],
        ["Can explain a flag", "Yes — names the site's features", "No — 1,536 unnamed numbers"],
        ["Trained on our data", "Yes", "Frozen; only the last layer is ours"],
    ], colWidths=[48 * mm, 70 * mm, 80 * mm])
    cost.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), BOLD),
        ("FONTNAME", (1, 1), (-1, -1), REGULAR), ("FONTNAME", (0, 1), (0, -1), BOLD), ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    curated_rows = [["Error type (330 hand-written snippets, labelled by hand)", "Bugs", "Before F1", "Now F1", "False alarms before → now"]]
    curated_path = MODELS / "curated_comparison_v1.csv"
    if curated_path.exists():
        with curated_path.open(encoding="utf-8") as handle:
            for r in csv.DictReader(handle):
                curated_rows.append([titles.get(r["error_type"], r["error_type"]), r["positives"], _f(r["old_f1"]), _f(r["new_f1"]),
                                     f"{r['old_false_alarms']} → {r['new_false_alarms']}"])
    curated = Table(curated_rows, colWidths=[98 * mm, 16 * mm, 22 * mm, 22 * mm, 40 * mm])
    curated.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), BOLD),
        ("FONTNAME", (0, 1), (-1, -1), REGULAR), ("FONTSIZE", (0, 0), (-1, -1), 8.2), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE), ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
    ]))

    review_note = ""
    review_path = MODELS / "logic_human_review_v1.csv"
    if review_path.exists():
        with review_path.open(encoding="utf-8") as handle:
            verdicts = [r["verdict"] or "unreviewed" for r in csv.DictReader(handle)]
        counts = {v: verdicts.count(v) for v in sorted(set(verdicts))}
        review_note = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in counts.items())

    story += [
        Paragraph("What each costs", h2), cost,
        Paragraph("On code written by people", h2),
        Paragraph("The tables above use generated programs. These do not: snippets written and labelled by people for the five types "
                  "that used to have a file-level model, which nothing in the new pipeline was trained on.", body),
        Spacer(1, 3), curated, Spacer(1, 3),
        Paragraph(f"All 48 PairPath reference solutions (correct by definition): one flag, the exercise that shows "
                  f"<font face='Courier'>total == receipt</font> on purpose. Every flag on the 337 human-written files reviewed: {review_note}.", body),
        Paragraph("Honest limits", h2),
        Paragraph("CodeBERT is used frozen; fine-tuning it would likely do better, but takes hours on a GPU we did not use. "
                  "The test sites are generated code with planted mistakes, so the next step is the same comparison on real students' "
                  "submissions once they are collected. Small test sets (a few dozen bugs) make single-type differences noisy: "
                  "read the counts and the mean, not one row.", body),
    ]
    doc.build(story)
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
