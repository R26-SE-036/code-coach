"""Generate a verified synthetic training corpus for all 5 ML targets.

WHY THIS EXISTS
    The manual corpus (data/ml/raw_snippets/) is small (30 pairs/target) and
    uniform (tiny single-bug files), which is exactly why the models failed on
    big files (features drift out of distribution). This tool generates a much
    larger corpus with CONTROLLED DIVERSITY: file sizes from 1 to ~9 methods,
    the bug planted at a random position among harmless distractor methods,
    randomized identifiers, and — critically — "intentional" negatives where
    the rule locator fires but the code is correct (commented fall-through,
    i <= arr.length - 1, Scanner-driven while loops). Those negatives are what
    teach an ML gate the judgment the rule cannot make.

LABEL SAFETY
    Labels are true by construction (the generator planted the bug or didn't)
    AND every generated file is verified before it is written:
      * it must parse with completeness 1.0 (no error nodes), and
      * the set of the 5 target locators that fire on it must EXACTLY equal
        the expected set for its kind.
    A template drifting out of sync with a locator kills the run loudly
    instead of silently poisoning the dataset.

REPRODUCIBILITY
    Everything is driven by one RNG seed (--seed, default 42). The output
    folder is wiped and rebuilt on every run, so the corpus is a pure
    function of (this file, the seed, the counts).

OUTPUT LAYOUT (mirrors the manual corpus; consumed by build_snippet_index.py)
    data/ml/raw_snippets_generated/<category>/buggy/GenXxxBugNNN.java
    data/ml/raw_snippets_generated/<category>/fixed/GenXxxFixNNN.java
    data/ml/raw_snippets_generated/clean/GenClean*.java   (negatives + generic)

USAGE (from backend/)
    python -m app.dev_tools.generate_snippets                # defaults
    python -m app.dev_tools.generate_snippets --pairs 170 --seed 42
"""

import argparse
import random
import shutil
import sys
from pathlib import Path
from typing import Callable, Dict, FrozenSet, List, Tuple

