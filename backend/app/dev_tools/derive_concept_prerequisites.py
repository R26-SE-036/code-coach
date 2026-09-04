"""Derive a concept prerequisite ordering from real student resolution data.

    python -m app.dev_tools.derive_concept_prerequisites
    python -m app.dev_tools.derive_concept_prerequisites --out prerequisites.json
    python -m app.dev_tools.derive_concept_prerequisites --explain

Study Guider needs to know which concepts a student should understand before
others, so it can point them at the earliest gap rather than re-teaching the
symptom. That ordering can be asserted by a teacher or inferred from what
students actually do. This infers it.

It lives in Code Coach because Code Coach owns `codeDiagnostics`. Study Guider
deliberately cannot read another student's data - every one of its Code Coach
calls forwards the student's own token, which is what makes authorization free
- so a cross-student aggregation cannot run there. It runs here and emits a
JSON artefact Study Guider loads.

============================ THE SUFFICIENCY GATE ============================
The important part of this script is that it REFUSES to answer when the data
cannot support an answer.

Run against the current database it refuses, and it is worth saying why,
because the numbers look adequate at a glance. There are 98 diagnostics - but
3 users, who resolved the identical 13 concepts, each within a window of
between 32 seconds and 3.5 minutes. That is app/dev_tools/seed_student.py
writing a loop, not people learning. Ordering derived from it would recover
the seed script's iteration order.

That failure mode is the dangerous one: it produces a plausible graph, backed
by a real query over real rows, that means nothing. A number with a method
behind it is much harder to disbelieve than an opinion, so the method has to
be the thing that says no.
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import timedelta

from app.db.storage import build_storage

# ── Sufficiency thresholds ───────────────────────────────────────────────────
# Deliberately conservative. Each one encodes a way the data can look usable
# and not be.

# Below this, no pairwise comparison has enough independent observations for
# the proportion to mean anything.
MIN_USERS = 20

# A real learner meets these concepts across sessions, over days. A history
# that starts and finishes inside an hour was written by a script.
MIN_MEDIAN_HISTORY_SPAN = timedelta(hours=1)

# How many users must have resolved BOTH concepts before their relative order
# is allowed to become an edge.
MIN_PAIR_OBSERVATIONS = 5

# Of those users, the fraction that must agree on the direction.
MIN_PRECEDENCE_RATIO = 0.70

# If every user resolved exactly the same set of concepts, they were dealt the
# same fixture. Real cohorts differ.
MAX_IDENTICAL_CONCEPT_SET_RATIO = 0.90


class InsufficientData(Exception):
    """Raised with every reason the data cannot support a derivation."""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


def load_first_resolutions(storage) -> dict[str, dict[str, object]]:
    """{user_id: {concept_tag: earliest resolvedAt}}.

    First resolution, not last: the question is when a student first got a
    concept right, and a later re-occurrence is a regression rather than a
    second first time.
    """
    first: dict[str, dict[str, object]] = defaultdict(dict)

    for document in storage.client.collection("codeDiagnostics").stream():
        record = document.to_dict()
        user = record.get("userId")
        concept = record.get("conceptTag")
        resolved_at = record.get("resolvedAt")

        if not (user and concept and resolved_at):
            continue

        seen = first[user].get(concept)
        if seen is None or resolved_at < seen:
            first[user][concept] = resolved_at

    return first


def assess(first: dict[str, dict[str, object]]) -> list[str]:
    """Every reason this data is unfit, rather than the first one found.

    Reporting all of them matters: fixing the user count on data that is also
    synthetic would just move the refusal, and someone would reasonably read
    one resolved complaint as the only complaint.
    """
    reasons = []

    users = [u for u, concepts in first.items() if len(concepts) >= 2]
    if len(users) < MIN_USERS:
        reasons.append(
            f"only {len(users)} user(s) have resolved 2+ concepts; "
            f"{MIN_USERS} needed for a pairwise proportion to mean anything"
        )

    spans = []
    for concepts in first.values():
        if len(concepts) >= 2:
            timestamps = sorted(concepts.values())
            try:
                spans.append(timestamps[-1] - timestamps[0])
            except TypeError:
                continue

    if spans:
        median_span = sorted(spans)[len(spans) // 2]
        if median_span < MIN_MEDIAN_HISTORY_SPAN:
            reasons.append(
                f"median history spans {median_span}, under the "
                f"{MIN_MEDIAN_HISTORY_SPAN} floor - a whole concept history "
                f"inside an hour indicates generated data, not learning"
            )

    concept_sets = [frozenset(c) for c in first.values() if len(c) >= 2]
    if concept_sets:
        most_common = max(
            (concept_sets.count(s) for s in set(concept_sets)), default=0
        )
        ratio = most_common / len(concept_sets)
        if ratio > MAX_IDENTICAL_CONCEPT_SET_RATIO:
            reasons.append(
                f"{most_common}/{len(concept_sets)} users resolved an identical "
                f"set of concepts ({ratio:.0%}) - a real cohort does not "
                f"converge like that; this is one fixture dealt repeatedly"
            )

    return reasons


def count_precedence(first: dict[str, dict[str, object]]):
    """For each ordered concept pair, how many users resolved A before B."""
    before = defaultdict(int)
    both = defaultdict(int)

    for concepts in first.values():
        items = sorted(concepts.items(), key=lambda kv: kv[1])
        for i, (earlier, _) in enumerate(items):
            for later, _ in items[i + 1:]:
                pair = (earlier, later)
                both[frozenset(pair)] += 1
                before[pair] += 1

    return before, both


def build_edges(before, both):
    """Directed edges that clear both the support and the agreement bar."""
    edges = []
    for (earlier, later), agreed in before.items():
        observations = both[frozenset((earlier, later))]
        if observations < MIN_PAIR_OBSERVATIONS:
            continue
        ratio = agreed / observations
        if ratio >= MIN_PRECEDENCE_RATIO:
            edges.append(
                {
                    "prerequisite": earlier,
                    "dependent": later,
                    "observations": observations,
                    "agreement": round(ratio, 3),
                }
            )
    return edges


def transitive_reduction(edges):
    """Keep only direct prerequisites.

    Without this the result is close to a complete DAG: if A precedes B and B
    precedes C then A also precedes C in the raw counts, and reporting all
    three makes "what should I study first" return everything the student has
    ever seen. Only edges with no alternative longer path survive.
    """
    successors = defaultdict(set)
    for edge in edges:
        successors[edge["prerequisite"]].add(edge["dependent"])

    def reachable(start, avoid):
        stack, seen = [start], set()
        while stack:
            node = stack.pop()
            for nxt in successors[node]:
                if (node, nxt) == avoid or nxt in seen:
                    continue
                seen.add(nxt)
                stack.append(nxt)
        return seen

    return [
        edge
        for edge in edges
        if edge["dependent"]
        not in reachable(edge["prerequisite"], (edge["prerequisite"], edge["dependent"]))
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="write the ordering to this JSON file")
    parser.add_argument(
        "--explain", action="store_true", help="show the data assessment in full"
    )
    args = parser.parse_args()

    storage = build_storage()
    first = load_first_resolutions(storage)

    if args.explain:
        print(f"\nusers with a resolution history: {len(first)}")
        for user, concepts in first.items():
            stamps = sorted(concepts.values())
            span = stamps[-1] - stamps[0] if len(stamps) > 1 else timedelta(0)
            print(f"  {user[:24]:26} {len(concepts):3} concepts   span={span}")

    reasons = assess(first)
    if reasons:
        print("\nREFUSING to derive an ordering from this data:\n")
        for reason in reasons:
            print(f"  - {reason}")
        print(
            "\nThe ordering would be an artefact of how the data was produced.\n"
            "Re-run once real student histories exist; nothing else needs to change."
        )
        raise SystemExit(2)

    before, both = count_precedence(first)
    edges = transitive_reduction(build_edges(before, both))

    payload = {
        "derived_from": {
            "users": len(first),
            "min_pair_observations": MIN_PAIR_OBSERVATIONS,
            "min_precedence_ratio": MIN_PRECEDENCE_RATIO,
        },
        "edges": sorted(edges, key=lambda e: (-e["agreement"], e["prerequisite"])),
    }

    print(f"\nderived {len(edges)} prerequisite edge(s) from {len(first)} users")
    for edge in payload["edges"]:
        print(
            f"  {edge['prerequisite']:24} -> {edge['dependent']:24} "
            f"n={edge['observations']:3}  agreement={edge['agreement']:.0%}"
        )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"\nwritten to {args.out}")


if __name__ == "__main__":
    main()
