import time
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data" / "ml"
SPLITS_DIR = DATA_ROOT / "splits"
MODELS_DIR = PROJECT_ROOT / "backend" / "models"

TRAIN_FILE = SPLITS_DIR / "train_v1.csv"
VAL_FILE = SPLITS_DIR / "val_v1.csv"
TEST_FILE = SPLITS_DIR / "test_v1.csv"

TARGET_COLUMNS = [
    "has_off_by_one",
    "has_incorrect_conditional",
    "has_array_length_index_misuse",
]

METADATA_COLUMNS = {
    "snippet_id",
    "file_path",
    "language",
    "primary_label",
    "is_clean",
    "has_off_by_one",
    "has_incorrect_conditional",
    "has_array_length_index_misuse",
    "pair_group",
    "pair_role",
    "source_type",
    "notes",
}

METRICS_OUTPUT_FILE = MODELS_DIR / "baseline_metrics_v1.csv"


def _load_split(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Split file not found: {path}")
    return pd.read_csv(path)


def _prepare_feature_columns(df: pd.DataFrame) -> List[str]:
    feature_columns = [col for col in df.columns if col not in METADATA_COLUMNS]

    numeric_feature_columns = []
    for col in feature_columns:
        if col in TARGET_COLUMNS:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().all():
            numeric_feature_columns.append(col)

    return numeric_feature_columns


def _convert_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    converted_df = df.copy()
    for col in columns:
        converted_df[col] = pd.to_numeric(converted_df[col], errors="coerce")
    return converted_df


def _build_models() -> Dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=200,
                        random_state=42,
                        class_weight="balanced",
                    ),
                ),
            ]
        ),
        "svm": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    SVC(
                        kernel="rbf",
                        probability=True,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        ),
    }


def _evaluate_model(model, x: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
    if len(x) == 0:
        raise ValueError("Evaluation dataset is empty.")

    start = time.perf_counter()
    predictions = model.predict(x)
    end = time.perf_counter()

    precision, recall, f1, _ = precision_recall_fscore_support(
        y,
        predictions,
        average="binary",
        zero_division=0,
    )
    accuracy = accuracy_score(y, predictions)

    total_time = end - start
    avg_latency_ms = (total_time / len(x)) * 1000

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "accuracy": float(accuracy),
        "avg_latency_ms_per_sample": float(avg_latency_ms),
        "positive_samples": int(y.sum()),
        "total_samples": int(len(y)),
    }


def _save_model(model, target_name: str, model_name: str) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = MODELS_DIR / f"{target_name}__{model_name}.joblib"
    joblib.dump(model, output_path)
    return output_path


def main() -> None:
    print("Loading dataset splits...")
    train_df = _load_split(TRAIN_FILE)
    val_df = _load_split(VAL_FILE)
    test_df = _load_split(TEST_FILE)

    feature_columns = _prepare_feature_columns(train_df)
    if not feature_columns:
        raise ValueError("No numeric feature columns found for training.")

    train_df = _convert_numeric(train_df, feature_columns + TARGET_COLUMNS)
    val_df = _convert_numeric(val_df, feature_columns + TARGET_COLUMNS)
    test_df = _convert_numeric(test_df, feature_columns + TARGET_COLUMNS)

    metrics_rows = []
    models = _build_models()

    print(f"Using {len(feature_columns)} feature columns.")
    print("Targets:", ", ".join(TARGET_COLUMNS))
    print()

    for target in TARGET_COLUMNS:
        print(f"Training models for target: {target}")

        x_train = train_df[feature_columns]
        y_train = train_df[target].astype(int)

        x_val = val_df[feature_columns]
        y_val = val_df[target].astype(int)

        x_test = test_df[feature_columns]
        y_test = test_df[target].astype(int)

        print(
            f"  Train positives: {y_train.sum()} / {len(y_train)} | "
            f"Val positives: {y_val.sum()} / {len(y_val)} | "
            f"Test positives: {y_test.sum()} / {len(y_test)}"
        )

        for model_name, model in models.items():
            model.fit(x_train, y_train)

            val_metrics = _evaluate_model(model, x_val, y_val)
            test_metrics = _evaluate_model(model, x_test, y_test)
            model_path = _save_model(model, target, model_name)

            metrics_rows.append(
                {
                    "target": target,
                    "model_name": model_name,
                    "model_path": str(model_path),
                    "val_precision": val_metrics["precision"],
                    "val_recall": val_metrics["recall"],
                    "val_f1": val_metrics["f1"],
                    "val_accuracy": val_metrics["accuracy"],
                    "val_avg_latency_ms_per_sample": val_metrics["avg_latency_ms_per_sample"],
                    "val_positive_samples": val_metrics["positive_samples"],
                    "val_total_samples": val_metrics["total_samples"],
                    "test_precision": test_metrics["precision"],
                    "test_recall": test_metrics["recall"],
                    "test_f1": test_metrics["f1"],
                    "test_accuracy": test_metrics["accuracy"],
                    "test_avg_latency_ms_per_sample": test_metrics["avg_latency_ms_per_sample"],
                    "test_positive_samples": test_metrics["positive_samples"],
                    "test_total_samples": test_metrics["total_samples"],
                }
            )

            print(
                f"    {model_name}: "
                f"val_f1={val_metrics['f1']:.3f}, "
                f"test_f1={test_metrics['f1']:.3f}, "
                f"saved={model_path.name}"
            )

        print()

    metrics_df = pd.DataFrame(metrics_rows)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(METRICS_OUTPUT_FILE, index=False)

    print("Training complete.")
    print(f"Metrics saved to: {METRICS_OUTPUT_FILE}")


if __name__ == "__main__":
    main()