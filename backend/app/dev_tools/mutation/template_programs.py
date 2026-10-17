"""Hand-written templates of CORRECT code, for the families the model-written
corpus has too little of.

The language model rarely writes a plain "find the largest value" loop, an
else-if chain on thresholds, or a loop whose condition tests something other
than its counter - so the mutation corpus had few max/min searches to mutate
and few legitimate counter-free conditions to learn from. These templates
fill that in with varied names, types and loop styles.

They are correct by construction and compiled before use, and they only
supply STARTING code: labels still come from running each mutant against its
original (build_mutation_corpus.py), never from these templates.

USAGE (from backend/)   python -m app.dev_tools.mutation.template_programs
OUTPUT  data/ml/mutation/base/templates_v1.jsonl (same shape as methods_v1.jsonl)
"""

from __future__ import annotations

import json
import random
from typing import List

from app.dev_tools.mutation.java_runner import PROJECT_ROOT

OUT_PATH = PROJECT_ROOT / "data" / "ml" / "mutation" / "base" / "templates_v1.jsonl"

ARRAYS = ["values", "scores", "temps", "prices", "marks", "readings", "heights", "ages", "points", "sales"]
MAX_NAMES = ["max", "largest", "highest", "best", "top", "maxValue", "biggest", "peak", "most"]
MIN_NAMES = ["min", "smallest", "lowest", "minValue", "least", "cheapest", "coldest", "fewest"]


def _extreme(rng: random.Random, index: int) -> str:
    keep_max = rng.random() < 0.5
    arr = rng.choice(ARRAYS)
    var = rng.choice(MAX_NAMES if keep_max else MIN_NAMES)
    kind = rng.choice(["int", "int", "double"])
    op = rng.choice([">", ">="]) if keep_max else rng.choice(["<", "<="])
    start = rng.choice(["element", "element", "constant"])
    if start == "constant":
        if kind == "int":
            init = "Integer.MIN_VALUE" if keep_max else "Integer.MAX_VALUE"
        else:
            init = "-Double.MAX_VALUE" if keep_max else "Double.MAX_VALUE"
    else:
        init = f"{arr}[0]"
    name = f"{'find' if rng.random() < 0.5 else 'get'}{var[0].upper()}{var[1:]}{index}"
    guard = rng.choice([
        f"        if ({arr}.length == 0) return 0;\n",
        f"        if ({arr} == null || {arr}.length == 0) {{\n            return 0;\n        }}\n",
    ])
    style = rng.choice(["for", "foreach", "while", "math"])
    if style == "for":
        first = 1 if start == "element" else 0
        loop = (f"        for (int i = {first}; i < {arr}.length; i++) {{\n"
                f"            if ({arr}[i] {op} {var}) {{\n                {var} = {arr}[i];\n            }}\n        }}\n")
    elif style == "foreach":
        item = rng.choice(["x", "value", "v", "item"])
        loop = (f"        for ({kind} {item} : {arr}) {{\n"
                f"            if ({item} {op} {var})\n                {var} = {item};\n        }}\n")
    elif style == "while":
        loop = (f"        int i = 0;\n        while (i < {arr}.length) {{\n"
                f"            if ({arr}[i] {op} {var}) {{\n                {var} = {arr}[i];\n            }}\n            i++;\n        }}\n")
    else:
        fn = "max" if keep_max else "min"
        loop = (f"        for (int i = 0; i < {arr}.length; i++) {{\n"
                f"            {var} = Math.{fn}({var}, {arr}[i]);\n        }}\n")
    return (f"public static {kind} {name}({kind}[] {arr}) {{\n{guard}"
            f"        {kind} {var} = {init};\n{loop}        return {var};\n}}").replace("\n        ", "\n    ")


def _chain(rng: random.Random, index: int) -> str:
    var = rng.choice(["score", "mark", "age", "temp", "speed", "total", "points", "percent"])
    labels = rng.sample(["\"A\"", "\"B\"", "\"C\"", "\"D\"", "\"Low\"", "\"High\"", "\"Mid\"", "\"Top\""], 4)
    thresholds = sorted(rng.sample(range(10, 100, 5), 3), reverse=True)
    style = rng.choice(["greater", "less", "range"])
    if style == "greater":
        tests = [f"{var} >= {t}" for t in thresholds]
    elif style == "less":
        ascending = sorted(thresholds)
        tests = [f"{var} < {t}" for t in ascending]
    else:
        a, b, c = sorted(thresholds)
        tests = [f"{var} >= {c}", f"{var} >= {b} && {var} < {c}", f"{var} >= {a} && {var} < {b}"]
    lines = [f"public static String classify{var[0].upper()}{var[1:]}{index}(int {var}) {{"]
    for k, test in enumerate(tests):
        keyword = "if" if k == 0 else "} else if"
        lines.append(f"    {keyword} ({test}) {{")
        lines.append(f"        return {labels[k]};")
    lines.append("    } else {")
    lines.append(f"        return {labels[3]};")
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines)


