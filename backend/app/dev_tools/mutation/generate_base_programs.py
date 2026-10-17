"""Ask a language model for CORRECT beginner Java methods, and keep only the
ones two independent versions agree on.

WHY
    The old corpus was written so the rule locators would fire on it, and its
    labels were checked against those same locators - so the ML gates learned
    to agree with the rules and scored 1.0 doing it. The mutation corpus
    starts from correct code instead and plants each bug itself
    (build_mutation_corpus.py), with labels decided by running the code.

    That only works if the starting code really is correct, and a model's code
    is not correct by default. So each method is written twice: once from a
    topic, and once more, separately, from nothing but the first version's
    name, signature and description. Both versions are compiled and run on the
    same 40 seeded inputs (harness/Fuzz.java). A method is kept only when the
    two behave identically on every input - two independent writers making the
    same mistake on the same inputs is far less likely than one making it.
    Both versions are kept: they are two different correct programs.

USAGE (from backend/)
    python -m app.dev_tools.mutation.generate_base_programs --env-file ../../Study-Guider/backend/.env
    (reads OPENAI_API_KEY from the environment or from --env-file; never prints it)

OUTPUT
    data/ml/mutation/base/methods_v1.jsonl   one JSON object per kept method
    data/ml/mutation/base/rejected_v1.jsonl  the rest, with the reason
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

from app.dev_tools.mutation.java_runner import (
    PROJECT_ROOT,
    WORK_ROOT,
    behaviour_many,
    compile_many,
    literals,
)
from app.services.llm_client import LLMUnavailable, complete

BASE_DIR = PROJECT_ROOT / "data" / "ml" / "mutation" / "base"
KEPT_PATH = BASE_DIR / "methods_v1.jsonl"
REJECTED_PATH = BASE_DIR / "rejected_v1.jsonl"
VERIFY_DIR = WORK_ROOT / "verify"

# Each topic is chosen so that the correct code contains the sites the new
# detectors look at - and, just as important, the CORRECT versions of the
# patterns that look like bugs (a[i + 1] with i < a.length - 1, a total reset
# at the top of each row, a braceless single-statement if).
TOPICS = [
    "running totals, averages and counts over int or double arrays",
    "finding the largest or smallest value, or its position, in an array (values may be negative)",
    "searching: contains, indexOf, all-match and any-match checks that return as soon as they know",
    "comparing neighbouring elements: is the array sorted, count rises, biggest jump, pairs a[i] and a[i + 1]",
    "2D int arrays: row totals, column totals, the main diagonal, counting cells, the largest row",
    "nested loops over pairs of positions (i, j): counting pairs, duplicates, pair sums, matching elements of two arrays",
    "String processing with charAt and length: counting vowels or digits, reversing, palindromes, run lengths",
    "classifying a number with an if / else if chain on thresholds: grades, BMI bands, tax brackets, age groups",
    "guarded checks that combine conditions with && and || so the second part is only evaluated when safe (null Strings, empty arrays, index in range, division by a non-zero value)",
    "while loops with a counter: digit sums, counting digits, Collatz steps, powers, gcd, repeated halving",
    "switch statements on int, char or String: day names, menu codes, simple calculators, letter grades",
    "changing an array in place: reverse, rotate by one, swap pairs, prefix sums, replacing negatives",
    "String arrays: longest word, count words that match a rule, join with a separator, first word alphabetically",
    "number arithmetic mixing int and double: percentages, averages that must not be truncated, unit conversions",
    "loops that skip or step: every second element, stepping by k, counting down, stopping early with break",
    "ArrayList<Integer> and List<String>: totals, filtering into a new list, counting matches, finding extremes",
    # Added so the corpus also holds the CORRECT forms of the new mistakes -
    # without them a model has nothing to tell the mistake apart from.
    "for loops that deliberately move the loop counter inside the body: skipping a character after a backslash, jumping over a run of equal values, reading values in pairs, run-length encoding",
    "loops with two counters or a flag condition: two-pointer palindrome checks, merging two sorted arrays, a for loop that stops when a boolean becomes true, walking two arrays at once",
    "tracking the largest or smallest value and where it is: start from the first element or from Integer.MIN_VALUE / MAX_VALUE, and also maxima of lengths or counts that may correctly start at 0",
    "streaks and runs: the longest streak of rising values, the longest run of one character, counting words by resetting a counter at spaces, per-row totals reset for every row of a 2D array",
]

ALLOWED_TYPES = (
    "int, long, double, boolean, char, String, Integer, Double, "
    "int[], double[], char[], boolean[], String[], int[][], List<Integer>, List<String>, ArrayList<Integer>"
)

WRITE_PROMPT = """You are writing practice code for first-year Java students.

Topic: {topic}

