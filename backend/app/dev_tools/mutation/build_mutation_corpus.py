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

Every row also records what the detector it replaces said about the same
site (`legacy_flag`): the rule, or for the five types that had one, the old
file-level gate followed by the rule. That is the "before" column of the
comparison, scored on exactly the rows the new model is scored on.

USAGE (from backend/)   python -m app.dev_tools.mutation.build_mutation_corpus
OUTPUT  data/ml/mutation/candidates/<error_type>_v1.csv
        data/ml/mutation/candidates/corpus_stats_v1.json
        data/ml/mutation/_work/sources_v1.jsonl   (unit -> source, for the
                                                   offline pretrained-model comparison)
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
from typing import Dict, List, Set, Tuple

import joblib
import pandas as pd

from app.analysis import issue_locators as rules
from app.analysis.candidate_extractor import extract_off_by_one_candidates
from app.analysis.feature_extractor import extract_features
from app.analysis.logic_candidates import PROPOSERS as LOGIC_PROPOSERS
from app.analysis.parser_utils import parse_java_code_safe
from app.analysis.promoted_candidates import PROMOTED_PROPOSERS
from app.dev_tools.mutation.java_runner import PROJECT_ROOT, WORK_ROOT, behaviour_many, compile_many, literals
from app.dev_tools.mutation.mutators import mutate

PROPOSERS = {**LOGIC_PROPOSERS, **PROMOTED_PROPOSERS}
MODELS_DIR = PROJECT_ROOT / "backend" / "models"

# The detectors the promoted types had before, frozen here so the comparison
# can be re-run after the catalog has moved on: the rule, and for the gated
# types the file-level model and threshold that decided whether it ran.
LEGACY_RULES = {
    "OFF_BY_ONE_LOOP_BOUNDARY": rules.locate_off_by_one_loop_boundaries,
    "INCORRECT_CONDITIONAL_OPERATOR": rules.locate_incorrect_conditional_operators,
    "ARRAY_LENGTH_INDEX_MISUSE": rules.locate_array_length_index_misuses,
    "MISSING_BREAK_IN_SWITCH": rules.locate_missing_breaks_in_switch,
    "WHILE_VARIABLE_NOT_UPDATED": rules.locate_while_variables_not_updated,
    "STRING_EQUALITY_WITH_OPERATOR": rules.locate_string_equality_with_operator,
    "LOOP_UPDATE_WRONG_DIRECTION": rules.locate_loop_update_wrong_directions,
    "CONSTANT_FALSE_LOOP_CONDITION": rules.locate_constant_false_loop_conditions,
    "IGNORED_STRING_METHOD_RESULT": rules.locate_ignored_string_method_results,
    "DIVISION_BY_ZERO_LITERAL": rules.locate_division_by_zero_literals,
    "INTEGER_DIVISION_IN_DECIMAL_CONTEXT": rules.locate_integer_division_in_decimal_context,
    "DECIMAL_EQUALITY_COMPARISON": rules.locate_decimal_equality_comparisons,
    "EMPTY_CONDITIONAL_BODY": rules.locate_empty_conditional_bodies,
}
LEGACY_GATES = {   # error type -> (file-level model, threshold)
    "INCORRECT_CONDITIONAL_OPERATOR": ("has_incorrect_conditional__logistic_regression.joblib", 0.5008),
    "ARRAY_LENGTH_INDEX_MISUSE": ("has_array_length_index_misuse__logistic_regression.joblib", 0.504),
    "MISSING_BREAK_IN_SWITCH": ("has_missing_break__logistic_regression.joblib", 0.5202),
    "WHILE_VARIABLE_NOT_UPDATED": ("has_while_not_updated__logistic_regression.joblib", 0.5027),
}
LEGACY_CANDIDATE_GATE = ("OFF_BY_ONE_LOOP_BOUNDARY", "candidate__has_off_by_one__logistic_regression.joblib", 0.5041)
_LEGACY_MODELS: Dict[str, object] = {}

