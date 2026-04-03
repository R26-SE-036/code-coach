from typing import Callable, Dict, List, Optional

from app.feature_extractor import extract_features
from app.hint_engine import build_diagnostic
from app.issue_locators import (
    locate_array_length_index_misuse,
    locate_incorrect_conditional_operator,
    locate_off_by_one_loop_boundary,
)
from app.ml_engine import MLPrediction, predict_issue_types
from app.models import DetectionResult, Diagnostic, ParseResult
from app.parser_utils import parse_java_code_safe

MIN_FILE_COMPLETENESS = 0.35

LOCATORS: Dict[str, Callable[[ParseResult], Optional[DetectionResult]]] = {L
    "OFF_BY_ONE_LOOP_BOUNDARY": locate_off_by_one_loop_boundary,
    "INCORRECT_CONDITIONAL_OPERATOR": locate_incorrect_conditional_operator,
    "ARRAY_LENGTH_INDEX_MISUSE": locate_array_length_index_misuse,
}


def _combine_confidence(prediction_probability: float, parse_completeness: float) -> float:
    combined = prediction_probability * parse_completeness
    return round(min(0.99, combined), 2)


def _prediction_to_result(
    prediction: MLPrediction,
    localized_result: DetectionResult,
    parse_result: ParseResult,
) -> DetectionResult:
    return DetectionResult(
        error_type=localized_result.error_type,
        line=localized_result.line,
        column=localized_result.column,
        confidence=_combine_confidence(
            prediction.probability,
            parse_result.health.completeness_score,
        ),
        message=localized_result.message,
        code_context=localized_result.code_context,
    )


def analyze_code(code: str) -> List[Diagnostic]:
    parse_result = parse_java_code_safe(code)

    if parse_result.crashed or parse_result.tree is None:
        return []

    if parse_result.health.completeness_score < MIN_FILE_COMPLETENESS:
        return []

    feature_dict = extract_features(code)
    predictions = predict_issue_types(feature_dict)

    diagnostics: List[Diagnostic] = []

    for prediction in predictions:
        if not prediction.predicted_positive:
            continue

        locator = LOCATORS.get(prediction.error_type)
        if locator is None:
            continue

        localized_result = locator(parse_result)
        if localized_result is None:
            continue

        final_result = _prediction_to_result(
            prediction,
            localized_result,
            parse_result,
        )
        diagnostics.append(build_diagnostic(final_result))

    diagnostics.sort(key=lambda item: item.confidence, reverse=True)
    return diagnostics