Write {count} different static Java methods on this topic. They must all be
CORRECT, and written the plain way a careful first-year student would write
them - simple loops and ifs, sensible variable names, no streams, no lambdas,
no recursion, no helper methods of your own (java.util.Arrays, Math and String
methods are fine).

Rules for every method:
- `public static`, with a return value or printing with System.out.println.
- Parameters only of these types: {allowed}.
- Deterministic: no input reading, no randomness, no time, no files.
- Handle empty arrays, empty Strings and null inputs in a definite way, and say
  exactly how in the description (for example "returns 0 for an empty array",
  "returns -1 when not found", "throws nothing; null counts as empty").
- Vary the style across the methods: for loops, while loops, enhanced for
  loops, early return, break, else if chains, && and || guards, nested loops,
  and some single-statement if/for bodies written without braces.
- Each method between 4 and 25 lines.
{avoid}
Return ONLY a JSON object of this shape, with the Java code as a JSON string:
{{"methods": [{{"name": "...", "signature": "public static int sumOf(int[] values)",
"description": "one or two sentences, including the edge cases", "code": "public static int sumOf(int[] values) {{ ... }}"}}]}}
"""

REWRITE_PROMPT = """You are writing practice code for first-year Java students.

Implement each method below from its signature and description alone. Write
it your own way - plain, correct, the way a careful first-year student would,
with no streams, lambdas, recursion or helper methods of your own
(java.util.Arrays, Math and String methods are fine). Follow the description
exactly, including what it says about empty, null and edge-case inputs.

{specs}

