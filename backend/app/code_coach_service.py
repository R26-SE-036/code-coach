from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from time import perf_counter
from typing import Iterable

from app.analyzer import analyze_code
from app.common import generate_prefixed_id, utcnow
from app.models import AnalyzeRequest, AnalyzeResponse, Diagnostic


def run_analysis(payload: AnalyzeRequest) -> tuple[list[Diagnostic], float]:
    started_at = perf_counter()
    diagnostics: list[Diagnostic] = []

    if payload.language.lower() == "java":
        diagnostics = analyze_code(payload.code)

    elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
    return diagnostics, elapsed_ms


def build_analyze_response(
    diagnostics: list[Diagnostic],
    analysis_duration_ms: float,
    *,
    message: str = "Analysis completed.",
    learning_session_id: str | None = None,
) -> AnalyzeResponse:
    return AnalyzeResponse(
        status="ok",
        message=message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis_duration_ms=analysis_duration_ms,
        learning_session_id=learning_session_id,
        diagnostics=diagnostics,
    )


def _code_context_hash(code_context: str) -> str:
    return hashlib.sha256(code_context.encode("utf-8")).hexdigest()[:16]


def build_diagnostic_records(
    user_id: str,
    learning_session_id: str,
    diagnostics: Iterable[Diagnostic],
) -> list[dict[str, object]]:
    created_at = utcnow()
    documents: list[dict[str, object]] = []

    for diagnostic in diagnostics:
        documents.append(
            {
                "diagnosticRecordId": generate_prefixed_id("diagrec"),
                "diagnosticId": diagnostic.diagnostic_id,
                "userId": user_id,
                "learningSessionId": learning_session_id,
                "errorType": diagnostic.error_type,
                "conceptTag": diagnostic.concept_tag,
                "explanationKey": diagnostic.explanation_key,
                "severity": diagnostic.severity,
                "line": diagnostic.line,
                "column": diagnostic.column,
                "confidence": diagnostic.confidence,
                "message": diagnostic.message,
                "detectionEngine": diagnostic.detection_engine,
                "mlProbability": diagnostic.ml_probability,
                "locatorConfidence": diagnostic.locator_confidence,
                "codeContextHash": _code_context_hash(diagnostic.code_context),
                "status": diagnostic.status,
                "createdAt": created_at,
                "resolvedAt": None,
            }
        )

    return documents
