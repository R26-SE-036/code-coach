"""Head-to-head: FILE-level vs CANDIDATE-level gating, per detected SITE.

Two evaluation sets:
  A. The held-out test split (candidates + their labels from
     build_candidate_dataset) — same data both architectures never saw.
  B. A generated MIXED-FILE challenge set: every file contains BOTH a real
     off-by-one loop AND a correct `<= length - 1` loop, so the crude locator
     fires twice per file. This is the failure class file-level gating cannot
     handle (docs/learning-sessions/10_*): if the gate opens, both sites get
     flagged. Candidate gating must accept exactly one.

Metric: per-site precision / recall / F1. A prediction is the (file, line) of
an emitted diagnostic; ground truth is the (file, line) of the planted bug.

USAGE (from backend/):  python -m app.dev_tools.evaluate_gating_architectures
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.analysis.candidate_extractor import extract_off_by_one_candidates
from app.analysis.error_catalog import ERROR_CATALOG
from app.analysis.feature_extractor import extract_features
from app.analysis.issue_locators import locate_off_by_one_loop_boundaries
from app.analysis.ml_engine import _get_model, _build_feature_frame, _positive_class_index, predict_candidates
from app.analysis.parser_utils import parse_java_code_safe

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPEC = ERROR_CATALOG["OFF_BY_ONE_LOOP_BOUNDARY"]


def file_gate_open(code: str) -> bool:
    model = _get_model(SPEC)
    frame = _build_feature_frame(model, extract_features(code))
    probability = float(model.predict_proba(frame)[0][_positive_class_index(model)])
    return probability >= SPEC.ml_threshold


def predicted_sites(code: str, architecture: str) -> set[int]:
    """Lines the architecture would underline for OFF_BY_ONE in this code."""
    parse_result = parse_java_code_safe(code)
    findings = locate_off_by_one_loop_boundaries(parse_result)

    if architecture == "file":
        return {f.line for f in findings} if file_gate_open(code) else set()

    candidates = predict_candidates(SPEC, parse_result)
    accepted = set()
    for finding in findings:
        match = next((c for c in candidates if c.line <= finding.line <= c.end_line), None)
        if match is not None and match.predicted_positive:
            accepted.add(finding.line)
    return accepted


def score(per_file: list[tuple[set[int], set[int]]]) -> tuple[int, int, int]:
    tp = fp = fn = 0
    for truth, predicted in per_file:
        tp += len(truth & predicted)
        fp += len(predicted - truth)
        fn += len(truth - predicted)
    return tp, fp, fn


def report(name: str, tp: int, fp: int, fn: int) -> None:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    print(f"  {name:16s} TP={tp:3d} FP={fp:3d} FN={fn:3d}  "
          f"precision={precision:.3f} recall={recall:.3f} F1={f1:.3f}")


# --------------------------------------------------- A. held-out test split
def evaluate_test_split() -> None:
    print("A) Held-out TEST split (per-site, both architectures blind to it)")
    truth_by_file: dict[str, set[int]] = {}
    for row in csv.DictReader(open(PROJECT_ROOT / "data/ml/candidates/off_by_one_test_v1.csv", encoding="utf-8")):
        truth_by_file.setdefault(row["file_path"], set())
        if row["label"] == "1":
            # Truth anchored to the locator's finding line inside the candidate
            truth_by_file[row["file_path"]].add(int(row["line"]))

    results = {"file": [], "candidate": []}
    for file_path, truth_candidate_lines in truth_by_file.items():
        code = (PROJECT_ROOT / file_path).read_text(encoding="utf-8")
        parse_result = parse_java_code_safe(code)
        # Anchor truth to finding lines (predictions are finding lines too)
        candidates = extract_off_by_one_candidates(parse_result)
        truth = set()
        for finding in locate_off_by_one_loop_boundaries(parse_result):
            match = next((c for c in candidates if c.line <= finding.line <= c.end_line), None)
            if match is not None and match.line in truth_candidate_lines:
                truth.add(finding.line)
        for arch in results:
            results[arch].append((truth, predicted_sites(code, arch)))

    for arch in ("file", "candidate"):
        report(f"{arch}-level", *score(results[arch]))


# --------------------------------------------- B. mixed-file challenge set
BUG_LOOP = "        for (int i = 0; i <= {arr}.length; i++) {{ total += {arr}[i]; }}\n"
OK_LOOP = "        for (int j = 0; j <= {arr}.length - 1; j++) {{ System.out.println({arr}[j]); }}\n"
DISTRACTOR = "        for (int k = 0; k < {arr}.length; k++) {{ total -= {arr}[k]; }}\n"


def build_mixed_file(index: int) -> tuple[str, int, int]:
    """One class holding a real bug loop AND a minus-one clean loop."""
    arr = f"data{index}"
    lines = [f"public class Mixed{index:03d} {{\n",
             f"    static int process(int[] {arr}) {{\n",
             "        int total = 0;\n"]
    bug_first = index % 2 == 0
    first, second = (BUG_LOOP, OK_LOOP) if bug_first else (OK_LOOP, BUG_LOOP)
    first_line = len(lines) + 1
    lines.append(first.format(arr=arr))
    if index % 3 == 0:
        lines.append(DISTRACTOR.format(arr=arr))
    second_line = len(lines) + 1
    lines.append(second.format(arr=arr))
    lines += ["        return total;\n", "    }\n", "}\n"]
    bug_line = first_line if bug_first else second_line
    ok_line = second_line if bug_first else first_line
    return "".join(lines), bug_line, ok_line


def evaluate_challenge() -> None:
    print("\nB) MIXED-FILE challenge set (50 files: real bug + correct `<= length-1`")
    print("   in the SAME file — the failure class file-level gating cannot solve)")
    per_arch = {"file": [], "candidate": []}
    sanity = 0
    for i in range(50):
        code, bug_line, ok_line = build_mixed_file(i)
        parse_result = parse_java_code_safe(code)
        finding_lines = {f.line for f in locate_off_by_one_loop_boundaries(parse_result)}
        assert bug_line in finding_lines and ok_line in finding_lines, "rule must fire on BOTH"
        sanity += 1
        truth = {bug_line}
        for arch in per_arch:
            per_arch[arch].append((truth, predicted_sites(code, arch)))
    print(f"   (sanity: crude rule fired on both loops in {sanity}/50 files)")
    for arch in ("file", "candidate"):
        report(f"{arch}-level", *score(per_arch[arch]))


if __name__ == "__main__":
    evaluate_test_split()
    evaluate_challenge()
