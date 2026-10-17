"""The eleven logic-error types decided per site by a model (candidate_ml).

Three things are held here:

1. The contract with the rest of the platform. Every type maps to one of the
   fourteen concept tags Study Guider, PairPath and the games already join
   on, and the diagnostic payload only GAINS fields - so nothing downstream
   has to change to keep working.
2. The proposers: they offer the buggy site, and they describe the correct
   look-alike differently (that difference is what the model learns from).
3. The trained models, end to end: clear mistakes are flagged and their
   correct look-alikes are not. These are hand-written, outside the
   generated corpus the models were trained on.
"""

import os
import unittest

from app.analysis.analyzer import analyze_code
from app.analysis.error_catalog import ERROR_CATALOG, validate_catalog
from app.analysis.hint_engine import ERROR_KNOWLEDGE_BASE, TARGETED_HINT_TEMPLATES
from app.analysis.logic_candidates import PROPOSERS
from app.analysis.parser_utils import parse_java_code_safe
from app.core.config import get_settings

# The vocabulary every other component joins on (Study Guider concepts.py,
# PairPath concept_tags.py, the gamification constants). Pinned: a new tag
# would need all three changed first.
PLATFORM_CONCEPT_TAGS = {
    "arithmetic_operations", "array_indexing", "assignment_logic", "boolean_logic",
    "conditional_logic", "control_flow", "immutable_strings", "loop_boundaries",
    "loop_control", "loop_initialization", "loop_termination", "statement_structure",
    "string_comparison", "switch_statements",
}

# The fields a diagnostic carried before the 30-type catalogue. Clients
# (the extension, the web app, Study Guider's struggle triggers) read these.
ORIGINAL_DIAGNOSTIC_FIELDS = {
    "diagnostic_id", "error_type", "severity", "line", "column", "confidence", "message",
    "code_context", "concept_tag", "explanation_key", "status", "detection_engine",
    "ml_probability", "locator_confidence", "hints",
}


def wrap(body: str) -> str:
    return "public class Probe {\n" + body + "\n}\n"


