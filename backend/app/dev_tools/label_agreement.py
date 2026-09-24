"""How far two raters agree on the labels of real students' files.

USAGE (from backend/):

    python -m app.dev_tools.label_agreement rater_a.csv rater_b.csv

Each file is a filled-in copy of to_label.csv (export_code_snapshots.py): one
row per file, and 0 or 1 in each of the five has_* columns.

For each mistake type it prints how often the raters agree and Cohen's kappa,
which is agreement corrected for the agreement two people would reach by
chance. Roughly: below 0.4 the label is not being understood the same way and
the labelling guide needs work; 0.6-0.8 is substantial; above 0.8 is strong.
It then lists every file the raters disagree on, to be settled together before
the labels are used - see import_labelled_snippets.py.

Reads two local CSV files; touches no database.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from app.dev_tools.export_code_snapshots import LABEL_COLUMNS


def cohen_kappa(a: list[int], b: list[int]) -> float:
    """Cohen's kappa for two raters' 0/1 labels on the same items."""
    n = len(a)
    if n == 0:
        return float("nan")
    observed = sum(x == y for x, y in zip(a, b)) / n
    p_a, p_b = sum(a) / n, sum(b) / n
    expected = p_a * p_b + (1 - p_a) * (1 - p_b)
    if expected == 1:
        return 1.0  # both gave every file the same single label: perfect, trivially
    return (observed - expected) / (1 - expected)


def _read(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["snippet_id"]: row for row in csv.DictReader(handle)}


def compare(rater_a: dict[str, dict[str, str]], rater_b: dict[str, dict[str, str]]):
    """(per-label rows, disagreements) over the files both raters labelled."""
    shared = sorted(set(rater_a) & set(rater_b))
    report, disagreements = [], []
    for column in LABEL_COLUMNS:
        pairs = [
            (rater_a[i][column].strip(), rater_b[i][column].strip(), i)
            for i in shared
            if rater_a[i][column].strip() in {"0", "1"} and rater_b[i][column].strip() in {"0", "1"}
        ]
        a = [int(x) for x, _, _ in pairs]
        b = [int(y) for _, y, _ in pairs]
        agreed = sum(x == y for x, y in zip(a, b))
        report.append(
            {
                "label": column,
                "files": len(pairs),
                "agreement": agreed / len(pairs) if pairs else float("nan"),
                "kappa": cohen_kappa(a, b),
            }
        )
        disagreements += [(i, column, x, y) for x, y, i in pairs if x != y]
    return report, disagreements


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print(__doc__)
        return 2

    report, disagreements = compare(_read(Path(args[0])), _read(Path(args[1])))
    print(f"{'label':32} {'files':>6} {'agree':>7} {'kappa':>7}")
    for row in report:
        print(f"{row['label']:32} {row['files']:>6} {row['agreement']:>7.1%} {row['kappa']:>7.2f}")

    print(f"\n{len(disagreements)} disagreement(s) to settle:")
    for snippet_id, column, a, b in disagreements:
        print(f"  {snippet_id}  {column}: rater A {a}, rater B {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
