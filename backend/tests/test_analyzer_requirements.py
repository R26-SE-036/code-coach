import unittest

from app.analysis.analyzer import analyze_code
from app.analysis.error_catalog import ERROR_CATALOG, validate_catalog


class AnalyzerRequirementTests(unittest.TestCase):
    def assert_detects(self, expected_error_type: str, code: str) -> None:
        diagnostics = analyze_code(code)
        detected_types = {diagnostic.error_type for diagnostic in diagnostics}
        self.assertIn(expected_error_type, detected_types)

    def test_detects_three_ml_target_error_categories(self) -> None:
        cases = {
            "OFF_BY_ONE_LOOP_BOUNDARY": (
                "class A{void m(){int[] a={1,2};"
                "for(int i=0;i<=a.length;i++){System.out.println(a[i]);}}}"
            ),
            "INCORRECT_CONDITIONAL_OPERATOR": (
                "class A{void m(){boolean ready=false;"
                "if(ready = true){System.out.println(ready);}}}"
            ),
            "ARRAY_LENGTH_INDEX_MISUSE": (
                "class A{void m(){int[] a={1,2};"
                "System.out.println(a[a.length]);}}"
            ),
        }

        for expected_error_type, code in cases.items():
            with self.subTest(expected_error_type=expected_error_type):
                self.assert_detects(expected_error_type, code)

    def test_detects_twelve_rule_only_error_categories(self) -> None:
        cases = {
            "STRING_EQUALITY_WITH_OPERATOR": (
                'class A{void m(){String s="hi";'
                'if(s == "hi"){System.out.println(s);}}}'
            ),
            "LOOP_UPDATE_WRONG_DIRECTION": (
                "class A{void m(){for(int i=0;i<10;i--){System.out.println(i);}}}"
            ),
            "UNREACHABLE_CODE_AFTER_RETURN": (
                "class A{int m(int x){return x; System.out.println(x);}}"
            ),
            "MISSING_BREAK_IN_SWITCH": (
                "class A{void m(int d){switch(d){case 1: System.out.println(1);"
                " case 2: break;}}}"
            ),
            "EMPTY_CONDITIONAL_BODY": (
                "class A{void m(int x){if(x > 0); {System.out.println(x);}}}"
            ),
            "SELF_ASSIGNMENT": "class A{void m(int x){x = x;}}",
            "ALWAYS_TRUE_OR_CONDITION": (
                "class A{void m(int x){if(x != 1 || x != 2){System.out.println(x);}}}"
            ),
            "IGNORED_STRING_METHOD_RESULT": (
                'class A{void m(){String s="hi"; s.toUpperCase();}}'
            ),
            "DIVISION_BY_ZERO_LITERAL": (
                "class A{void m(int x){System.out.println(x / 0);}}"
            ),
            "CONSTANT_FALSE_LOOP_CONDITION": (
                "class A{void m(){for(int i=10;i<5;i++){System.out.println(i);}}}"
            ),
            "DUPLICATE_IF_ELSE_CONDITION": (
                "class A{void m(int x){if(x > 5){System.out.println(1);}"
                "else if(x > 5){System.out.println(2);}}}"
            ),
            "WHILE_VARIABLE_NOT_UPDATED": (
                "class A{void m(){int i = 0;"
                ' while(i < 5){System.out.println("x");}}}'
            ),
        }

        for expected_error_type, code in cases.items():
            with self.subTest(expected_error_type=expected_error_type):
                self.assert_detects(expected_error_type, code)

    def test_catalog_registers_fifteen_validated_error_types(self) -> None:
        self.assertEqual(len(ERROR_CATALOG), 15)
        validate_catalog()

    def test_diagnostic_payload_explains_ml_and_locator_roles(self) -> None:
        diagnostics = analyze_code(
            "class A{void m(){int[] a={1,2}; System.out.println(a[a.length]);}}"
        )

        self.assertGreater(len(diagnostics), 0)
        diagnostic = diagnostics[0]

        self.assertTrue(diagnostic.diagnostic_id.startswith("cc_"))
        self.assertEqual(diagnostic.status, "active")
        self.assertEqual(diagnostic.detection_engine, "ml_gated_ast_locator")
        self.assertIsNotNone(diagnostic.ml_probability)
        self.assertIsNotNone(diagnostic.locator_confidence)
        self.assertGreaterEqual(diagnostic.ml_probability or 0, 0.65)
        self.assertIn(diagnostic.severity, {"warning", "error"})
        self.assertGreaterEqual(diagnostic.confidence, 0)
        self.assertLessEqual(diagnostic.confidence, 0.99)
        self.assertTrue(diagnostic.concept_tag)
        self.assertTrue(diagnostic.explanation_key)
        self.assertTrue(diagnostic.hints.concept)
        self.assertTrue(diagnostic.hints.guidance)
        self.assertTrue(diagnostic.hints.targeted)

    def test_rule_only_diagnostic_reports_ast_locator_engine(self) -> None:
        diagnostics = analyze_code("class A{void m(int x){x = x;}}")

        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]

        self.assertEqual(diagnostic.error_type, "SELF_ASSIGNMENT")
        self.assertEqual(diagnostic.detection_engine, "ast_locator_rule")
        self.assertIsNone(diagnostic.ml_probability)
        self.assertIsNotNone(diagnostic.locator_confidence)
        self.assertTrue(diagnostic.hints.concept)

    def test_non_target_errors_are_not_reported(self) -> None:
        diagnostics = analyze_code(
            'class A{void m(String name){if(name.equals("Ali")){System.out.println(name);}}}'
        )
        self.assertEqual([], diagnostics)

    def test_partial_code_does_not_crash(self) -> None:
        diagnostics = analyze_code("class A { void m( ")
        self.assertIsInstance(diagnostics, list)


if __name__ == "__main__":
    unittest.main()
