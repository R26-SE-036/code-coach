from pydantic import BaseModel

from app.models import DetectionResult, Diagnostic, HintSet


class ErrorKnowledge(BaseModel):
    concept_tag: str
    explanation_key: str
    hints: HintSet


ERROR_KNOWLEDGE_BASE: dict[str, ErrorKnowledge] = {
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


def build_diagnostic(finding: DetectionResult) -> Diagnostic:
    knowledge = get_error_knowledge(finding.error_type)

    return Diagnostic(
        error_type=finding.error_type,
        line=finding.line,
        column=finding.column,
        confidence=finding.confidence,
        message=finding.message,
        code_context=finding.code_context,
        concept_tag=knowledge.concept_tag,
        explanation_key=knowledge.explanation_key,
        hints=knowledge.hints,
    )