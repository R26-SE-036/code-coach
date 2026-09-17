"""How often students dispute each kind of finding.

The extension lets a student report a finding as a false positive, and
services/dispute_service.py keeps one dispute per student per finding. This
is the other half: the first measure of the detector on code students
actually wrote, rather than on snippets written to test it.

READ THE RATE AS A SIGNAL, NOT AS PRECISION
    Most students who see a wrong finding will ignore it rather than report
    it, so a dispute rate is a floor under the false-positive rate, not the
    rate itself. And a student can dispute a finding that was right. A type
    with a high rate is one to read by hand; a type with a low rate is not
    thereby correct.

    Findings are counted once per student per finding (per diagnostic id),
    not once per analysis. Analysis re-runs every time a student pauses, and
    a finding seen in fifty analyses is still one finding they could have
    disputed.

USAGE (from backend/, with MONGODB_URI set)
    python -m app.dev_tools.dispute_report
    python -m app.dev_tools.dispute_report --csv ../data/dispute_report.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional

UNKNOWN = "UNKNOWN"


def summarise_disputes(
    diagnostic_records: Iterable[dict[str, Any]],
    dispute_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """One row per error type: findings, the students who saw them, disputes, and the rate."""
    findings: dict[str, set[tuple[str, str]]] = defaultdict(set)
    type_of: dict[tuple[str, str], str] = {}

    for record in diagnostic_records:
        user_id, diagnostic_id = record.get("userId"), record.get("diagnosticId")
        if not user_id or not diagnostic_id:
            continue
        error_type = record.get("errorType") or UNKNOWN
        findings[error_type].add((user_id, diagnostic_id))
        type_of[(user_id, diagnostic_id)] = error_type

    disputes: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for dispute in dispute_records:
        user_id, diagnostic_id = dispute.get("userId"), dispute.get("diagnosticId")
        if not user_id or not diagnostic_id:
            continue
        key = (user_id, diagnostic_id)
        # The record's own type first: the extension's report carries one, but
        # the stored finding is the authority on what was shown.
        error_type = type_of.get(key) or dispute.get("errorType") or UNKNOWN
        disputes[error_type].add(key)
        # A dispute is evidence the finding was shown, even if its record has
        # since gone, so the rate can never exceed one.
        findings[error_type].add(key)

    rows = []
    for error_type, keys in findings.items():
        disputed = len(disputes.get(error_type, ()))
        rows.append(
            {
                "error_type": error_type,
                "findings": len(keys),
                "students": len({user_id for user_id, _ in keys}),
                "disputes": disputed,
                "dispute_rate": round(disputed / len(keys), 4),
            }
        )
    rows.sort(key=lambda row: (-row["dispute_rate"], -row["findings"], row["error_type"]))
    return rows


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, help="also write the table to this CSV file")
    arguments = parser.parse_args(argv)

    from app.db.storage import build_storage

    storage = build_storage()
    database = getattr(storage, "db", None)
    if database is None:
        raise SystemExit("This report reads MongoDB. Set MONGODB_URI and try again.")

    projection = {"_id": 0, "userId": 1, "diagnosticId": 1, "errorType": 1}
    rows = summarise_disputes(
        database.codeDiagnostics.find({}, projection),
        database.diagnosticDisputes.find({}, projection),
    )

    if not rows:
        print("No findings on record yet.")
        return

    print(f"{'error type':40s} {'findings':>8s} {'students':>8s} {'disputes':>8s} {'rate':>6s}")
    for row in rows:
        print(
            f"{row['error_type']:40s} {row['findings']:8d} {row['students']:8d} "
            f"{row['disputes']:8d} {row['dispute_rate']:6.2f}"
        )
    print("\nA dispute rate is a floor under the false-positive rate, not the rate - see the module docstring.")

    if arguments.csv:
        arguments.csv.parent.mkdir(parents=True, exist_ok=True)
        with arguments.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Written to {arguments.csv}")


if __name__ == "__main__":
    main()
