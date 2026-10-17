"""Old detector against new model, on hand-written code with human labels.

The mutation corpus is model-written code with planted mistakes, so its test
split - however carefully held out - is still the kind of code the models
learned from. The 330 manually curated snippets in the original test split
(data/ml/splits/test_v1.csv, source_type == manual_curated) were written by
people, one mistake or a deliberate look-alike each, and labelled by hand for
the five types that had file-level gates. Nothing in the new pipeline was
trained on them, and the old file-level gates were trained only on the
synthetic rows.

For each snippet and each of the five types: did the OLD detector (its
file-level gate, then its rule) report the type, and does the NEW pipeline
(proposer + per-site model, what /analyze runs now)? Scored against the
snippet's label - per file, because that is what the labels say.

USAGE (from backend/)   python -m app.dev_tools.mutation.compare_on_curated_snippets
OUTPUT  backend/models/curated_comparison_v1.csv
"""

from __future__ import annotations

import csv

import pandas as pd

from app.analysis.analyzer import analyze_code
from app.analysis.feature_extractor import extract_features
from app.analysis.parser_utils import parse_java_code_safe
from app.dev_tools.mutation.build_mutation_corpus import legacy_flags
from app.dev_tools.mutation.java_runner import PROJECT_ROOT

TARGETS = {
    "OFF_BY_ONE_LOOP_BOUNDARY": "has_off_by_one",
    "INCORRECT_CONDITIONAL_OPERATOR": "has_incorrect_conditional",
    "ARRAY_LENGTH_INDEX_MISUSE": "has_array_length_index_misuse",
    "MISSING_BREAK_IN_SWITCH": "has_missing_break",
    "WHILE_VARIABLE_NOT_UPDATED": "has_while_not_updated",
}
OUT_PATH = PROJECT_ROOT / "backend" / "models" / "curated_comparison_v1.csv"


def _scores(labels, flags) -> dict:
    tp = sum(1 for y, f in zip(labels, flags) if y and f)
    fp = sum(1 for y, f in zip(labels, flags) if not y and f)
    fn = sum(1 for y, f in zip(labels, flags) if y and not f)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": round(f1, 4)}


def main() -> None:
    rows = pd.read_csv(PROJECT_ROOT / "data" / "ml" / "splits" / "test_v1.csv")
    rows = rows[rows["source_type"] == "manual_curated"].reset_index(drop=True)
    old = {t: [] for t in TARGETS}
    new = {t: [] for t in TARGETS}
    labels = {t: [] for t in TARGETS}
    for _, row in rows.iterrows():
        code = (PROJECT_ROOT / row["file_path"]).read_text(encoding="utf-8")
        parse_result = parse_java_code_safe(code)
        features = {}

        def file_features():
            if not features:
                features.update(extract_features(code))
            return features

        found = {d.error_type for d in analyze_code(code)}
        for error_type, column in TARGETS.items():
            labels[error_type].append(int(row[column]))
            old[error_type].append(bool(parse_result.tree is not None and legacy_flags(error_type, parse_result, file_features)))
            new[error_type].append(error_type in found)

    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["error_type", "snippets", "positives", "old_precision", "old_recall", "old_f1", "old_false_alarms",
                         "new_precision", "new_recall", "new_f1", "new_false_alarms"])
        print(f"{len(rows)} hand-written snippets")
        for error_type in TARGETS:
            o, n = _scores(labels[error_type], old[error_type]), _scores(labels[error_type], new[error_type])
            writer.writerow([error_type, len(rows), sum(labels[error_type]), o["precision"], o["recall"], o["f1"], o["fp"],
                             n["precision"], n["recall"], n["f1"], n["fp"]])
            print(f"  {error_type}: {sum(labels[error_type])} positive | old P={o['precision']} R={o['recall']} F1={o['f1']} FP={o['fp']} "
                  f"| new P={n['precision']} R={n['recall']} F1={n['f1']} FP={n['fp']}")


if __name__ == "__main__":
    main()
