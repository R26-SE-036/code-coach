"""Build the per-candidate training data for the logic-error models by running
code, not by asking the rules.

For every correct base method (generate_base_programs.py) and every error type:

  1. Propose candidates on the CORRECT program. Every one is a negative: the
     program is correct, so whatever the proposer saw there is not a bug.
     These are the realistic hard negatives - `i < a.length - 1` next to
     a[i + 1], a total reset at the top of each row.
  2. Mutate the program with that type's operator (mutators.py), compile, and
     run original and mutant on the same seeded inputs (harness/Fuzz.java).
  3. Propose candidates on the mutant. The one covering the edit is labelled
         1 - if the mutant behaves differently (a real bug), or
         0 - if it behaves identically (an equivalent mutant: it looks like
             the mistake and is harmless, which a rule cannot tell apart).
     Candidates away from the edit are copies of the original's and skipped.

Base methods are split into train / validation / test by their spec id, so
the two versions of one method, and every mutant of either, always land in the
same split - no near-duplicate leaks from training into the test.

USAGE (from backend/)   python -m app.dev_tools.mutation.build_mutation_corpus
OUTPUT  data/ml/mutation/candidates/<error_type>_v1.csv
        data/ml/mutation/candidates/corpus_stats_v1.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from app.analysis.logic_candidates import PROPOSERS
from app.analysis.parser_utils import parse_java_code_safe
from app.dev_tools.mutation.java_runner import PROJECT_ROOT, WORK_ROOT, behaviour_many, compile_many, literals
from app.dev_tools.mutation.mutators import mutate

BASE_PATH = PROJECT_ROOT / "data" / "ml" / "mutation" / "base" / "methods_v1.jsonl"
# Hand-written templates for families the model-written corpus is thin on
# (template_programs.py). Optional; labels come from execution either way.
TEMPLATES_PATH = PROJECT_ROOT / "data" / "ml" / "mutation" / "base" / "templates_v1.jsonl"
OUT_DIR = PROJECT_ROOT / "data" / "ml" / "mutation" / "candidates"
BUILD_DIR = WORK_ROOT / "corpus"
MAX_MUTANTS_PER_TYPE_PER_PROGRAM = 4

# Labelled by how the mutant was made rather than by what it prints. Taking
# the braces off a two-statement body leaves the second statement indented as
# if it still belonged to the if - the original showed that it did - so the
# code no longer says what its author meant even when running it every time
# happens to give the same output. For every other type a mutant that prints
# the same as the original is an equivalent mutant, and a negative.
LABEL_BY_CONSTRUCTION = {"MISLEADING_INDENTATION_NO_BRACES"}


def split_for(group: str) -> str:
    bucket = int(hashlib.sha1(group.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if bucket < 70 else "val" if bucket < 85 else "test"


def class_source(class_name: str, method_code: str) -> str:
    return (
        "import java.util.*;\n\n"
        f"public class {class_name} {{\n"
        + "\n".join("    " + line if line else "" for line in method_code.splitlines())
        + "\n}\n"
    )


def overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the mutation corpus.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--inputs", type=int, default=60, help="random inputs per method")
    parser.add_argument("--types", default="", help="comma-separated error types (default all)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    types = [t for t in args.types.split(",") if t] or list(PROPOSERS)
    items = [json.loads(line) for line in BASE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if TEMPLATES_PATH.exists():
        items += [json.loads(line) for line in TEMPLATES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    programs = []          # (program id, group, class name, source)
    for item in items:
        for version in ("a", "b"):
            code = item.get(f"code_{version}")
            if code:
                name = f"P{item['id']}{version}"
                programs.append((name, item["id"], name, class_source(name, code)))

    # ── originals and mutants, written out for compiling ──
    units = []             # dicts: name, group, program, error_type (None = original), source, span, note
    for name, group, class_name, source in programs:
        units.append({"unit": name, "group": group, "program": name, "class": class_name,
                      "error_type": None, "source": source, "spans": [], "note": "original"})
        parse_result = parse_java_code_safe(source)
        if parse_result.tree is None:
            continue
        for error_type in types:
            mutants = mutate(error_type, parse_result, rng)
            rng.shuffle(mutants)
            for index, mutation in enumerate(mutants[:MAX_MUTANTS_PER_TYPE_PER_PROGRAM]):
                units.append({"unit": f"{name}__{error_type}__{index}", "group": group, "program": name,
                              "class": class_name, "error_type": error_type, "source": mutation.source,
                              "spans": mutation.spans, "note": mutation.note})

    jobs = []
    for unit in units:
        folder = BUILD_DIR / unit["unit"]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{unit['class']}.java"
        path.write_text(unit["source"], encoding="utf-8")
        unit["path"], unit["classes"] = path, folder / "classes"
        jobs.append((path, unit["classes"]))
    print(f"{len(programs)} programs, {len(units) - len(programs)} mutants; compiling...")
    compiled = compile_many(jobs)
    runnable = [u for u in units if compiled.get(str(u["path"])) is None]
    print(f"compiled {len(runnable)} / {len(units)}; running...")
    # Every mutant probes around its ORIGINAL's constants, so it sees exactly
    # the inputs its original saw.
    original_source = {u["program"]: u["source"] for u in units if u["error_type"] is None}
    jobs = [(u["classes"], u["class"], literals(original_source.get(u["program"], ""))) for u in runnable]
    transcripts = behaviour_many(jobs, inputs=args.inputs)
    for unit, job in zip(runnable, jobs):
        unit["behaviour"] = transcripts[job]

    by_program = {u["program"]: u for u in runnable if u["error_type"] is None}

    # ── label ──
    rows: Dict[str, List[dict]] = defaultdict(list)
    stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for unit in runnable:
        original = by_program.get(unit["program"])
        if original is None or "HARNESS" in original["behaviour"] or "TIMEOUT" in original["behaviour"]:
            continue
        split = split_for(unit["group"])
        parse_result = parse_java_code_safe(unit["source"])
        if parse_result.tree is None:
            continue
        if unit["error_type"] is None:
            for error_type in types:
                for candidate in PROPOSERS[error_type](parse_result):
                    rows[error_type].append(_row(unit, split, candidate, 0, "original"))
                    stats[error_type]["original_candidates"] += 1
            continue

        error_type = unit["error_type"]
        changed = unit["behaviour"] != original["behaviour"] or error_type in LABEL_BY_CONSTRUCTION
        stats[error_type]["mutants"] += 1
        stats[error_type]["behaviour_changed" if changed else "equivalent"] += 1
        hits = [c for c in PROPOSERS[error_type](parse_result)
                if any(overlaps(s, edit) for s in c.spans for edit in unit["spans"])]
        if not hits:
            stats[error_type]["proposer_missed_" + ("bug" if changed else "equivalent")] += 1
            continue
        for candidate in hits:
            rows[error_type].append(_row(unit, split, candidate, 1 if changed else 0, "mutant" if changed else "equivalent_mutant"))

    for unit in units:
        if compiled.get(str(unit["path"])) is not None and unit["error_type"]:
            stats[unit["error_type"]]["mutant_compile_errors"] += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for error_type in types:
        type_rows = rows[error_type]
        if not type_rows:
            print(f"{error_type}: no rows")
            continue
        feature_names = list(type_rows[0]["features"].keys())
        path = OUT_DIR / f"{error_type}_v1.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["group", "unit", "split", "origin", "line", "label", *feature_names])
            for row in type_rows:
                writer.writerow([row["group"], row["unit"], row["split"], row["origin"], row["line"], row["label"],
                                 *[row["features"].get(name, 0.0) for name in feature_names]])
        counts = {split: {"rows": 0, "positives": 0} for split in ("train", "val", "test")}
        for row in type_rows:
            counts[row["split"]]["rows"] += 1
            counts[row["split"]]["positives"] += row["label"]
        summary[error_type] = {**{k: v for k, v in stats[error_type].items()}, "splits": counts}
        print(f"{error_type}: {len(type_rows)} rows, {sum(r['label'] for r in type_rows)} positive | {dict(stats[error_type])}")

    (OUT_DIR / "corpus_stats_v1.json").write_text(json.dumps({
        "base_programs": len(programs),
        "base_methods": len(items),
        "seed": args.seed,
        "inputs_per_method": args.inputs,
        "types": summary,
    }, indent=2), encoding="utf-8")


def _row(unit: dict, split: str, candidate, label: int, origin: str) -> dict:
    return {"group": unit["group"], "unit": unit["unit"], "split": split, "origin": origin,
            "line": candidate.finding.line, "label": label, "features": candidate.features}


if __name__ == "__main__":
    main()
