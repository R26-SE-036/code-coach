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
    locate_always_true_or_conditions,
    locate_array_length_index_misuses,
    locate_constant_false_loop_conditions,
    locate_division_by_zero_literals,
    locate_duplicate_if_else_conditions,
    locate_empty_conditional_bodies,
    locate_ignored_string_method_results,
    locate_incorrect_conditional_operators,
    locate_loop_update_wrong_directions,
    locate_missing_breaks_in_switch,
    locate_off_by_one_loop_boundaries,
    locate_self_assignments,
    locate_string_equality_with_operator,
    locate_unreachable_code_after_return,
    locate_while_variables_not_updated,
)
from app.models import DetectionResult, ParseResult

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = BACKEND_ROOT / "models"

DetectionMode = Literal["ml_gated", "rule_only"]
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


# Model choice and ml_threshold for ml_gated entries come from
# app/dev_tools/calibrate_thresholds.py (best validation F1, ties broken by
# latency; threshold at the validation separation-margin midpoint). The full
# calibration record lives in backend/models/calibration_v1.json — rerun the
# tool after retraining models and copy the recommended values here.
ERROR_CATALOG: dict[str, ErrorTypeSpec] = {
    "OFF_BY_ONE_LOOP_BOUNDARY": ErrorTypeSpec(
        error_type="OFF_BY_ONE_LOOP_BOUNDARY",
        detection_mode="ml_gated",
        locator=locate_off_by_one_loop_boundaries,
        target_column="has_off_by_one",
        model_file="has_off_by_one__logistic_regression.joblib",
        ml_threshold=0.6321,
    ),
    "INCORRECT_CONDITIONAL_OPERATOR": ErrorTypeSpec(
        error_type="INCORRECT_CONDITIONAL_OPERATOR",
        detection_mode="ml_gated",
        locator=locate_incorrect_conditional_operators,
        target_column="has_incorrect_conditional",
        model_file="has_incorrect_conditional__random_forest.joblib",
        ml_threshold=0.285,
    ),
    "ARRAY_LENGTH_INDEX_MISUSE": ErrorTypeSpec(
        error_type="ARRAY_LENGTH_INDEX_MISUSE",
        detection_mode="ml_gated",
        locator=locate_array_length_index_misuses,
        target_column="has_array_length_index_misuse",
        model_file="has_array_length_index_misuse__logistic_regression.joblib",
        ml_threshold=0.5371,
    ),
    "STRING_EQUALITY_WITH_OPERATOR": ErrorTypeSpec(
        error_type="STRING_EQUALITY_WITH_OPERATOR",
        detection_mode="rule_only",
        locator=locate_string_equality_with_operator,
    ),
    "LOOP_UPDATE_WRONG_DIRECTION": ErrorTypeSpec(
        error_type="LOOP_UPDATE_WRONG_DIRECTION",
        detection_mode="rule_only",
        locator=locate_loop_update_wrong_directions,
    ),
    "UNREACHABLE_CODE_AFTER_RETURN": ErrorTypeSpec(
        error_type="UNREACHABLE_CODE_AFTER_RETURN",
        detection_mode="rule_only",
        locator=locate_unreachable_code_after_return,
    ),
    "MISSING_BREAK_IN_SWITCH": ErrorTypeSpec(
        error_type="MISSING_BREAK_IN_SWITCH",
        detection_mode="rule_only",
        locator=locate_missing_breaks_in_switch,
    ),
    "EMPTY_CONDITIONAL_BODY": ErrorTypeSpec(
        error_type="EMPTY_CONDITIONAL_BODY",
        detection_mode="rule_only",
        locator=locate_empty_conditional_bodies,
    ),
    "SELF_ASSIGNMENT": ErrorTypeSpec(
        error_type="SELF_ASSIGNMENT",
        detection_mode="rule_only",
        locator=locate_self_assignments,
    ),
    "ALWAYS_TRUE_OR_CONDITION": ErrorTypeSpec(
        error_type="ALWAYS_TRUE_OR_CONDITION",
        detection_mode="rule_only",
        locator=locate_always_true_or_conditions,
    ),
    "IGNORED_STRING_METHOD_RESULT": ErrorTypeSpec(
        error_type="IGNORED_STRING_METHOD_RESULT",
        detection_mode="rule_only",
        locator=locate_ignored_string_method_results,
    ),
    "DIVISION_BY_ZERO_LITERAL": ErrorTypeSpec(
        error_type="DIVISION_BY_ZERO_LITERAL",
        detection_mode="rule_only",
        locator=locate_division_by_zero_literals,
    ),
    "CONSTANT_FALSE_LOOP_CONDITION": ErrorTypeSpec(
        error_type="CONSTANT_FALSE_LOOP_CONDITION",
        detection_mode="rule_only",
        locator=locate_constant_false_loop_conditions,
    ),
    "DUPLICATE_IF_ELSE_CONDITION": ErrorTypeSpec(
        error_type="DUPLICATE_IF_ELSE_CONDITION",
        detection_mode="rule_only",
        locator=locate_duplicate_if_else_conditions,
    ),
    "WHILE_VARIABLE_NOT_UPDATED": ErrorTypeSpec(
        error_type="WHILE_VARIABLE_NOT_UPDATED",
        detection_mode="rule_only",
        locator=locate_while_variables_not_updated,
    ),
}


# Called by ml_engine.predict_issue_types(): the only error types that need a
# trained model loaded and scored. Currently the 3 original types.
def ml_gated_specs() -> list[ErrorTypeSpec]:
    return [
        spec
        for spec in ERROR_CATALOG.values()
        if spec.detection_mode == "ml_gated"
    ]


# The 12 pure-AST error types (no model). Provided for symmetry/introspection;
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

        if spec.detection_mode == "ml_gated":
            if not spec.target_column:
                problems.append(f"{key}: ml_gated spec is missing target_column")
            if not spec.model_file:
                problems.append(f"{key}: ml_gated spec is missing model_file")
            elif not (MODELS_DIR / spec.model_file).exists():
                problems.append(
                    f"{key}: model file not found: {MODELS_DIR / spec.model_file}"
                )

        if key not in ERROR_KNOWLEDGE_BASE:
            problems.append(
                f"{key}: no hints entry in knowledge_base/code_coach_errors.json"
            )

    if problems:
        raise RuntimeError(
            "Error catalog validation failed:\n" + "\n".join(f"- {p}" for p in problems)
        )
