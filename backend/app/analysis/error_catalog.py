"""Single registry describing every logical error type Code Coach can detect.

Each error type is fully defined by one ErrorTypeSpec entry in ERROR_CATALOG:
how it is detected (ML-gated or pure AST rule), which locator finds the exact
source location, and which knowledge-base entry supplies the hints. Adding a
new error type means adding one entry here (plus its locator function and a
hints entry in knowledge_base/code_coach_errors.json) instead of editing
separate dictionaries in ml_engine, issue_locators, and hint_engine.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Literal, Optional

from app.analysis.issue_locators import (
    locate_always_false_and_conditions,
    locate_always_true_or_conditions,
    locate_array_length_index_misuses,
    locate_constant_false_loop_conditions,
    locate_decimal_equality_comparisons,
    locate_division_by_zero_literals,
    locate_duplicate_if_else_conditions,
    locate_empty_conditional_bodies,
    locate_ignored_string_method_results,
    locate_incorrect_conditional_operators,
    locate_integer_division_in_decimal_context,
    locate_loop_update_wrong_directions,
    locate_missing_breaks_in_switch,
    locate_off_by_one_loop_boundaries,
    locate_postfix_increment_assigned_back,
    locate_self_assignments,
    locate_string_equality_with_operator,
    locate_unreachable_code_after_return,
    locate_while_variables_not_updated,
)
from app.analysis.logic_candidates import PROPOSERS, ProposerFn, located
from app.analysis.promoted_candidates import PROMOTED_PROPOSERS
from app.models import DetectionResult, ParseResult

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = BACKEND_ROOT / "models"

DetectionMode = Literal["ml_gated", "rule_only", "candidate_ml"]
LocatorFn = Callable[[ParseResult], List[DetectionResult]]


@dataclass(frozen=True)
class ErrorTypeSpec:
    error_type: str
    detection_mode: DetectionMode
    locator: LocatorFn
    # ML gating fields; required when detection_mode == "ml_gated".
    target_column: Optional[str] = None
    model_file: Optional[str] = None
    ml_threshold: float = 0.65
    # CANDIDATE-level gating (upgrade of ml_gated): when set, the file-level
    # gate is replaced by per-site scoring — the locator proposes every rule
    # match and the candidate model accepts/rejects EACH site individually.
    # Eliminates the file-level failure class where an open gate lets the
    # crude locator flag correct sites (see docs/learning-sessions/10_*).
    candidate_model_file: Optional[str] = None
    candidate_ml_threshold: Optional[float] = None
    # CANDIDATE_ML (the logic errors added for the 30-type catalogue): a
    # proposer offers every site that MIGHT be the mistake, with features,
    # and the per-type model trained on executed mutants decides each one.
    # There is no file-level gate and no rule verdict at all.
    proposer: Optional[ProposerFn] = None
    # What the editor and the web app call this mistake. Plain words, not
    # the SCREAMING_CASE id.
    title: str = ""


# Model choice and ml_threshold for ml_gated entries come from
# app/dev_tools/calibrate_thresholds.py (best validation F1, ties broken by
# latency; threshold at the validation separation-margin midpoint). The full
# calibration record lives in backend/models/calibration_v1.json — rerun the
# tool after retraining models and copy the recommended values here.
ERROR_CATALOG: dict[str, ErrorTypeSpec] = {
    "OFF_BY_ONE_LOOP_BOUNDARY": ErrorTypeSpec(
        error_type="OFF_BY_ONE_LOOP_BOUNDARY",
        title="Loop runs one step too far",
        detection_mode="ml_gated",
        locator=locate_off_by_one_loop_boundaries,
        target_column="has_off_by_one",
        model_file="has_off_by_one__logistic_regression.joblib",
        ml_threshold=0.5295,
        # Candidate-level gating (per-loop scoring); calibrated by
        # app/dev_tools/train_candidate_model.py — margin 0.9888 on val.
        candidate_model_file="candidate__has_off_by_one__logistic_regression.joblib",
        candidate_ml_threshold=0.5041,
    ),
    "INCORRECT_CONDITIONAL_OPERATOR": ErrorTypeSpec(
        error_type="INCORRECT_CONDITIONAL_OPERATOR",
        title="Assignment used as a comparison",
        detection_mode="ml_gated",
        locator=locate_incorrect_conditional_operators,
        target_column="has_incorrect_conditional",
        model_file="has_incorrect_conditional__logistic_regression.joblib",
        ml_threshold=0.5008,
    ),
    "ARRAY_LENGTH_INDEX_MISUSE": ErrorTypeSpec(
        error_type="ARRAY_LENGTH_INDEX_MISUSE",
        title="Index equal to the array length",
        detection_mode="ml_gated",
        locator=locate_array_length_index_misuses,
        target_column="has_array_length_index_misuse",
        model_file="has_array_length_index_misuse__logistic_regression.joblib",
        ml_threshold=0.504,
    ),
    "STRING_EQUALITY_WITH_OPERATOR": ErrorTypeSpec(
        error_type="STRING_EQUALITY_WITH_OPERATOR",
        title="Strings compared with ==",
        detection_mode="rule_only",
        locator=locate_string_equality_with_operator,
    ),
    "LOOP_UPDATE_WRONG_DIRECTION": ErrorTypeSpec(
        error_type="LOOP_UPDATE_WRONG_DIRECTION",
        title="Loop counter moves the wrong way",
        detection_mode="rule_only",
        locator=locate_loop_update_wrong_directions,
    ),
    "UNREACHABLE_CODE_AFTER_RETURN": ErrorTypeSpec(
        error_type="UNREACHABLE_CODE_AFTER_RETURN",
        title="Code after a return never runs",
        detection_mode="rule_only",
        locator=locate_unreachable_code_after_return,
    ),
    # Promoted from rule_only: intentional fall-through is a legal idiom the
    # rule cannot judge; the gate learned the distinction from commented /
    # stacked-label negatives in the synthetic corpus.
    "MISSING_BREAK_IN_SWITCH": ErrorTypeSpec(
        error_type="MISSING_BREAK_IN_SWITCH",
        title="Missing break in a switch",
        detection_mode="ml_gated",
        locator=locate_missing_breaks_in_switch,
        target_column="has_missing_break",
        model_file="has_missing_break__logistic_regression.joblib",
        ml_threshold=0.5202,
    ),
    "EMPTY_CONDITIONAL_BODY": ErrorTypeSpec(
        error_type="EMPTY_CONDITIONAL_BODY",
        title="Stray semicolon empties the body",
        detection_mode="rule_only",
        locator=locate_empty_conditional_bodies,
    ),
    "SELF_ASSIGNMENT": ErrorTypeSpec(
        error_type="SELF_ASSIGNMENT",
        title="Variable assigned to itself",
        detection_mode="rule_only",
        locator=locate_self_assignments,
    ),
    "ALWAYS_TRUE_OR_CONDITION": ErrorTypeSpec(
        error_type="ALWAYS_TRUE_OR_CONDITION",
        title="Condition is always true",
        detection_mode="rule_only",
        locator=locate_always_true_or_conditions,
    ),
    "IGNORED_STRING_METHOD_RESULT": ErrorTypeSpec(
        error_type="IGNORED_STRING_METHOD_RESULT",
        title="String method result thrown away",
        detection_mode="rule_only",
        locator=locate_ignored_string_method_results,
    ),
    "DIVISION_BY_ZERO_LITERAL": ErrorTypeSpec(
        error_type="DIVISION_BY_ZERO_LITERAL",
        title="Division by zero",
        detection_mode="rule_only",
        locator=locate_division_by_zero_literals,
    ),
    "CONSTANT_FALSE_LOOP_CONDITION": ErrorTypeSpec(
        error_type="CONSTANT_FALSE_LOOP_CONDITION",
        title="Loop body never runs",
        detection_mode="rule_only",
        locator=locate_constant_false_loop_conditions,
    ),
    "DUPLICATE_IF_ELSE_CONDITION": ErrorTypeSpec(
        error_type="DUPLICATE_IF_ELSE_CONDITION",
        title="Same condition tested twice",
        detection_mode="rule_only",
        locator=locate_duplicate_if_else_conditions,
    ),
    # Promoted from rule_only: loop state can change through side effects the
    # rule cannot track; the gate learned from Scanner-style and
    # while(true)+break negatives in the synthetic corpus.
    "WHILE_VARIABLE_NOT_UPDATED": ErrorTypeSpec(
        error_type="WHILE_VARIABLE_NOT_UPDATED",
        title="While loop may never end",
        detection_mode="ml_gated",
        locator=locate_while_variables_not_updated,
        target_column="has_while_not_updated",
        model_file="has_while_not_updated__logistic_regression.joblib",
        ml_threshold=0.5027,
    ),
    # Added together, all rule-only, each under a concept that already has a
    # lesson, a game and a collaboration prompt - so a student who keeps
    # making one of them is sent somewhere real, not to the generic fallback.
    "INTEGER_DIVISION_IN_DECIMAL_CONTEXT": ErrorTypeSpec(
        error_type="INTEGER_DIVISION_IN_DECIMAL_CONTEXT",
        title="Integer division loses the decimals",
        detection_mode="rule_only",
        locator=locate_integer_division_in_decimal_context,
    ),
    "DECIMAL_EQUALITY_COMPARISON": ErrorTypeSpec(
        error_type="DECIMAL_EQUALITY_COMPARISON",
        title="Decimals compared with ==",
        detection_mode="rule_only",
        locator=locate_decimal_equality_comparisons,
    ),
    "POSTFIX_INCREMENT_ASSIGNED_BACK": ErrorTypeSpec(
        error_type="POSTFIX_INCREMENT_ASSIGNED_BACK",
        title="x = x++ changes nothing",
        detection_mode="rule_only",
        locator=locate_postfix_increment_assigned_back,
    ),
    "ALWAYS_FALSE_AND_CONDITION": ErrorTypeSpec(
        error_type="ALWAYS_FALSE_AND_CONDITION",
        title="Condition is always false",
        detection_mode="rule_only",
        locator=locate_always_false_and_conditions,
    ),
}

# ── The logic errors that need judgment (candidate_ml) ──
# Each is proposed broadly and decided per site by its own model. Thresholds
# come from app/dev_tools/mutation/train_logic_models.py: the lowest
# threshold that keeps validation precision at or above 0.95, so a wrong
# underline is rarer than a missed one. Rerun it after rebuilding the corpus
# and copy the values from backend/models/logic_calibration_v1.json.
_LOGIC_TITLES = {
    "LOOP_SKIPS_LAST_ELEMENT": "Loop stops one element early",
    "INDEX_PLUS_ONE_OUT_OF_BOUNDS": "Neighbour index runs past the end",
    "WRONG_LOOP_VARIABLE_IN_INDEX": "Wrong counter used as an index",
    "NESTED_LOOP_WRONG_COUNTER": "Loop header uses the wrong counter",
    "LOOP_COUNTER_CHANGED_IN_BODY": "Loop counter changed inside the body",
    "ACCUMULATOR_RESET_INSIDE_LOOP": "Running total reset inside the loop",
    "WRONG_EXTREME_INITIAL_VALUE": "Max/min search starts from the wrong value",
    "EARLY_RETURN_IN_LOOP": "Loop returns on its first pass",
    "UNREACHABLE_ELSE_IF_ORDER": "An else-if branch can never run",
    "MISLEADING_INDENTATION_NO_BRACES": "Indented line is outside the if or loop",
    "NON_SHORT_CIRCUIT_OPERATOR": "& or | used instead of && or ||",
}


def _load_logic_calibration() -> dict:
    import json

    path = MODELS_DIR / "logic_calibration_v1.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("selected", {})
    except (OSError, ValueError):
        return {}


_LOGIC_CALIBRATION = _load_logic_calibration()

for _error_type, _title in _LOGIC_TITLES.items():
    _chosen = _LOGIC_CALIBRATION.get(_error_type, {})
    ERROR_CATALOG[_error_type] = ErrorTypeSpec(
        error_type=_error_type,
        title=_title,
        detection_mode="candidate_ml",
        locator=located(PROPOSERS[_error_type]),
        proposer=PROPOSERS[_error_type],
        candidate_model_file=_chosen.get("model_file", f"logic__{_error_type.lower()}.joblib"),
        candidate_ml_threshold=_chosen.get("threshold", 0.5),
    )

# ── The thirteen moved onto per-site models ──
# Five had a file-level gate in front of a rule, eight were rules alone. Each
# now works like the logic errors above: proposer + its own model trained on
# executed mutants. The definitions above are kept as LEGACY_SPECS - the
# corpus builder scores them as the "before" baseline - and a type falls back
# to its legacy detector when its model has not been trained, or when the
# server lists it in LEGACY_DETECTORS (a switch for a model that misbehaves,
# without a deploy).
LEGACY_SPECS: dict[str, ErrorTypeSpec] = {}


def _legacy_detector_names() -> set[str]:
    try:
        from app.core.config import get_settings

        raw = get_settings().legacy_detectors or ""
    except Exception:
        raw = ""
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


_FORCED_LEGACY = _legacy_detector_names()
for _error_type, _proposer in PROMOTED_PROPOSERS.items():
    _legacy = ERROR_CATALOG[_error_type]
    LEGACY_SPECS[_error_type] = _legacy
    _chosen = _LOGIC_CALIBRATION.get(_error_type)
    if not _chosen or _error_type in _FORCED_LEGACY or not (MODELS_DIR / _chosen["model_file"]).exists():
        continue
    ERROR_CATALOG[_error_type] = ErrorTypeSpec(
        error_type=_error_type,
        title=_legacy.title,
        detection_mode="candidate_ml",
        locator=located(_proposer),
        proposer=_proposer,
        candidate_model_file=_chosen["model_file"],
        candidate_ml_threshold=_chosen["threshold"],
    )


def title_for(error_type: str) -> str:
    spec = ERROR_CATALOG.get(error_type)
    if spec is not None and spec.title:
        return spec.title
    return error_type.replace("_", " ").capitalize()


def shadow_error_types() -> set[str]:
    """Types detected but kept out of the response (settings.shadow_error_types)."""
    from app.core.config import get_settings

    raw = get_settings().shadow_error_types or ""
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


# Called by ml_engine.predict_issue_types(): the error types still behind a
# file-level gate. None, once the per-site models are trained - a type is only
# here again if it has been switched back to its legacy detector.
def ml_gated_specs() -> list[ErrorTypeSpec]:
    return [
        spec
        for spec in ERROR_CATALOG.values()
        if spec.detection_mode == "ml_gated"
    ]


# The pure-AST error types (no model). Provided for symmetry/introspection;
# analyzer actually iterates the whole ERROR_CATALOG and branches per spec.
def rule_only_specs() -> list[ErrorTypeSpec]:
    return [
        spec
        for spec in ERROR_CATALOG.values()
        if spec.detection_mode == "rule_only"
    ]


def validate_catalog() -> None:
    """Fail loudly at startup when a catalog entry is only half registered.

    A missing model file or hints entry would otherwise surface as silently
    dropped diagnostics or generic fallback hints at analysis time.

    Called by main.py during app startup. It cross-checks the catalog against
    the other two "sources of truth": the model files on disk (MODELS_DIR) and
    hint_engine.ERROR_KNOWLEDGE_BASE (loaded from the knowledge_base JSON). This
    is what keeps the three registries in sync now that adding an error type
    only touches this file plus its locator and its JSON hint entry.
    """
    from app.analysis.hint_engine import ERROR_KNOWLEDGE_BASE

    problems: list[str] = []

    for key, spec in ERROR_CATALOG.items():
        if key != spec.error_type:
            problems.append(
                f"{key}: catalog key does not match spec error_type {spec.error_type!r}"
            )

        if spec.detection_mode == "candidate_ml":
            if spec.proposer is None:
                problems.append(f"{key}: candidate_ml spec has no proposer")
            if not spec.candidate_model_file or not (MODELS_DIR / spec.candidate_model_file).exists():
                problems.append(f"{key}: candidate model file not found: {spec.candidate_model_file}")
        elif spec.candidate_model_file:
            if spec.candidate_ml_threshold is None:
                problems.append(f"{key}: candidate model set but no candidate_ml_threshold")
            if not (MODELS_DIR / spec.candidate_model_file).exists():
                problems.append(
                    f"{key}: candidate model file not found: {spec.candidate_model_file}"
                )
            from app.analysis.candidate_extractor import CANDIDATE_EXTRACTORS
            if spec.target_column not in CANDIDATE_EXTRACTORS:
                problems.append(
                    f"{key}: no candidate extractor registered for {spec.target_column}"
                )

        if spec.detection_mode == "ml_gated":
            if not spec.target_column:
                problems.append(f"{key}: ml_gated spec is missing target_column")
            if not spec.model_file:
                problems.append(f"{key}: ml_gated spec is missing model_file")
            elif not (MODELS_DIR / spec.model_file).exists():
                problems.append(
                    f"{key}: model file not found: {MODELS_DIR / spec.model_file}"
                )

        if not spec.title:
            problems.append(f"{key}: no title")

        if key not in ERROR_KNOWLEDGE_BASE:
            problems.append(
                f"{key}: no hints entry in knowledge_base/code_coach_errors.json"
            )

    if problems:
        raise RuntimeError(
            "Error catalog validation failed:\n" + "\n".join(f"- {p}" for p in problems)
        )
