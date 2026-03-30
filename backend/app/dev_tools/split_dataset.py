import csv
import random
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data" / "ml"
EXTRACTED_DIR = DATA_ROOT / "extracted"
SPLITS_DIR = DATA_ROOT / "splits"

MASTER_INPUT_FILE = EXTRACTED_DIR / "features_v1.csv"

TRAIN_OUTPUT_FILE = SPLITS_DIR / "train_v1.csv"
VAL_OUTPUT_FILE = SPLITS_DIR / "val_v1.csv"
TEST_OUTPUT_FILE = SPLITS_DIR / "test_v1.csv"

RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


def _read_rows(file_path: Path) -> List[Dict[str, str]]:
    if not file_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {file_path}")

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"No rows found in {file_path}")

    return rows


def _write_rows(file_path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write into {file_path}")

    file_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys())

    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _group_rows_by_pair(rows: List[Dict[str, str]]) -> Tuple[List[List[Dict[str, str]]], List[Dict[str, str]]]:
    paired_groups = {}
    standalone_rows = []

    for row in rows:
        pair_group = (row.get("pair_group") or "").strip()

        if pair_group:
            paired_groups.setdefault(pair_group, []).append(row)
        else:
            standalone_rows.append(row)

    grouped_pairs = list(paired_groups.values())
    return grouped_pairs, standalone_rows


def _split_grouped_data(
    grouped_pairs: List[List[Dict[str, str]]],
    standalone_rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    random.seed(RANDOM_SEED)

    random.shuffle(grouped_pairs)
    random.shuffle(standalone_rows)

    total_units = len(grouped_pairs) + len(standalone_rows)

    if total_units == 0:
        raise ValueError("No data units available for splitting.")

    train_target = round(total_units * TRAIN_RATIO)
    val_target = round(total_units * VAL_RATIO)

    train_rows: List[Dict[str, str]] = []
    val_rows: List[Dict[str, str]] = []
    test_rows: List[Dict[str, str]] = []

    used_units = 0

    for group in grouped_pairs:
        if used_units < train_target:
            train_rows.extend(group)
        elif used_units < train_target + val_target:
            val_rows.extend(group)
        else:
            test_rows.extend(group)
        used_units += 1

    for row in standalone_rows:
        if used_units < train_target:
            train_rows.append(row)
        elif used_units < train_target + val_target:
            val_rows.append(row)
        else:
            test_rows.append(row)
        used_units += 1

    return train_rows, val_rows, test_rows


def main() -> None:
    print("Reading master dataset ...")
    rows = _read_rows(MASTER_INPUT_FILE)

    grouped_pairs, standalone_rows = _group_rows_by_pair(rows)
    train_rows, val_rows, test_rows = _split_grouped_data(grouped_pairs, standalone_rows)

    if not train_rows or not val_rows or not test_rows:
        raise ValueError(
            "One of the splits is empty. Add more dataset rows or adjust split ratios."
        )

    _write_rows(TRAIN_OUTPUT_FILE, train_rows)
    _write_rows(VAL_OUTPUT_FILE, val_rows)
    _write_rows(TEST_OUTPUT_FILE, test_rows)

    print(f"Train split written to: {TRAIN_OUTPUT_FILE} ({len(train_rows)} rows)")
    print(f"Validation split written to: {VAL_OUTPUT_FILE} ({len(val_rows)} rows)")
    print(f"Test split written to: {TEST_OUTPUT_FILE} ({len(test_rows)} rows)")
    print(f"Total rows processed: {len(rows)}")


if __name__ == "__main__":
    main()