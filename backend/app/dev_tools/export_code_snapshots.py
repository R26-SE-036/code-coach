"""Export the code kept with consent, ready for people to label.

USAGE (from backend/, with backend/.env pointing at the database):

    python -m app.dev_tools.export_code_snapshots --out C:/Hello/research-data/code-coach --dry-run
    python -m app.dev_tools.export_code_snapshots --out C:/Hello/research-data/code-coach

Writes, under --out:

    snippets/<snapshotId>.java   one file per kept snapshot
    to_label.csv                 one row per file: what the detector found,
                                 which findings the student disputed, and five
                                 empty label columns for a rater to fill in
    manifest.json                counts and the consent version, no dates

Consent is checked AGAIN here, not only when the code was kept: a student who
withdrew after their file was saved - if deletion had failed, say - is still
left out, as is anyone whose agreement was to an older consent version.

Email addresses in the code are replaced with [email removed]; names in
comments cannot be found reliably, so raters are asked to remove any they see.

--out must be OUTSIDE the repository. This is students' work: it must never
be committed. data/ml/raw_snippets_real/ is git-ignored for the same reason.
The script refuses an --out inside this repository.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from app.core.research_consent import RESEARCH_CONSENT_VERSION
from app.services.research_collection import consent_is_current, participant_id

PROJECT_ROOT = Path(__file__).resolve().parents[3]

LABEL_COLUMNS = [
    "has_off_by_one",
    "has_incorrect_conditional",
    "has_array_length_index_misuse",
    "has_missing_break",
    "has_while_not_updated",
]

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def mask_emails(code: str) -> str:
    return _EMAIL.sub("[email removed]", code)


def exportable(snapshots: Iterable[dict[str, Any]], consents: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """The snapshots whose student's LATEST decision is GRANTED under the current version."""
    agreed = {
        participant_id(consent["userId"])
        for consent in consents
        if consent_is_current(consent)
    }
    agreed.discard(None)
    return [snapshot for snapshot in snapshots if snapshot["participant"] in agreed]


def label_row(snapshot: dict[str, Any], file_path: str) -> dict[str, Any]:
    findings = snapshot.get("findings") or []
    describe = lambda f: f"{f['errorType']}@line{f['line']}"  # noqa: E731
    return {
        "snippet_id": snapshot["snapshotId"],
        "file_path": file_path,
        "source_type": "real_student",
        "participant": snapshot["participant"],
        "times_analysed": snapshot.get("timesAnalysed", 1),
        "detector_findings": "; ".join(describe(f) for f in findings),
        "disputed_findings": "; ".join(describe(f) for f in findings if f.get("disputed")),
        **{column: "" for column in LABEL_COLUMNS},
        "rater": "",
        "notes": "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", required=True, help="a folder OUTSIDE the repository")
    parser.add_argument("--dry-run", action="store_true", help="count only; write nothing")
    args = parser.parse_args(argv)

    out = Path(args.out).resolve()
    if out == PROJECT_ROOT or PROJECT_ROOT in out.parents:
        print(f"Refusing: {out} is inside the repository. Students' code must never be committed.")
        return 2

    # Imported here so --help works without a database configured.
    from app.db.storage import build_storage

    storage = build_storage()
    snapshots = storage.list_code_snapshots(limit=1_000_000)
    chosen = exportable(snapshots, storage.list_latest_research_consents())
    participants = {snapshot["participant"] for snapshot in chosen}

    print(f"Consent version: {RESEARCH_CONSENT_VERSION}")
    print(f"{len(snapshots)} kept file(s); {len(chosen)} exportable, from {len(participants)} student(s).")
    if args.dry_run:
        return 0

    (out / "snippets").mkdir(parents=True, exist_ok=True)
    rows = []
    for snapshot in chosen:
        name = f"snippets/{snapshot['snapshotId']}.java"
        (out / name).write_text(mask_emails(snapshot["code"]), encoding="utf-8")
        rows.append(label_row(snapshot, name))

    with (out / "to_label.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(label_row({"snapshotId": "", "participant": ""}, "")))
        writer.writeheader()
        writer.writerows(rows)

    (out / "manifest.json").write_text(
        json.dumps(
            {
                "consent_version": RESEARCH_CONSENT_VERSION,
                "files": len(rows),
                "students": len(participants),
                "label_columns": LABEL_COLUMNS,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} file(s) and to_label.csv to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
