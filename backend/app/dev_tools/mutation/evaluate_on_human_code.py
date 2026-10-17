"""Run the logic-error models on human-written code they never saw, and list
every flag for a person to judge.

The mutation corpus's test split is held out by base method, but it is still
model-written code with planted mistakes. This is the other check: the
manually curated snippets in data/ml/raw_snippets/ (written for the original
five error types) and the extension's sample programs. Nobody wrote them with
the eleven new mistakes in mind, so every flag is either a real find or a
false alarm - the CSV has a blank `verdict` column for a reviewer to fill in.

USAGE (from backend/)   python -m app.dev_tools.mutation.evaluate_on_human_code
OUTPUT  backend/models/logic_human_review_v1.csv
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from app.analysis.error_catalog import ERROR_CATALOG
from app.analysis.ml_engine import score_candidates
from app.analysis.parser_utils import parse_java_code_safe
from app.dev_tools.mutation.java_runner import PROJECT_ROOT

SOURCES = [
    PROJECT_ROOT / "data" / "ml" / "raw_snippets",
    PROJECT_ROOT / "extension" / "code-coach-vscode" / "src" / "sample-java",
]
OUT_PATH = PROJECT_ROOT / "backend" / "models" / "logic_human_review_v1.csv"


def main() -> None:
    files = sorted(path for root in SOURCES if root.exists() for path in root.rglob("*.java"))
    specs = [spec for spec in ERROR_CATALOG.values() if spec.detection_mode == "candidate_ml"]
    rows, proposed, flagged = [], Counter(), Counter()
    for path in files:
        source = path.read_text(encoding="utf-8", errors="replace")
        parse_result = parse_java_code_safe(source)
        if parse_result.tree is None:
            continue
        lines = source.splitlines()
        for spec in specs:
            candidates = spec.proposer(parse_result)
            proposed[spec.error_type] += len(candidates)
            for candidate, probability in zip(candidates, score_candidates(spec, candidates)):
                if probability < (spec.candidate_ml_threshold or 0.5):
                    continue
                flagged[spec.error_type] += 1
                line = candidate.finding.line
                rows.append({
                    "file": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                    "line": line,
                    "error_type": spec.error_type,
                    "probability": probability,
                    "code": lines[line - 1].strip() if 0 < line <= len(lines) else "",
                    "verdict": "",
                })
    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "line", "error_type", "probability", "code", "verdict"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(files)} human-written files")
    for spec in specs:
        print(f"  {spec.error_type}: {proposed[spec.error_type]} sites proposed, {flagged[spec.error_type]} flagged")
    print(f"-> {OUT_PATH.relative_to(PROJECT_ROOT)} ({len(rows)} flags to review)")


if __name__ == "__main__":
    main()
