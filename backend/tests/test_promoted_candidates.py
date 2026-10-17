"""The thirteen types moved off rules and file-level gates onto per-site models.

Held here:

1. Each has its own trained model and keeps its old detector as a fallback
   (LEGACY_SPECS), and nothing about what it reports changed shape: the same
   line, column and `details` keys its old locator produced.
2. The go-live gate: a clear, hand-written mistake of each kind is flagged and
   a correct look-alike - the kind the old rule had to flag or skip wholesale -
   is not. None of these is from the generated corpus the models learned on.
"""

import unittest

from app.analysis.analyzer import analyze_code
from app.analysis.error_catalog import ERROR_CATALOG, LEGACY_SPECS
from app.analysis.parser_utils import parse_java_code_safe
from app.analysis.promoted_candidates import PROMOTED_PROPOSERS


def wrap(body: str) -> str:
    return "public class Probe {\n" + body + "\n}\n"


# (error type, buggy method, correct look-alike)
CASES = {
    "OFF_BY_ONE_LOOP_BOUNDARY": (
        "static int total(int[] marks) {\n  int sum = 0;\n  for (int i = 0; i <= marks.length; i++) {\n    sum += marks[i];\n  }\n  return sum;\n}",
        "static int sumTo(int n) {\n  int total = 0;\n  for (int i = 1; i <= n; i++) {\n    total += i;\n  }\n  return total;\n}",
    ),
    "INCORRECT_CONDITIONAL_OPERATOR": (
        "static String status(boolean done) {\n  if (done = true) {\n    return \"finished\";\n  }\n  return \"working\";\n}",
        "static int count(String text) {\n  int n = 0;\n  int from = 0;\n  int pos;\n  while ((pos = text.indexOf('a', from)) != -1) {\n    n++;\n    from = pos + 1;\n  }\n  return n;\n}",
    ),
    "ARRAY_LENGTH_INDEX_MISUSE": (
        "static int last(int[] values) {\n  return values[values.length];\n}",
        "static int[] withExtra(int[] values, int extra) {\n  int[] longer = new int[values.length + 1];\n  for (int i = 0; i < values.length; i++) {\n    longer[i] = values[i];\n  }\n  longer[values.length] = extra;\n  return longer;\n}",
    ),
    "MISSING_BREAK_IN_SWITCH": (
        "static String day(int d) {\n  String name;\n  switch (d) {\n    case 1:\n      name = \"Mon\";\n    case 2:\n      name = \"Tue\";\n      break;\n    default:\n      name = \"?\";\n  }\n  return name;\n}",
        "static int bonus(int level) {\n  int bonus = 0;\n  switch (level) {\n    case 3:\n      bonus += 50;\n      // falls through: level 3 also gets the level 2 bonus\n    case 2:\n      bonus += 20;\n      break;\n    default:\n      bonus = 0;\n  }\n  return bonus;\n}",
    ),
    "WHILE_VARIABLE_NOT_UPDATED": (
        "static int total(int n) {\n  int i = 0;\n  int sum = 0;\n  while (i < n) {\n    sum += i;\n  }\n  return sum;\n}",
        "static int digitSum(int n) {\n  int sum = 0;\n  while (n > 0) {\n    sum += n % 10;\n    n = n / 10;\n  }\n  return sum;\n}",
    ),
    "STRING_EQUALITY_WITH_OPERATOR": (
        "static boolean isYes(String answer) {\n  return answer.trim() == \"yes\";\n}",
        "static boolean isYes(String answer) {\n  return answer != null && answer.trim().equals(\"yes\");\n}",
    ),
    "LOOP_UPDATE_WRONG_DIRECTION": (
        "static void show(int[] a) {\n  for (int i = 0; i < a.length; i--) {\n    System.out.println(a[i]);\n  }\n}",
        "static void showBackwards(int[] a) {\n  for (int i = a.length - 1; i >= 0; i--) {\n    System.out.println(a[i]);\n  }\n}",
    ),
    # `for (i = 0; i > a.length; i++)` is the case only the model sees - but
    # it is also a counter moving away from its bound, and one underline is
    # shown for the two; test_one_underline_... covers it.
    "CONSTANT_FALSE_LOOP_CONDITION": (
        "static int countdown() {\n  int printed = 0;\n  for (int i = 10; i < 5; i++) {\n    System.out.println(i);\n    printed++;\n  }\n  return printed;\n}",
        "static void countToTen() {\n  for (int i = 1; i <= 10; i++) {\n    System.out.println(i);\n  }\n}",
    ),
    "IGNORED_STRING_METHOD_RESULT": (
        "static String shout(String word) {\n  word.toUpperCase();\n  return word + \"!\";\n}",
        "static String reversed(String word) {\n  StringBuilder sb = new StringBuilder(word);\n  sb.reverse();\n  return sb.toString();\n}",
    ),
    "DIVISION_BY_ZERO_LITERAL": (
        "static int half(int x) {\n  return x / 0;\n}",
        "static int average(int[] marks) {\n  if (marks.length == 0) {\n    return 0;\n  }\n  int total = 0;\n  for (int m : marks) {\n    total += m;\n  }\n  return total / marks.length;\n}",
    ),
    "INTEGER_DIVISION_IN_DECIMAL_CONTEXT": (
        "static double average(int total, int count) {\n  double average = total / count;\n  return average;\n}",
        "static int middle(int low, int high) {\n  int mid = (low + high) / 2;\n  return mid;\n}",
    ),
    "DECIMAL_EQUALITY_COMPARISON": (
        "static boolean paidExactly(double first, double second) {\n  double total = first + second;\n  return total == 0.3;\n}",
        "static double ratio(double part, double whole) {\n  if (whole == 0.0) {\n    return 0.0;\n  }\n  return part / whole;\n}",
    ),
    "EMPTY_CONDITIONAL_BODY": (
        "static int countPositive(int x, int count) {\n  if (x > 0); {\n    count++;\n  }\n  return count;\n}",
        "static int positionOf(int[] a, int key) {\n  int i;\n  for (i = 0; i < a.length && a[i] != key; i++);\n  return i;\n}",
    ),
}