# Original programs whose own transcript shows this failure cannot vouch for
# their sites of that type: both versions dividing by zero on the same empty
# array agree with each other and are still wrong.
SKIP_ORIGINAL_IF = {"DIVISION_BY_ZERO_LITERAL": "THROWS ArithmeticException"}

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
#
# The same holds for three of the promoted types, which are mistakes in what
# the code SAYS whether or not a given input exposes them: `a == b` on Strings
# that happen to be the same object, `total == 0.3` on inputs that happen to
# add up exactly, and `name.trim();` whose lost result happens not to matter
# for the inputs tried. Their negatives are still the correct programs' sites.
LABEL_BY_CONSTRUCTION = {
    "MISLEADING_INDENTATION_NO_BRACES",
    "STRING_EQUALITY_WITH_OPERATOR",
    "DECIMAL_EQUALITY_COMPARISON",
    "IGNORED_STRING_METHOD_RESULT",
}
# One mutation of an otherwise execution-labelled type: a `return` as the
# last statement of a loop body means the loop can never start a second
# pass. When the inputs tried happen to need only one pass the transcripts
# agree, but the code is wrong in what it says, and labelling those mutants
# "harmless" taught the model that a loop ending in return can be fine.
LABEL_BY_CONSTRUCTION_NOTES = {("EARLY_RETURN_IN_LOOP", "unconditional return in the loop")}


def _legacy_model(name: str):
    if name not in _LEGACY_MODELS:
        _LEGACY_MODELS[name] = joblib.load(MODELS_DIR / name)
    return _LEGACY_MODELS[name]


def _probability(model, row: Dict[str, float]) -> float:
    columns = list(getattr(model, "feature_names_in_", sorted(row)))
    frame = pd.DataFrame([[float(row.get(c, 0.0)) for c in columns]], columns=columns)
    return float(model.predict_proba(frame)[0, list(model.classes_).index(1)])


