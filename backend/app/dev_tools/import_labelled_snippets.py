"""Bring labelled real students' files into the training data.

USAGE (from backend/):

    python -m app.dev_tools.import_labelled_snippets \\
        --export C:/Hello/research-data/code-coach --labels C:/Hello/research-data/code-coach/agreed.csv

--export is the folder export_code_snapshots.py wrote (it holds snippets/).
--labels is the FINAL labels: to_label.csv with every disagreement between
the raters settled (label_agreement.py lists them), and 0 or 1 in all five
has_* columns.

Copies each labelled file into data/ml/raw_snippets_real/ and writes
data/ml/raw_snippets_real/labels.csv, which build_snippet_index.py reads to
add them to the index as source_type real_student. Both are git-ignored.

A row with any label missing is skipped and reported, never guessed.
Importing again replaces earlier labels for the same file.

Reads and writes local files only; touches no database.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

from app.dev_tools.export_code_snapshots import LABEL_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REAL_DIR = PROJECT_ROOT / "data" / "ml" / "raw_snippets_real"
LABELS_FILE = REAL_DIR / "labels.csv"
FIELDS = ["snippet_id", "file_path", "participant", *LABEL_COLUMNS, "rater", "notes"]


def complete(row: dict[str, str]) -> bool:
    return all(row.get(column, "").strip() in {"0", "1"} for column in LABEL_COLUMNS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import labelled real snippets.")
    parser.add_argument("--export", required=True, help="the folder export_code_snapshots.py wrote")
    parser.add_argument("--labels", required=True, help="the final, agreed labels CSV")
    args = parser.parse_args(argv)

    export_dir = Path(args.export)
    with Path(args.labels).open(newline="", encoding="utf-8") as handle:
        labelled = list(csv.DictReader(handle))

    existing: dict[str, dict[str, str]] = {}
    if LABELS_FILE.exists():
        with LABELS_FILE.open(newline="", encoding="utf-8") as handle:
            existing = {row["snippet_id"]: row for row in csv.DictReader(handle)}

    REAL_DIR.mkdir(parents=True, exist_ok=True)
    imported, skipped = 0, []
    for row in labelled:
        source = export_dir / "snippets" / f"{row['snippet_id']}.java"
        if not complete(row) or not source.exists():
            skipped.append(row.get("snippet_id", "?"))
            continue
        target = REAL_DIR / f"{row['snippet_id']}.java"
        shutil.copyfile(source, target)
        existing[row["snippet_id"]] = {
            "snippet_id": row["snippet_id"],
            "file_path": f"data/ml/raw_snippets_real/{target.name}",
            "participant": row.get("participant", ""),
            **{column: row[column].strip() for column in LABEL_COLUMNS},
            "rater": row.get("rater", ""),
            "notes": row.get("notes", ""),
        }
        imported += 1

    with LABELS_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing.values())

    print(f"Imported {imported} file(s); {len(existing)} real file(s) labelled in total.")
    if skipped:
        print(f"Skipped {len(skipped)} with a missing label or file: {', '.join(skipped[:20])}")
    print("Next: python -m app.dev_tools.build_snippet_index, then build_dataset and split_dataset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
