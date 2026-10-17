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


# ── families added with the promoted types: the correct look-alikes ──

def _sort(rng: random.Random, index: int) -> str:
    # n - 1 passes are enough: `pass < a.length - 1` is the LOOP_SKIPS look-alike.
    arr = rng.choice(ARRAYS)
    outer, inner = rng.choice([("pass", "i"), ("i", "j"), ("round", "k")])
    kind = rng.choice(["bubble", "selection", "insertion"])
    if kind == "bubble":
        return (f"public static void bubbleSort{index}(int[] {arr}) {{\n    if ({arr} == null) return;\n"
                f"    for (int {outer} = 0; {outer} < {arr}.length - 1; {outer}++) {{\n"
                f"        for (int {inner} = 0; {inner} < {arr}.length - 1 - {outer}; {inner}++) {{\n"
                f"            if ({arr}[{inner}] > {arr}[{inner} + 1]) {{\n                int swap = {arr}[{inner}];\n"
                f"                {arr}[{inner}] = {arr}[{inner} + 1];\n                {arr}[{inner} + 1] = swap;\n            }}\n        }}\n    }}\n}}")
    if kind == "selection":
        return (f"public static void selectionSort{index}(int[] {arr}) {{\n    if ({arr} == null) return;\n"
                f"    for (int {outer} = 0; {outer} < {arr}.length - 1; {outer}++) {{\n        int smallest = {outer};\n"
                f"        for (int {inner} = {outer} + 1; {inner} < {arr}.length; {inner}++) {{\n"
                f"            if ({arr}[{inner}] < {arr}[smallest]) smallest = {inner};\n        }}\n"
                f"        int swap = {arr}[{outer}];\n        {arr}[{outer}] = {arr}[smallest];\n        {arr}[smallest] = swap;\n    }}\n}}")
    return (f"public static void insertionSort{index}(int[] {arr}) {{\n    if ({arr} == null) return;\n"
            f"    for (int {outer} = 1; {outer} < {arr}.length; {outer}++) {{\n        int key = {arr}[{outer}];\n        int {inner} = {outer} - 1;\n"
            f"        while ({inner} >= 0 && {arr}[{inner}] > key) {{\n            {arr}[{inner} + 1] = {arr}[{inner}];\n            {inner}--;\n        }}\n"
            f"        {arr}[{inner} + 1] = key;\n    }}\n}}")


def _header_does_the_work(rng: random.Random, index: int) -> str:
    # Empty loop bodies on purpose, and assignments inside conditions on purpose.
    arr = rng.choice(ARRAYS)
    kind = rng.choice(["search", "skip", "indexof", "digits", "compound"])
    if kind == "search":
        return (f"public static int positionOf{index}(int[] {arr}, int target) {{\n    if ({arr} == null) return -1;\n    int i;\n"
                f"    for (i = 0; i < {arr}.length && {arr}[i] != target; i++);\n    return i == {arr}.length ? -1 : i;\n}}")
    if kind == "skip":
        return (f"public static int firstNonSpace{index}(String text) {{\n    if (text == null) return -1;\n    int i = 0;\n"
                f"    for (; i < text.length() && text.charAt(i) == ' '; i++)\n        ;\n    return i;\n}}")
    if kind == "indexof":
        c = rng.choice(["a", "b", " "])
        return (f"public static int occurrences{index}(String text) {{\n    if (text == null) return 0;\n    int count = 0;\n    int from = 0;\n    int pos;\n"
                f"    while ((pos = text.indexOf('{c}', from)) != -1) {{\n        count++;\n        from = pos + 1;\n    }}\n    return count;\n}}")
    if kind == "digits":
        return (f"public static int digitsAfterFirst{index}(int n) {{\n    n = Math.abs(n);\n    int count = 0;\n"
                f"    while ((n = n / 10) > 0) {{\n        count++;\n    }}\n    return count;\n}}")
    return (f"public static int stepsToReach{index}(int[] {arr}, int limit) {{\n    if ({arr} == null) return 0;\n    int total = 0;\n    int steps = 0;\n"
            f"    for (int i = 0; i < {arr}.length; i++) {{\n        if ((total = total + Math.abs({arr}[i])) > limit) break;\n        steps++;\n    }}\n    return steps;\n}}")


