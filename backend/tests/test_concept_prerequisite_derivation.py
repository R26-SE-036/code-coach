"""Tests for the concept prerequisite derivation.

This tool's successful path cannot be exercised by running it. Against the
current database it refuses - correctly, because that data is 3 seeded
fixtures - and it will keep refusing until there is real student history. So
the only thing standing between the derivation logic and silent rot is this
file.

The tests build cohorts by hand rather than reading the database, which also
means they do not need Firestore credentials to run in CI.
"""

import random
import unittest
from datetime import datetime, timedelta, timezone

from app.dev_tools import derive_concept_prerequisites as derivation


UTC_START = datetime(2026, 1, 1, tzinfo=timezone.utc)

TRUE_ORDER = [
    "assignment_logic",
    "boolean_logic",
    "conditional_logic",
    "loop_initialization",
    "loop_control",
    "loop_boundaries",
    "array_indexing",
]


def build_realistic_cohort(users: int = 40, seed: int = 7, noise: float = 0.2):
    """A cohort that should clear the gate: varied, spread over weeks, noisy."""
    random.seed(seed)
    cohort = {}

    for index in range(users):
        # Individual variation: nobody meets every concept.
        concepts = [c for c in TRUE_ORDER if random.random() > 0.15]
        moment = UTC_START + timedelta(days=random.randint(0, 20))

        history = {}
        for concept in concepts:
            moment += timedelta(days=random.randint(1, 4), hours=random.randint(0, 20))
            history[concept] = moment

        # Some learners genuinely meet two concepts out of order.
        if random.random() < noise and len(concepts) > 3:
            first, second = concepts[1], concepts[2]
            history[first], history[second] = history[second], history[first]

        cohort[f"user_{index:03}"] = history

    return cohort


class SufficiencyGateTests(unittest.TestCase):
    """The gate is the point of the tool, so it is tested hardest."""

    def test_accepts_a_realistic_cohort(self) -> None:
        self.assertEqual(derivation.assess(build_realistic_cohort()), [])

    def test_rejects_too_few_users(self) -> None:
        reasons = derivation.assess(build_realistic_cohort(users=3))
        self.assertTrue(any("user(s) have resolved" in r for r in reasons))

    def test_rejects_histories_that_span_minutes(self) -> None:
        """The seed_student.py signature: a whole history inside one window."""
        cohort = {
            f"user_{i}": {
                concept: UTC_START + timedelta(seconds=10 * position)
                for position, concept in enumerate(TRUE_ORDER)
            }
            for i in range(30)
        }
        reasons = derivation.assess(cohort)
        self.assertTrue(any("median history spans" in r for r in reasons))

    def test_rejects_a_cohort_dealt_one_identical_fixture(self) -> None:
        cohort = {
            f"user_{i}": {
                concept: UTC_START + timedelta(days=position)
                for position, concept in enumerate(TRUE_ORDER)
            }
            for i in range(30)
        }
        reasons = derivation.assess(cohort)
        self.assertTrue(any("identical set of concepts" in r for r in reasons))

    def test_reports_every_reason_not_just_the_first(self) -> None:
        """Fixing one complaint on bad data should not look like fixing it."""
        cohort = {
            f"user_{i}": {
                concept: UTC_START + timedelta(seconds=position)
                for position, concept in enumerate(TRUE_ORDER)
            }
            for i in range(3)
        }
        self.assertGreaterEqual(len(derivation.assess(cohort)), 3)


class DerivationTests(unittest.TestCase):
    def test_recovers_the_true_ordering(self) -> None:
        cohort = build_realistic_cohort()
        before, both = derivation.count_precedence(cohort)
        edges = derivation.transitive_reduction(derivation.build_edges(before, both))

        recovered = {(e["prerequisite"], e["dependent"]) for e in edges}
        expected = set(zip(TRUE_ORDER, TRUE_ORDER[1:]))
        self.assertEqual(recovered, expected)

    def test_transitive_reduction_keeps_only_direct_prerequisites(self) -> None:
        """Without it, "what should I study first" returns everything.

        A precedes C in the raw counts whenever A precedes B and B precedes C,
        so the unreduced graph is close to complete.
        """
        cohort = build_realistic_cohort()
        before, both = derivation.count_precedence(cohort)
        raw = derivation.build_edges(before, both)
        reduced = derivation.transitive_reduction(raw)

        self.assertLess(len(reduced), len(raw))
        self.assertEqual(len(reduced), len(TRUE_ORDER) - 1)

    def test_ignores_pairs_with_too_few_observations(self) -> None:
        cohort = build_realistic_cohort(users=derivation.MIN_USERS + 5)
        rare = "a_concept_almost_nobody_reaches"
        # Fewer users than MIN_PAIR_OBSERVATIONS ever see it.
        for name in list(cohort)[: derivation.MIN_PAIR_OBSERVATIONS - 1]:
            cohort[name][rare] = UTC_START + timedelta(days=365)

        before, both = derivation.count_precedence(cohort)
        edges = derivation.build_edges(before, both)
        self.assertNotIn(rare, {e["dependent"] for e in edges})

    def test_disagreement_below_the_ratio_produces_no_edge(self) -> None:
        """Two concepts learned in no consistent order are not a prerequisite."""
        cohort = {}
        for index in range(30):
            first, second = ("alpha", "beta") if index % 2 else ("beta", "alpha")
            cohort[f"user_{index}"] = {
                first: UTC_START + timedelta(days=1),
                second: UTC_START + timedelta(days=2),
            }

        before, both = derivation.count_precedence(cohort)
        self.assertEqual(derivation.build_edges(before, both), [])


if __name__ == "__main__":
    unittest.main()