from app.analysis.parser_utils import parse_java_code_safe
from app.analysis.issue_locators import (
    locate_off_by_one_loop_boundaries,
    locate_incorrect_conditional_operators,
    locate_array_length_index_misuses,
    locate_missing_breaks_in_switch,
    locate_while_variables_not_updated,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GENERATED_ROOT = PROJECT_ROOT / "data" / "ml" / "raw_snippets_generated"

TARGET_LOCATORS = {
    "OFF_BY_ONE_LOOP_BOUNDARY": locate_off_by_one_loop_boundaries,
    "INCORRECT_CONDITIONAL_OPERATOR": locate_incorrect_conditional_operators,
    "ARRAY_LENGTH_INDEX_MISUSE": locate_array_length_index_misuses,
    "MISSING_BREAK_IN_SWITCH": locate_missing_breaks_in_switch,
    "WHILE_VARIABLE_NOT_UPDATED": locate_while_variables_not_updated,
}

# ---------------------------------------------------------------- name pools

ARRAY_NAMES = ["scores", "prices", "marks", "values", "weights", "totals",
               "ratings", "sizes", "ages", "stocks"]
INT_NAMES = ["count", "total", "limit", "attempts", "budget", "steps",
             "level", "stock", "points", "quota"]
FLAG_NAMES = ["ready", "active", "enabled", "running", "valid", "open",
              "done", "verified", "loaded", "armed"]
THING_NAMES = ["Order", "Item", "Ticket", "Student", "Account", "Report",
               "Invoice", "Session", "Task", "Batch"]
LABEL_WORDS = ["new", "paid", "shipped", "closed", "queued", "active",
               "archived", "expired", "draft", "final"]


class VerificationError(RuntimeError):
    pass


# ------------------------------------------------------------------ helpers

def _method(lines: List[str]) -> List[str]:
    """Indent a method body by 4 spaces for placement inside the class."""
    return ["    " + line if line else "" for line in lines]


def _verify(code: str, expected: FrozenSet[str], context: str) -> None:
    parse_result = parse_java_code_safe(code)
    if parse_result.crashed or parse_result.tree is None:
        raise VerificationError(f"{context}: parse crashed\n{code}")
    if parse_result.health.completeness_score < 1.0:
        raise VerificationError(f"{context}: parse not clean\n{code}")

    fired = frozenset(
        error_type
        for error_type, locator in TARGET_LOCATORS.items()
        if locator(parse_result)
    )
    if fired != expected:
        raise VerificationError(
            f"{context}: locators fired {set(fired)} but expected {set(expected)}\n{code}"
        )


def _assemble_class(class_name: str, method_blocks: List[List[str]]) -> str:
    lines: List[str] = [f"public class {class_name} " + "{"]
    for index, block in enumerate(method_blocks):
        if index > 0:
            lines.append("")
        lines.extend(_method(block))
    lines.append("}")
    return "\n".join(lines) + "\n"


# ------------------------------------------------- distractor method library
# Every distractor must be silent on ALL five target locators (verified at
# file level). They exist to vary file size and add realistic context noise.

def _d_sum_proper(rng: random.Random, sfx: int) -> List[str]:
    arr = rng.choice(ARRAY_NAMES)
    return [
        f"static int sum{sfx}(int[] {arr}) " + "{",
        "    int total = 0;",
        f"    for (int i = 0; i < {arr}.length; i++) " + "{",
        f"        total += {arr}[i];",
        "    }",
        "    return total;",
        "}",
    ]


def _d_max_proper(rng: random.Random, sfx: int) -> List[str]:
    arr = rng.choice(ARRAY_NAMES)
    return [
        f"static int largest{sfx}(int[] {arr}) " + "{",
        f"    int best = {arr}[0];",
        f"    for (int i = 1; i < {arr}.length; i++) " + "{",
        f"        if ({arr}[i] > best) " + "{",
        f"            best = {arr}[i];",
        "        }",
        "    }",
        "    return best;",
        "}",
    ]


def _d_label_format(rng: random.Random, sfx: int) -> List[str]:
    n = rng.choice(INT_NAMES)
    lo, hi = rng.choice([(10, 50), (5, 20), (100, 500)])
    return [
        f"static String describe{sfx}(int {n}) " + "{",
        f"    if ({n} < {lo}) " + "{",
        "        return \"low\";",
        f"    }} else if ({n} > {hi}) ".replace("}}", "}") + "{",
        "        return \"high\";",
        "    }",
        "    return \"medium\";",
        "}",
    ]


def _d_switch_all_breaks(rng: random.Random, sfx: int) -> List[str]:
    words = rng.sample(LABEL_WORDS, 3)
    return [
        f"static String status{sfx}(int code) " + "{",
        "    String label;",
        "    switch (code) {",
        "        case 1:",
        f"            label = \"{words[0]}\";",
        "            break;",
        "        case 2:",
        f"            label = \"{words[1]}\";",
        "            break;",
        "        default:",
        f"            label = \"{words[2]}\";",
        "    }",
        "    return label;",
        "}",
    ]


def _d_while_proper(rng: random.Random, sfx: int) -> List[str]:
    n = rng.choice(INT_NAMES)
    return [
        f"static int drain{sfx}(int {n}) " + "{",
        "    int handled = 0;",
        f"    while ({n} > 0) " + "{",
        f"        handled += {n};",
        f"        {n}--;",
        "    }",
        "    return handled;",
        "}",
    ]


def _d_foreach_print(rng: random.Random, sfx: int) -> List[str]:
    arr = rng.choice(ARRAY_NAMES)
    return [
        f"static void printAll{sfx}(int[] {arr}) " + "{",
        f"    for (int value : {arr}) " + "{",
        "        System.out.println(value);",
        "    }",
        "}",
    ]


def _d_avg_guard(rng: random.Random, sfx: int) -> List[str]:
    return [
        f"static int average{sfx}(int total, int count) " + "{",
        "    if (count != 0) {",
        "        return total / count;",
        "    }",
        "    return 0;",
        "}",
    ]


def _d_clamp(rng: random.Random, sfx: int) -> List[str]:
    return [
        f"static int clamp{sfx}(int value, int low, int high) " + "{",
        "    if (value < low) {",
        "        return low;",
        "    } else if (value > high) {",
        "        return high;",
        "    }",
        "    return value;",
        "}",
    ]


def _d_join(rng: random.Random, sfx: int) -> List[str]:
    return [
        f"static String join{sfx}(String[] parts) " + "{",
        "    StringBuilder builder = new StringBuilder();",
        "    for (int i = 0; i < parts.length; i++) {",
        "        builder.append(parts[i]);",
        "        builder.append(\",\");",
        "    }",
        "    return builder.toString();",
        "}",
    ]


def _d_parity(rng: random.Random, sfx: int) -> List[str]:
    n = rng.choice(INT_NAMES)
    return [
        f"static boolean isEven{sfx}(int {n}) " + "{",
        f"    return {n} % 2 == 0;",
        "}",
    ]


DISTRACTORS: List[Callable[[random.Random, int], List[str]]] = [
    _d_sum_proper, _d_max_proper, _d_label_format, _d_switch_all_breaks,
    _d_while_proper, _d_foreach_print, _d_avg_guard, _d_clamp, _d_join,
    _d_parity,
]


def _pick_method_count(rng: random.Random) -> int:
    """Size diversity is the point: single-method files must NOT dominate."""
    roll = rng.random()
    if roll < 0.35:
        return 1
    if roll < 0.70:
        return rng.randint(2, 3)
    if roll < 0.95:
        return rng.randint(4, 6)
    return rng.randint(7, 9)


# -------------------------------------------------- payload template builders
# Each returns (buggy_method_lines, fixed_method_lines). Buggy and fixed are
# TRUE MINIMAL PAIRS: identical except for the planted bug.

def _p_off_by_one(rng: random.Random) -> Tuple[List[str], List[str]]:
    arr = rng.choice(ARRAY_NAMES)
    kind = rng.randrange(4)

    def loop(op: str, body: List[str], head: List[str], tail: List[str]) -> List[str]:
        return head + [
            f"    for (int i = 0; i {op} {arr}.length; i++) " + "{",
            *["    " + line for line in body],
            "    }",
        ] + tail

    if kind == 0:  # sum
        head = [f"static int addUp(int[] {arr}) " + "{", "    int total = 0;"]
        body = [f"    total += {arr}[i];"]
        tail = ["    return total;", "}"]
    elif kind == 1:  # print
        head = [f"static void show(int[] {arr}) " + "{"]
        body = [f"    System.out.println({arr}[i]);"]
        tail = ["}"]
    elif kind == 2:  # copy
        head = [
            f"static int[] duplicate(int[] {arr}) " + "{",
            f"    int[] copy = new int[{arr}.length];",
        ]
        body = [f"    copy[i] = {arr}[i];"]
        tail = ["    return copy;", "}"]
    else:  # count above threshold
        head = [f"static int countAbove(int[] {arr}, int threshold) " + "{", "    int hits = 0;"]
        body = [f"    if ({arr}[i] > threshold) " + "{", "        hits++;", "    }"]
        tail = ["    return hits;", "}"]

    return loop("<=", body, head, tail), loop("<", body, head, tail)


def _p_incorrect_conditional(rng: random.Random) -> Tuple[List[str], List[str]]:
    kind = rng.randrange(3)

    if kind == 0:  # boolean flag against literal
        flag = rng.choice(FLAG_NAMES)
        word_on, word_off = rng.sample(LABEL_WORDS, 2)

        def variant(op: str) -> List[str]:
            return [
                f"static String report(boolean {flag}) " + "{",
                f"    if ({flag} {op} true) " + "{",
                f"        return \"{word_on}\";",
                "    }",
                f"    return \"{word_off}\";",
                "}",
            ]

        return variant("="), variant("==")

    if kind == 1:  # two boolean parameters
        a, b = rng.sample(FLAG_NAMES, 2)

        def variant(op: str) -> List[str]:
            return [
                f"static boolean matches(boolean {a}, boolean {b}) " + "{",
                f"    if ({a} {op} {b}) " + "{",
                "        return true;",
                "    }",
                "    return false;",
                "}",
            ]

        return variant("="), variant("==")

    # int typo: does not compile, but students type exactly this and the
    # extension analyzes code long before it compiles.
    n = rng.choice(INT_NAMES)
    target = rng.choice([5, 10, 100])

    def variant(op: str) -> List[str]:
        return [
            f"static void announce(int {n}) " + "{",
            f"    if ({n} {op} {target}) " + "{",
            "        System.out.println(\"hit the target\");",
            "    }",
            "}",
        ]

    return variant("="), variant("==")


def _p_array_length(rng: random.Random) -> Tuple[List[str], List[str]]:
    arr = rng.choice(ARRAY_NAMES)
    kind = rng.randrange(3)

    if kind == 0:  # read last
        def variant(index: str) -> List[str]:
            return [
                f"static int lastOf(int[] {arr}) " + "{",
                f"    return {arr}[{index}];",
                "}",
            ]
    elif kind == 1:  # write last
        def variant(index: str) -> List[str]:
            return [
                f"static void stampLast(int[] {arr}, int value) " + "{",
                f"    {arr}[{index}] = value;",
                "}",
            ]
    else:  # print last
        def variant(index: str) -> List[str]:
            return [
                f"static void showLast(int[] {arr}) " + "{",
                f"    System.out.println({arr}[{index}]);",
                "}",
            ]

    return variant(f"{arr}.length"), variant(f"{arr}.length - 1")


def _p_missing_break(rng: random.Random) -> Tuple[List[str], List[str]]:
    thing = rng.choice(THING_NAMES)
    case_count = rng.randint(3, 5)
    words = rng.sample(LABEL_WORDS, case_count + 1)
    # Bug goes in a non-last case group (the rule exempts the last group).
    broken = rng.randrange(case_count - 1)

    def variant(with_bug: bool) -> List[str]:
        lines = [
            f"static String describe{thing}(int code) " + "{",
            "    String label = \"\";",
            "    switch (code) {",
        ]
        for case_index in range(case_count):
            lines.append(f"        case {case_index + 1}:")
            lines.append(f"            label = \"{words[case_index]}\";")
            if not (with_bug and case_index == broken):
                lines.append("            break;")
        lines.append("        default:")
        lines.append(f"            label = \"{words[case_count]}\";")
        lines.append("    }")
        lines.append("    return label;")
        lines.append("}")
        return lines

    return variant(True), variant(False)


def _p_while_not_updated(rng: random.Random) -> Tuple[List[str], List[str]]:
    kind = rng.randrange(3)

    if kind == 0:  # countdown that never counts down
        n = rng.choice(INT_NAMES)

        def variant(fixed: bool) -> List[str]:
            lines = [
                f"static void countdown(int {n}) " + "{",
                f"    while ({n} > 0) " + "{",
                f"        System.out.println(\"left: \" + {n});",
            ]
            if fixed:
                lines.append(f"        {n}--;")
            lines += ["    }", "}"]
            return lines

        return variant(False), variant(True)

    if kind == 1:  # accumulates into the wrong variable
        idx, limit = rng.sample(INT_NAMES, 2)

        def variant(fixed: bool) -> List[str]:
            lines = [
                f"static int gather(int {idx}, int {limit}) " + "{",
                "    int sum = 0;",
                f"    while ({idx} < {limit}) " + "{",
                f"        sum += {idx};",
            ]
            if fixed:
                lines.append(f"        {idx}++;")
            lines += ["    }", "    return sum;", "}"]
            return lines

        return variant(False), variant(True)

    # flag never set by the loop body
    flag = rng.choice(FLAG_NAMES)
    n = rng.choice(INT_NAMES)

    def variant(fixed: bool) -> List[str]:
        lines = [
            f"static void pump(boolean {flag}, int {n}) " + "{",
            f"    while (!{flag}) " + "{",
            f"        System.out.println({n});",
            f"        {n}++;",
        ]
        if fixed:
            lines.append(f"        {flag} = {n} > 10;")
        lines += ["    }", "}"]
        return lines

    return variant(False), variant(True)


PAYLOADS: Dict[str, Tuple[str, str, Callable[[random.Random], Tuple[List[str], List[str]]]]] = {
    # category folder -> (error type, file stem base, pair builder)
    "off_by_one": ("OFF_BY_ONE_LOOP_BOUNDARY", "GenOffByOne", _p_off_by_one),
    "incorrect_conditional_operator": (
        "INCORRECT_CONDITIONAL_OPERATOR", "GenIncorrectConditional", _p_incorrect_conditional
    ),
    "array_length_index_misuse": (
        "ARRAY_LENGTH_INDEX_MISUSE", "GenArrayIndex", _p_array_length
    ),
    "missing_break_in_switch": (
        "MISSING_BREAK_IN_SWITCH", "GenMissingBreak", _p_missing_break
    ),
    "while_variable_not_updated": (
        "WHILE_VARIABLE_NOT_UPDATED", "GenWhileNoUpdate", _p_while_not_updated
    ),
}


# ------------------------------------------ intentional / hard negatives
# Clean-labeled files that still light features (and sometimes the rule).
# These teach the gate the judgment the rule cannot make.

def _n_off_by_one_minus_one(rng: random.Random) -> Tuple[List[str], FrozenSet[str]]:
    # CORRECT Java the crude rule still flags: <= arr.length - 1
    arr = rng.choice(ARRAY_NAMES)
    lines = [
        f"static int tally(int[] {arr}) " + "{",
        "    int total = 0;",
        f"    for (int i = 0; i <= {arr}.length - 1; i++) " + "{",
        f"        total += {arr}[i];",
        "    }",
        "    return total;",
        "}",
    ]
    return lines, frozenset({"OFF_BY_ONE_LOOP_BOUNDARY"})


def _n_commented_fallthrough(rng: random.Random) -> Tuple[List[str], FrozenSet[str]]:
    # Intentional, documented fall-through: the rule fires, the code is right.
    lines = [
        "static void printPermissions(int level) {",
        "    switch (level) {",
        "        case 3:",
        "            System.out.println(\"can delete\");",
        "            // fall through: higher levels include lower rights",
        "        case 2:",
        "            System.out.println(\"can edit\");",
        "            // fall through",
        "        case 1:",
        "            System.out.println(\"can view\");",
        "            break;",
        "        default:",
        "            System.out.println(\"no access\");",
        "    }",
        "}",
    ]
    return lines, frozenset({"MISSING_BREAK_IN_SWITCH"})


def _n_stacked_labels(rng: random.Random) -> Tuple[List[str], FrozenSet[str]]:
    # Stacked empty labels are idiomatic; the rule already skips them.
    word_a, word_b = rng.sample(LABEL_WORDS, 2)
    lines = [
        "static String bucket(int code) {",
        "    String label;",
        "    switch (code) {",
        "        case 1:",
        "        case 2:",
        f"            label = \"{word_a}\";",
        "            break;",
        "        default:",
        f"            label = \"{word_b}\";",
        "    }",
        "    return label;",
        "}",
    ]
    return lines, frozenset()


def _n_scanner_while(rng: random.Random) -> Tuple[List[str], FrozenSet[str]]:
    # Method-call condition: state advances invisibly; the rule skips these.
    lines = [
        "static void readAll(java.util.Scanner scanner) {",
        "    while (scanner.hasNextLine()) {",
        "        System.out.println(scanner.nextLine());",
        "    }",
        "}",
    ]
    return lines, frozenset()


def _n_while_true_break(rng: random.Random) -> Tuple[List[str], FrozenSet[str]]:
    n = rng.choice(INT_NAMES)
    lines = [
        f"static int spin(int {n}) " + "{",
        "    int rounds = 0;",
        "    while (true) {",
        "        rounds++;",
        f"        if (rounds > {n}) " + "{",
        "            break;",
        "        }",
        "    }",
        "    return rounds;",
        "}",
    ]
    return lines, frozenset()


def _n_verbose_boolean(rng: random.Random) -> Tuple[List[str], FrozenSet[str]]:
    # 'if (flag == true)' — verbose but correct; hard negative for the
    # incorrect-conditional model (boolean literal feature lights up).
    flag = rng.choice(FLAG_NAMES)
    lines = [
        f"static String toggle(boolean {flag}) " + "{",
        f"    if ({flag} == true) " + "{",
        "        return \"on\";",
        "    }",
        "    return \"off\";",
        "}",
    ]
    return lines, frozenset()


def _n_correct_last_index(rng: random.Random) -> Tuple[List[str], FrozenSet[str]]:
    # arr[arr.length - 1]: correct; '.length in index' feature lights up.
    arr = rng.choice(ARRAY_NAMES)
    lines = [
        f"static int tail(int[] {arr}) " + "{",
        f"    return {arr}[{arr}.length - 1];",
        "}",
    ]
    return lines, frozenset()


NEGATIVES: List[Tuple[str, int, Callable[[random.Random], Tuple[List[str], FrozenSet[str]]]]] = [
    # (file stem base, how many, builder)
    ("GenCleanBoundaryMinusOne", 40, _n_off_by_one_minus_one),
    ("GenCleanFallThrough", 30, _n_commented_fallthrough),
    ("GenCleanStackedLabels", 20, _n_stacked_labels),
    ("GenCleanScannerLoop", 20, _n_scanner_while),
    ("GenCleanWhileTrueBreak", 20, _n_while_true_break),
    ("GenCleanVerboseBoolean", 30, _n_verbose_boolean),
    ("GenCleanTailIndex", 30, _n_correct_last_index),
]


# ------------------------------------------------------------------ assembly

def _build_file(
    rng: random.Random,
    class_name: str,
    payload_lines: List[str],
    expected: FrozenSet[str],
) -> str:
    """Surround the payload with 0..8 distractor methods at a random slot."""
    method_count = _pick_method_count(rng)
    blocks: List[List[str]] = []
    for sfx in range(method_count - 1):
        distractor = rng.choice(DISTRACTORS)
        blocks.append(distractor(rng, sfx + 1))
    position = rng.randint(0, len(blocks))
    blocks.insert(position, payload_lines)

    code = _assemble_class(class_name, blocks)
    _verify(code, expected, class_name)
    return code


def _write(path: Path, code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=170,
                        help="buggy/fixed pairs per target (default 170)")
    parser.add_argument("--generic-cleans", type=int, default=120,
                        help="generic clean files (default 120)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # Wipe and rebuild: the corpus is a pure function of code + seed + counts.
    if GENERATED_ROOT.exists():
        assert "raw_snippets_generated" in str(GENERATED_ROOT)
        shutil.rmtree(GENERATED_ROOT)

    rng = random.Random(args.seed)
    written = 0

    # 1) buggy/fixed minimal pairs per target
    for category, (error_type, stem_base, build_pair) in PAYLOADS.items():
        for number in range(1, args.pairs + 1):
            buggy_payload, fixed_payload = build_pair(rng)

            # The pair shares distractors: clone the RNG state so both files
            # get the SAME surroundings and differ only in the bug.
            surroundings_seed = rng.random()
            buggy_rng = random.Random(surroundings_seed)
            fixed_rng = random.Random(surroundings_seed)

            buggy_name = f"{stem_base}Bug{number:03d}"
            fixed_name = f"{stem_base}Fix{number:03d}"

            buggy_code = _build_file(buggy_rng, buggy_name, buggy_payload,
                                     frozenset({error_type}))
            fixed_code = _build_file(fixed_rng, fixed_name, fixed_payload,
                                     frozenset())

            _write(GENERATED_ROOT / category / "buggy" / f"{buggy_name}.java", buggy_code)
            _write(GENERATED_ROOT / category / "fixed" / f"{fixed_name}.java", fixed_code)
            written += 2
        print(f"{category}: {args.pairs} verified pairs")

    # 2) intentional / hard negatives (all labeled clean)
    for stem_base, count, build_negative in NEGATIVES:
        for number in range(1, count + 1):
            payload_lines, expected = build_negative(rng)
            name = f"{stem_base}{number:03d}"
            code = _build_file(rng, name, payload_lines, expected)
            _write(GENERATED_ROOT / "clean" / f"{name}.java", code)
            written += 1
        print(f"{stem_base}: {count} verified negatives")

    # 3) generic cleans (pure distractor assemblies, size-varied)
    for number in range(1, args.generic_cleans + 1):
        name = f"GenCleanGeneric{number:03d}"
        method_count = _pick_method_count(rng)
        blocks = [rng.choice(DISTRACTORS)(rng, sfx + 1) for sfx in range(method_count)]
        code = _assemble_class(name, blocks)
        _verify(code, frozenset(), name)
        _write(GENERATED_ROOT / "clean" / f"{name}.java", code)
        written += 1
    print(f"GenCleanGeneric: {args.generic_cleans} verified cleans")

    print(f"\nTotal files written: {written} (seed={args.seed})")
    print("Next: python -m app.dev_tools.build_snippet_index")
    return 0


if __name__ == "__main__":
    sys.exit(main())