def _flags(rng: random.Random, index: int) -> str:
    arr = rng.choice(ARRAYS)
    flag = rng.choice(["found", "seen", "hasNegative", "valid", "done", "ok"])
    kind = rng.choice(["any", "all", "until", "toggle"])
    if kind == "any":
        return (f"public static boolean anyAbove{index}(int[] {arr}, int limit) {{\n    if ({arr} == null) return false;\n    boolean {flag} = false;\n"
                f"    for (int i = 0; i < {arr}.length; i++) {{\n        if ({arr}[i] > limit) {{\n            {flag} = true;\n        }}\n    }}\n"
                f"    if ({flag}) {{\n        return true;\n    }}\n    return false;\n}}")
    if kind == "all":
        return (f"public static boolean allPositive{index}(int[] {arr}) {{\n    if ({arr} == null) return false;\n    boolean {flag} = true;\n"
                f"    for (int i = 0; i < {arr}.length && {flag}; i++) {{\n        if ({arr}[i] <= 0) {flag} = false;\n    }}\n    return {flag};\n}}")
    if kind == "until":
        return (f"public static int stepsUntil{index}(int start, int goal) {{\n    boolean {flag} = false;\n    int steps = 0;\n    int value = start;\n"
                f"    while (!{flag} && steps < 100) {{\n        value = value * 2 + 1;\n        steps++;\n        if (value >= goal) {flag} = true;\n    }}\n    return steps;\n}}")
    return (f"public static int countFlips{index}(boolean[] switches) {{\n    if (switches == null) return 0;\n    int flips = 0;\n    boolean on = false;\n"
            f"    for (int i = 0; i < switches.length; i++) {{\n        if (switches[i] != on) {{\n            flips++;\n            on = switches[i];\n        }}\n    }}\n    return flips;\n}}")


def _tolerance(rng: random.Random, index: int) -> str:
    eps = rng.choice(["0.0001", "1e-9", "0.000001", "0.001"])
    kind = rng.choice(["match", "whole", "zero", "close"])
    if kind == "match":
        return (f"public static boolean totalMatches{index}(double[] prices, double expected) {{\n    if (prices == null) return false;\n    double total = 0;\n"
                f"    for (double p : prices) total += p;\n    return Math.abs(total - expected) < {eps};\n}}")
    if kind == "whole":
        return (f"public static boolean isWhole{index}(double value) {{\n    return value == Math.floor(value);\n}}")
    if kind == "zero":
        return (f"public static double safeRatio{index}(double part, double whole) {{\n    if (whole == 0.0) {{\n        return 0.0;\n    }}\n    return part / whole;\n}}")
    return (f"public static int countClose{index}(double[] values, double target) {{\n    if (values == null) return 0;\n    int count = 0;\n"
            f"    for (int i = 0; i < values.length; i++) {{\n        if (Math.abs(values[i] - target) <= {eps}) count++;\n    }}\n    return count;\n}}")


def _exact_checks(rng: random.Random, index: int) -> str:
    # Exact checks that are deliberate - zero, a whole number, a sentinel -
    # written every way a student writes them, not only inside an if.
    name = rng.choice(["balance", "value", "amount", "reading", "total", "level"])
    kind = rng.choice(["zeroflag", "returnzero", "sentinel", "ternary", "wholecount"])
    if kind == "zeroflag":
        return (f"public static boolean isEmptyAccount{index}(double {name}) {{\n    boolean empty = {name} == 0.0;\n    return empty;\n}}")
    if kind == "returnzero":
        return (f"public static boolean nothingLeft{index}(double {name}) {{\n    return {name} == 0.0;\n}}")
    if kind == "sentinel":
        return (f"public static int validReadings{index}(double[] readings) {{\n    if (readings == null) return 0;\n    int count = 0;\n"
                f"    for (double r : readings) {{\n        if (r != -1.0) count++;\n    }}\n    return count;\n}}")
    if kind == "ternary":
        return (f"public static double share{index}(double part, double whole) {{\n    return whole == 0.0 ? 0.0 : part / whole;\n}}")
    return (f"public static int countWhole{index}(double[] values) {{\n    if (values == null) return 0;\n    int count = 0;\n"
            f"    for (int i = 0; i < values.length; i++) {{\n        boolean whole = values[i] == Math.floor(values[i]);\n        if (whole) count++;\n    }}\n    return count;\n}}")