def _counter_free_condition(rng: random.Random, index: int) -> str:
    # Legitimate loops whose condition does not mention the counter - the
    # correct look-alikes of NESTED_LOOP_WRONG_COUNTER.
    kind = rng.choice(["collatz", "halve", "digits", "budget"])
    counter = rng.choice(["steps", "count", "rounds", "k", "tries"])
    if kind == "collatz":
        return (f"public static int collatzSteps{index}(int n) {{\n    if (n < 1) return 0;\n    int {counter};\n"
                f"    for ({counter} = 0; n != 1; {counter}++) {{\n        if (n % 2 == 0) n = n / 2;\n        else n = 3 * n + 1;\n"
                f"        if ({counter} > 500) break;\n    }}\n    return {counter};\n}}")
    if kind == "halve":
        return (f"public static int halvings{index}(int n) {{\n    int {counter} = 0;\n"
                f"    for (int value = n; value > 1; {counter}++) {{\n        value = value / 2;\n    }}\n    return {counter};\n}}")
    if kind == "digits":
        return (f"public static int digitCount{index}(int n) {{\n    if (n == 0) return 1;\n    int {counter} = 0;\n"
                f"    for (int rest = Math.abs(n); rest > 0; {counter}++) {{\n        rest = rest / 10;\n    }}\n    return {counter};\n}}")
    return (f"public static int purchases{index}(int[] prices, int budget) {{\n    if (prices == null) return 0;\n    int {counter} = 0;\n"
            f"    for (int i = 0; i < prices.length; i++) {{\n        if (prices[i] < 0 || prices[i] > budget) continue;\n"
            f"        budget -= prices[i];\n        {counter}++;\n    }}\n    return {counter};\n}}")


def _deliberate_skip(rng: random.Random, index: int) -> str:
    # Correct for loops that move their counter on purpose to consume the
    # next character - the look-alikes of LOOP_COUNTER_CHANGED_IN_BODY.
    text = rng.choice(["text", "line", "input", "word", "message"])
    i = rng.choice(["i", "pos", "k"])
    kind = rng.choice(["escape", "marker", "digits"])
    if kind == "escape":
        return (f"public static String unescape{index}(String {text}) {{\n    if ({text} == null) return \"\";\n    String out = \"\";\n"
                f"    for (int {i} = 0; {i} < {text}.length(); {i}++) {{\n        char c = {text}.charAt({i});\n"
                f"        if (c == '\\\\' && {i} + 1 < {text}.length()) {{\n            {i}++;\n            c = {text}.charAt({i});\n        }}\n"
                f"        out += c;\n    }}\n    return out;\n}}")
    if kind == "marker":
        return (f"public static String capitaliseMarked{index}(String {text}) {{\n    if ({text} == null) return \"\";\n    String out = \"\";\n"
                f"    for (int {i} = 0; {i} < {text}.length(); {i}++) {{\n        char c = {text}.charAt({i});\n"
                f"        if (c == '#' && {i} + 1 < {text}.length()) {{\n            {i}++;\n            out += Character.toUpperCase({text}.charAt({i}));\n        }} else {{\n            out += c;\n        }}\n"
                f"    }}\n    return out;\n}}")
    return (f"public static int sumOfNumbers{index}(String {text}) {{\n    if ({text} == null) return 0;\n    int total = 0;\n"
            f"    for (int {i} = 0; {i} < {text}.length(); {i}++) {{\n        if (Character.isDigit({text}.charAt({i}))) {{\n            int value = 0;\n"
            f"            while ({i} < {text}.length() && Character.isDigit({text}.charAt({i}))) {{\n                value = value * 10 + ({text}.charAt({i}) - '0');\n                {i}++;\n            }}\n"
            f"            total += value;\n            {i}--;\n        }}\n    }}\n    return total;\n}}")


def main() -> None:
    rng = random.Random(11)
    items: List[dict] = []
    for index in range(160):
        items.append({"id": f"x_ext{index:03d}", "topic_index": 100, "topic": "template: max/min search",
                      "name": f"extreme{index}", "code_a": _extreme(rng, index), "code_b": None, "verdict": "kept"})
    for index in range(90):
        items.append({"id": f"x_chn{index:03d}", "topic_index": 101, "topic": "template: else-if chain",
                      "name": f"chain{index}", "code_a": _chain(rng, index), "code_b": None, "verdict": "kept"})
    for index in range(40):
        items.append({"id": f"x_cnt{index:03d}", "topic_index": 102, "topic": "template: counter-free condition",
                      "name": f"counter{index}", "code_a": _counter_free_condition(rng, index), "code_b": None, "verdict": "kept"})
    for index in range(45):
        items.append({"id": f"x_skp{index:03d}", "topic_index": 103, "topic": "template: deliberate counter skip",
                      "name": f"skip{index}", "code_a": _deliberate_skip(rng, index), "code_b": None, "verdict": "kept"})
    OUT_PATH.write_text("".join(json.dumps(item) + "\n" for item in items), encoding="utf-8")
    print(f"{len(items)} template programs -> {OUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
