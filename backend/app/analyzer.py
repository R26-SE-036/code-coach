from typing import List

from app.detectors.array_length_index_misuse import detect_array_length_index_misuse
from app.detectors.incorrect_conditional_operator import (
    detect_incorrect_conditional_operator,
)
from app.detectors.off_by_one import detect_off_by_one_loop_boundary
from app.hint_engine import build_diagnostic
from app.models import DetectionCandidate, DetectionResult, Diagnostic, Span
from app.parser_utils import parse_java_code_safe

MIN_CONFIDENCE = 0.70
MIN_FILE_COMPLETENESS = 0.35

DETECTORS = [
    detect_off_by_one_loop_boundary,
    detect_incorrect_conditional_operator,
    detect_array_length_index_misuse,
]


def spans_overlap(a: Span, b: Span, line_margin: int = 1) -> bool:
    a_start = a.start_line - line_margin
    a_end = a.end_line + line_margin
    b_start = b.start_line
    b_end = b.end_line
    return not (a_end < b_start or b_end < a_start)


def candidate_overlaps_unstable_region(
    candidate_span: Span,
    unstable_spans: list[Span],
) -> bool:
    return any(spans_overlap(candidate_span, unstable) for unstable in unstable_spans)


def adjust_confidence(
    base_confidence: float,
    parse_completeness: float,
    near_unstable: bool,
) -> float:
    adjusted = base_confidence * parse_completeness

    if near_unstable:
        adjusted *= 0.45

    return round(adjusted, 2)


def candidate_to_result(candidate: DetectionCandidate, confidence: float) -> DetectionResult:
    return DetectionResult(
        error_type=candidate.error_type,
        line=candidate.line,
        column=candidate.column,
        confidence=confidence,
        message=candidate.message,
        code_context=candidate.code_context,
    )


def analyze_code(code: str) -> List[Diagnostic]:
    parse_result = parse_java_code_safe(code)

    if parse_result.crashed or parse_result.tree is None:
        return []

    if parse_result.health.completeness_score < MIN_FILE_COMPLETENESS:
        return []

    raw_candidates: List[DetectionCandidate] = []

    for detector in DETECTORS:
        try:
            raw_candidates.extend(
                detector(parse_result.tree, parse_result.source_bytes)
            )
        except Exception:
            continue

    final_diagnostics: List[Diagnostic] = []

    for candidate in raw_candidates:
        near_unstable = False

        if candidate.requires_stable_region:
            near_unstable = candidate_overlaps_unstable_region(
                candidate.source_span,
                parse_result.health.unstable_spans,
            )

            if near_unstable:
                continue

        adjusted_confidence = adjust_confidence(
            candidate.base_confidence,
            parse_result.health.completeness_score,
            near_unstable,
        )

        if adjusted_confidence < MIN_CONFIDENCE:
            continue

        result = candidate_to_result(candidate, adjusted_confidence)
        final_diagnostics.append(build_diagnostic(result))

    return final_diagnostics