def _literal_tolerance(rng: random.Random, index: int) -> str:
    # Tolerance checks against a decimal LITERAL - the correct form of the
    # textbook mistake `total == 0.3`, which mutating these produces.
    target = rng.choice(["0.3", "0.7", "1.1", "2.5", "0.15", "3.3", "0.1"])
    eps = rng.choice(["0.0001", "1e-9", "0.000001"])
    kind = rng.choice(["sum", "count", "branch", "average"])
    if kind == "sum":
        return (f"public static boolean addsUp{index}(double first, double second) {{\n    double total = first + second;\n"
                f"    return Math.abs(total - {target}) < {eps};\n}}")
    if kind == "count":
        return (f"public static int countNear{index}(double[] values) {{\n    if (values == null) return 0;\n    int count = 0;\n"
                f"    for (int i = 0; i < values.length; i++) {{\n        if (Math.abs(values[i] - {target}) < {eps}) count++;\n    }}\n    return count;\n}}")
    if kind == "branch":
        return (f"public static String check{index}(double price) {{\n    double withTax = price * 1.1;\n"
                f"    if (Math.abs(withTax - {target}) < {eps}) {{\n        return \"match\";\n    }}\n    return \"different\";\n}}")
    return (f"public static boolean averageIs{index}(double[] values) {{\n    if (values == null || values.length == 0) return false;\n    double sum = 0;\n"
            f"    for (double v : values) sum += v;\n    double average = sum / values.length;\n    return Math.abs(average - {target}) < {eps};\n}}")


_STRING_SWITCHES = [
    ("tier", ["gold", "silver", "bronze"], "discount", "int", ["20", "10", "5"], "0"),
    ("role", ["admin", "editor", "viewer"], "level", "int", ["3", "2", "1"], "0"),
    ("light", ["RED", "GREEN", "YELLOW"], "next", "String", ['"GREEN"', '"YELLOW"', '"RED"'], '"?"'),
    ("month", ["January", "February", "April"], "days", "int", ["31", "28", "30"], "-1"),
    ("answer", ["never", "often", "always"], "score", "int", ["0", "2", "3"], "-1"),
    ("move", ["rock", "paper", "scissors"], "beats", "String", ['"scissors"', '"rock"', '"paper"'], '"none"'),
]


def _string_switch(rng: random.Random, index: int) -> str:
    # Switches on a String, each case setting the result and breaking - the
    # shape of most hand-written switch exercises. Removing a break makes the
    # next case overwrite the result.
    param, cases, result, kind, values, fallback = rng.choice(_STRING_SWITCHES)
    style = rng.choice(["assign", "assign", "print"])
    lines = [f"public static {kind if style == 'assign' else 'void'} lookup{index}(String {param}) {{"]
    if style == "assign":
        lines.append(f"    {kind} {result} = {fallback};")
    lines.append(f"    if ({param} == null) return{' ' + result if style == 'assign' else ''};")
    lines.append(f"    switch ({param}) {{")
    for case, value in zip(cases, values):
        lines.append(f"        case \"{case}\":")
        lines.append(f"            {result} = {value};" if style == "assign" else f"            System.out.println({value});")
        lines.append("            break;")
    lines.append("        default:")
    lines.append(f"            {result} = {fallback};" if style == "assign" else f"            System.out.println({fallback});")
    lines.append("    }")
    if style == "assign":
        lines.append(f"    return {result};")
    lines.append("}")
    return "\n".join(lines)


