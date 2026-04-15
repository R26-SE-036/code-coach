import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from app.models import DetectionResult, Diagnostic, HintSet


class ErrorKnowledge(BaseModel):
    concept_tag: str
    explanation_key: str
    hints: HintSet


EMBEDDED_ERROR_KNOWLEDGE_BASE: dict[str, ErrorKnowledge] = {
    "OFF_BY_ONE_LOOP_BOUNDARY": ErrorKnowledge(
        concept_tag="loop_boundaries",
        explanation_key="loop_index_exceeds_array_limit",
        hints=HintSet(
            concept="Think about what the last valid index of an array should be.",
            guidance="An array with length n usually has valid indexes from 0 up to n - 1.",
            targeted="Check whether this loop condition should use < instead of <= when comparing with an array length."
        ),
    ),
    "INCORRECT_CONDITIONAL_OPERATOR": ErrorKnowledge(
        concept_tag="conditional_logic",
        explanation_key="assignment_used_in_condition",
        hints=HintSet(
            concept="Conditions usually check a true or false result, not change a value.",
            guidance="Think about whether this condition is comparing two values or assigning a new value.",
            targeted="Check whether you meant to use == instead of = inside this condition."
        ),
    ),
    "ARRAY_LENGTH_INDEX_MISUSE": ErrorKnowledge(
        concept_tag="array_indexing",
        explanation_key="array_length_used_as_index",
        hints=HintSet(
            concept="Array length tells you how many items exist, not the last valid position.",
            guidance="Think about the difference between the number of elements and the final usable index.",
            targeted="Check whether the array length is being used directly as an index. The last valid index is usually length - 1."
        ),
    ),
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "knowledge_base" / "code_coach_errors.json"


def _load_error_knowledge_base() -> dict[str, ErrorKnowledge]:
    if not KNOWLEDGE_BASE_PATH.exists():
        return EMBEDDED_ERROR_KNOWLEDGE_BASE

    try:
        raw_items = json.loads(KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8"))
        return {
            error_type: ErrorKnowledge(**knowledge)
            for error_type, knowledge in raw_items.items()
        }
    except (OSError, json.JSONDecodeError, TypeError, ValidationError):
        return EMBEDDED_ERROR_KNOWLEDGE_BASE


ERROR_KNOWLEDGE_BASE = _load_error_knowledge_base()

DEFAULT_ERROR_KNOWLEDGE = ErrorKnowledge(
    concept_tag="general_programming_logic",
    explanation_key="generic_programming_issue",
    hints=HintSet(
        concept="Look carefully at this line and think about what the code is trying to do.",
        guidance="Check the values, condition, and indexes used in this statement.",
        targeted="Review this statement step by step and compare it with the expected Java syntax and logic."
    ),
)


def get_error_knowledge(error_type: str) -> ErrorKnowledge:
    return ERROR_KNOWLEDGE_BASE.get(error_type, DEFAULT_ERROR_KNOWLEDGE)


def _diagnostic_id_for(finding: DetectionResult) -> str:
    stable_key = "|".join(
        [
            finding.error_type,
            str(finding.line),
            str(finding.column),
            finding.code_context,
        ]
    )
    digest = hashlib.sha1(stable_key.encode("utf-8")).hexdigest()[:12]
    return f"cc_{digest}"


def build_diagnostic(finding: DetectionResult) -> Diagnostic:
    knowledge = get_error_knowledge(finding.error_type)

    return Diagnostic(
        diagnostic_id=_diagnostic_id_for(finding),
        error_type=finding.error_type,
        severity=finding.severity,
        line=finding.line,
        column=finding.column,
        confidence=finding.confidence,
        message=finding.message,
        code_context=finding.code_context,
        concept_tag=knowledge.concept_tag,
        explanation_key=knowledge.explanation_key,
        status="active",
        detection_engine=finding.detection_engine,
        ml_probability=finding.ml_probability,
        locator_confidence=finding.locator_confidence,
        hints=knowledge.hints,
    )