Return ONLY a JSON object: {{"methods": [{{"name": "...", "code": "public static ... {{ ... }}"}}]}}
"""


def _load_env_file(path: Optional[str]) -> None:
    if not path:
        return
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("OPENAI_API_KEY=") and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")


def _ask_json(prompt: str, api_key: str) -> dict:
    text = complete(
        prompt,
        api_key=api_key,
        max_output_tokens=9000,
        timeout=240,
        json_output=True,
        reasoning_effort="medium",
    )
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _clean(method: dict) -> Optional[dict]:
    name = str(method.get("name") or "").strip()
    code = str(method.get("code") or "").strip()
    if not _NAME.match(name) or f" {name}(" not in code or "static" not in code:
        return None
    if re.search(r"\bScanner\b|Random\b|System\.in|\.stream\(|->|Thread", code):
        return None
    return {**method, "name": name, "code": code}


def _class_source(class_name: str, method_code: str) -> str:
    return (
        "import java.util.*;\n\n"
        f"public class {class_name} {{\n"
        + "\n".join("    " + line for line in method_code.splitlines())
        + "\n}\n"
    )


def _verify(batch: List[dict]) -> List[dict]:
    """Compile and run both versions of each method; mark agreement."""
    jobs = []
    for item in batch:
        for version in ("a", "b"):
            code = item.get(f"code_{version}")
            if not code:
                continue
            class_name = f"V{version.upper()}_{item['id']}"
            folder = VERIFY_DIR / class_name
            folder.mkdir(parents=True, exist_ok=True)
            source = folder / f"{class_name}.java"
            source.write_text(_class_source(class_name, code), encoding="utf-8")
            jobs.append((source, folder / "classes", item, version, class_name))

    compiled = compile_many([(source, out) for source, out, *_ in jobs])
    shared = {id(item): literals(item.get("code_a") or "", item.get("code_b") or "") for item in batch}
    runnable = [(out, name, shared[id(owner)]) for source, out, owner, _, name in jobs if compiled.get(str(source)) is None]
    transcripts = behaviour_many(runnable, inputs=60)

    for item in batch:
        results = {}
        for source, out, owner, version, name in jobs:
            if owner is not item:
                continue
            error = compiled.get(str(source))
            results[version] = ("ERR " + (error or "")) if error else transcripts.get((out, name, shared[id(owner)]), "")
        a, b = results.get("a", "missing"), results.get("b", "missing")
        if a.startswith("ERR") or b.startswith("ERR"):
            item["verdict"] = "compile_error"
        elif "TIMEOUT" in a or "TIMEOUT" in b or "HARNESS" in a or "HARNESS" in b:
            item["verdict"] = "timeout"
        elif "SKIP " in a:
            item["verdict"] = "unsupported_parameters"
        elif a != b:
            item["verdict"] = "versions_disagree"
        elif a.count("THROWS") > 0.6 * max(1, a.count("RETURNS") + a.count("THROWS")):
            item["verdict"] = "mostly_throws"
        else:
            item["verdict"] = "kept"
    return batch


def _round(topic_index: int, round_index: int, count: int, api_key: str, seen_names: set) -> List[dict]:
    topic = TOPICS[topic_index]
    avoid = ""
    if seen_names:
        sample = ", ".join(sorted(seen_names)[:40])
        avoid = f"- Do not repeat these method ideas, already written: {sample}\n"
    try:
        first = _ask_json(WRITE_PROMPT.format(topic=topic, count=count, allowed=ALLOWED_TYPES, avoid=avoid), api_key)
    except (LLMUnavailable, json.JSONDecodeError) as error:
        print(f"  topic {topic_index} round {round_index}: first pass failed ({error})")
        return []

    methods = [m for m in (_clean(m) for m in first.get("methods") or []) if m]
    if not methods:
        return []
    specs = "\n\n".join(
        f"{i + 1}. name: {m['name']}\n   signature: {m.get('signature', '')}\n   description: {m.get('description', '')}"
        for i, m in enumerate(methods)
    )
    try:
        second = _ask_json(REWRITE_PROMPT.format(specs=specs), api_key)
    except (LLMUnavailable, json.JSONDecodeError) as error:
        print(f"  topic {topic_index} round {round_index}: second pass failed ({error})")
        return []
    rewritten = {m["name"]: m["code"] for m in (_clean(m) for m in second.get("methods") or []) if m}

    items = []
    for j, method in enumerate(methods):
        items.append({
            "id": f"t{topic_index:02d}r{round_index:02d}m{j:02d}",
            "topic_index": topic_index,
            "topic": topic,
            "name": method["name"],
            "signature": method.get("signature", ""),
            "description": method.get("description", ""),
            "code_a": method["code"],
            "code_b": rewritten.get(method["name"]),
        })
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--env-file", help="a .env holding OPENAI_API_KEY (read, never printed)")
    parser.add_argument("--rounds", type=int, default=4, help="rounds per topic")
    parser.add_argument("--count", type=int, default=8, help="methods per round")
    parser.add_argument("--topics", type=str, default="", help="comma-separated topic indexes (default all)")
    parser.add_argument("--parallel", type=int, default=6)
    parser.add_argument("--append", action="store_true", help="add to the existing corpus instead of replacing it")
    parser.add_argument("--reverify", action="store_true",
                        help="re-run the two-version check on the kept corpus (after the harness changes) and stop")
    args = parser.parse_args()

    if args.reverify:
        items = [json.loads(line) for line in KEPT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        old_rejected = [json.loads(line) for line in REJECTED_PATH.read_text(encoding="utf-8").splitlines() if line.strip()] if REJECTED_PATH.exists() else []
        if VERIFY_DIR.exists():
            shutil.rmtree(VERIFY_DIR)
        checked = _verify(items)
        kept = [item for item in checked if item["verdict"] == "kept"]
        dropped = [item for item in checked if item["verdict"] != "kept"]
        KEPT_PATH.write_text("".join(json.dumps(item) + "\n" for item in kept), encoding="utf-8")
        REJECTED_PATH.write_text("".join(json.dumps(item) + "\n" for item in old_rejected + dropped), encoding="utf-8")
        print(f"re-verified {len(checked)}: kept {len(kept)}, dropped {len(dropped)}")
        return

    _load_env_file(args.env_file)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set (pass --env-file).")

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    if VERIFY_DIR.exists():
        shutil.rmtree(VERIFY_DIR)
    topics = [int(t) for t in args.topics.split(",") if t.strip()] or list(range(len(TOPICS)))

    kept: List[dict] = []
    rejected: List[dict] = []
    if args.append and KEPT_PATH.exists():
        kept = [json.loads(line) for line in KEPT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        if REJECTED_PATH.exists():
            rejected = [json.loads(line) for line in REJECTED_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing_ids = {item["id"] for item in kept}

    # Rounds of one topic run one after another (each avoids the names before
    # it); different topics run side by side.
    def run_topic(topic_index: int) -> List[dict]:
        names: set = {item["name"] for item in kept if item["topic_index"] == topic_index}
        items: List[dict] = []
        offset = sum(1 for item in kept if item["topic_index"] == topic_index) // max(1, args.count) + 1
        for r in range(args.rounds):
            batch = _round(topic_index, offset + r, args.count, api_key, names)
            names.update(item["name"] for item in batch)
            items.extend(item for item in batch if item["id"] not in existing_ids)
        return items

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        generated = [item for part in pool.map(run_topic, topics) for item in part]

    print(f"generated {len(generated)} methods; verifying...")
    for item in _verify(generated):
        (kept if item["verdict"] == "kept" else rejected).append(item)

    rng = random.Random(42)
    rng.shuffle(rejected)
    KEPT_PATH.write_text("".join(json.dumps(item) + "\n" for item in kept), encoding="utf-8")
    REJECTED_PATH.write_text("".join(json.dumps(item) + "\n" for item in rejected), encoding="utf-8")

    verdicts: Dict[str, int] = {}
    for item in generated:
        verdicts[item["verdict"]] = verdicts.get(item["verdict"], 0) + 1
    print("verdicts:", verdicts)
    print(f"kept total: {len(kept)} -> {KEPT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