def _strings(rng: random.Random, index: int) -> str:
    word = rng.choice(["quit", "yes", "admin", "stop", "red", "java"])
    kind = rng.choice(["command", "count", "clean", "builder", "chars", "ignorecase"])
    if kind == "command":
        return (f"public static boolean isCommand{index}(String input) {{\n    if (input == null) return false;\n    String cleaned = input;\n"
                f"    cleaned = cleaned.trim();\n    cleaned = cleaned.toLowerCase();\n    return cleaned.equals(\"{word}\");\n}}")
    if kind == "count":
        return (f"public static int countEqual{index}(String[] words, String target) {{\n    if (words == null || target == null) return 0;\n    int count = 0;\n"
                f"    for (String w : words) {{\n        if (w != null && w.equals(target)) count++;\n    }}\n    return count;\n}}")
    if kind == "clean":
        return (f"public static String normalise{index}(String text) {{\n    if (text == null) return \"\";\n    text = text.trim();\n"
                f"    text = text.replace(\"  \", \" \");\n    text = text.toUpperCase();\n    return text;\n}}")
    if kind == "builder":
        return (f"public static String reversedUpper{index}(String text) {{\n    if (text == null) return \"\";\n    StringBuilder sb = new StringBuilder(text);\n"
                f"    sb.reverse();\n    sb.append('!');\n    return sb.toString().toUpperCase();\n}}")
    if kind == "chars":
        return (f"public static int countLetter{index}(String text, char letter) {{\n    if (text == null) return 0;\n    int count = 0;\n"
                f"    for (int i = 0; i < text.length(); i++) {{\n        if (text.charAt(i) == letter) count++;\n    }}\n    return count;\n}}")
    return (f"public static boolean sameWord{index}(String a, String b) {{\n    if (a == null || b == null) return a == b;\n    return a.trim().equalsIgnoreCase(b.trim());\n}}")


def _division(rng: random.Random, index: int) -> str:
    arr = rng.choice(ARRAYS)
    kind = rng.choice(["guard", "ternary", "ifwrap", "cast", "pct", "mid", "boxes", "digits"])
    if kind == "guard":
        return (f"public static int average{index}(int[] {arr}) {{\n    if ({arr} == null || {arr}.length == 0) return 0;\n    int total = 0;\n"
                f"    for (int x : {arr}) total += x;\n    return total / {arr}.length;\n}}")
    if kind == "ternary":
        return (f"public static double meanPositive{index}(int[] {arr}) {{\n    if ({arr} == null) return 0;\n    int total = 0;\n    int count = 0;\n"
                f"    for (int x : {arr}) {{\n        if (x > 0) {{\n            total += x;\n            count++;\n        }}\n    }}\n"
                f"    return count == 0 ? 0.0 : (double) total / count;\n}}")
    if kind == "ifwrap":
        return (f"public static int share{index}(int amount, int people) {{\n    int each = 0;\n    if (people > 0) {{\n        each = amount / people;\n    }}\n    return each;\n}}")
    if kind == "cast":
        return (f"public static double exactAverage{index}(int[] {arr}) {{\n    if ({arr} == null || {arr}.length == 0) return 0.0;\n    int sum = 0;\n"
                f"    for (int i = 0; i < {arr}.length; i++) sum += {arr}[i];\n    double average = (double) sum / {arr}.length;\n    return average;\n}}")
    if kind == "pct":
        return (f"public static double percentPassed{index}(int passed, int total) {{\n    if (total == 0) return 0.0;\n    double percent = 100.0 * passed / total;\n    return percent;\n}}")
    if kind == "mid":
        return (f"public static int middleValue{index}(int[] {arr}) {{\n    if ({arr} == null || {arr}.length == 0) return 0;\n    int low = 0;\n    int high = {arr}.length - 1;\n"
                f"    int mid = (low + high) / 2;\n    return {arr}[mid];\n}}")
    if kind == "boxes":
        return (f"public static int fullBoxes{index}(int items, int perBox) {{\n    if (perBox <= 0) return 0;\n    int boxes = items / perBox;\n    return boxes;\n}}")
    return (f"public static int digitSum{index}(int n) {{\n    n = Math.abs(n);\n    int sum = 0;\n    while (n > 0) {{\n        sum += n % 10;\n        n = n / 10;\n    }}\n    return sum;\n}}")


