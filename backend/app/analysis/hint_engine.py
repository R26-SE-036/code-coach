"""The last step: wrap a located finding into the Diagnostic sent to VS Code.

Pipeline position: runs at the very end of analyze_code(), after a DetectionResult
has been produced and its confidence finalized. It attaches the teaching content:
the concept tag, the explanation key, and the 3-level HintSet (concept / guidance
/ targeted) the student sees when hovering the yellow underline.

Where the hints come from: knowledge_base/code_coach_errors.json, loaded once at
import time into ERROR_KNOWLEDGE_BASE (keyed by error_type). That JSON is the
single source of truth for hint text; error_catalog.validate_catalog() checks at
startup that every registered error type has an entry, so a missing entry fails
loudly instead of silently falling back to the generic default.

Data flow:
    DetectionResult (from a locator, refined by analyzer)
      -> look up its error_type in ERROR_KNOWLEDGE_BASE
      -> build a stable diagnostic_id (hash of type+line+column+context)
      -> Diagnostic (returned)  ->  serialized to JSON  ->  VS Code underline+hints
"""

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


# Look up the hints for one error type, falling back to the generic default if
# it is somehow missing (validate_catalog normally prevents that at startup).
def get_error_knowledge(error_type: str) -> ErrorKnowledge:
    return ERROR_KNOWLEDGE_BASE.get(error_type, DEFAULT_ERROR_KNOWLEDGE)


# Build a STABLE id from the bug's identity (type + line + column + snippet).
# Same bug in the same place always hashes to the same "cc_..." id, which lets
# the service layer recognize a recurring mistake across analyses (used for the
# repeat-struggle tracking sent to the downstream Study Guider).
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

# THE public entry point, called once per finding by analyzer.analyze_code().
# Merges two things into the final Diagnostic:
#   - detection facts from the finding (where/how it was found, confidence),
#   - teaching content from the knowledge base (concept_tag, explanation_key,
#     3-level hints).
# The returned Diagnostic is exactly what travels back through the service and
# route layers to the extension.
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
