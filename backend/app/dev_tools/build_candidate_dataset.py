"""Build the per-CANDIDATE dataset for off_by_one from the existing corpus.

No new data and no generator changes are needed. For every file already in
the train/val/test splits:
  1. enumerate its for-loop candidates (candidate_extractor),
  2. label each candidate: in a file labeled has_off_by_one=1, the candidate
     containing the locator's verified finding line is positive; every other
     candidate — including every candidate in clean files where the crude
     rule still fires (the `<= length - 1` hard negatives) — is negative.

Candidates INHERIT their file's split, so the manual-holdout guarantee
("tested on human-written code") carries over unchanged.

USAGE (from backend/):  python -m app.dev_tools.build_candidate_dataset
Writes: data/ml/candidates/off_by_one_{train,val,test}_v1.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.analysis.candidate_extractor import extract_off_by_one_candidates
from app.analysis.issue_locators import locate_off_by_one_loop_boundaries
from app.analysis.parser_utils import parse_java_code_safe

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPLITS_DIR = PROJECT_ROOT / "data" / "ml" / "splits"
OUT_DIR = PROJECT_ROOT / "data" / "ml" / "candidates"

SPLITS = [("train", "train_v1.csv"), ("val", "val_v1.csv"), ("test", "test_v1.csv")]


def build_rows_for_split(split_csv: Path) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    feature_names: list[str] = []

    with split_csv.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            file_path = PROJECT_ROOT / record["file_path"]
            code = file_path.read_text(encoding="utf-8")
            parse_result = parse_java_code_safe(code)

            candidates = extract_off_by_one_candidates(parse_result)
            if not candidates:
                continue
            if not feature_names:
                feature_names = list(candidates[0].features.keys())

            finding_lines: set[int] = set()
            if record["has_off_by_one"] == "1":
                finding_lines = {
                    finding.line
                    for finding in locate_off_by_one_loop_boundaries(parse_result)
                }

            for site in candidates:
                label = int(any(site.line <= ln <= site.end_line for ln in finding_lines))
                rows.append({
                    "snippet_id": record["snippet_id"],
                    "file_path": record["file_path"],
                    "line": site.line,
                    "label": label,
                    **site.features,
                })

    return rows, feature_names


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for split_name, filename in SPLITS:
        rows, feature_names = build_rows_for_split(SPLITS_DIR / filename)
        out_path = OUT_DIR / f"off_by_one_{split_name}_v1.csv"
        fieldnames = ["snippet_id", "file_path", "line", "label"] + feature_names
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        positives = sum(row["label"] for row in rows)
        crude_fp = sum(
            1 for row in rows
            if row["label"] == 0 and row["cond_crude_off_by_one"] == 1.0
        )
        print(
            f"{split_name}: {len(rows)} candidates from files, "
            f"{positives} positive, {crude_fp} rule-firing NEGATIVES (the hard cases) "
            f"-> {out_path.name}"
        )


if __name__ == "__main__":
    main()