# (error type, buggy method, correct look-alike)
CASES = {
    "LOOP_SKIPS_LAST_ELEMENT": (
        "static int total(int[] marks) {\n  int sum = 0;\n  for (int i = 0; i < marks.length - 1; i++) {\n    sum += marks[i];\n  }\n  return sum;\n}",
        "static boolean sorted(int[] marks) {\n  for (int i = 0; i < marks.length - 1; i++) {\n    if (marks[i] > marks[i + 1]) return false;\n  }\n  return true;\n}",
    ),
    "INDEX_PLUS_ONE_OUT_OF_BOUNDS": (
        "static int rises(int[] values) {\n  int count = 0;\n  for (int i = 0; i < values.length; i++) {\n    if (values[i + 1] > values[i]) count++;\n  }\n  return count;\n}",
        "static int rises(int[] values) {\n  int count = 0;\n  for (int i = 0; i < values.length - 1; i++) {\n    if (values[i + 1] > values[i]) count++;\n  }\n  return count;\n}",
    ),
    "WRONG_LOOP_VARIABLE_IN_INDEX": (
        "static int total(int[][] grid) {\n  int sum = 0;\n  for (int r = 0; r < grid.length; r++) {\n    for (int c = 0; c < grid[r].length; c++) {\n      sum += grid[r][r];\n    }\n  }\n  return sum;\n}",
        "static int pairs(int[] a) {\n  int n = 0;\n  for (int i = 0; i < a.length; i++) {\n    for (int j = i + 1; j < a.length; j++) {\n      if (a[i] == a[j]) n++;\n    }\n  }\n  return n;\n}",
    ),
    "NESTED_LOOP_WRONG_COUNTER": (
        "static int cells(int[][] grid) {\n  int count = 0;\n  for (int i = 0; i < grid.length; i++) {\n    for (int j = 0; j < grid[i].length; i++) {\n      count++;\n    }\n  }\n  return count;\n}",
        "static int steps(int n) {\n  int steps;\n  for (steps = 0; n > 1; steps++) {\n    n = n / 2;\n  }\n  return steps;\n}",
    ),
    "LOOP_COUNTER_CHANGED_IN_BODY": (
        "static int total(int[] values) {\n  int sum = 0;\n  for (int i = 0; i < values.length; i++) {\n    sum += values[i];\n    i++;\n  }\n  return sum;\n}",
        "static String unescape(String text) {\n  String out = \"\";\n  for (int i = 0; i < text.length(); i++) {\n    char c = text.charAt(i);\n    if (c == '\\\\' && i + 1 < text.length()) {\n      i++;\n      c = text.charAt(i);\n    }\n    out += c;\n  }\n  return out;\n}",
    ),
    "ACCUMULATOR_RESET_INSIDE_LOOP": (
        "static int total(int[] values) {\n  int sum = 0;\n  for (int i = 0; i < values.length; i++) {\n    sum = 0;\n    sum += values[i];\n  }\n  return sum;\n}",
        "static int bestRow(int[][] grid) {\n  int best = 0;\n  for (int r = 0; r < grid.length; r++) {\n    int rowSum = 0;\n    for (int c = 0; c < grid[r].length; c++) {\n      rowSum += grid[r][c];\n    }\n    if (rowSum > best) best = rowSum;\n  }\n  return best;\n}",
    ),
    "WRONG_EXTREME_INITIAL_VALUE": (
        "static int coldest(int[] temps) {\n  int min = 0;\n  for (int i = 0; i < temps.length; i++) {\n    if (temps[i] < min) {\n      min = temps[i];\n    }\n  }\n  return min;\n}",
        "static int coldest(int[] temps) {\n  int min = temps[0];\n  for (int i = 1; i < temps.length; i++) {\n    if (temps[i] < min) {\n      min = temps[i];\n    }\n  }\n  return min;\n}",
    ),
    "EARLY_RETURN_IN_LOOP": (
        "static boolean contains(int[] values, int target) {\n  for (int i = 0; i < values.length; i++) {\n    if (values[i] == target) {\n      return true;\n    } else {\n      return false;\n    }\n  }\n  return false;\n}",
        "static boolean contains(int[] values, int target) {\n  for (int i = 0; i < values.length; i++) {\n    if (values[i] == target) {\n      return true;\n    }\n  }\n  return false;\n}",
    ),
    "UNREACHABLE_ELSE_IF_ORDER": (
        "static String grade(int score) {\n  if (score >= 50) {\n    return \"C\";\n  } else if (score >= 75) {\n    return \"B\";\n  } else if (score >= 90) {\n    return \"A\";\n  } else {\n    return \"F\";\n  }\n}",
        "static String grade(int score) {\n  if (score >= 90) {\n    return \"A\";\n  } else if (score >= 75) {\n    return \"B\";\n  } else if (score >= 50) {\n    return \"C\";\n  } else {\n    return \"F\";\n  }\n}",
    ),
    "MISLEADING_INDENTATION_NO_BRACES": (
        "static int lastBig(int[] a) {\n  int count = 0;\n  int last = -1;\n  for (int i = 0; i < a.length; i++) {\n    if (a[i] > 10)\n      count++;\n      last = i;\n  }\n  return last;\n}",
        "static int count(int[] a) {\n  int count = 0;\n  for (int i = 0; i < a.length; i++) {\n    if (a[i] > 10)\n      count++;\n  }\n  return count;\n}",
    ),
    "NON_SHORT_CIRCUIT_OPERATOR": (
        "static boolean longName(String name) {\n  return name != null & name.length() > 5;\n}",
        "static boolean longName(String name) {\n  return name != null && name.length() > 5;\n}",
    ),
}


def types_found(code: str) -> set:
    return {d.error_type for d in analyze_code(code)}


class ContractTests(unittest.TestCase):
    def test_thirty_types_all_validated(self) -> None:
        self.assertEqual(len(ERROR_CATALOG), 30)
        # The eleven here plus the thirteen moved off rules and gates
        # (test_promoted_candidates.py).
        self.assertEqual(sum(1 for s in ERROR_CATALOG.values() if s.detection_mode == "candidate_ml"), 24)
        validate_catalog()

    def test_every_type_maps_to_an_existing_concept_tag(self) -> None:
        for error_type in ERROR_CATALOG:
            with self.subTest(error_type=error_type):
                self.assertIn(ERROR_KNOWLEDGE_BASE[error_type].concept_tag, PLATFORM_CONCEPT_TAGS)

    def test_every_type_has_a_title_and_a_targeted_template(self) -> None:
        for error_type, spec in ERROR_CATALOG.items():
            with self.subTest(error_type=error_type):
                self.assertTrue(spec.title)
                self.assertNotIn("_", spec.title)
                self.assertIn(error_type, TARGETED_HINT_TEMPLATES)

    def test_the_payload_only_gains_fields(self) -> None:
        diagnostics = analyze_code(wrap(CASES["NON_SHORT_CIRCUIT_OPERATOR"][0]) + wrap("static int x(int[] a) { return a[a.length]; }"))
        self.assertTrue(diagnostics)
        for diagnostic in diagnostics:
            fields = set(diagnostic.model_dump())
            self.assertLessEqual(ORIGINAL_DIAGNOSTIC_FIELDS, fields)
            self.assertLessEqual(fields - ORIGINAL_DIAGNOSTIC_FIELDS, {"title", "end_line", "end_column"})
            self.assertTrue(diagnostic.title)
            self.assertGreaterEqual(diagnostic.end_line, diagnostic.line)


