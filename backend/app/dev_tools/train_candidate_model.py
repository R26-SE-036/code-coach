"""Train + select + calibrate the per-CANDIDATE off_by_one model.

Mirrors the file-level recipe (train_baselines + calibrate_thresholds) on the
candidate dataset: three model families, selection by validation F1 (ties ->
latency), threshold at the validation margin midpoint when the classes
separate, best-F1 sweep when they overlap.

USAGE (from backend/):  python -m app.dev_tools.train_candidate_model
Writes: backend/models/candidate__has_off_by_one__<family>.joblib
        backend/models/candidate_calibration_v1.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CAND_DIR = PROJECT_ROOT / "data" / "ml" / "candidates"
MODELS_DIR = PROJECT_ROOT / "backend" / "models"

METADATA = {"snippet_id", "file_path", "line", "label"}
TARGET = "has_off_by_one"


def load(split: str) -> tuple[pd.DataFrame, pd.Series]:
    frame = pd.read_csv(CAND_DIR / f"off_by_one_{split}_v1.csv")
    features = frame[[c for c in frame.columns if c not in METADATA]]
    return features, frame["label"].astype(int)


def families() -> dict:
    return {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=200, class_weight="balanced", random_state=42,
        ),
        "svm": Pipeline([
            ("scaler", StandardScaler()),
            ("model", SVC(kernel="rbf", probability=True, class_weight="balanced", random_state=42)),
        ]),
    }


def calibrate(probs: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    """Margin-midpoint threshold; best-F1 sweep when the classes overlap."""
    pos_min = float(probs[labels == 1].min())
    neg_max = float(probs[labels == 0].max())
    margin = pos_min - neg_max
    if margin > 0:
        return round((pos_min + neg_max) / 2, 4), round(margin, 4)

    best_threshold, best_f1 = 0.5, -1.0
    for threshold in np.arange(0.05, 0.96, 0.005):
        score = f1_score(labels, (probs >= threshold).astype(int), zero_division=0)
        if score > best_f1:
            best_f1, best_threshold = score, float(threshold)
    return round(best_threshold, 4), 0.0


def main() -> None:
    x_train, y_train = load("train")
    x_val, y_val = load("val")
    x_test, y_test = load("test")
    print(f"candidates: train {len(y_train)} ({y_train.sum()}+), "
          f"val {len(y_val)} ({y_val.sum()}+), test {len(y_test)} ({y_test.sum()}+)")

    results = []
    for name, model in families().items():
        model.fit(x_train, y_train)

        start = time.perf_counter()
        val_probs = model.predict_proba(x_val)[:, 1]
        latency_ms = (time.perf_counter() - start) * 1000 / len(y_val)
        test_probs = model.predict_proba(x_test)[:, 1]

        threshold, margin = calibrate(val_probs, y_val.to_numpy())
        val_f1 = f1_score(y_val, (val_probs >= threshold).astype(int), zero_division=0)
        test_f1 = f1_score(y_test, (test_probs >= threshold).astype(int), zero_division=0)

        path = MODELS_DIR / f"candidate__{TARGET}__{name}.joblib"
        joblib.dump(model, path)
        results.append({
            "family": name, "threshold": threshold, "margin": margin,
            "val_f1": round(float(val_f1), 4), "test_f1": round(float(test_f1), 4),
            "latency_ms": round(latency_ms, 4), "model_file": path.name,
        })
        print(f"  {name}: thr={threshold} margin={margin} "
              f"val_f1={val_f1:.4f} test_f1={test_f1:.4f} lat={latency_ms:.4f}ms")

    selected = sorted(results, key=lambda r: (-r["val_f1"], r["latency_ms"]))[0]
    print(f"\nSELECTED: {selected['family']} @ threshold {selected['threshold']}")
    print(f"Catalog values: candidate_model_file={selected['model_file']} "
          f"candidate_ml_threshold={selected['threshold']}")

    record = {"target": TARGET, "results": results, "selected": selected}
    (MODELS_DIR / "candidate_calibration_v1.json").write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
