import unittest

from app.analysis.analyzer import analyze_code


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

    def test_non_target_errors_are_not_reported(self) -> None:
        diagnostics = analyze_code(
            'class A{void m(String name){if(name == "Ali"){System.out.println(name);}}}'
        )
        self.assertEqual([], diagnostics)

    def test_partial_code_does_not_crash(self) -> None:
        diagnostics = analyze_code("class A { void m( ")
        self.assertIsInstance(diagnostics, list)


if __name__ == "__main__":
    unittest.main()
