import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from app.models import DetectionResult, Diagnostic, HintSet


class ErrorKnowledge(BaseModel):
    concept_tag: str
    explanation_key: str
    hints: HintSet


# knowledge_base/code_coach_errors.json is the single source of truth for
# hints. error_catalog.validate_catalog() checks at startup that every
# registered error type has an entry here, so a missing or broken file fails
# loudly instead of silently serving the generic default hints.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "knowledge_base" / "code_coach_errors.json"


def _load_error_knowledge_base() -> dict[str, ErrorKnowledge]:
    if not KNOWLEDGE_BASE_PATH.exists():
        return {}

    try:
        raw_items = json.loads(KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8"))
        return {
            error_type: ErrorKnowledge(**knowledge)
            for error_type, knowledge in raw_items.items()
        }
    except (OSError, json.JSONDecodeError, TypeError, ValidationError):
        return {}


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

# It loads hint templates from: knowledge_base\code_coach_errors.json
# Then it creates the final diagnostic with containing:
# diagnostic ID, error type, line and column, confidence, message, code context, concept tag, explanation key, detection engine, ML probability, locator confidence, concept hint, guidance hint, targeted hint
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
