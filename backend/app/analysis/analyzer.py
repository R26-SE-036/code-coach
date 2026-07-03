from typing import Dict, List

from app.analysis.feature_extractor import extract_features
from app.analysis.hint_engine import build_diagnostic
from app.analysis.issue_locators import TARGET_LOCATORS
from app.analysis.ml_engine import MLPrediction, predict_issue_types
from app.models import DetectionResult, Diagnostic, ParseResult
from app.analysis.parser_utils import parse_java_code_safe

MIN_FILE_COMPLETENESS = 0.35
ML_CONFIDENCE_WEIGHT = 0.8
LOCATOR_CONFIDENCE_WEIGHT = 0.2


def _safe_predict_issue_types(feature_dict: Dict[str, float]) -> List[MLPrediction]:
    try:
        return predict_issue_types(feature_dict)
    except Exception:
        return []


def _combine_confidence(
    prediction: MLPrediction,
    finding: DetectionResult,
    parse_result: ParseResult,
) -> float:
    locator_confidence = finding.locator_confidence or finding.confidence
    weighted_confidence = (
        prediction.probability * ML_CONFIDENCE_WEIGHT
        + locator_confidence * LOCATOR_CONFIDENCE_WEIGHT
    )
    parse_adjusted_confidence = (
        weighted_confidence * parse_result.health.completeness_score
    )
    return round(min(0.99, parse_adjusted_confidence), 2)


def _prediction_to_localized_result(
    prediction: MLPrediction,
    finding: DetectionResult,
    parse_result: ParseResult,
) -> DetectionResult:
    locator_confidence = finding.locator_confidence or finding.confidence

    return DetectionResult(
        error_type=finding.error_type,
        line=finding.line,
        column=finding.column,
        confidence=_combine_confidence(prediction, finding, parse_result),
        severity=finding.severity,
        message=finding.message,
        code_context=finding.code_context,
        detection_engine="ml_gated_ast_locator",
        ml_probability=prediction.probability,
        locator_confidence=locator_confidence,
    )

#For each positive ML prediction, use AST locator to find exact location.
def _localize_ml_positive_prediction(
    prediction: MLPrediction,
    parse_result: ParseResult,
) -> List[DetectionResult]:
    
    #use issue_locators.py
    locator = TARGET_LOCATORS.get(prediction.error_type)

    if locator is None:
        return []

    findings = locator(parse_result)
    return [
        _prediction_to_localized_result(prediction, finding, parse_result)
        for finding in findings
    ]

# 1. Parse Java safely.
# 2. Reject crashed or very incomplete parse results.
# 3. Extract features.
# 4. Ask ML engine to predict target issue types.
# 5. For each positive ML prediction, use AST locator to find exact location.
# 6. Build final diagnostic with hints.
# 7.Sort diagnostics by confidence.
def analyze_code(code: str) -> List[Diagnostic]:
    # 1. parse code
    parse_result = parse_java_code_safe(code)

    if parse_result.crashed or parse_result.tree is None:
        return []

    if parse_result.health.completeness_score < MIN_FILE_COMPLETENESS:
        return []

    # 2. extract features
    feature_dict = extract_features(code)
    # 3. predict issue types
    predictions = _safe_predict_issue_types(feature_dict)

    # 4. localize issue types
    diagnostics: List[Diagnostic] = []

    for prediction in predictions:
        if not prediction.predicted_positive:
            continue

        # 5. For each positive ML prediction, use AST locator to find exact location.
        # This is why the implementation is called: ml_gated_ast_locator
        localized_findings = _localize_ml_positive_prediction(
            prediction,
            parse_result,
        )

        for finding in localized_findings:
            diagnostics.append(build_diagnostic(finding))
    
    # 5. build diagnostics
    diagnostics.sort(key=lambda item: item.confidence, reverse=True)
    return diagnostics
