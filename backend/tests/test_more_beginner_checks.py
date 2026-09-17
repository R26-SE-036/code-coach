"""Four more beginner mistakes, each checked in both directions.

A rule that finds its mistake is half a rule. The other half is leaving alone
the code that only resembles it, and those near-misses are usually what a
student writes once they have got it right - a cast on one side of the
division, a comparison with zero, a prefix increment. A detector that flags
correct code teaches students to stop reading its findings, so every check
here has cases it must not flag.
"""

import unittest

from app.analysis.analyzer import analyze_code


def method(body: str, parameters: str = "") -> str:
    lines = "\n".join("        " + line for line in body.strip().split("\n"))
    return f"class Sample {{\n    void run({parameters}) {{\n{lines}\n    }}\n}}\n"


def findings(code: str, error_type: str) -> list:
    return [item for item in analyze_code(code) if item.error_type == error_type]


class IntegerDivisionInDecimalContextTests(unittest.TestCase):
    TYPE = "INTEGER_DIVISION_IN_DECIMAL_CONTEXT"

    def test_flags_a_whole_number_division_stored_in_a_double(self) -> None:
        [finding] = findings(method("int total = 7;\nint count = 2;\ndouble average = total / count;"), self.TYPE)
        self.assertIn("total / count", finding.hints.targeted)
        self.assertIn("average", finding.hints.targeted)

    def test_flags_two_literals(self) -> None:
        self.assertEqual(1, len(findings(method("double half = 1 / 2;"), self.TYPE)))

    def test_flags_an_assignment_to_a_double_declared_earlier(self) -> None:
        code = method("int sum = 9;\nint n = 4;\ndouble mean;\nmean = sum / n;")
        self.assertEqual(1, len(findings(code, self.TYPE)))

    def test_flags_a_cast_of_the_finished_division(self) -> None:
        # (double) (a / b) converts the already-truncated answer.
        code = method("int a = 5;\nint b = 2;\ndouble ratio = (double) (a / b);")
        self.assertEqual(1, len(findings(code, self.TYPE)))

    def test_leaves_alone_the_ways_of_getting_it_right(self) -> None:
        for body in (
            "int a = 5;\nint b = 2;\ndouble ratio = (double) a / b;",
            "int a = 5;\ndouble ratio = a / 2.0;",
            "double a = 5;\nint b = 2;\ndouble ratio = a / b;",
            "int a = 5;\nint b = 2;\nint quotient = a / b;",
        ):
            with self.subTest(body=body):
                self.assertEqual([], findings(method(body), self.TYPE))

    def test_leaves_division_by_zero_to_its_own_check(self) -> None:
        code = method("int a = 5;\ndouble ratio = a / 0;")
        self.assertEqual([], findings(code, self.TYPE))
        self.assertEqual(1, len(findings(code, "DIVISION_BY_ZERO_LITERAL")))


class DecimalEqualityComparisonTests(unittest.TestCase):
    TYPE = "DECIMAL_EQUALITY_COMPARISON"

    def test_flags_a_comparison_with_a_decimal_literal(self) -> None:
        code = method('double price = 0.1 + 0.2;\nif (price == 0.3) {\n    System.out.println("equal");\n}')
        [finding] = findings(code, self.TYPE)
        self.assertIn("price == 0.3", finding.hints.targeted)

    def test_flags_two_decimal_variables(self) -> None:
        code = method("double a = 0.1 + 0.2;\ndouble b = 0.3;\nboolean same = a != b;")
        self.assertEqual(1, len(findings(code, self.TYPE)))

    def test_leaves_alone_whole_numbers_zero_and_ordering(self) -> None:
        for body in (
            "int count = 3;\nboolean three = count == 3;",
            "double balance = 0.5;\nboolean empty = balance == 0.0;",
            "double price = 0.5;\nboolean cheap = price < 0.3;",
        ):
            with self.subTest(body=body):
                self.assertEqual([], findings(method(body), self.TYPE))


class PostfixIncrementAssignedBackTests(unittest.TestCase):
    TYPE = "POSTFIX_INCREMENT_ASSIGNED_BACK"

    def test_flags_x_equals_x_plus_plus_and_minus_minus(self) -> None:
        [finding] = findings(method("int count = 0;\ncount = count++;"), self.TYPE)
        self.assertIn("count = count++", finding.hints.targeted)
        self.assertEqual(1, len(findings(method("int i = 5;\ni = i--;"), self.TYPE)))

    def test_leaves_alone_increments_that_do_change_the_variable(self) -> None:
        for body in (
            "int count = 0;\ncount = ++count;",
            "int count = 0;\ncount++;",
            "int count = 0;\nint total = count++;",
        ):
            with self.subTest(body=body):
                self.assertEqual([], findings(method(body), self.TYPE))

    def test_is_not_also_reported_as_a_self_assignment(self) -> None:
        self.assertEqual([], findings(method("int count = 0;\ncount = count++;"), "SELF_ASSIGNMENT"))


class AlwaysFalseAndConditionTests(unittest.TestCase):
    TYPE = "ALWAYS_FALSE_AND_CONDITION"

    def test_flags_ranges_no_value_can_satisfy(self) -> None:
        for condition in ("x > 10 && x < 5", "x == 1 && x == 2", "x >= 18 && x < 18", "10 < x && x < 5"):
            with self.subTest(condition=condition):
                code = method(f"boolean possible = {condition};", "int x")
                [finding] = findings(code, self.TYPE)
                self.assertIn(condition, finding.hints.targeted)

    def test_leaves_alone_ranges_some_value_satisfies(self) -> None:
        for condition in ("x > 5 && x < 10", "x >= 5 && x <= 5", "x > 5 && y < 3"):
            with self.subTest(condition=condition):
                self.assertEqual([], findings(method(f"boolean possible = {condition};", "int x, int y"), self.TYPE))


if __name__ == "__main__":
    unittest.main()
