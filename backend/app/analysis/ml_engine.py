from dataclasses import dataclass
from typing import Dict, List

import joblib
import pandas as pd

from app.analysis.error_catalog import MODELS_DIR, ErrorTypeSpec, ml_gated_specs


@dataclass
class MLPrediction:
    error_type: str
    target_column: str
    probability: float
    predicted_positive: bool


_LOADED_MODELS: Dict[str, object] = {}


def _get_model(spec: ErrorTypeSpec):
    if spec.target_column in _LOADED_MODELS:
        return _LOADED_MODELS[spec.target_column]

    model_path = MODELS_DIR / spec.model_file

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = joblib.load(model_path)
    _LOADED_MODELS[spec.target_column] = model
    return model


def _build_feature_frame(model, feature_dict: Dict[str, float]) -> pd.DataFrame:
    expected_columns = list(getattr(model, "feature_names_in_", []))

    if not expected_columns:
        expected_columns = sorted(feature_dict.keys())

    row = {}
    for col in expected_columns:
        value = feature_dict.get(col, 0)
        row[col] = float(value)

    return pd.DataFrame([row], columns=expected_columns)

# It loads the trained .joblib model for every ml_gated entry in the error
# catalog and predicts the probability that the issue type is present.
# ML decides whether the issue type is likely present. It does not directly find the line number.
def predict_issue_types(feature_dict: Dict[str, float]) -> List[MLPrediction]:
    predictions: List[MLPrediction] = []

    for spec in ml_gated_specs():
        model = _get_model(spec)
        x = _build_feature_frame(model, feature_dict)

        probability = float(model.predict_proba(x)[0][1])
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
