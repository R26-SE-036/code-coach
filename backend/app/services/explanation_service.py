"""Explanations written for the student's own code.

Three things the editor can ask for, all on demand (a button), never on a
keystroke:

  explain_diagnostic      "Explain in my code": why THIS flagged line is a
                          problem, traced with a small example value, ending
                          in a question. Never the corrected code - the three
                          hint levels are there to be worked through first.
  explain_compiler_error  what a javac / VS Code Java error means in plain
                          words, for a beginner, pointing at their line.
  similar_example         the closest worked example from the free course for
                          the same mistake.

The model is OpenAI's, like Study Guider's and PairPath's. Every student has a
daily allowance (settings.llm_daily_limit); answers are cached by the lines
they explain, and a cached answer costs nothing. With no key, with the
allowance used up, or when the model fails, the answer comes from the hint
templates and the compiler-error table below - the button always answers.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from app.analysis.error_catalog import ERROR_CATALOG, title_for
from app.analysis.hint_engine import get_error_knowledge
from app.core.config import get_settings
from app.services import llm_client

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKED_EXAMPLES_PATH = PROJECT_ROOT / "knowledge_base" / "worked_examples.json"
WINDOW = 8
MAX_CODE_CHARS = 20_000


@dataclass
class Explanation:
    text: str
    source: str            # "llm", "cache" or "template"
    remaining_today: int
    limit: int
    limit_reached: bool = False


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def code_window(code: str, line: int, radius: int = WINDOW) -> str:
    """The lines around `line`, numbered the way the editor numbers them."""
    lines = code[:MAX_CODE_CHARS].splitlines()
    if not lines:
        return ""
    line = max(1, min(line, len(lines)))
    start, end = max(1, line - radius), min(len(lines), line + radius)
    width = len(str(end))
    return "\n".join(
        f"{n:>{width}}{'>' if n == line else ' '} {lines[n - 1]}" for n in range(start, end + 1)
    )


def _cache_key(kind: str, subject: str, window: str) -> str:
    normalised = "\n".join(" ".join(line.split()) for line in window.splitlines())
    return hashlib.sha1(f"{kind}|{subject}|{normalised}".encode("utf-8")).hexdigest()


def _strip_code(text: str) -> str:
    # The prompt says no corrected code. A model that writes a block anyway
    # has the block taken out rather than handed to the student.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:1200]


def _remaining(storage: Any, user_id: str) -> int:
    limit = get_settings().llm_daily_limit
    return max(0, limit - storage.llm_uses_on(user_id, _today()))


def _answer(storage: Any, user_id: str, *, kind: str, subject: str, window: str,
            prompt: str, instructions: str, fallback: str) -> Explanation:
    settings = get_settings()
    limit = settings.llm_daily_limit
    key = _cache_key(kind, subject, window)
    cached = storage.get_cached_explanation(key)
    if cached and cached.get("text"):
        return Explanation(cached["text"], "cache", _remaining(storage, user_id), limit)

    remaining = _remaining(storage, user_id)
    if not llm_client.configured() or remaining <= 0:
        return Explanation(fallback, "template", remaining, limit, limit_reached=remaining <= 0)

    try:
        text = _strip_code(llm_client.complete(prompt, instructions=instructions, max_output_tokens=700))
    except llm_client.LLMUnavailable:
        return Explanation(fallback, "template", remaining, limit)
    if not text:
        return Explanation(fallback, "template", remaining, limit)

    used = storage.add_llm_use(user_id, _today())
    storage.save_cached_explanation(key, {"text": text, "kind": kind, "subject": subject,
                                          "createdAt": datetime.now(timezone.utc)})
    return Explanation(text, "llm", max(0, limit - used), limit)


# ═════════════════════════════════ Explain in my code ═════════════════════════

EXPLAIN_INSTRUCTIONS = """You are Code Coach, a patient tutor for first-year Java students.
A detector has flagged a likely logic mistake in the student's code. Help the
student see the problem so they can fix it THEMSELVES.

Rules:
- Talk about THEIR code: name their variables and refer to the line number.
- Say what the code does now, then trace it with one small concrete example
  (two or three steps) that shows where it goes wrong.
