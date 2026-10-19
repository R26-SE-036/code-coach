"""The model cards as a PDF: an overview page, then one page per model.

Reads only backend/models/model_cards_v1.json (written by model_cards.py), so
it needs reportlab and nothing from the service:

    python backend/app/dev_tools/mutation/model_cards_report.py --out Model_Cards.pdf
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidate_sites import with_site  # noqa: E402

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

CARDS = Path(__file__).resolve().parents[3] / "models" / "model_cards_v1.json"
_FONTS = Path("C:/Windows/Fonts")

INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#616e7c")
HEAD = colors.HexColor("#243b53")
RULE = colors.HexColor("#cbd2d9")
BAD = colors.HexColor("#fdecec")
GOOD = colors.HexColor("#e7f6ec")
ZEBRA = colors.HexColor("#f5f7fa")


def _fonts() -> tuple[str, str, str]:
    try:
        pdfmetrics.registerFont(TTFont("Body", str(_FONTS / "arial.ttf")))
        pdfmetrics.registerFont(TTFont("Body-Bold", str(_FONTS / "arialbd.ttf")))
        pdfmetrics.registerFont(TTFont("Mono", str(_FONTS / "consola.ttf")))
        pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")
        return "Body", "Body-Bold", "Mono"
    except Exception:
        return "Helvetica", "Helvetica-Bold", "Courier"


REGULAR, BOLD, MONO = _fonts()
body = ParagraphStyle("body", fontName=REGULAR, fontSize=8.8, leading=11.6, textColor=INK, spaceAfter=2)
muted = ParagraphStyle("muted", parent=body, fontSize=8, leading=10.4, textColor=MUTED)
cell = ParagraphStyle("cell", parent=body, fontSize=8, leading=9.8, spaceAfter=0)
small_cell = ParagraphStyle("small_cell", parent=cell, fontSize=7.4, leading=8.6)
small_head = ParagraphStyle("small_head", parent=small_cell, fontName=BOLD, textColor=colors.white)
head_cell = ParagraphStyle("head_cell", parent=cell, fontName=BOLD, textColor=colors.white)
h1 = ParagraphStyle("h1", fontName=BOLD, fontSize=15, leading=18, textColor=HEAD, spaceAfter=1)
h2 = ParagraphStyle("h2", fontName=BOLD, fontSize=9.5, leading=12, textColor=HEAD, spaceBefore=6, spaceAfter=2)
code = ParagraphStyle("code", fontName=MONO, fontSize=7.6, leading=9.4, textColor=INK)
label = ParagraphStyle("label", parent=body, fontName=BOLD, fontSize=8, spaceAfter=1)

WIDTH = 182 * mm


def _p(text: str, style=body) -> Paragraph:
    return Paragraph(escape(text), style)


def _bullets(items) -> ListFlowable:
    return ListFlowable([ListItem(_p(item), leftIndent=10) for item in items], bulletType="bullet", start="\u2022",
                        bulletFontName=REGULAR, bulletFontSize=7, leftIndent=10)


def _pct(value) -> str:
    return "\u2014" if value is None else f"{value * 100:.0f}%"


def _f1(value) -> str:
    return "\u2014" if value is None else f"{value:.2f}"


def _code(text: str) -> Paragraph:
    """Code that wraps instead of running out of its box; indentation kept."""
    lines = [escape(line) for line in text.splitlines()]
    lines = [("&nbsp;" * (len(line) - len(line.lstrip(" ")))) + line.lstrip(" ") for line in lines]
    return Paragraph("<br/>".join(lines), code)


def _table(rows, widths, bold_rows=(), small=False) -> Table:
    body_style, head_style = (small_cell, small_head) if small else (cell, head_cell)
    data = [[Paragraph(c, head_style) for c in rows[0]]] + [[Paragraph(c, body_style) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), HEAD), ("GRID", (0, 0), (-1, -1), 0.4, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 1.6 if small else 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 if small else 2.5),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA])]
    style += [("FONTNAME", (0, r), (-1, r), BOLD) for r in bold_rows]
    t.setStyle(TableStyle(style))
    return t


def _code_pair(mistake: str, lookalike: str) -> Table:
    half = (WIDTH - 4 * mm) / 2
    t = Table([[_p("The mistake", label), _p("Looks similar, but correct", label)],
               [_code(mistake), _code(lookalike)]],
              colWidths=[half, half], hAlign="LEFT", spaceBefore=3, spaceAfter=2)
    t.setStyle(TableStyle([("BACKGROUND", (0, 1), (0, 1), BAD), ("BACKGROUND", (1, 1), (1, 1), GOOD),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 1), (-1, 1), 5), ("BOTTOMPADDING", (0, 1), (-1, 1), 5)]))
    return t


def _human_sentence(perf: dict) -> str:
    human, curated = perf["human_code"], perf.get("curated")
    text = (f"On the human-written files it raised {human['flags']} flag{'s' if human['flags'] != 1 else ''}, reviewed by "
            f"hand: {human['real']} real, {human['plausible']} plausible, {human['wrong']} wrong."
            if human["flags"] else "It raised no flags on the human-written files it was checked on.")
    if curated:
        found = round(curated["recall"] * curated["mistakes"])
        before = round(curated["previous_recall"] * curated["mistakes"])
        text += (f" On {curated['snippets']} hand-labelled snippets it finds {found} of {curated['mistakes']} mistakes with "
                 f"{curated['false_alarms']} false alarm{'s' if curated['false_alarms'] != 1 else ''} (the detector before: "
                 f"{before}, with {curated['previous_false_alarms']}).")
    return text


def overview(cards: dict, generated: str) -> list:
    rows = [["Error type", "Model", "Test sites (mistakes)", "Precision", "Recall", "F1", "Before or rule F1", "CodeBERT F1"]]
    for error_type, card in sorted(cards.items(), key=lambda c: c[1]["title"].lower()):
        perf, data = card["performance"], card["training_data"]
        family = {"random_forest": "Random forest", "gradient_boosting": "Gradient boosting",
                  "logistic_regression": "Logistic regression"}.get(card["model"]["family"], card["model"]["family_name"])
        rows.append([escape(with_site(error_type, card["title"])), family,
                     f"{data['test_sites']} ({data['test_mistakes']})", _pct(perf["test"]["precision"]), _pct(perf["test"]["recall"]),
                     f"<b>{_f1(perf['test']['f1'])}</b>", _f1(perf["previous"].get("f1")), _f1((perf.get("codebert") or {}).get("f1"))])
    first = next(iter(cards.values()))
    return [
        _p("Code Coach model cards", h1),
        _p(f"One card for each of the {len(cards)} error types a model decides. Generated {generated} from the training "
           "and test results; every number comes from those files.", muted),
        Spacer(1, 4),
        _p("How every model works", h2),
        _p("For each error type a proposer finds every place in the code that could be the mistake, including the "
           "correct look-alikes, and describes it with a few dozen facts (for example, does the loop body also read "
           "a[i + 1]?). The type's own model scores each place, and Code Coach flags it when the score reaches the "
           "type's threshold. Thresholds favour precision, because a wrong flag costs a beginner more than a missed one."),
        _p("Training data", h2),
        _p(first["training_data"]["description"].replace("this mistake", "each type's mistake")),
        _p(first["training_data"]["split"]),
        _p("Results on the held-out test sites", h2),
        _table(rows, [56 * mm, 27 * mm, 21 * mm, 16 * mm, 13 * mm, 11 * mm, 19 * mm, 19 * mm], small=True),
        _p("Precision: of the places it flags, how many are real mistakes. Recall: of the real mistakes, how many it flags. "
           "\u201cBefore or rule\u201d is the detector the type had before, or for the 11 new types a simple hand-written rule, "
           "scored on the same sites. CodeBERT is the offline comparison (see CodeBERT_Comparison.pdf).", muted),
        _p("Limitations that apply to every model", h2),
        _bullets(first["general_limitations"]),
        PageBreak(),
    ]


def card_page(card: dict) -> list:
    model, data, perf = card["model"], card["training_data"], card["performance"]
    previous_label = "Detector before" if perf["previous"]["name"].startswith("the detector") else "Simple rule (new type)"
    metric_rows = [["", "Precision", "Recall", "F1", "Average precision"]]
    for name, m in (("This model", perf["test"]), (previous_label, perf["previous"]), ("CodeBERT (offline)", perf.get("codebert"))):
        if m:
            metric_rows.append([name, _pct(m.get("precision")), _pct(m.get("recall")), _f1(m.get("f1")), _f1(m.get("average_precision"))])
    data_rows = [["", "Places", "Real mistakes", "Look-alikes"],
                 ["Training", f"{data['training_sites']:,}", f"{data['training_mistakes']:,}", f"{data['training_sites'] - data['training_mistakes']:,}"],
                 ["Test (never seen)", f"{data['test_sites']:,}", f"{data['test_mistakes']:,}", f"{data['test_sites'] - data['test_mistakes']:,}"]]
    return [
        _p(card["title"], h1),
        Paragraph(f'<font name="{MONO}">{escape(card["error_type"])}</font> \u00b7 concept: {escape(card["concept_tag"].replace("_", " "))} '
                  f'\u00b7 model card {escape(card["version"])}', muted),
        _p("What it detects", h2), _p(card["detects"]),
        _p(f"Which places it considers: {card['considers']}", muted),
        _code_pair(card["example"]["mistake"], card["example"]["lookalike"]),
        _p("Model", h2),
        _p(f"{model['family_name']} over {model['feature_count']} facts about each place. A place is flagged when its score "
           f"reaches {model['threshold']:.2f}: {model['threshold_rule']}."),
        Paragraph("Facts that matter most: " + ", ".join(f'<font name="{MONO}">{escape(f)}</font>' for f in model["top_features"])
                  if model["top_features"] else "", muted) if model["top_features"] else Spacer(1, 0),
        _p("Trained on", h2), _p(data["description"]),
        KeepTogether([_table(data_rows, [40 * mm, 30 * mm, 30 * mm, 30 * mm], bold_rows=())]),
        _p("How well it does on the test sites", h2),
        KeepTogether([_table(metric_rows, [44 * mm, 26 * mm, 26 * mm, 22 * mm, 32 * mm], bold_rows=(1,))]),
        Spacer(1, 2),
        _p(_human_sentence(perf)),
        _p("When not to trust it", h2), _bullets(card["unreliable_when"]),
        _p("Known limitations", h2), _bullets(card["limitations"] or ["None beyond those on page 1."]),
        _p("The limitations on page 1 apply to this model too.", muted),
        PageBreak(),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the model cards as a PDF.")
    parser.add_argument("--out", default="Model_Cards.pdf")
    args = parser.parse_args()
    stored = json.loads(CARDS.read_text(encoding="utf-8"))
    cards = stored["cards"]
    story = overview(cards, stored.get("generated", ""))
    for card in sorted(cards.values(), key=lambda c: c["title"].lower()):
        story += card_page(card)
    story.pop()  # no blank page at the end

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(REGULAR, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(14 * mm, 8 * mm, "Code Coach \u00b7 model cards")
        canvas.drawRightString(A4[0] - 14 * mm, 8 * mm, f"{doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(args.out, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm, bottomMargin=14 * mm,
                            title="Code Coach model cards")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"{len(cards)} cards -> {args.out}")


if __name__ == "__main__":
    main()