def _switch(rng: random.Random, index: int) -> str:
    kind = rng.choice(["stacked", "comment", "cumulative", "plain", "print"])
    if kind == "stacked":
        return (f"public static String dayType{index}(int day) {{\n    String type;\n    switch (day) {{\n        case 6:\n        case 7:\n            type = \"weekend\";\n            break;\n"
                f"        case 1: case 2: case 3: case 4: case 5:\n            type = \"weekday\";\n            break;\n        default:\n            type = \"invalid\";\n    }}\n    return type;\n}}")
    if kind == "comment":
        return (f"public static int bonus{index}(int level) {{\n    int bonus = 0;\n    switch (level) {{\n        case 3:\n            bonus += 50;\n            // falls through: level 3 also gets the level 2 bonus\n"
                f"        case 2:\n            bonus += 20;\n            break;\n        case 1:\n            bonus += 5;\n            break;\n        default:\n            bonus = 0;\n    }}\n    return bonus;\n}}")
    if kind == "cumulative":
        return (f"public static int daysLeftInQuarter{index}(int month) {{\n    int days = 0;\n    switch (month) {{\n        case 1:\n            days += 31;\n        case 2:\n            days += 28;\n"
                f"        case 3:\n            days += 31;\n            break;\n        default:\n            days = -1;\n    }}\n    return days;\n}}")
    if kind == "plain":
        return (f"public static String grade{index}(char letter) {{\n    String word;\n    switch (letter) {{\n        case 'A':\n            word = \"excellent\";\n            break;\n"
                f"        case 'B':\n            word = \"good\";\n            break;\n        case 'C':\n            word = \"pass\";\n            break;\n        default:\n            word = \"unknown\";\n    }}\n    return word;\n}}")
    return (f"public static void announce{index}(int code) {{\n    switch (code) {{\n        case 1:\n            System.out.println(\"start\");\n            break;\n"
            f"        case 2:\n            System.out.println(\"pause\");\n            break;\n        case 3:\n            System.out.println(\"stop\");\n            break;\n        default:\n            System.out.println(\"?\");\n    }}\n}}")


def _while_updates(rng: random.Random, index: int) -> str:
    arr = rng.choice(ARRAYS)
    kind = rng.choice(["binary", "pointers", "double", "countdown", "dowhile"])
    if kind == "binary":
        return (f"public static int find{index}(int[] {arr}, int target) {{\n    if ({arr} == null) return -1;\n    int low = 0;\n    int high = {arr}.length - 1;\n"
                f"    while (low <= high) {{\n        int mid = (low + high) / 2;\n        if ({arr}[mid] == target) return mid;\n"
                f"        if ({arr}[mid] < target) low = mid + 1;\n        else high = mid - 1;\n    }}\n    return -1;\n}}")
    if kind == "pointers":
        return (f"public static boolean isPalindrome{index}(String text) {{\n    if (text == null) return false;\n    int left = 0;\n    int right = text.length() - 1;\n"
                f"    while (left < right) {{\n        if (text.charAt(left) != text.charAt(right)) return false;\n        left++;\n        right--;\n    }}\n    return true;\n}}")
    if kind == "double":
        return (f"public static int doublings{index}(int start, int limit) {{\n    if (start <= 0) return 0;\n    int value = start;\n    int count = 0;\n"
                f"    while (value < limit) {{\n        value = value * 2;\n        count++;\n    }}\n    return count;\n}}")
    if kind == "countdown":
        return (f"public static int countdownSum{index}(int n) {{\n    int total = 0;\n    while (n > 0) {{\n        total += n;\n        n--;\n    }}\n    return total;\n}}")
    return (f"public static int digitCount{index}(int n) {{\n    n = Math.abs(n);\n    int count = 0;\n    do {{\n        count++;\n        n = n / 10;\n    }} while (n > 0);\n    return count;\n}}")