- Finish with one short guiding question.
- Never write the corrected line or any corrected code, and never use code
  blocks. Backticks only around short fragments of their own code.
- At most 120 words, friendly and plain. Explain any term you use.
- If the flagged code is in fact correct, say so and explain briefly why it
  looks like the mistake."""


def explain_diagnostic(storage: Any, user_id: str, *, error_type: str, code: str, line: int,
                       message: str = "") -> Explanation:
    knowledge = get_error_knowledge(error_type)
    window = code_window(code, line)
    fallback = (
        f"{knowledge.hints.concept}\n\n{knowledge.hints.guidance}\n\n{knowledge.hints.targeted}"
    )
    prompt = (
        f"Mistake: {title_for(error_type)}\n"
        f"What it is about: {knowledge.hints.concept}\n"
        f"Detector's note: {message or knowledge.hints.targeted}\n"
        f"Flagged line: {line} (marked with >)\n\n"
        f"Student's code:\n{window}\n"
    )
    return _answer(storage, user_id, kind="diagnostic", subject=error_type, window=window,
                   prompt=prompt, instructions=EXPLAIN_INSTRUCTIONS, fallback=fallback)


# ═══════════════════════════════ compiler errors ══════════════════════════════
# javac's wording and the VS Code Java extension's (Eclipse JDT) differ, so
# each entry matches both.

COMPILER_ERRORS: List[tuple[str, str]] = [
    (r"';' expected|insert \";\"|Syntax error, insert \";\"",
     "Java needs a semicolon at the end of this statement. Look at the end of the line the error points to - and at the line just above it, because a missing ; is often only noticed on the next line."),
    (r"cannot find symbol|cannot be resolved to a variable|cannot be resolved",
     "Java does not know this name here. Check the spelling and capital letters, and check that the variable was declared before this line and inside a block that this line can see - a variable made inside a loop or an if is gone once that block ends."),
    (r"incompatible types|Type mismatch|cannot convert from",
     "The value on the right is not the type the left side expects - for example a double going into an int, or a String into a number. Decide which type you really need, then change the variable's type or convert the value."),
    (r"possible lossy conversion",
     "You are putting a value with decimals (or a bigger number type) into a smaller type such as int, and Java will not drop the extra part silently. Use a wider variable type, or cast if you really mean to cut the value."),
    (r"missing return statement|must return a result of type",
     "This method promises to return a value, but there is a way through it that reaches the end without a return - often when every return is inside an if or a loop. Follow each path to the closing brace and check it returns something."),
    (r"unreachable statement|Unreachable code",
     "This line can never run, because something before it always leaves first - usually a return, break or continue just above it. Was this line meant to come before that statement?"),
    (r"might not have been initialized|may not have been initialized",
     "This variable is read before it is guaranteed to have a value - there is a path (an if without an else, a loop that might not run) where nothing was stored in it. Give it a starting value when you declare it."),
    (r"already defined|Duplicate local variable",
     "This name is declared twice in the same part of the method. Use a different name for the second variable, or remove the type from the second line if you only meant to change the first one."),
    (r"not applicable for the arguments|cannot be applied to|method .* in class .* cannot be applied",
     "The method is being called with arguments that do not match its parameters - the wrong number of them, or the wrong types, or the wrong order. Compare the call with the method's header."),
    (r"non-static (method|variable).*static context|Cannot make a static reference",
     "A static method (such as main) is using something that belongs to an object. Either make that method or variable static too, or create an object and call it on the object."),
    (r"class .* is public, should be declared in a file named|must be defined in its own file",
     "A public class has to live in a file with exactly its name - class Grades goes in Grades.java. Rename the file or the class so they match, including capital letters."),
    (r"bad operand types|The operator .* is undefined for the argument type|Incompatible operand types",
     "This operator cannot be used with these two kinds of value - for example comparing a String with an int, or using && on numbers. Check the type of each side."),
    (r"cannot be dereferenced|Cannot invoke .* on the primitive type",
     "You are calling a method on a primitive value such as an int or char, and primitives have no methods. Check whether you meant a String or an array here, or use a helper such as Integer.toString or Character.isDigit."),
    (r"unclosed string literal|String literal is not properly closed",
     "A String is opened with \" but not closed on the same line. Add the closing quote, or use \\\" if you need a quote inside the text."),
    (r"reached end of file while parsing|Syntax error, insert \"}\"",
     "A { has no matching }. Count the braces of each method and class - the editor highlights the matching brace when you click next to one."),
    (r"unreported exception|Unhandled exception type",
     "This call can throw a checked exception, and Java needs you to deal with it - catch it with try / catch, or add throws to the method header."),
    (r"else without if|Syntax error on token \"else\"",
     "Java found an else with no if just before it. A semicolon right after the if's condition, or a missing brace, usually splits them apart."),
]

COMPILER_INSTRUCTIONS = """You are Code Coach, a patient tutor for first-year Java students.
The student's Java code does not compile. Explain the error so they can fix it
THEMSELVES.

