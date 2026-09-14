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
    every DetectionResult in the file (from the locators, refined by analyzer)
      -> look up each error_type in ERROR_KNOWLEDGE_BASE
      -> build a stable diagnostic_id (type + flagged line's text + occurrence)
      -> Diagnostic (returned)  ->  serialized to JSON  ->  VS Code underline+hints
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

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


# A STABLE id for a finding: the same mistake keeps the same id while the
# student edits the rest of the file. Storage recognises a finding by this id
# from one analysis to the next, and a student's dispute is kept against it.
#
# ================== NOT THE LINE NUMBER, NOT THE COLUMN ==================
# This used to hash type + line + column + snippet. Analysis re-runs 900 ms
# after every pause in typing, so as soon as a student added a line anywhere
# above a mistake, its id changed - and storage recorded the old id as
# RESOLVED and the same mistake as NEWLY DETECTED. One comment line added
# above the first finding in each of the extension's sample files turned all
# fifteen findings into fifteen fixes and fifteen new mistakes. Repeat counts,
# time to fix, mastery and Study Guider's struggle triggers are all computed
# from those records.
#
# The id is now the error type, the flagged line's text with its whitespace
# normalised (re-indenting is not a fix either), and which occurrence of that
# exact text this is, counted top to bottom - so two identical mistakes in one
# file are still two findings. Editing the flagged line itself does change
# the id, and that is the one edit that should.
# ========================================================================
def normalise_code_context(code_context: str) -> str:
    return " ".join(code_context.split())


def diagnostic_id_for(error_type: str, code_context: str, occurrence: int = 0) -> str:
    stable_key = "|".join(
        [
            error_type,
            normalise_code_context(code_context),
            str(occurrence),
        ]
    )
    digest = hashlib.sha1(stable_key.encode("utf-8")).hexdigest()[:12]
    return f"cc_{digest}"


# Merges two things into the final Diagnostic:
#   - detection facts from the finding (where/how it was found, confidence),
#   - teaching content from the knowledge base (concept_tag, explanation_key,
#     3-level hints).
# `occurrence` is which appearance of this mistake, in these exact words, the
# finding is. build_diagnostics counts it; call that rather than this.
def build_diagnostic(finding: DetectionResult, *, occurrence: int = 0) -> Diagnostic:
    knowledge = get_error_knowledge(finding.error_type)

    return Diagnostic(
        diagnostic_id=diagnostic_id_for(
            finding.error_type,
            finding.code_context,
            occurrence,
        ),
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


# THE public entry point, called once per analysis by analyzer.analyze_code()
# with every finding in the file. Occurrences are counted in reading order, so
# a finding's id depends only on identical mistakes ABOVE it: an edit below
# it, or to any line that is not a copy of it, leaves the id unchanged.
def build_diagnostics(findings: Iterable[DetectionResult]) -> List[Diagnostic]:
    seen: Dict[Tuple[str, str], int] = {}
    diagnostics: List[Diagnostic] = []

    for finding in sorted(findings, key=lambda item: (item.line, item.column)):
        key = (finding.error_type, normalise_code_context(finding.code_context))
        occurrence = seen.get(key, 0)
        seen[key] = occurrence + 1
        diagnostics.append(build_diagnostic(finding, occurrence=occurrence))

    return diagnostics
