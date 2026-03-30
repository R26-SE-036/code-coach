from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import joblib
import pandas as pd


@dataclass
class MLPrediction:
    error_type: str
    target_column: str
    probability: float
    predicted_positive: bool


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = BACKEND_ROOT / "models"

TARGET_SPECS = {
    "has_off_by_one": {
        "error_type": "OFF_BY_ONE_LOOP_BOUNDARY",
        "model_file": "has_off_by_one__logistic_regression.joblib",
        "threshold": 0.65,
    },
    "has_incorrect_conditional": {
        "error_type": "INCORRECT_CONDITIONAL_OPERATOR",
        "model_file": "has_incorrect_conditional__logistic_regression.joblib",
        "threshold": 0.65,
    },
    "has_array_length_index_misuse": {
        "error_type": "ARRAY_LENGTH_INDEX_MISUSE",
        "model_file": "has_array_length_index_misuse__logistic_regression.joblib",
        "threshold": 0.65,
    },
}

_LOADED_MODELS: Dict[str, object] = {}


def _get_model(target_column: str):
    if target_column in _LOADED_MODELS:
        return _LOADED_MODELS[target_column]

    spec = TARGET_SPECS[target_column]
    model_path = MODELS_DIR / spec["model_file"]

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = joblib.load(model_path)
    _LOADED_MODELS[target_column] = model
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


def predict_issue_types(feature_dict: Dict[str, float]) -> List[MLPrediction]:
    predictions: List[MLPrediction] = []

    for target_column, spec in TARGET_SPECS.items():
        model = _get_model(target_column)
        x = _build_feature_frame(model, feature_dict)

        probability = float(model.predict_proba(x)[0][1])
        predicted_positive = probability >= spec["threshold"]

        predictions.append(
            MLPrediction(
                error_type=spec["error_type"],
                target_column=target_column,
                probability=round(probability, 4),
                predicted_positive=predicted_positive,
            )
        )

    return predictions