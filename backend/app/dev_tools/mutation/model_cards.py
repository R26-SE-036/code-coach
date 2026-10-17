"""Model cards: one page per error type that a model decides.

A card says what the model looks for, what it learned from, how well it did
on sites it never saw, and where it should not be trusted. The numbers are
read from what training and the checks wrote, never typed in, so a card
cannot drift from its model: train_logic_models.py rebuilds the cards after
every run, and this can be run on its own after the checks are re-run.

The words a number cannot give - an example of the mistake next to a correct
look-alike, which sites are considered at all, the type's own weak spots -
come from model_card_notes.json beside this file.

    python -m app.dev_tools.mutation.model_cards        (from backend/)

READS   backend/models/logic_calibration_v1.json        training and test results
        data/ml/mutation/candidates/corpus_stats_v1.json how the data was made
        backend/models/logic_human_review_v1.csv        flags on human-written code
        backend/models/curated_comparison_v1.csv        hand-labelled snippets, old vs new
        backend/models/pretrained_comparison_v1.json    the offline CodeBERT comparison
WRITES  backend/models/model_cards_v1.json              served by /api/v1/code-coach/model-cards
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from app.analysis.error_catalog import ERROR_CATALOG, MODELS_DIR
from app.analysis.hint_engine import get_error_knowledge
from app.dev_tools.mutation.train_logic_models import CAND_DIR

NOTES_PATH = Path(__file__).with_name("model_card_notes.json")
OUT_PATH = MODELS_DIR / "model_cards_v1.json"

FAMILY_NAMES = {
    "logistic_regression": "Logistic regression",
    "random_forest": "Random forest (300 trees)",
    "gradient_boosting": "Gradient-boosted trees (300 rounds)",
}

THRESHOLD_RULES = {
    "precision_0.95": "the highest threshold that keeps precision at 0.95 or more with recall at 0.75 or more, "
                      "chosen on the training data by cross-validation",
    "f0.5": "the threshold with the best F0.5 (precision counts twice as much as recall), because precision 0.95 "
            "was not reachable with recall at 0.75 or more",
}

TRAINING_DATA = (
    "Correct beginner Java methods - {methods:,} of them across {topics} topics, from templates and written by "
    "OpenAI - with this mistake planted at known places. Each changed program was run against the original on "
    "{inputs} generated inputs: a change that crashed, never finished or printed something different is a real "
    "mistake; one that behaved the same is a look-alike. Each candidate site in the correct programs is a look-alike too."
)

TRAINING_DATA_BY_CONSTRUCTION = (
    "Correct beginner Java methods - {methods:,} of them across {topics} topics, from templates and written by "
    "OpenAI - with this mistake planted at known places. A planted change of this kind is a mistake by definition, "
    "because running the code rarely shows it (the inputs would have to hit the exact case); every candidate site "
    "in the correct programs is a look-alike."
)

SPLIT = ("Split by base method, so no method - or its other version - is in both training and test. The model and its "
         "threshold were chosen on the training part; the test part was scored once.")

GENERAL_LIMITATIONS = [
    "Trained and tested on generated code, not on student submissions; the checks on human-written code are "
    "the only evidence from code people wrote.",
    "Reads one file without running it, and follows values only within a method: anything decided in another "
    "class, another method or at run time is invisible to it.",
    "Java only, and only code that parses.",
]


def _read_csv(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _metrics(record: Optional[dict]) -> Optional[dict]:
    if not record:
        return None
    keep = ("precision", "recall", "f1", "average_precision")
    return {key: record[key] for key in keep if key in record}


def _number(value) -> Optional[float]:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _type_limitations(error_type: str, test: dict, counts: dict, stats: dict) -> List[str]:
    """Limits that follow from the numbers, worded the same way on every card."""
    found = []
    positives = counts.get("test_positives", 0)
    if positives and positives < 30:
        found.append(f"Measured on only {positives} real mistakes in the test split, so each one moves recall by "
                     f"{100 / positives:.0f} points.")
    equivalent = counts.get("test_negatives_from_equivalent_mutants", 0)
    rate = test.get("false_alarm_rate_on_equivalent_mutant")
    if equivalent and rate:
        flagged = round(rate * equivalent)
        found.append(f"{flagged} of the {equivalent} planted changes in the test split that behaved like the original "
                     f"were flagged. Some of those are real mistakes the test inputs did not reach, so the measured "
                     f"precision is probably a little lower than the true one.")
    changed, missed = stats.get("behaviour_changed", 0), stats.get("proposer_missed_bug", 0)
    if changed and missed and missed / changed >= 0.02:
        found.append(f"{missed} of {changed} planted mistakes that changed behaviour were in places this type does not "
                     f"consider, so they could never be flagged; recall is measured on the places it does consider.")
    return found


def build_cards() -> Dict[str, dict]:
    calibration = json.loads((MODELS_DIR / "logic_calibration_v1.json").read_text(encoding="utf-8"))["results"]
    corpus = json.loads((CAND_DIR / "corpus_stats_v1.json").read_text(encoding="utf-8"))
    notes = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
    by_construction = set(corpus.get("label_by_construction", []))
    methods = corpus.get("base_methods", 0)
    topics = len({json.loads(line).get("topic_index") for line in
                  (CAND_DIR.parent / "base" / "methods_v1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()})

    reviews: Dict[str, Counter] = defaultdict(Counter)
    for row in _read_csv(MODELS_DIR / "logic_human_review_v1.csv"):
        reviews[row["error_type"]][row.get("verdict") or "unreviewed"] += 1
    curated = {row["error_type"]: row for row in _read_csv(MODELS_DIR / "curated_comparison_v1.csv")}
    pretrained_path = MODELS_DIR / "pretrained_comparison_v1.json"
    pretrained = json.loads(pretrained_path.read_text(encoding="utf-8")).get("results", {}) if pretrained_path.exists() else {}

    cards: Dict[str, dict] = {}
    for error_type, record in sorted(calibration.items()):
        if "selected" not in record or "test" not in record or error_type not in ERROR_CATALOG:
            continue
        note = notes.get(error_type, {})
        selected, test, counts = record["selected"], record["test"], record.get("counts", {})
        stats = corpus.get("types", {}).get(error_type, {})
        had_detector = str(record.get("rule_baseline_is", "")).startswith("the detector")
        review = reviews.get(error_type, Counter())
        curated_row = curated.get(error_type)
        codebert = (pretrained.get(error_type, {}).get("variants") or [{}])[0].get("test")

        template = TRAINING_DATA_BY_CONSTRUCTION if error_type in by_construction else TRAINING_DATA
        cards[error_type] = {
            "error_type": error_type,
            "title": ERROR_CATALOG[error_type].title,
            "concept_tag": get_error_knowledge(error_type).concept_tag,
            "version": "v1",
            "detects": note.get("detects", ""),
            "considers": note.get("considers", ""),
            "example": {"mistake": note.get("mistake", ""), "lookalike": note.get("lookalike", "")},
            "model": {
                "family": selected["family"],
                "family_name": FAMILY_NAMES.get(selected["family"], selected["family"]),
                "threshold": selected["threshold"],
                "threshold_rule": THRESHOLD_RULES.get(selected["precision_target_reached"], selected["precision_target_reached"]),
                "feature_count": len(record.get("features", [])),
                "top_features": [name for name, _ in record.get("top_features", [])[:5]],
                "ms_per_site": selected.get("latency_ms_per_candidate"),
                "file": selected["model_file"],
            },
            "training_data": {
                "description": template.format(methods=methods, topics=topics, inputs=corpus.get("inputs_per_method", 60)),
                "labels": "construction" if error_type in by_construction else "execution",
                "split": SPLIT,
                "training_sites": counts.get("fit_rows"),
                "training_mistakes": counts.get("fit_positives"),
                "test_sites": counts.get("test_rows"),
                "test_mistakes": counts.get("test_positives"),
                "test_lookalikes_from_correct_code": counts.get("test_negatives_from_correct_code"),
                "test_lookalikes_from_planted_changes": counts.get("test_negatives_from_equivalent_mutants"),
                "planted_mistakes": stats.get("mutants"),
                "planted_mistakes_that_changed_behaviour": stats.get("behaviour_changed"),
            },
            "performance": {
                "test": _metrics(test.get("model")),
                "previous": {
                    "name": "the detector this type had before" if had_detector
                            else "a hand-written rule (a new type, with no detector before)",
                    **(_metrics(test.get("rule_baseline")) or {}),
                },
                "codebert": _metrics(codebert),
                "human_code": {
                    "flags": sum(review.values()),
                    "real": review.get("true_find", 0),
                    "plausible": review.get("plausible", 0),
                    "wrong": review.get("false_alarm", 0) + review.get("wrong", 0),
                },
                "curated": None if curated_row is None else {
                    "snippets": int(curated_row["snippets"]),
                    "mistakes": int(curated_row["positives"]),
                    "precision": _number(curated_row["new_precision"]),
                    "recall": _number(curated_row["new_recall"]),
                    "false_alarms": int(float(curated_row["new_false_alarms"])),
                    "previous_recall": _number(curated_row["old_recall"]),
                    "previous_false_alarms": int(float(curated_row["old_false_alarms"])),
                },
            },
            "unreliable_when": note.get("unreliable_when", []),
            "limitations": [*note.get("limitations", []), *_type_limitations(error_type, test, counts, stats)],
            "general_limitations": GENERAL_LIMITATIONS,
        }
    return cards


def write_cards() -> Path:
    cards = build_cards()
    OUT_PATH.write_text(json.dumps({"generated": date.today().isoformat(), "cards": cards}, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    return OUT_PATH


def main() -> None:
    path = write_cards()
    cards = json.loads(path.read_text(encoding="utf-8"))["cards"]
    missing = [t for t, card in cards.items() if not card["detects"]]
    print(f"{len(cards)} model cards -> {path}")
    if missing:
        print(f"no notes yet for: {', '.join(missing)}")


if __name__ == "__main__":
    main()
