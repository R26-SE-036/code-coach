"""Train, choose and calibrate one candidate model per logic-error type.

For each type's corpus (build_mutation_corpus.py):

  * Three families - logistic regression, random forest, gradient boosting -
    are compared on OUT-OF-FOLD predictions over train + validation, using
    5-fold GroupKFold by base method, so no method and its mutants are ever
    on both sides of a fold. Selection is by average precision (the area
    under the precision-recall curve), which does not depend on a threshold.
  * The threshold is the lowest one at which out-of-fold precision is still
    at least 0.95 - the go-live rule agreed for new detectors: a wrong
    underline costs a student more than a missed one. When no threshold
    reaches it, the best-F1 threshold is used and the record says so.
  * The chosen family is refitted on train + validation and scored ONCE on
    the held-out test split.

Two baselines are scored on the same test rows, for the thesis comparison:
  - "proposer": flag every candidate (what a pattern-only rule does), and
  - "rule": for the thirteen types that had a detector before, exactly that
    detector (the rule, behind the old file-level gate where there was one -
    the corpus builder records its verdict per row as `legacy_flag`); for the
    eleven new types, a hand-written rule over the same features, the best a
    rule author could reasonably write without seeing the data.

USAGE (from backend/)   python -m app.dev_tools.mutation.train_logic_models
OUTPUT  backend/models/logic__<type>.joblib
        backend/models/logic_calibration_v1.json
        backend/models/logic_metrics_v1.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Callable, Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.dev_tools.mutation.java_runner import PROJECT_ROOT

CAND_DIR = PROJECT_ROOT / "data" / "ml" / "mutation" / "candidates"
MODELS_DIR = PROJECT_ROOT / "backend" / "models"
META = {"group", "unit", "split", "origin", "line", "label", "legacy_flag", "span_start", "span_end"}
PRECISION_TARGET = 0.95
MIN_RECALL = 0.75

# The rule a careful author would write from the same features. Scored only
# as a baseline; it is never used to label anything.
RULES: Dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "LOOP_SKIPS_LAST_ELEMENT": lambda f: (f["body_uses_next"] == 0),
    "INDEX_PLUS_ONE_OUT_OF_BOUNDS": lambda f: (f["slack_negative"] == 1) & (f["guarded"] == 0),
    "WRONG_LOOP_VARIABLE_IN_INDEX": lambda f: (f["inner_var_used_in_statement"] == 0),
    "NESTED_LOOP_WRONG_COUNTER": lambda f: (f["update_writes_outer_var"] == 1) | (f["cond_uses_outer_var"] == 1),
    "LOOP_COUNTER_CHANGED_IN_BODY": lambda f: (f["write_conditional"] == 0),
    "ACCUMULATOR_RESET_INSIDE_LOOP": lambda f: (f["update_in_same_loop"] == 1) & (f["reset_conditional"] == 0),
    "WRONG_EXTREME_INITIAL_VALUE": lambda f: (f["init_zero"] == 1) | (f["constant_mismatch"] == 1),
    "EARLY_RETURN_IN_LOOP": lambda f: pd.Series(True, index=f.index),
    "UNREACHABLE_ELSE_IF_ORDER": lambda f: (f["has_unreachable_branch"] == 1),
    "MISLEADING_INDENTATION_NO_BRACES": lambda f: (f["next_indent_deeper"] == 1),
    "NON_SHORT_CIRCUIT_OPERATOR": lambda f: pd.Series(True, index=f.index),
}


def families() -> Dict[str, object]:
    return {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=4000, class_weight="balanced", C=1.0)),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1,
        ),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_leaf_nodes=15, l2_regularization=1.0,
            class_weight="balanced", random_state=42,
        ),
    }


def _metrics(labels: np.ndarray, predicted: np.ndarray, scores: np.ndarray | None = None) -> dict:
    out = {
        "precision": round(float(precision_score(labels, predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(labels, predicted, zero_division=0)), 4),
        "f1": round(float(f1_score(labels, predicted, zero_division=0)), 4),
        "flagged": int(predicted.sum()),
        "positives": int(labels.sum()),
        "rows": int(len(labels)),
    }
    if scores is not None and 0 < labels.sum() < len(labels):
        out["average_precision"] = round(float(average_precision_score(labels, scores)), 4)
    return out


def _f_half(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 1.25 * precision * recall / (0.25 * precision + recall)


def choose_threshold(scores: np.ndarray, labels: np.ndarray) -> tuple[float, str]:
    """Where the underline appears.

    First choice: the lowest threshold whose precision is at least 0.95 -
    the go-live rule for new detectors - provided it still catches at least
    three bugs in four. Some mutants behave like the bug on every input and
    look identical to it, so for a few types 0.95 is only reachable by
    discarding half the real bugs; there the threshold maximising F0.5 (the
    standard score that weighs precision twice as heavily as recall) is used
    instead. Returns (threshold, which rule chose it).
    """
    candidates = np.unique(np.round(scores, 4))
    best_recall, strict = -1.0, None
    best_half, half = -1.0, 0.5
    positives = labels.sum()
    for threshold in candidates:
        predicted = scores >= threshold
        if predicted.sum() == 0:
            continue
        precision = float(labels[predicted].mean())
        recall = float(predicted[labels == 1].mean()) if positives else 0.0
        # `>=`: of the thresholds that catch the most bugs, the highest - the
        # one with the fewest wrong underlines. Taking the lowest let a model
        # whose recall saturates early sit at 0.01 and flag everything near it.
        if precision >= PRECISION_TARGET and recall >= best_recall:
            best_recall, strict = recall, float(threshold)
        score = _f_half(precision, recall)
        if score > best_half:
            best_half, half = score, float(threshold)
    if strict is not None and best_recall >= MIN_RECALL:
        return strict, "precision_0.95"
    return half, "f0.5"


def out_of_fold(model_factory, x: pd.DataFrame, y: np.ndarray, groups: np.ndarray) -> np.ndarray:
    folds = min(5, len(np.unique(groups)))
    scores = np.zeros(len(y))
    for train_index, test_index in GroupKFold(n_splits=folds).split(x, y, groups):
        model = model_factory()
        if len(np.unique(y[train_index])) < 2:
            scores[test_index] = float(y[train_index][0])
            continue
        model.fit(x.iloc[train_index], y[train_index])
        scores[test_index] = model.predict_proba(x.iloc[test_index])[:, 1]
    return scores


def train_type(error_type: str) -> dict | None:
    path = CAND_DIR / f"{error_type}_v1.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    features = [c for c in frame.columns if c not in META]
    fit_frame = frame[frame["split"] != "test"].reset_index(drop=True)
    test_frame = frame[frame["split"] == "test"].reset_index(drop=True)
    x, y, groups = fit_frame[features], fit_frame["label"].to_numpy(), fit_frame["group"].to_numpy()
    x_test, y_test = test_frame[features], test_frame["label"].to_numpy()

    record = {
        "error_type": error_type,
        "features": features,
        "counts": {
            "fit_rows": int(len(y)), "fit_positives": int(y.sum()),
            "test_rows": int(len(y_test)), "test_positives": int(y_test.sum()),
            "test_negatives_from_correct_code": int(((test_frame["origin"] == "original") & (test_frame["label"] == 0)).sum()),
            "test_negatives_from_equivalent_mutants": int((test_frame["origin"] == "equivalent_mutant").sum()),
        },
        "families": {},
    }
    if len(np.unique(y)) < 2:
        record["note"] = "only one class in the training data - no model can be learned"
        return record

    for name, template in families().items():
        oof = out_of_fold(lambda template=template: clone(template), x, y, groups)
        threshold, reached = choose_threshold(oof, y)
        record["families"][name] = {
            "oof": _metrics(y, oof >= threshold, oof),
            "threshold": round(threshold, 4),
            "precision_target_reached": reached,
        }

    chosen = max(record["families"], key=lambda n: (record["families"][n]["oof"].get("average_precision", 0), record["families"][n]["oof"]["f1"]))
    model = families()[chosen]
    model.fit(x, y)
    threshold = record["families"][chosen]["threshold"]
    start = time.perf_counter()
    test_scores = model.predict_proba(x_test)[:, 1] if len(x_test) else np.array([])
    latency = (time.perf_counter() - start) * 1000 / max(1, len(x_test))
    model_file = f"logic__{error_type.lower()}.joblib"
    if hasattr(model, "n_jobs"):
        model.n_jobs = 1  # parallel to train, single-threaded to serve
    joblib.dump(model, MODELS_DIR / model_file)

    record["selected"] = {
        "family": chosen,
        "model_file": model_file,
        "threshold": threshold,
        "precision_target_reached": record["families"][chosen]["precision_target_reached"],
        "latency_ms_per_candidate": round(latency, 4),
    }
    if len(x_test):
        legacy = test_frame["legacy_flag"] if "legacy_flag" in test_frame else pd.Series(dtype=float)
        if legacy.notna().any():
            rule_flags = legacy.fillna(0).astype(int).to_numpy().astype(bool)
            record["rule_baseline_is"] = "the detector this type had before (rule, behind its file-level gate if it had one)"
        else:
            rule_flags = RULES[error_type](x_test).to_numpy().astype(bool)
            record["rule_baseline_is"] = "a hand-written rule over the same features"
        record["test"] = {
            "model": _metrics(y_test, test_scores >= threshold, test_scores),
            "proposer_baseline": _metrics(y_test, np.ones(len(y_test), dtype=bool)),
            "rule_baseline": _metrics(y_test, rule_flags),
        }
        negatives = test_frame["label"] == 0
        for origin in ("original", "equivalent_mutant"):
            mask = (negatives & (test_frame["origin"] == origin)).to_numpy()
            if mask.any():
                record["test"][f"false_alarm_rate_on_{origin}"] = round(float((test_scores[mask] >= threshold).mean()), 4)
    record["top_features"] = _top_features(model, features)
    return record


def _top_features(model, features: List[str]) -> List[List]:
    if hasattr(model, "named_steps"):
        weights = np.abs(model.named_steps["model"].coef_[0])
    elif hasattr(model, "feature_importances_"):
        weights = model.feature_importances_
    else:
        return []
    order = np.argsort(weights)[::-1][:6]
    return [[features[i], round(float(weights[i]), 4)] for i in order]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the logic-error candidate models.")
    parser.add_argument("--types", default="")
    args = parser.parse_args()
    from app.analysis.logic_candidates import PROPOSERS
    from app.analysis.promoted_candidates import PROMOTED_PROPOSERS

    types = [t for t in args.types.split(",") if t] or [*PROPOSERS, *PROMOTED_PROPOSERS]
    calibration_path = MODELS_DIR / "logic_calibration_v1.json"
    existing = json.loads(calibration_path.read_text(encoding="utf-8")) if calibration_path.exists() else {"results": {}, "selected": {}}

    for error_type in types:
        record = train_type(error_type)
        if record is None:
            print(f"{error_type}: no corpus")
            continue
        existing["results"][error_type] = record
        if "selected" in record:
            existing["selected"][error_type] = {k: record["selected"][k] for k in ("model_file", "threshold", "family")}
            test = record.get("test", {})
            m, r, p = test.get("model", {}), test.get("rule_baseline", {}), test.get("proposer_baseline", {})
            print(f"{error_type}: {record['selected']['family']} thr={record['selected']['threshold']} "
                  f"target={record['selected']['precision_target_reached']} | test model P={m.get('precision')} R={m.get('recall')} F1={m.get('f1')} "
                  f"| rule P={r.get('precision')} R={r.get('recall')} F1={r.get('f1')} | proposer P={p.get('precision')}")
        else:
            print(f"{error_type}: {record.get('note')}")

    existing["precision_target"] = PRECISION_TARGET
    calibration_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    with (MODELS_DIR / "logic_metrics_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["error_type", "family", "threshold", "precision_target_reached", "test_rows", "test_positives",
                         "model_precision", "model_recall", "model_f1", "model_average_precision",
                         "baseline", "rule_precision", "rule_recall", "rule_f1", "proposer_precision"])
        for error_type, record in sorted(existing["results"].items()):
            if "selected" not in record or "test" not in record:
                continue
            m, r, p = record["test"]["model"], record["test"]["rule_baseline"], record["test"]["proposer_baseline"]
            baseline = "previous detector" if str(record.get("rule_baseline_is", "")).startswith("the detector") else "hand-written rule"
            writer.writerow([error_type, record["selected"]["family"], record["selected"]["threshold"],
                             record["selected"]["precision_target_reached"], m["rows"], m["positives"],
                             m["precision"], m["recall"], m["f1"], m.get("average_precision", ""),
                             baseline, r["precision"], r["recall"], r["f1"], p["precision"]])


if __name__ == "__main__":
    main()
