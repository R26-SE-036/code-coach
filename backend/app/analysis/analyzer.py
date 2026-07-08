"""The orchestrator: one function, analyze_code(), that runs the whole pipeline.

This is the conductor. Every other file in app/analysis does one job; this file
calls them in order and stitches their outputs together. The imports below map
one-to-one onto the pipeline stages:

    parser_utils.parse_java_code_safe   -> parse text into a tree (+ health)
    feature_extractor.extract_features  -> tree into a row of numbers
    ml_engine.predict_issue_types       -> numbers into MLPredictions (the gate)
    error_catalog.ERROR_CATALOG         -> the list of error types + their mode
    issue_locators (via spec.locator)   -> tree into located DetectionResults
    hint_engine.build_diagnostic        -> DetectionResult into final Diagnostic

Input: raw Java source (str) from the request. Output: a list of Diagnostic,
sorted by confidence, that the service/route layers serialize back to VS Code.
Nothing above this file knows how detection works; nothing below it knows about
the request. analyze_code() is the seam between the two.
"""

from typing import Dict, List, Optional

from app.analysis.error_catalog import ERROR_CATALOG, ErrorTypeSpec
from app.analysis.feature_extractor import extract_features
from app.analysis.hint_engine import build_diagnostic
from app.analysis.ml_engine import MLPrediction, predict_issue_types
from app.models import DetectionResult, Diagnostic, ParseResult
from app.analysis.parser_utils import parse_java_code_safe

MIN_FILE_COMPLETENESS = 0.35
ML_CONFIDENCE_WEIGHT = 0.8
LOCATOR_CONFIDENCE_WEIGHT = 0.2


# Fail-safe wrapper around ml_engine.predict_issue_types(). If a model file is
# missing or prediction throws, this returns [] instead of crashing the request,
# so a broken model just means "no ml_gated diagnostics", never a 500. (Trade-off:
# failures are currently silent — a logged warning here is a planned improvement.)
def _safe_predict_issue_types(feature_dict: Dict[str, float]) -> List[MLPrediction]:
    try:
        return predict_issue_types(feature_dict)
    except Exception:
        return []


# Blend the two confidence signals into the number VS Code shows:
#   - ml_gated: 80% the model's probability + 20% the locator's own confidence,
#   - rule_only: the locator's confidence stands alone (no model to blend).
# Then scale by parse completeness (from parser_utils' health), so findings in
# half-typed files come back less confident. Capped at 0.99.
def _combine_confidence(
    ml_probability: Optional[float],
    finding: DetectionResult,
    parse_result: ParseResult,
) -> float:
    locator_confidence = finding.locator_confidence or finding.confidence

    if ml_probability is None:
        # Rule-only detection: the locator confidence stands on its own.
        weighted_confidence = locator_confidence
    else:
        weighted_confidence = (
            ml_probability * ML_CONFIDENCE_WEIGHT
            + locator_confidence * LOCATOR_CONFIDENCE_WEIGHT
        )

    parse_adjusted_confidence = (
        weighted_confidence * parse_result.health.completeness_score
    )
    return round(min(0.99, parse_adjusted_confidence), 2)


# Take a raw finding from a locator and stamp on the pipeline-level fields the
# locator didn't know: the combined confidence, which engine produced it
# ("ml_gated_ast_locator" vs "ast_locator_rule"), and the ML probability if any.
# Returns a filled-in DetectionResult ready for hint_engine.build_diagnostic().
def _finalize_finding(
    finding: DetectionResult,
    parse_result: ParseResult,
    *,
    detection_engine: str,
    ml_probability: Optional[float] = None,
) -> DetectionResult:
    locator_confidence = finding.locator_confidence or finding.confidence

    return DetectionResult(
        error_type=finding.error_type,
        line=finding.line,
        column=finding.column,
        confidence=_combine_confidence(ml_probability, finding, parse_result),
        severity=finding.severity,
        message=finding.message,
        code_context=finding.code_context,
        detection_engine=detection_engine,
        ml_probability=ml_probability,
        locator_confidence=locator_confidence,
    )


# For each error type in the catalog, decide whether it fires and locate it:
# - ml_gated: run the locator only when the ML model predicts the issue type
#   is present (this is why the engine is called: ml_gated_ast_locator).
# - rule_only: the AST locator is deterministic enough to run on its own,
#   with no trained model needed.
# Step 1: ML model → probability score (file-level: "does this file likely have this error?")
# Step 2: if probability >= threshold → run AST locator → find exact line/column
def _detect_for_spec(
    spec: ErrorTypeSpec,
    parse_result: ParseResult,
    predictions_by_error_type: Dict[str, MLPrediction],
) -> List[DetectionResult]:
    if spec.detection_mode == "ml_gated":
        prediction = predictions_by_error_type.get(spec.error_type)
        if prediction is None or not prediction.predicted_positive:
            return []

        return [
            _finalize_finding(
                finding,
                parse_result,
                detection_engine="ml_gated_ast_locator",
                ml_probability=prediction.probability,
            )
            for finding in spec.locator(parse_result)
        ]

    return [
        _finalize_finding(
            finding,
            parse_result,
            detection_engine="ast_locator_rule",
        )
        for finding in spec.locator(parse_result)
    ]


# 1. Parse Java safely.
# 2. Reject crashed or very incomplete parse results.
# 3. Extract features.
# 4. Ask ML engine to predict target issue types (for ml_gated catalog entries).
# 5. For each catalog entry, run its AST locator to find exact locations.
# 6. Build final diagnostics with hints.
# 7. Sort diagnostics by confidence.
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
    predictions_by_error_type = {
        prediction.error_type: prediction
        for prediction in _safe_predict_issue_types(feature_dict)
    }

    # 4. detect and localize each catalog entry
    diagnostics: List[Diagnostic] = []

    for spec in ERROR_CATALOG.values():
        findings = _detect_for_spec(spec, parse_result, predictions_by_error_type)

        # 5. build diagnostics with hints
        for finding in findings:
            diagnostics.append(build_diagnostic(finding))

    # 6. sort diagnostics by confidence
    diagnostics.sort(key=lambda item: item.confidence, reverse=True)
    return diagnostics