def types_found(code: str) -> set:
    return {d.error_type for d in analyze_code(code)}


class ContractTests(unittest.TestCase):
    def test_all_thirteen_run_on_their_own_model_with_the_old_detector_kept(self) -> None:
        self.assertEqual(set(PROMOTED_PROPOSERS), set(CASES))
        self.assertEqual(set(LEGACY_SPECS), set(CASES))
        for error_type in CASES:
            with self.subTest(error_type=error_type):
                self.assertEqual(ERROR_CATALOG[error_type].detection_mode, "candidate_ml")
                self.assertIn(LEGACY_SPECS[error_type].detection_mode, {"rule_only", "ml_gated"})
                self.assertEqual(LEGACY_SPECS[error_type].title, ERROR_CATALOG[error_type].title)

    def test_six_rules_and_twenty_four_models(self) -> None:
        modes = [spec.detection_mode for spec in ERROR_CATALOG.values()]
        self.assertEqual(modes.count("rule_only"), 6)
        self.assertEqual(modes.count("candidate_ml"), 24)
        self.assertEqual(modes.count("ml_gated"), 0)

    def test_every_site_the_old_rule_found_is_still_proposed_where_it_was(self) -> None:
        for error_type, (buggy, _) in CASES.items():
            with self.subTest(error_type=error_type):
                parse_result = parse_java_code_safe(wrap(buggy))
                old = LEGACY_SPECS[error_type].locator(parse_result)
                new = PROMOTED_PROPOSERS[error_type](parse_result)
                self.assertTrue(old, f"the old {error_type} rule does not see the sample")
                old_sites = {(f.line, f.column) for f in old}
                new_sites = {(c.finding.line, c.finding.column) for c in new}
                self.assertLessEqual(old_sites, new_sites)
                old_keys = set(old[0].details)
                match = next(c for c in new if (c.finding.line, c.finding.column) == (old[0].line, old[0].column))
                self.assertLessEqual(old_keys, set(match.finding.details))


class TrainedModelTests(unittest.TestCase):
    def test_clear_mistakes_are_flagged(self) -> None:
        for error_type, (buggy, _) in CASES.items():
            with self.subTest(error_type=error_type):
                self.assertIn(error_type, types_found(wrap(buggy)))

    def test_correct_look_alikes_are_not_flagged(self) -> None:
        for error_type, (_, correct) in CASES.items():
            with self.subTest(error_type=error_type):
                self.assertNotIn(error_type, types_found(wrap(correct)))

    def test_flagged_sites_carry_the_models_probability(self) -> None:
        [diagnostic] = [d for d in analyze_code(wrap(CASES["ARRAY_LENGTH_INDEX_MISUSE"][0])) if d.error_type == "ARRAY_LENGTH_INDEX_MISUSE"]
        self.assertEqual(diagnostic.detection_engine, "candidate_ml")
        self.assertGreaterEqual(diagnostic.ml_probability, ERROR_CATALOG["ARRAY_LENGTH_INDEX_MISUSE"].candidate_ml_threshold)
        self.assertEqual(diagnostic.concept_tag, "array_indexing")

    def test_one_underline_when_two_types_describe_one_condition(self) -> None:
        # Never true for any array, which the literal-only rule could not see;
        # reported once, under whichever of the two models is surer.
        code = wrap("static int total(int[] values) {\n  int sum = 0;\n  for (int i = 0; i > values.length; i++) {\n    sum += values[i];\n  }\n  return sum;\n}")
        found = [d for d in analyze_code(code) if d.error_type in ("CONSTANT_FALSE_LOOP_CONDITION", "LOOP_UPDATE_WRONG_DIRECTION")]
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