class ProposerTests(unittest.TestCase):
    def test_every_buggy_case_is_proposed(self) -> None:
        for error_type, (buggy, _) in CASES.items():
            with self.subTest(error_type=error_type):
                self.assertTrue(PROPOSERS[error_type](parse_java_code_safe(wrap(buggy))))

    def test_look_alikes_are_described_differently(self) -> None:
        def features(error_type: str, code: str) -> dict:
            [candidate] = PROPOSERS[error_type](parse_java_code_safe(wrap(code)))[:1]
            return candidate.features

        self.assertEqual(features("LOOP_SKIPS_LAST_ELEMENT", CASES["LOOP_SKIPS_LAST_ELEMENT"][1])["body_uses_next"], 1.0)
        self.assertEqual(features("LOOP_SKIPS_LAST_ELEMENT", CASES["LOOP_SKIPS_LAST_ELEMENT"][0])["body_uses_next"], 0.0)
        self.assertEqual(features("NON_SHORT_CIRCUIT_OPERATOR", CASES["NON_SHORT_CIRCUIT_OPERATOR"][0])["right_derefs_checked_var"], 1.0)
        prefix = "static int[] prefix(int[] a) {\n  int[] p = new int[a.length + 1];\n  for (int i = 0; i < a.length; i++) {\n    p[i + 1] = p[i] + a[i];\n  }\n  return p;\n}"
        self.assertEqual(features("INDEX_PLUS_ONE_OUT_OF_BOUNDS", prefix)["collection_declared_longer"], 1.0)

    def test_the_row_selector_of_a_2d_access_is_not_a_candidate(self) -> None:
        code = wrap("static int t(int[][] g) {\n  int s = 0;\n  for (int i = 0; i < g.length; i++) {\n    for (int j = 0; j < g[i].length; j++) {\n      s += g[i][j];\n    }\n  }\n  return s;\n}")
        self.assertEqual(PROPOSERS["WRONG_LOOP_VARIABLE_IN_INDEX"](parse_java_code_safe(code)), [])


class TrainedModelTests(unittest.TestCase):
    def test_clear_mistakes_are_flagged(self) -> None:
        for error_type, (buggy, _) in CASES.items():
            with self.subTest(error_type=error_type):
                self.assertIn(error_type, types_found(wrap(buggy)))

    def test_correct_look_alikes_are_not_flagged(self) -> None:
        for error_type, (_, correct) in CASES.items():
            with self.subTest(error_type=error_type):
                self.assertNotIn(error_type, types_found(wrap(correct)))

    def test_flagged_sites_come_from_the_model(self) -> None:
        [diagnostic] = [d for d in analyze_code(wrap(CASES["EARLY_RETURN_IN_LOOP"][0])) if d.error_type == "EARLY_RETURN_IN_LOOP"]
        self.assertEqual(diagnostic.detection_engine, "candidate_ml")
        self.assertGreaterEqual(diagnostic.ml_probability, ERROR_CATALOG["EARLY_RETURN_IN_LOOP"].candidate_ml_threshold)
        self.assertEqual(diagnostic.concept_tag, "control_flow")


class ShadowModeTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SHADOW_ERROR_TYPES"] = "NON_SHORT_CIRCUIT_OPERATOR, early_return_in_loop"
        get_settings.cache_clear()

    def tearDown(self) -> None:
        os.environ.pop("SHADOW_ERROR_TYPES", None)
        get_settings.cache_clear()

    def test_shadowed_types_are_withheld_and_the_rest_still_reported(self) -> None:
        code = wrap(CASES["NON_SHORT_CIRCUIT_OPERATOR"][0]) + wrap(CASES["EARLY_RETURN_IN_LOOP"][0]) + wrap("static int x(int[] a) { return a[a.length]; }")
        found = types_found(code)
        self.assertNotIn("NON_SHORT_CIRCUIT_OPERATOR", found)
        self.assertNotIn("EARLY_RETURN_IN_LOOP", found)
        self.assertIn("ARRAY_LENGTH_INDEX_MISUSE", found)


if __name__ == "__main__":
    unittest.main()
