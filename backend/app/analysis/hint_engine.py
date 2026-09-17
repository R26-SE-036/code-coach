"""The last step: wrap a located finding into the Diagnostic sent to VS Code.

Pipeline position: runs at the very end of analyze_code(), after a DetectionResult
has been produced and its confidence finalized. It attaches the teaching content:
the concept tag, the explanation key, and the 3-level HintSet (concept / guidance
/ targeted) the student sees when hovering the yellow underline.

Where the hints come from: knowledge_base/code_coach_errors.json, loaded once at
import time into ERROR_KNOWLEDGE_BASE (keyed by error_type). That JSON is the
single source of truth for hint text; error_catalog.validate_catalog() checks at
startup that every registered error type has an entry, so a missing entry fails
loudly instead of silently falling back to the generic default. The targeted
hint can instead quote the student's own code - see targeted_hint_for().

Data flow:
    every DetectionResult in the file (from the locators, refined by analyzer)
      -> look up each error_type in ERROR_KNOWLEDGE_BASE
      -> fill the targeted hint with what the locator matched, when it can
      -> build a stable diagnostic_id (type + flagged line's text + occurrence)
      -> Diagnostic (returned)  ->  serialized to JSON  ->  VS Code underline+hints
"""

import hashlib
import json
from pathlib import Path
from string import Formatter
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

# Targeted hints that quote the student's code, keyed by error type. A separate
# file on purpose: code_coach_errors.json is also read by PairPath and Study
# Guider, which have no use for templates and should not have to tolerate a
# new key in order to keep working.
HINT_TEMPLATES_PATH = PROJECT_ROOT / "knowledge_base" / "code_coach_hint_templates.json"


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


def _load_targeted_hint_templates() -> dict[str, str]:
    if not HINT_TEMPLATES_PATH.exists():
        return {}

    try:
        raw_items = json.loads(HINT_TEMPLATES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return {
        error_type: entry["targeted"]
        for error_type, entry in raw_items.items()
        if isinstance(entry, dict) and isinstance(entry.get("targeted"), str)
    }


ERROR_KNOWLEDGE_BASE = _load_error_knowledge_base()
TARGETED_HINT_TEMPLATES = _load_targeted_hint_templates()

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


def template_fields(template: str) -> set[str]:
    """The {placeholders} a template names."""
    return {name for _, name, _, _ in Formatter().parse(template) if name}


# ===================== A TARGETED HINT ABOUT THIS CODE =====================
# "Check whether the loop condition should stop before the array length" is
# the same sentence for every student and every loop, so the most specific of
# the three hints was the one that said least about the code in front of them.
#
# The targeted hint now names what the locator actually matched: "This loop
# keeps going while `i <= scores.length`, so on its last pass the index is
# scores.length...". It still asks rather than tells - no template contains
# the corrected code - because the concept and guidance levels are there to
# be worked through first.
#
# The template is used only when the locator supplied EVERY field it names.
# Otherwise the generic hint stands: a half-filled sentence is worse than a
# general one.
# =========================================================================
def targeted_hint_for(finding: DetectionResult, fallback: str) -> str:
    template = TARGETED_HINT_TEMPLATES.get(finding.error_type)
    if not template:
        return fallback

    supplied = {key for key, value in (finding.details or {}).items() if value}
    if not template_fields(template) <= supplied:
        return fallback

    # format_map parses only the template, so braces in the student's code
    # are inserted as they are.
    return template.format_map(finding.details)


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
#     3-level hints, the targeted one filled in from the finding if it can be).
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
        hints=HintSet(
            concept=knowledge.hints.concept,
            guidance=knowledge.hints.guidance,
            targeted=targeted_hint_for(finding, knowledge.hints.targeted),
        ),
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