def _ends(rng: random.Random, index: int) -> str:
    arr = rng.choice(ARRAYS)
    kind = rng.choice(["last", "lastchar", "listlast", "append", "prefix", "inclusive", "upto", "down", "step"])
    if kind == "last":
        return f"public static int lastOf{index}(int[] {arr}) {{\n    if ({arr} == null || {arr}.length == 0) return -1;\n    return {arr}[{arr}.length - 1];\n}}"
    if kind == "lastchar":
        return f"public static char lastLetter{index}(String text) {{\n    if (text == null || text.isEmpty()) return '?';\n    return text.charAt(text.length() - 1);\n}}"
    if kind == "listlast":
        return f"public static int lastItem{index}(List<Integer> items) {{\n    if (items == null || items.isEmpty()) return 0;\n    return items.get(items.size() - 1);\n}}"
    if kind == "append":
        return (f"public static int[] withExtra{index}(int[] {arr}, int extra) {{\n    if ({arr} == null) return new int[] {{extra}};\n    int[] longer = new int[{arr}.length + 1];\n"
                f"    for (int i = 0; i < {arr}.length; i++) longer[i] = {arr}[i];\n    longer[{arr}.length] = extra;\n    return longer;\n}}")
    if kind == "prefix":
        return (f"public static int[] prefixSums{index}(int[] {arr}) {{\n    if ({arr} == null) return new int[0];\n    int[] sums = new int[{arr}.length + 1];\n"
                f"    for (int i = 1; i <= {arr}.length; i++) {{\n        sums[i] = sums[i - 1] + {arr}[i - 1];\n    }}\n    return sums;\n}}")
    if kind == "inclusive":
        return f"public static int sumTo{index}(int n) {{\n    int total = 0;\n    for (int i = 1; i <= n; i++) {{\n        total += i;\n    }}\n    return total;\n}}"
    if kind == "upto":
        return (f"public static int sumAll{index}(int[] {arr}) {{\n    if ({arr} == null) return 0;\n    int total = 0;\n"
                f"    for (int i = 0; i <= {arr}.length - 1; i++) total += {arr}[i];\n    return total;\n}}")
    if kind == "down":
        return (f"public static String backwards{index}(int[] {arr}) {{\n    if ({arr} == null) return \"\";\n    String out = \"\";\n"
                f"    for (int i = {arr}.length - 1; i >= 0; i--) {{\n        out += {arr}[i] + \" \";\n    }}\n    return out.trim();\n}}")
    step = rng.choice([2, 3])
    return (f"public static int everyOther{index}(int[] {arr}) {{\n    if ({arr} == null) return 0;\n    int total = 0;\n"
            f"    for (int i = 0; i < {arr}.length; i += {step}) total += {arr}[i];\n    return total;\n}}")


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
    families = [
        ("srt", 104, "sorting passes", _sort, 45),
        ("hdr", 105, "loop header does the work", _header_does_the_work, 60),
        ("flg", 106, "boolean flags", _flags, 60),
        ("tol", 107, "decimal tolerance", _tolerance, 60),
        ("str", 108, "String comparison and stored results", _strings, 80),
        ("div", 109, "division", _division, 90),
        ("swt", 110, "switch cases", _switch, 60),
        ("whl", 111, "while updates", _while_updates, 60),
        ("end", 112, "ends and inclusive bounds", _ends, 90),
        # Last, so adding it changed none of the programs drawn before it.
        ("exa", 113, "deliberate exact decimal checks", _exact_checks, 60),
        ("sws", 114, "switch on a String", _string_switch, 60),
        ("ltl", 115, "tolerance against a decimal literal", _literal_tolerance, 80),
    ]
    for prefix, topic_index, topic, make, count in families:
        for index in range(count):
            items.append({"id": f"x_{prefix}{index:03d}", "topic_index": topic_index, "topic": f"template: {topic}",
                          "name": f"{prefix}{index}", "code_a": make(rng, index), "code_b": None, "verdict": "kept"})
    OUT_PATH.write_text("".join(json.dumps(item) + "\n" for item in items), encoding="utf-8")
    print(f"{len(items)} template programs -> {OUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
