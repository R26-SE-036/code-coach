"""Regenerate data/ml/metadata/snippet_index.csv from the raw_snippets folders.

WHY THIS EXISTS
    Every column of snippet_index.csv except `notes` is mechanically derivable
    from where a .java file sits on disk: its category folder, its buggy/fixed
    subfolder, and the number in its filename. Maintaining that by hand (copy-
    pasting a row for every new snippet) is slow and error-prone. This script
    scans the folders and rebuilds the whole index deterministically.

WHAT IT PRESERVES
    The `notes` column is the only human-authored field, so it is never thrown
    away: existing notes are read back in (keyed by snippet_id) and re-attached.
    Brand-new snippets get a sensible default note you can edit afterwards.
    `source_type` is preserved the same way.

USAGE (run from the backend/ directory, like the other dev_tools)
    python -m app.dev_tools.build_snippet_index          # rewrite the CSV
    python -m app.dev_tools.build_snippet_index --check   # report drift, write nothing

    --check exits non-zero if the CSV on disk differs from what the folders
    imply. Handy as a pre-commit / CI guard so the index can't silently rot.

TYPICAL WORKFLOW
    1. Drop new .java files into the right category/buggy|fixed folder.
    2. Run this script.  ->  snippet_index.csv now has their rows.
    3. (Optional) edit the `notes` for anything that needs a specific comment.
    4. Re-run build_dataset.py then split_dataset.py as usual.
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data" / "ml"
RAW_SNIPPETS_DIR = DATA_ROOT / "raw_snippets"
GENERATED_SNIPPETS_DIR = DATA_ROOT / "raw_snippets_generated"
METADATA_FILE = DATA_ROOT / "metadata" / "snippet_index.csv"

# The corpus can come from more than one root. Each root carries its own
# source_type (provenance is a first-class column — split_dataset.py holds all
# manual_curated units out as the test set once synthetic rows exist) and an
# id prefix so snippet_ids never collide across roots.
# (root directory, source_type, snippet_id prefix)
SOURCE_ROOTS = [
    (RAW_SNIPPETS_DIR, "manual_curated", ""),
    (GENERATED_SNIPPETS_DIR, "synthetic_generated", "gen_"),
]

DEFAULT_SOURCE_TYPE = "manual_curated"


# Each bug category folder maps to the pieces the index needs. `order` fixes the
# category sequence in the output (and the global pair_group numbering) so the
# regenerated file matches the existing hand-built one.
class Category:
    def __init__(
        self,
        folder: str,
        order: int,
        id_prefix: str,
        label: str,
        flag_column: str,
        buggy_note: str,
        fixed_note: str,
    ) -> None:
        self.folder = folder
        self.order = order
        self.id_prefix = id_prefix
        self.label = label
        self.flag_column = flag_column
        self.buggy_note = buggy_note
        self.fixed_note = fixed_note


CATEGORIES: List[Category] = [
    Category(
        folder="off_by_one",
        order=0,
        id_prefix="off_by_one",
        label="OFF_BY_ONE_LOOP_BOUNDARY",
        flag_column="has_off_by_one",
        buggy_note="starts from .length instead of .length - 1",
        fixed_note="corrected with < length boundary",
    ),
    Category(
        folder="incorrect_conditional_operator",
        order=1,
        id_prefix="incorrect_cond",
        label="INCORRECT_CONDITIONAL_OPERATOR",
        flag_column="has_incorrect_conditional",
        buggy_note="uses assignment (=) instead of equality (==) in condition",
        fixed_note="uses == for comparison correctly",
    ),
    Category(
        folder="array_length_index_misuse",
        order=2,
        id_prefix="array_index",
        label="ARRAY_LENGTH_INDEX_MISUSE",
        flag_column="has_array_length_index_misuse",
        buggy_note="accesses array[array.length] directly (out of bounds)",
        fixed_note="corrected with .length - 1 as last valid index",
    ),
    # --- Promotion candidates (rule_only -> ml_gated). Folders may be empty
    # --- until data is authored; empty folders simply produce no rows.
    Category(
        folder="missing_break_in_switch",
        order=3,
        id_prefix="missing_break",
        label="MISSING_BREAK_IN_SWITCH",
        flag_column="has_missing_break",
        buggy_note="case falls through without break (unintentional)",
        fixed_note="every case ends with break/return",
    ),
    Category(
        folder="while_variable_not_updated",
        order=4,
        id_prefix="while_no_update",
        label="WHILE_VARIABLE_NOT_UPDATED",
        flag_column="has_while_not_updated",
        buggy_note="no condition variable changes inside the while body (infinite loop)",
        fixed_note="condition variable updated inside the loop body",
    ),
]

CATEGORY_BY_FOLDER = {c.folder: c for c in CATEGORIES}

ALL_FLAG_COLUMNS = [c.flag_column for c in CATEGORIES]

# Derived from CATEGORIES so a new category's flag column can never be
# forgotten here.
FIELDNAMES = [
    "snippet_id",
    "file_path",
    "language",
    "primary_label",
    "is_clean",
    *ALL_FLAG_COLUMNS,
    "pair_group",
    "pair_role",
    "source_type",
    "notes",
]

CLEAN_FOLDER = "clean"


def _trailing_number(file_stem: str) -> Optional[str]:
    """`OffByOneBug007` -> `007`. Returns None if the name has no trailing digits."""
    match = re.search(r"(\d+)$", file_stem)
    return match.group(1) if match else None


def _slug(file_stem: str) -> str:
    """CamelCase stem -> snake_case id. `Clean001` -> `clean_001`,
    `GenCleanFallThrough001` -> `gen_clean_fall_through_001`.

    Used for clean snippets, whose stems vary — the trailing number alone is
    not unique across different stem families."""
    with_breaks = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", file_stem)
    with_breaks = re.sub(r"(?<=[A-Za-z])(?=[0-9])", "_", with_breaks)
    return with_breaks.lower()


def _relative_path(java_file: Path) -> str:
    # Always POSIX-style forward slashes so the CSV is identical on Windows/Unix.
    return java_file.relative_to(PROJECT_ROOT).as_posix()


def _load_existing() -> Dict[str, Dict[str, str]]:
    """Read the current CSV so we can preserve human-authored fields (notes)."""
    if not METADATA_FILE.exists():
        return {}

    with METADATA_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {
            (row.get("snippet_id") or "").strip(): row
            for row in reader
            if (row.get("snippet_id") or "").strip()
        }


def _zeros() -> Dict[str, str]:
    return {column: "0" for column in ALL_FLAG_COLUMNS}


def _collect_category_rows(
    category: Category,
    root_dir: Path,
    source_type: str,
    id_prefix: str,
    existing: Dict[str, Dict[str, str]],
    pair_counter: List[int],
) -> List[Dict[str, str]]:
    """Build all buggy/fixed rows for one category, paired by filename number."""
    category_dir = root_dir / category.folder

    # Map number -> {role: java_file}, so a buggy/fixed pair shares a pair_group.
    by_number: Dict[str, Dict[str, Path]] = {}
    for role in ("buggy", "fixed"):
        role_dir = category_dir / role
        if not role_dir.is_dir():
            continue
        for java_file in role_dir.glob("*.java"):
            number = _trailing_number(java_file.stem)
            if number is None:
                print(f"  ! skipping (no number in name): {java_file.name}")
                continue
            by_number.setdefault(number, {})[role] = java_file

    rows: List[Dict[str, str]] = []
    for number in sorted(by_number.keys()):
        pair_counter[0] += 1
        pair_group = f"pair_{pair_counter[0]:03d}"
        roles = by_number[number]

        # buggy first, then fixed (matches the existing file ordering).
        if "buggy" in roles:
            rows.append(
                _make_bug_row(
                    category, number, roles["buggy"], pair_group,
                    existing, source_type, id_prefix,
                )
            )
        if "fixed" in roles:
            rows.append(
                _make_fix_row(
                    category, number, roles["fixed"], pair_group,
                    existing, source_type, id_prefix,
                )
            )

    return rows


def _preserved(existing: Dict[str, Dict[str, str]], snippet_id: str, field: str,
               default: str) -> str:
    """Keep an existing hand-authored value; fall back to the default for new rows."""
    prior = existing.get(snippet_id)
    if prior is None:
        return default
    value = prior.get(field)
    # Treat a missing key as "no prior value"; keep empty strings the user set.
    return value if value is not None else default


def _make_bug_row(category: Category, number: str, java_file: Path,
                  pair_group: str, existing: Dict[str, Dict[str, str]],
                  source_type: str, id_prefix: str) -> Dict[str, str]:
    snippet_id = f"{id_prefix}{category.id_prefix}_bug_{number}"
    row = {
        "snippet_id": snippet_id,
        "file_path": _relative_path(java_file),
        "language": "java",
        "primary_label": category.label,
        "is_clean": "0",
        **_zeros(),
        "pair_group": pair_group,
        "pair_role": "buggy",
        "source_type": _preserved(existing, snippet_id, "source_type", source_type),
        "notes": _preserved(existing, snippet_id, "notes", category.buggy_note),
    }
    row[category.flag_column] = "1"
    return row


def _make_fix_row(category: Category, number: str, java_file: Path,
                  pair_group: str, existing: Dict[str, Dict[str, str]],
                  source_type: str, id_prefix: str) -> Dict[str, str]:
    snippet_id = f"{id_prefix}{category.id_prefix}_fix_{number}"
    return {
        "snippet_id": snippet_id,
        "file_path": _relative_path(java_file),
        "language": "java",
        "primary_label": "NO_ISSUE",
        "is_clean": "1",
        **_zeros(),
        "pair_group": pair_group,
        "pair_role": "fixed",
        "source_type": _preserved(existing, snippet_id, "source_type", source_type),
        "notes": _preserved(existing, snippet_id, "notes", category.fixed_note),
    }


def _collect_clean_rows(
    root_dir: Path,
    source_type: str,
    existing: Dict[str, Dict[str, str]],
) -> List[Dict[str, str]]:
    clean_dir = root_dir / CLEAN_FOLDER
    if not clean_dir.is_dir():
        return []

    rows: List[Dict[str, str]] = []
    for java_file in sorted(clean_dir.glob("*.java"), key=lambda p: p.stem):
        if _trailing_number(java_file.stem) is None:
            print(f"  ! skipping (no number in name): {java_file.name}")
            continue
        # Clean ids come from the FULL stem, not the trailing number alone:
        # generated clean families (GenCleanFallThrough001, GenCleanScanner001)
        # share numbers. Manual stems are unaffected: Clean001 -> clean_001.
        snippet_id = _slug(java_file.stem)
        rows.append(
            {
                "snippet_id": snippet_id,
                "file_path": _relative_path(java_file),
                "language": "java",
                "primary_label": "NO_ISSUE",
                "is_clean": "1",
                **_zeros(),
                "pair_group": "",  # clean snippets are standalone units
                "pair_role": "clean",
                "source_type": _preserved(existing, snippet_id, "source_type", source_type),
                "notes": _preserved(
                    existing, snippet_id, "notes", f"clean snippet {java_file.stem}"
                ),
            }
        )
    return rows


def build_rows() -> List[Dict[str, str]]:
    if not RAW_SNIPPETS_DIR.is_dir():
        raise FileNotFoundError(f"raw_snippets folder not found: {RAW_SNIPPETS_DIR}")

    existing = _load_existing()

    rows: List[Dict[str, str]] = []
    pair_counter = [0]  # shared, mutable so pair_group numbering is global + ascending

    # Manual root first so the hand-curated block of the CSV stays stable.
    for root_dir, source_type, id_prefix in SOURCE_ROOTS:
        if not root_dir.is_dir():
            continue
        for category in sorted(CATEGORIES, key=lambda c: c.order):
            rows.extend(
                _collect_category_rows(
                    category, root_dir, source_type, id_prefix,
                    existing, pair_counter,
                )
            )
        rows.extend(_collect_clean_rows(root_dir, source_type, existing))

    return rows


def _render_csv(rows: List[Dict[str, str]]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _print_summary(rows: List[Dict[str, str]]) -> None:
    total = len(rows)
    per_label: Dict[str, int] = {}
    for row in rows:
        per_label[row["primary_label"]] = per_label.get(row["primary_label"], 0) + 1

    print(f"Rows generated: {total}")
    for label in sorted(per_label):
        print(f"  {label}: {per_label[label]}")
    for column in ALL_FLAG_COLUMNS:
        positives = sum(1 for row in rows if row.get(column) == "1")
        print(f"  {column} positives: {positives}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report whether the CSV is out of date without writing it (exit 1 if drift).",
    )
    args = parser.parse_args()

    rows = build_rows()
    new_content = _render_csv(rows)

    if args.check:
        current = METADATA_FILE.read_text(encoding="utf-8") if METADATA_FILE.exists() else ""
        if current == new_content:
            print("snippet_index.csv is up to date.")
            return 0
        print("snippet_index.csv is OUT OF DATE. Run without --check to regenerate.")
        _print_summary(rows)
        return 1

    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(new_content, encoding="utf-8")
    print(f"Wrote {METADATA_FILE}")
    _print_summary(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
