"""A targeted hint about THIS code, not about the error type in general.

The targeted hint used to be one sentence per error type - "Check whether the
loop condition should stop before the array length" - for every student and
every loop. It now quotes what the locator matched. These tests hold each of
the fifteen types to that, and hold the fallback: a template the locator
cannot fully fill must give way to the generic hint, never to a half-filled
sentence.
"""

import unittest

from app.analysis.analyzer import analyze_code
from app.analysis.error_catalog import ERROR_CATALOG
from app.analysis.hint_engine import (
    TARGETED_HINT_TEMPLATES,
    build_diagnostics,
    get_error_knowledge,
    template_fields,
)
from app.analysis.parser_utils import parse_java_code_safe
from app.models import DetectionResult

# One small piece of code per error type, and a fragment of it the targeted
# hint must quote. Locators are called directly, so the ML-gated types are
# exercised without depending on a model's threshold.
SAMPLES = {
    "OFF_BY_ONE_LOOP_BOUNDARY": (
        "class A { void m(int[] scores) { for (int i = 0; i <= scores.length; i++) { System.out.println(scores[i]); } } }",
        "i <= scores.length",
    ),
    "INCORRECT_CONDITIONAL_OPERATOR": (
        "class A { void m(boolean ready) { if (ready = true) { System.out.println(1); } } }",
        "ready = true",
    ),
    "ARRAY_LENGTH_INDEX_MISUSE": (
        "class A { int m(int[] marks) { return marks[marks.length]; } }",
        "marks[marks.length]",
    ),
    "STRING_EQUALITY_WITH_OPERATOR": (
        'class A { boolean m(String name) { return name == "admin"; } }',
        'name == "admin"',
    ),
    "LOOP_UPDATE_WRONG_DIRECTION": (
        "class A { void m() { for (int i = 0; i < 10; i--) { System.out.println(i); } } }",
        "i--",
    ),
    "UNREACHABLE_CODE_AFTER_RETURN": (
        "class A { int m(int total) { return total; total = 0; } }",
        "total = 0;",
    ),
    "MISSING_BREAK_IN_SWITCH": (
        "class A { int m(int day) { int x = 0; switch (day) { case 1: x = 1; case 2: x = 2; break; } return x; } }",
        "case 1",
    ),
    "EMPTY_CONDITIONAL_BODY": (
        "class A { void m(int count) { if (count > 0); { System.out.println(count); } } }",
        "if (count > 0);",
    ),
    "SELF_ASSIGNMENT": (
        "class A { int total; void m(int total) { total = total; } }",
        "total = total",
    ),
    "ALWAYS_TRUE_OR_CONDITION": (
        "class A { boolean m(int grade) { return grade != 1 || grade != 2; } }",
        "grade != 1 || grade != 2",
    ),
    "IGNORED_STRING_METHOD_RESULT": (
        "class A { String m(String name) { name.trim(); return name; } }",
        "name.trim()",
    ),
    "DIVISION_BY_ZERO_LITERAL": (
        "class A { int m(int total) { return total / 0; } }",
        "total / 0",
    ),
    "CONSTANT_FALSE_LOOP_CONDITION": (
        "class A { void m() { for (int i = 10; i < 5; i++) { System.out.println(i); } } }",
        "i < 5",
    ),
    "DUPLICATE_IF_ELSE_CONDITION": (
        'class A { String m(int score) { if (score > 50) { return "pass"; } else if (score > 50) { return "merit"; } return "fail"; } }',
        "score > 50",
    ),
    "WHILE_VARIABLE_NOT_UPDATED": (
        "class A { void m() { int count = 1; while (count <= 5) { System.out.println(count); } } }",
        "count <= 5",
    ),
    "INTEGER_DIVISION_IN_DECIMAL_CONTEXT": (
        "class A { void m(int total, int count) { double average = total / count; } }",
        "total / count",
    ),
    "DECIMAL_EQUALITY_COMPARISON": (
        "class A { boolean m(double price) { return price == 0.3; } }",
        "price == 0.3",
    ),
    "POSTFIX_INCREMENT_ASSIGNED_BACK": (
        "class A { void m(int count) { count = count++; } }",
        "count = count++",
    ),
    "ALWAYS_FALSE_AND_CONDITION": (
        "class A { boolean m(int x) { return x > 10 && x < 5; } }",
        "x > 10 && x < 5",
    ),
}


