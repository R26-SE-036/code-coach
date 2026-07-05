"""Calibrate the runtime ML decision threshold and model choice per target.

For each ML-gated target this tool compares the trained candidate models
(logistic regression, random forest, SVM) on the validation split and
recommends:

- the model with the best validation F1, tie-broken by prediction latency,
- a decision threshold placed at the midpoint of the separation margin
  (halfway between the highest-scoring negative and the lowest-scoring
  positive on validation).

The margin midpoint is used instead of a plain F1-maximizing sweep because
the validation set is small; when several thresholds reach the same F1, the
midpoint is the one most robust to unseen samples.

Results are written to backend/models/calibration_v1.json as a record and
printed as the values to place in ERROR_CATALOG, which stays the single
source of truth the runtime reads.
"""

import json
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPLITS_DIR = PROJECT_ROOT / "data" / "ml" / "splits"
MODELS_DIR = PROJECT_ROOT / "backend" / "models"
OUTPUT_FILE = MODELS_DIR / "calibration_v1.json"

TARGET_COLUMNS = [
    "has_off_by_one",
    "has_incorrect_conditional",
    "has_array_length_index_misuse",
]

CANDIDATE_MODEL_NAMES = ["logistic_regression", "random_forest", "svm"]

METADATA_COLUMNS = {
    "snippet_id",
    "file_path",
    "language",
    "primary_label",
    "is_clean",
    "pair_group",
    "pair_role",
    "source_type",
    "notes",
    *TARGET_COLUMNS,
}


def _feature_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col not in METADATA_COLUMNS]


def _probabilities(model, x: pd.DataFrame) -> tuple[list[float], float]:
    start = time.perf_counter()
    probabilities = model.predict_proba(x)[:, 1]
    elapsed_ms = ((time.perf_counter() - start) / len(x)) * 1000
    return list(map(float, probabilities)), elapsed_ms


def _metrics_at_threshold(y_true, probabilities, threshold: float) -> dict[str, float]:
    predictions = [1 if p >= threshold else 0 for p in probabilities]
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        predictions,
        average="binary",
        zero_division=0,
    )
    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
    }


def _margin_midpoint_threshold(y_true, probabilities) -> tuple[float, float]:
    """Threshold halfway between the highest-scoring negative and the
    lowest-scoring positive, with the margin width for reporting.

    Falls back to the F1-optimal sweep point when classes overlap."""
    positive_scores = [p for p, y in zip(probabilities, y_true) if y == 1]
    negative_scores = [p for p, y in zip(probabilities, y_true) if y == 0]

    lowest_positive = min(positive_scores)
    highest_negative = max(negative_scores)

    if lowest_positive > highest_negative:
        midpoint = (lowest_positive + highest_negative) / 2
        margin = lowest_positive - highest_negative
        return round(midpoint, 4), round(margin, 4)

    # Overlapping classes: sweep candidate thresholds for best F1.
    best_threshold, best_f1 = 0.5, -1.0
    for candidate in sorted(set(probabilities)):
        f1 = _metrics_at_threshold(y_true, probabilities, candidate)["f1"]
        if f1 > best_f1:
            best_threshold, best_f1 = candidate, f1
    return round(best_threshold, 4), 0.0


def main() -> None:
    val_df = pd.read_csv(SPLITS_DIR / "val_v1.csv")
    test_df = pd.read_csv(SPLITS_DIR / "test_v1.csv")
    feature_columns = _feature_columns(val_df)

    calibration: dict[str, dict] = {}

    for target in TARGET_COLUMNS:
        y_val = val_df[target].astype(int).tolist()
        y_test = test_df[target].astype(int).tolist()

        print(f"=== {target} ===")
        candidates = []

        for model_name in CANDIDATE_MODEL_NAMES:
            model_file = f"{target}__{model_name}.joblib"
            model = joblib.load(MODELS_DIR / model_file)

            expected = list(getattr(model, "feature_names_in_", feature_columns))
            x_val = val_df.reindex(columns=expected, fill_value=0)
            x_test = test_df.reindex(columns=expected, fill_value=0)

            val_probs, latency_ms = _probabilities(model, x_val)
            threshold, margin = _margin_midpoint_threshold(y_val, val_probs)

            val_metrics = _metrics_at_threshold(y_val, val_probs, threshold)
            test_probs, _ = _probabilities(model, x_test)
            test_metrics = _metrics_at_threshold(y_test, test_probs, threshold)

            candidates.append(
                {
                    "model_name": model_name,
                    "model_file": model_file,
                    "threshold": threshold,
                    "margin": margin,
                    "latency_ms": round(latency_ms, 4),
                    "val": val_metrics,
                    "test": test_metrics,
                }
            )
            print(
                f"  {model_name}: threshold={threshold} margin={margin} "
                f"val_f1={val_metrics['f1']} test_f1={test_metrics['f1']} "
                f"latency={latency_ms:.3f}ms"
            )

        # Best validation F1 first; break ties with the faster model.
        candidates.sort(key=lambda c: (-c["val"]["f1"], c["latency_ms"]))
        selected = candidates[0]
        calibration[target] = {
            "selected_model_file": selected["model_file"],
            "selected_threshold": selected["threshold"],
            "selection_reason": (
                "highest validation F1, ties broken by per-sample latency; "
                "threshold is the midpoint of the validation separation margin"
            ),
            "validation_margin": selected["margin"],
            "val_metrics": selected["val"],
            "test_metrics": selected["test"],
            "candidates": candidates,
        }
        print(f"  -> selected {selected['model_name']} @ threshold {selected['threshold']}")
        print()

    OUTPUT_FILE.write_text(json.dumps(calibration, indent=2) + "\n", encoding="utf-8")
    print(f"Calibration record written to {OUTPUT_FILE}")
    print("\nValues for ERROR_CATALOG:")
    for target, entry in calibration.items():
        print(
            f"  {target}: model_file={entry['selected_model_file']} "
            f"ml_threshold={entry['selected_threshold']}"
        )


if __name__ == "__main__":
    main()
