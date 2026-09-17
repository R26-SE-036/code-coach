"""How the DEPLOYED detector does on hand-written code, and on generated code, separately.

WHY THIS EXISTS
    Every model was trained and calibrated on generated snippets only:
    split_dataset.py sends every hand-written snippet to the test split. The
    saved metrics report that test split as one number per target, and a
    generated snippet is easy for a model trained on the generator's own
    output - validation F1 is 1.0 for every target. Averaged together, the
    generated rows lift the number that was meant to say how the detector
    does on code a person wrote.

    This reports the two sources separately, for the configuration that
    actually runs: the model file and threshold in ERROR_CATALOG, and the
    whole analysis pipeline as a student meets it.

TWO MEASURES PER TARGET
    gate      The file-level model at its catalog threshold: "does this file
              contain the mistake?" This is what train_baselines measures.
    pipeline  analyze_code() on the file: is the mistake actually REPORTED?
              Off-by-one is decided per candidate site rather than by the file
              gate, and every gated type also needs its locator to fire, so
              this is the number a student experiences.

NOT EVALUATED IS NOT A SCORE
    With no positive examples from a source there is no recall; with nothing
    predicted positive there is no precision. Both are left empty, never
    written as 0 or 1: "has no hand-written examples" and "perfect on
    hand-written code" must not look alike in a table. False alarms on that
    source's negatives are still counted.

USAGE (from backend/):  python -m app.dev_tools.evaluate_by_source
Writes: backend/models/evaluation_by_source_v1.csv
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence

import joblib
import pandas as pd

from app.analysis.analyzer import analyze_code
from app.analysis.error_catalog import MODELS_DIR, ErrorTypeSpec, ml_gated_specs

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEST_FILE = PROJECT_ROOT / "data" / "ml" / "splits" / "test_v1.csv"
OUTPUT_FILE = PROJECT_ROOT / "backend" / "models" / "evaluation_by_source_v1.csv"

MEASURES = ("gate", "pipeline")


@dataclass(frozen=True)
class Outcome:
    target: str
    error_type: str
    source_type: str
    actual: bool
    gate: bool
    pipeline: bool


def _rates(tp: int, fp: int, fn: int) -> tuple[Optional[float], Optional[float], Optional[float]]:
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    if precision is None or recall is None:
        return precision, recall, None
    if precision + recall == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def summarise(outcomes: Iterable[Outcome]) -> list[dict[str, Any]]:
    """One row per target per source, for both measures."""
    groups: dict[tuple[str, str, str], list[Outcome]] = defaultdict(list)
    for outcome in outcomes:
        groups[(outcome.target, outcome.error_type, outcome.source_type)].append(outcome)

    rows: list[dict[str, Any]] = []
    for (target, error_type, source_type), items in sorted(groups.items()):
        positives = sum(1 for item in items if item.actual)
        row: dict[str, Any] = {
            "target": target,
            "error_type": error_type,
            "source_type": source_type,
            "positives": positives,
            "negatives": len(items) - positives,
            "has_positive_examples": positives > 0,
        }
        for measure in MEASURES:
            predicted = [getattr(item, measure) for item in items]
            tp = sum(1 for item, hit in zip(items, predicted) if item.actual and hit)
            fp = sum(1 for item, hit in zip(items, predicted) if not item.actual and hit)
            fn = sum(1 for item, hit in zip(items, predicted) if item.actual and not hit)
            precision, recall, f1 = _rates(tp, fp, fn)
            row.update(
                {
                    f"{measure}_tp": tp,
                    f"{measure}_fp": fp,
                    f"{measure}_fn": fn,
                    f"{measure}_precision": precision,
                    f"{measure}_recall": recall,
                    f"{measure}_f1": f1,
                }
            )
        rows.append(row)
    return rows


def _positive_probabilities(model: Any, rows: pd.DataFrame) -> Sequence[float]:
    columns = list(model.feature_names_in_)
    positive = list(model.classes_).index(1)
    return model.predict_proba(rows[columns].astype(float))[:, positive]


def collect_outcomes(
    test_rows: pd.DataFrame,
    *,
    specs: Optional[Iterable[ErrorTypeSpec]] = None,
    analyze: Callable[[str], list] = analyze_code,
    project_root: Path = PROJECT_ROOT,
) -> list[Outcome]:
    specs = list(ml_gated_specs() if specs is None else specs)
    rows = test_rows.reset_index(drop=True)

    gate_hits = {
        spec.target_column: [
            float(probability) >= spec.ml_threshold
            for probability in _positive_probabilities(joblib.load(MODELS_DIR / spec.model_file), rows)
        ]
        for spec in specs
    }

    outcomes: list[Outcome] = []
    for index, row in rows.iterrows():
        code = (project_root / row["file_path"]).read_text(encoding="utf-8")
        reported = {diagnostic.error_type for diagnostic in analyze(code)}
        for spec in specs:
            outcomes.append(
                Outcome(
                    target=spec.target_column,
                    error_type=spec.error_type,
                    source_type=str(row["source_type"]),
                    actual=bool(int(row[spec.target_column])),
                    gate=gate_hits[spec.target_column][index],
                    pipeline=spec.error_type in reported,
                )
            )
    return outcomes


def _cell(value: Any) -> str:
    if value is None:
        # ASCII: a Windows console prints an em dash as a replacement character.
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def main() -> None:
    test_rows = pd.read_csv(TEST_FILE)
    rows = summarise(collect_outcomes(test_rows))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if value is None else value for key, value in row.items()})

    header = f"{'target':32s} {'source':20s} {'pos':>4s} {'neg':>4s}   {'gate P':>6s} {'gate R':>6s}   {'pipe P':>6s} {'pipe R':>6s} {'pipe FP':>7s}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['target']:32s} {row['source_type']:20s} {row['positives']:4d} {row['negatives']:4d}   "
            f"{_cell(row['gate_precision']):>6s} {_cell(row['gate_recall']):>6s}   "
            f"{_cell(row['pipeline_precision']):>6s} {_cell(row['pipeline_recall']):>6s} {row['pipeline_fp']:7d}"
        )
    unevaluated = sorted(
        {row["target"] for row in rows if row["source_type"] == "manual_curated" and not row["has_positive_examples"]}
    )
    if unevaluated:
        print(f"\nNo hand-written positive examples, so no recall on written code: {', '.join(unevaluated)}")
    print(f"\nWritten to {OUTPUT_FILE.relative_to(PROJECT_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
