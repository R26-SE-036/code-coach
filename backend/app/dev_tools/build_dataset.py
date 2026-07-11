import csv
from pathlib import Path
from typing import Dict, List

from app.analysis.feature_extractor import extract_features

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data" / "ml"
METADATA_FILE = DATA_ROOT / "metadata" / "snippet_index.csv"
EXTRACTED_DIR = DATA_ROOT / "extracted"

MASTER_OUTPUT_FILE = EXTRACTED_DIR / "features_v1.csv"

# One binary dataset per ML target: target_column -> output file.
TARGET_BINARY_OUTPUTS = {
    "has_off_by_one": EXTRACTED_DIR / "off_by_one_binary_v1.csv",
    "has_incorrect_conditional": EXTRACTED_DIR / "incorrect_conditional_binary_v1.csv",
    "has_array_length_index_misuse": EXTRACTED_DIR / "array_length_index_binary_v1.csv",
    "has_missing_break": EXTRACTED_DIR / "missing_break_binary_v1.csv",
    "has_while_not_updated": EXTRACTED_DIR / "while_not_updated_binary_v1.csv",
}

# Columns that describe a snippet rather than measure its code. These must be
# excluded from the feature columns of the binary datasets — letting a has_*
# label column leak in as a "feature" would poison training (the model would
# read the answer key instead of the code).
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
    *TARGET_BINARY_OUTPUTS.keys(),
}


def _read_metadata_rows() -> List[Dict[str, str]]:
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Metadata file not found: {METADATA_FILE}")

    with METADATA_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("snippet_index.csv is empty.")

    return rows


def _load_code_from_row(row: Dict[str, str]) -> str:
    relative_path = row["file_path"].strip()
    snippet_path = PROJECT_ROOT / relative_path

    if not snippet_path.exists():
        raise FileNotFoundError(f"Snippet file not found: {snippet_path}")

    return snippet_path.read_text(encoding="utf-8")


def _normalize_metadata(row: Dict[str, str]) -> Dict[str, str]:
    normalized = {
        "snippet_id": row.get("snippet_id", "").strip(),
        "file_path": row.get("file_path", "").strip(),
        "language": row.get("language", "").strip(),
        "primary_label": row.get("primary_label", "").strip(),
        "is_clean": row.get("is_clean", "").strip(),
        "pair_group": row.get("pair_group", "").strip(),
        "pair_role": row.get("pair_role", "").strip(),
        "source_type": row.get("source_type", "").strip(),
        "notes": row.get("notes", "").strip(),
    }
    # Target flags: default missing columns to "0" so an older snippet_index.csv
    # (without the newer has_* columns) still builds cleanly.
    for target_column in TARGET_BINARY_OUTPUTS:
        normalized[target_column] = (row.get(target_column) or "0").strip() or "0"
    return normalized


def _build_master_rows() -> List[Dict[str, object]]:
    metadata_rows = _read_metadata_rows()
    dataset_rows: List[Dict[str, object]] = []

    for row in metadata_rows:
        metadata = _normalize_metadata(row)
        code = _load_code_from_row(row)
        features = extract_features(code)

        combined_row: Dict[str, object] = {}
        combined_row.update(metadata)
        combined_row.update(features)

        dataset_rows.append(combined_row)

    return dataset_rows


def _write_csv(file_path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows available to write into {file_path}")

    file_path.parent.mkdir(parents=True, exist_ok=True)

    all_fieldnames = list(rows[0].keys())

    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_binary_dataset(
    master_rows: List[Dict[str, object]],
    target_column: str,
) -> List[Dict[str, object]]:
    binary_rows: List[Dict[str, object]] = []

    for row in master_rows:
        binary_row: Dict[str, object] = {}

        for key, value in row.items():
            if key not in METADATA_COLUMNS:
                binary_row[key] = value

        binary_row["target"] = int(str(row.get(target_column) or "0").strip() or "0")
        binary_row["snippet_id"] = row["snippet_id"]
        binary_row["primary_label"] = row["primary_label"]

        binary_rows.append(binary_row)

    return binary_rows


def main() -> None:
    print("Building dataset from snippet_index.csv ...")

    master_rows = _build_master_rows()
    _write_csv(MASTER_OUTPUT_FILE, master_rows)
    print(f"Master dataset written to: {MASTER_OUTPUT_FILE}")

    for target_column, output_file in TARGET_BINARY_OUTPUTS.items():
        binary_rows = _build_binary_dataset(master_rows, target_column)
        _write_csv(output_file, binary_rows)
        positives = sum(int(row["target"]) for row in binary_rows)
        print(f"{target_column}: {positives} positives -> {output_file.name}")

    print(f"Total rows processed: {len(master_rows)}")


if __name__ == "__main__":
    main()