def findings_for(error_type: str) -> list[DetectionResult]:
    code, _ = SAMPLES[error_type]
    return ERROR_CATALOG[error_type].locator(parse_java_code_safe(code))


class TemplateCoverageTests(unittest.TestCase):
    def test_every_error_type_has_a_sample_and_a_template(self) -> None:
        self.assertEqual(set(ERROR_CATALOG), set(SAMPLES))
        self.assertEqual(set(ERROR_CATALOG), set(TARGETED_HINT_TEMPLATES))

    def test_each_locator_supplies_everything_its_template_names(self) -> None:
        for error_type in ERROR_CATALOG:
            with self.subTest(error_type=error_type):
                findings = findings_for(error_type)
                self.assertTrue(findings, f"the {error_type} sample is not found by its locator")
                supplied = {key for key, value in findings[0].details.items() if value}
                self.assertLessEqual(template_fields(TARGETED_HINT_TEMPLATES[error_type]), supplied)

    def test_the_targeted_hint_quotes_the_students_code(self) -> None:
        for error_type in ERROR_CATALOG:
            with self.subTest(error_type=error_type):
                _, fragment = SAMPLES[error_type]
                [diagnostic] = build_diagnostics(findings_for(error_type)[:1])
                self.assertIn(fragment, diagnostic.hints.targeted)
                self.assertNotEqual(get_error_knowledge(error_type).hints.targeted, diagnostic.hints.targeted)

    def test_the_concept_and_guidance_hints_stay_general(self) -> None:
        # They are for working the problem out; only the last level points at the code.
        [diagnostic] = build_diagnostics(findings_for("WHILE_VARIABLE_NOT_UPDATED")[:1])
        knowledge = get_error_knowledge("WHILE_VARIABLE_NOT_UPDATED")
        self.assertEqual(knowledge.hints.concept, diagnostic.hints.concept)
        self.assertEqual(knowledge.hints.guidance, diagnostic.hints.guidance)


class FallbackTests(unittest.TestCase):
    @staticmethod
    def finding(error_type: str, details: dict) -> DetectionResult:
        return DetectionResult(
            error_type=error_type,
            line=1,
            column=1,
            confidence=0.9,
            message="m",
            code_context="x",
            details=details,
        )

    def test_a_finding_missing_part_of_what_the_template_needs_gets_the_generic_hint(self) -> None:
        # The off-by-one template names both the condition and the array.
        [diagnostic] = build_diagnostics([self.finding("OFF_BY_ONE_LOOP_BOUNDARY", {"condition": "i <= n"})])
        self.assertEqual(get_error_knowledge("OFF_BY_ONE_LOOP_BOUNDARY").hints.targeted, diagnostic.hints.targeted)

    def test_braces_in_the_students_code_are_quoted_as_they_are(self) -> None:
        [diagnostic] = build_diagnostics(
            [self.finding("STRING_EQUALITY_WITH_OPERATOR", {"comparison": 'code == "{0}"'})]
        )
        self.assertIn('code == "{0}"', diagnostic.hints.targeted)

    def test_long_code_is_shortened_for_the_hint(self) -> None:
        code = (
            "class A { void m(int firstRunningCounter, int secondRunningCounter, int maximumAllowedTotal) {"
            " while (firstRunningCounter + secondRunningCounter <= maximumAllowedTotal) { System.out.println(1); } } }"
        )
        [finding] = ERROR_CATALOG["WHILE_VARIABLE_NOT_UPDATED"].locator(parse_java_code_safe(code))
        self.assertLessEqual(len(finding.details["condition"]), 60)
        self.assertTrue(finding.details["condition"].endswith("…"))


class ThroughTheAnalyzerTests(unittest.TestCase):
    def test_the_hint_reaches_the_diagnostic_the_extension_receives(self) -> None:
        # analyze_code rebuilds every finding on the way through; the details
        # must survive that or every hint quietly falls back to the generic one.
        code = 'class Login {\n    boolean check(String name) {\n        return name == "admin";\n    }\n}\n'
        [diagnostic] = analyze_code(code)
        self.assertIn('name == "admin"', diagnostic.hints.targeted)


if __name__ == "__main__":
    unittest.main()
