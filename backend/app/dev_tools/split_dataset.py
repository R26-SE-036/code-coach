import csv
import random
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Tuple

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

TARGET_COLUMNS = [
    "has_off_by_one",
    "has_incorrect_conditional",
    "has_array_length_index_misuse",
]


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


def _to_int(value: str) -> int:
    text = str(value).strip()
    return int(text) if text else 0


def _build_units(rows: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    paired_groups: Dict[str, List[Dict[str, str]]] = {}
    standalone_units: List[List[Dict[str, str]]] = []

    for row in rows:
        pair_group = (row.get("pair_group") or "").strip()

        if pair_group:
            paired_groups.setdefault(pair_group, []).append(row)
        else:
            standalone_units.append([row])

    return list(paired_groups.values()) + standalone_units


def _get_unit_label(unit: List[Dict[str, str]]) -> str:
    if any(_to_int(row.get("has_off_by_one", "0")) == 1 for row in unit):
        return "OFF_BY_ONE_LOOP_BOUNDARY"

    if any(_to_int(row.get("has_incorrect_conditional", "0")) == 1 for row in unit):
        return "INCORRECT_CONDITIONAL_OPERATOR"

    if any(_to_int(row.get("has_array_length_index_misuse", "0")) == 1 for row in unit):
        return "ARRAY_LENGTH_INDEX_MISUSE"

    return "NO_ISSUE"


def _allocate_unit_counts(total_units: int) -> Tuple[int, int, int]:
    if total_units <= 0:
        raise ValueError("Cannot allocate split counts for zero units.")

    if total_units == 1:
        return 1, 0, 0

    if total_units == 2:
        return 1, 0, 1

    train_count = max(1, round(total_units * TRAIN_RATIO))
    val_count = max(1, round(total_units * VAL_RATIO))
    test_count = total_units - train_count - val_count

    while test_count < 1:
        if train_count >= val_count and train_count > 1:
            train_count -= 1
        elif val_count > 1:
            val_count -= 1
        else:
            break
        test_count = total_units - train_count - val_count

    return train_count, val_count, test_count


def _split_units_stratified(
    units: List[List[Dict[str, str]]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    rng = random.Random(RANDOM_SEED)

    buckets: DefaultDict[str, List[List[Dict[str, str]]]] = defaultdict(list)
    for unit in units:
        buckets[_get_unit_label(unit)].append(unit)

    for label_units in buckets.values():
        rng.shuffle(label_units)

    train_units: List[List[Dict[str, str]]] = []
    val_units: List[List[Dict[str, str]]] = []
    test_units: List[List[Dict[str, str]]] = []

    for label in sorted(buckets.keys()):
        label_units = buckets[label]
        train_count, val_count, test_count = _allocate_unit_counts(len(label_units))

        train_units.extend(label_units[:train_count])
        val_units.extend(label_units[train_count:train_count + val_count])
        test_units.extend(label_units[train_count + val_count:train_count + val_count + test_count])

    rng.shuffle(train_units)
    rng.shuffle(val_units)
    rng.shuffle(test_units)

    train_rows = [row for unit in train_units for row in unit]
    val_rows = [row for unit in val_units for row in unit]
    test_rows = [row for unit in test_units for row in unit]

    return train_rows, val_rows, test_rows


def _count_positive(rows: List[Dict[str, str]], target_column: str) -> int:
    return sum(_to_int(row.get(target_column, "0")) for row in rows)


def _print_split_summary(split_name: str, rows: List[Dict[str, str]]) -> None:
    label_counts: Dict[str, int] = {}
    for row in rows:
        label = row.get("primary_label", "").strip()
        label_counts[label] = label_counts.get(label, 0) + 1

    print(f"{split_name} rows: {len(rows)}")
    for target_column in TARGET_COLUMNS:
        positives = _count_positive(rows, target_column)
        print(f"  {target_column}: {positives} positives")
    print(f"  primary_label_counts: {label_counts}")


def _validate_split_coverage(
    train_rows: List[Dict[str, str]],
    val_rows: List[Dict[str, str]],
    test_rows: List[Dict[str, str]],
) -> None:
    for target_column in TARGET_COLUMNS:
        train_pos = _count_positive(train_rows, target_column)
        val_pos = _count_positive(val_rows, target_column)
        test_pos = _count_positive(test_rows, target_column)

        if train_pos == 0:
            raise ValueError(f"Train split has zero positives for {target_column}")

        if val_pos == 0:
            raise ValueError(f"Validation split has zero positives for {target_column}")

        if test_pos == 0:
            raise ValueError(f"Test split has zero positives for {target_column}")


def main() -> None:
    print("Reading master dataset ...")
    rows = _read_rows(MASTER_INPUT_FILE)

    units = _build_units(rows)
    train_rows, val_rows, test_rows = _split_units_stratified(units)

    if not train_rows or not val_rows or not test_rows:
        raise ValueError(
            "One of the splits is empty. Add more dataset rows or adjust split ratios."
        )

    _validate_split_coverage(train_rows, val_rows, test_rows)

    _write_rows(TRAIN_OUTPUT_FILE, train_rows)
    _write_rows(VAL_OUTPUT_FILE, val_rows)
    _write_rows(TEST_OUTPUT_FILE, test_rows)

    print(f"Train split written to: {TRAIN_OUTPUT_FILE} ({len(train_rows)} rows)")
    print(f"Validation split written to: {VAL_OUTPUT_FILE} ({len(val_rows)} rows)")
    print(f"Test split written to: {TEST_OUTPUT_FILE} ({len(test_rows)} rows)")
    print(f"Total rows processed: {len(rows)}")
    print()

    _print_split_summary("Train", train_rows)
    _print_split_summary("Validation", val_rows)
    _print_split_summary("Test", test_rows)


if __name__ == "__main__":
    main()