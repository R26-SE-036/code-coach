"""The two reports that say how good the detector is, and how far to trust that.

evaluate_by_source separates hand-written from generated code, because the
models were trained only on generated code and averaging the two flattered
the number that was meant to be about code people write. dispute_report turns
students' false-positive reports into a rate per kind of finding.

Both are easy to get subtly wrong in the direction that looks good - an
unevaluated target printed as perfect, a finding counted once per analysis -
so those are what these tests pin down.
"""

import unittest

import pandas as pd

from app.dev_tools.dispute_report import summarise_disputes
from app.dev_tools.evaluate_by_source import (
    TEST_FILE,
    Outcome,
    collect_outcomes,
    summarise,
)


def outcome(source: str, actual: bool, pipeline: bool, *, target: str = "has_x", gate: bool = False) -> Outcome:
    return Outcome(target, "X_ERROR", source, actual, gate, pipeline)


class EvaluateBySourceTests(unittest.TestCase):
    def test_reports_each_source_separately(self) -> None:
        rows = summarise(
            [
                outcome("manual_curated", True, True),
                outcome("manual_curated", True, False),
                outcome("synthetic_generated", True, True),
                outcome("synthetic_generated", True, True),
            ]
        )
        recall = {row["source_type"]: row["pipeline_recall"] for row in rows}
        self.assertEqual({"manual_curated": 0.5, "synthetic_generated": 1.0}, recall)

    def test_no_positive_examples_is_not_a_perfect_score(self) -> None:
        [row] = summarise([outcome("manual_curated", False, False), outcome("manual_curated", False, False)])

        self.assertFalse(row["has_positive_examples"])
        self.assertIsNone(row["pipeline_recall"])
        self.assertIsNone(row["pipeline_precision"])
        self.assertIsNone(row["pipeline_f1"])

    def test_a_false_alarm_is_counted_even_without_positive_examples(self) -> None:
        [row] = summarise([outcome("manual_curated", False, True), outcome("manual_curated", False, False)])

        self.assertEqual(1, row["pipeline_fp"])
        self.assertEqual(0.0, row["pipeline_precision"])
        self.assertIsNone(row["pipeline_recall"])

    def test_runs_on_the_committed_test_split(self) -> None:
        split = pd.read_csv(TEST_FILE)
        # A few rows of each source keeps this quick; the full run is the tool's job.
        sample = split.groupby("source_type", group_keys=False).head(4)

        rows = summarise(collect_outcomes(sample))

        self.assertEqual({"manual_curated", "synthetic_generated"}, {row["source_type"] for row in rows})
        for row in rows:
            self.assertEqual(4, row["positives"] + row["negatives"])


class DisputeReportTests(unittest.TestCase):
    @staticmethod
    def finding(user: str, diagnostic_id: str, error_type: str = "SELF_ASSIGNMENT") -> dict:
        return {"userId": user, "diagnosticId": diagnostic_id, "errorType": error_type}

    def test_a_finding_is_counted_once_however_many_analyses_saw_it(self) -> None:
        records = [self.finding("u1", "cc_a")] * 50
        [row] = summarise_disputes(records, [])

        self.assertEqual(1, row["findings"])
        self.assertEqual(1, row["students"])

    def test_the_same_finding_for_two_students_is_two_findings(self) -> None:
        [row] = summarise_disputes([self.finding("u1", "cc_a"), self.finding("u2", "cc_a")], [])
        self.assertEqual(2, row["findings"])
        self.assertEqual(2, row["students"])

    def test_rate_per_error_type(self) -> None:
        records = [
            self.finding("u1", "cc_a"),
            self.finding("u2", "cc_b"),
            self.finding("u1", "cc_c", "DIVISION_BY_ZERO_LITERAL"),
        ]
        rows = summarise_disputes(records, [{"userId": "u2", "diagnosticId": "cc_b"}])

        rates = {row["error_type"]: row["dispute_rate"] for row in rows}
        self.assertEqual({"SELF_ASSIGNMENT": 0.5, "DIVISION_BY_ZERO_LITERAL": 0.0}, rates)
        self.assertEqual("SELF_ASSIGNMENT", rows[0]["error_type"])

    def test_a_dispute_whose_record_has_gone_cannot_push_the_rate_past_one(self) -> None:
        [row] = summarise_disputes([], [{"userId": "u1", "diagnosticId": "cc_gone", "errorType": "SELF_ASSIGNMENT"}])

        self.assertEqual(1, row["findings"])
        self.assertEqual(1.0, row["dispute_rate"])


if __name__ == "__main__":
    unittest.main()
