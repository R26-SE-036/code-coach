"""The ML gate: given a feature row, say which ml_gated errors are likely present.

Pipeline position: sits above feature_extractor and is driven by analyzer.
It answers ONE question per ml_gated error type: "does this file probably
contain this kind of bug?" — a yes/no plus a probability. It never says WHERE
the bug is; that is the AST locator's job (issue_locators.py).

Data flow:
    feature_dict (from feature_extractor)
      -> for each ml_gated spec in the catalog:
           load its trained .joblib model (cached)
           line the feature_dict up with the model's expected columns
           model.predict_proba -> probability
           probability >= spec.ml_threshold -> predicted_positive
      -> list of MLPrediction (returned)

Who reads the catalog: ml_gated_specs() and MODELS_DIR both come from
error_catalog.py, so the catalog is the single place that decides which models
exist, which file each loads, and what threshold gates it.

Who consumes the output: analyzer._safe_predict_issue_types() calls this, then
_detect_for_spec() uses predicted_positive to decide whether to even run the
locator. If this raises, analyzer swallows it and simply produces no ml_gated
diagnostics (fail-safe, never crashes the request).
"""

from dataclasses import dataclass
from typing import Dict, List

import joblib
import pandas as pd

from app.analysis.error_catalog import MODELS_DIR, ErrorTypeSpec, ml_gated_specs


# The object this file hands back to analyzer, one per ml_gated error type.
# predicted_positive is the gate: analyzer only runs the locator when it is True.
@dataclass
class MLPrediction:
    error_type: str
    target_column: str
    probability: float
    predicted_positive: bool


# Models are loaded from disk once and cached here (loading joblib files is slow;
# the API stays warm across requests). Keyed by target_column.
_LOADED_MODELS: Dict[str, object] = {}


# Lazy-load and cache the trained model for one error type. The filename and
# location come from the catalog spec (spec.model_file) + MODELS_DIR, so which
# model is used is decided in error_catalog.py, not here.
def _get_model(spec: ErrorTypeSpec):
    if spec.target_column in _LOADED_MODELS:
        return _LOADED_MODELS[spec.target_column]

    model_path = MODELS_DIR / spec.model_file

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = joblib.load(model_path)
    _LOADED_MODELS[spec.target_column] = model
    return model


# CRITICAL alignment step. A scikit-learn model expects its feature columns in
# the exact names and order it was trained on (model.feature_names_in_). The
# feature_dict from feature_extractor may have extra keys or a different order,
# so this picks out the expected columns, fills any missing one with 0, and
# builds a single-row DataFrame. Get this wrong and the model reads garbage.
def _build_feature_frame(model, feature_dict: Dict[str, float]) -> pd.DataFrame:
    expected_columns = list(getattr(model, "feature_names_in_", []))

    if not expected_columns:
        expected_columns = sorted(feature_dict.keys())

    row = {}
    for col in expected_columns:
        value = feature_dict.get(col, 0)
        row[col] = float(value)

    return pd.DataFrame([row], columns=expected_columns)

# Index of the "issue present" class in the model's probability output.
# predict_proba's columns follow model.classes_ order — for our 0/1 integer
# labels that is [0, 1], but reading classes_ instead of hard-coding [1] means
# a model trained with different label encoding can never be misread.
def _positive_class_index(model) -> int:
    classes = list(getattr(model, "classes_", [0, 1]))
    return classes.index(1)


# THE public entry point. Loops over ml_gated_specs() from the catalog and
# scores the feature row against each model. predict_proba gives the model's
# probability for the "positive" class (issue present). Comparing it to the
# per-target spec.ml_threshold gives predicted_positive.
#
# All current models are trained on the same 52 columns, so the single-row
# feature frame is built once and shared (measured: frame construction was
# ~5% of request time per model). Frames are keyed by column tuple, so models
# trained on different feature sets would still each get a correct frame.
#
# Returns one MLPrediction per ml_gated type. It decides IF each issue type is
# likely present; it never finds the line number — that is issue_locators' job.
def predict_issue_types(feature_dict: Dict[str, float]) -> List[MLPrediction]:
    predictions: List[MLPrediction] = []
    frames_by_columns: Dict[tuple, pd.DataFrame] = {}

    for spec in ml_gated_specs():
        model = _get_model(spec)

        columns = tuple(getattr(model, "feature_names_in_", []))
        x = frames_by_columns.get(columns)
        if x is None:
            x = _build_feature_frame(model, feature_dict)
            frames_by_columns[columns] = x

        probability = float(model.predict_proba(x)[0][_positive_class_index(model)])
        predicted_positive = probability >= spec.ml_threshold

        predictions.append(
            MLPrediction(
                error_type=spec.error_type,
                target_column=spec.target_column,
                probability=round(probability, 4),
                predicted_positive=predicted_positive,
            )
        )
    return predictions