Rules:
- Say in plain words what the error message means.
- Point to the most likely cause in THEIR code at the line given.
- Say what to check, as one or two short steps.
- Never write the corrected code, and never use code blocks. Backticks only
  around short fragments of their own code.
- At most 100 words, friendly and plain."""


def compiler_error_template(message: str) -> str:
    for pattern, explanation in COMPILER_ERRORS:
        if re.search(pattern, message, flags=re.IGNORECASE):
            return explanation
    return ("Read the first error first - later ones are often caused by it. Look at the line it points to and the "
            "line just above it, and check the spelling, the brackets and the semicolons there.")


def explain_compiler_error(storage: Any, user_id: str, *, message: str, code: str, line: int) -> Explanation:
    window = code_window(code, line)
    prompt = f"Error message: {message[:400]}\nError line: {line} (marked with >)\n\nStudent's code:\n{window}\n"
    return _answer(storage, user_id, kind="compiler", subject=message[:200], window=window,
                   prompt=prompt, instructions=COMPILER_INSTRUCTIONS,
                   fallback=compiler_error_template(message))


# ═════════════════════════════ similar worked example ═════════════════════════

def _load_examples() -> dict:
    if not WORKED_EXAMPLES_PATH.exists():
        return {}
    try:
        return json.loads(WORKED_EXAMPLES_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


_EXAMPLES = _load_examples()


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _tokens(text: str) -> set:
    return set(re.findall(r"[A-Za-z_]\w*|<=|>=|==|!=|&&|\|\||\+\+|--", text))


def similar_example(*, error_type: str, code: str = "", line: int = 1) -> dict:
    examples = list(_EXAMPLES.get(error_type, []))
    if error_type not in ERROR_CATALOG or not examples:
        return {"error_type": error_type, "title": title_for(error_type), "examples": [],
                "course_path": f"/study/course/{error_type}", "source": "none"}

    window = code_window(code, line, radius=4) if code else ""
    ranked, source = examples, "first"
    if window and examples[0].get("embedding") and llm_client.configured():
        try:
            dims = len(examples[0]["embedding"])
            [query] = llm_client.embed([window], dimensions=dims, timeout=8)
            ranked = sorted(examples, key=lambda e: -_cosine(query, e["embedding"]))
            source = "embedding"
        except llm_client.LLMUnavailable:
            ranked = examples
    if source != "embedding" and window:
        student = _tokens(window)
        ranked = sorted(examples, key=lambda e: -len(student & _tokens(e.get("buggy", "") + e.get("code", ""))))
        source = "keywords"
    shown = [{k: v for k, v in example.items() if k != "embedding"} for example in ranked[:2]]
    return {"error_type": error_type, "title": title_for(error_type), "examples": shown,
            "course_path": f"/study/course/{error_type}", "source": source}


def catalogue() -> List[dict]:
    """Every error type the editor can show: id, title, concept and how it is decided."""
    return [
        {
            "error_type": error_type,
            "title": spec.title,
            "concept_tag": get_error_knowledge(error_type).concept_tag,
            "detection_mode": spec.detection_mode,
            "course_path": f"/study/course/{error_type}",
        }
        for error_type, spec in ERROR_CATALOG.items()
    ]