def legacy_flags(error_type: str, parse_result, file_features) -> Set[Tuple[int, int]]:
    """The (line, column) sites the pre-upgrade detector flagged.
    `file_features` is a callable, so the whole-file row is only built when a
    gate actually needs it."""
    locator = LEGACY_RULES.get(error_type)
    if locator is None:
        return set()
    found = locator(parse_result)
    if not found:
        return set()
    if error_type in LEGACY_GATES:
        model_file, threshold = LEGACY_GATES[error_type]
        if _probability(_legacy_model(model_file), file_features()) < threshold:
            return set()
    if error_type == LEGACY_CANDIDATE_GATE[0]:
        model = _legacy_model(LEGACY_CANDIDATE_GATE[1])
        sites = extract_off_by_one_candidates(parse_result)
        keep = []
        for finding in found:
            site = next((s for s in sites if s.line <= finding.line <= s.end_line), None)
            if site is not None and _probability(model, site.features) >= LEGACY_CANDIDATE_GATE[2]:
                keep.append(finding)
        found = keep
    return {(f.line, f.column) for f in found}


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
    parser.add_argument("--limit", type=int, default=0, help="use every n-th base item only (a quick trial run)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    types = [t for t in args.types.split(",") if t] or list(PROPOSERS)
    items = [json.loads(line) for line in BASE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if TEMPLATES_PATH.exists():
        items += [json.loads(line) for line in TEMPLATES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        items = items[::args.limit]
        global OUT_DIR
        OUT_DIR = WORK_ROOT / "trial_candidates"
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
    shared_literals = {program: literals(source) for program, source in original_source.items()}
    jobs = [(u["classes"], u["class"], shared_literals.get(u["program"], "")) for u in runnable]
    transcripts = behaviour_many(jobs, inputs=args.inputs)
    for unit, job in zip(runnable, jobs):
        unit["behaviour"] = transcripts[job]

    by_program = {u["program"]: u for u in runnable if u["error_type"] is None}

    # ── label ──
    used_sources: Dict[str, str] = {}
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
        cached: Dict[str, float] = {}

        def file_features() -> Dict[str, float]:
            if not cached:
                cached.update(extract_features(unit["source"]))
            return cached

        def legacy(error_type: str) -> Set[Tuple[int, int]]:
            return legacy_flags(error_type, parse_result, file_features)

        if unit["error_type"] is None:
            used_sources[unit["unit"]] = unit["source"]
            for error_type in types:
                marker = SKIP_ORIGINAL_IF.get(error_type)
                if marker and marker in unit["behaviour"]:
                    stats[error_type]["originals_skipped_failing"] += 1
                    continue
                flagged = legacy(error_type)
                for candidate in PROPOSERS[error_type](parse_result):
                    rows[error_type].append(_row(unit, split, candidate, 0, "original", flagged))
                    stats[error_type]["original_candidates"] += 1
            continue

        error_type = unit["error_type"]
        changed = (unit["behaviour"] != original["behaviour"] or error_type in LABEL_BY_CONSTRUCTION
                   or (error_type, unit["note"]) in LABEL_BY_CONSTRUCTION_NOTES)
        stats[error_type]["mutants"] += 1
        stats[error_type]["behaviour_changed" if changed else "equivalent"] += 1
        hits = [c for c in PROPOSERS[error_type](parse_result)
                if any(overlaps(s, edit) for s in c.spans for edit in unit["spans"])]
        if not hits:
            stats[error_type]["proposer_missed_" + ("bug" if changed else "equivalent")] += 1
            continue
        used_sources[unit["unit"]] = unit["source"]
        flagged = legacy(error_type)
        for candidate in hits:
            rows[error_type].append(_row(unit, split, candidate, 1 if changed else 0, "mutant" if changed else "equivalent_mutant", flagged))

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
            writer.writerow(["group", "unit", "split", "origin", "line", "label", "legacy_flag", "span_start", "span_end", *feature_names])
            for row in type_rows:
                writer.writerow([row["group"], row["unit"], row["split"], row["origin"], row["line"], row["label"],
                                 row["legacy_flag"], row["span"][0], row["span"][1],
                                 *[row["features"].get(name, 0.0) for name in feature_names]])
        counts = {split: {"rows": 0, "positives": 0} for split in ("train", "val", "test")}
        for row in type_rows:
            counts[row["split"]]["rows"] += 1
            counts[row["split"]]["positives"] += row["label"]
        summary[error_type] = {**{k: v for k, v in stats[error_type].items()}, "splits": counts}
        print(f"{error_type}: {len(type_rows)} rows, {sum(r['label'] for r in type_rows)} positive | {dict(stats[error_type])}")

    stats_path = OUT_DIR / "corpus_stats_v1.json"
    previous = json.loads(stats_path.read_text(encoding="utf-8")).get("types", {}) if stats_path.exists() and args.types else {}
    stats_path.write_text(json.dumps({
        "base_programs": len(programs),
        "base_methods": len(items),
        "seed": args.seed,
        "inputs_per_method": args.inputs,
        "label_by_construction": sorted(LABEL_BY_CONSTRUCTION),
        "types": {**previous, **summary},
    }, indent=2), encoding="utf-8")
    sources_path = WORK_ROOT / "sources_v1.jsonl"
    if args.types and sources_path.exists():
        # A partial rebuild keeps every other type's sources.
        for line in sources_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                used_sources.setdefault(item["unit"], item["source"])
    sources_path.write_text("".join(json.dumps({"unit": k, "source": v}) + "\n" for k, v in used_sources.items()), encoding="utf-8")


def _row(unit: dict, split: str, candidate, label: int, origin: str, legacy: Set[Tuple[int, int]]) -> dict:
    flagged = "" if candidate.finding.error_type not in LEGACY_RULES else int((candidate.finding.line, candidate.finding.column) in legacy)
    return {"group": unit["group"], "unit": unit["unit"], "split": split, "origin": origin,
            "line": candidate.finding.line, "label": label, "legacy_flag": flagged,
            "span": candidate.spans[0] if candidate.spans else (0, 0), "features": candidate.features}


if __name__ == "__main__":
    main()
