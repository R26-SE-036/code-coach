from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

from app.core.common import generate_prefixed_id, utcnow
from app.models import (
    ConceptStruggleResponse,
    ConceptStruggleView,
    ConceptSummaryView,
    DiagnosticSummaryResponse,
    DiagnosticSyncResult,
    ErrorTypeSummaryView,
)


def build_learning_event_document(
    user_id: str,
    learning_session_id: str,
    *,
    component: str,
    event_type: str,
    payload: dict[str, Any],
    concept_tag: str | None = None,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    created_at = utcnow()
    return {
        "eventId": generate_prefixed_id("evt"),
        "userId": user_id,
        "learningSessionId": learning_session_id,
        "component": component,
        "eventType": event_type,
        "conceptTag": concept_tag,
        "occurredAt": occurred_at or created_at,
        "createdAt": created_at,
        "payload": dict(payload),
    }


def _event_payload_from_diagnostic(document: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "diagnostic_id": document["diagnosticId"],
        "error_type": document["errorType"],
        "concept_tag": document["conceptTag"],
        "explanation_key": document["explanationKey"],
        "line": document["line"],
        "column": document["column"],
        "confidence": document["confidence"],
        "status": document["status"],
        "detection_engine": document["detectionEngine"],
    }

    if document.get("mlProbability") is not None:
        payload["ml_probability"] = document["mlProbability"]
    if document.get("locatorConfidence") is not None:
        payload["locator_confidence"] = document["locatorConfidence"]

    return payload


def build_code_coach_learning_events(
    user_id: str,
    learning_session_id: str,
    sync_result: DiagnosticSyncResult,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for document in sync_result.newly_detected_documents:
        events.append(
            build_learning_event_document(
                user_id,
                learning_session_id,
                component="code_coach",
                event_type="code_diagnostic_detected",
                concept_tag=document["conceptTag"],
                occurred_at=document["createdAt"],
                payload=_event_payload_from_diagnostic(document),
            )
        )

    for document in sync_result.resolved_documents:
        resolved_at = document.get("resolvedAt") or utcnow()
        time_to_fix_seconds = 0
        created_at_for_diagnostic = document.get("createdAt")
        if isinstance(created_at_for_diagnostic, datetime):
            time_to_fix_seconds = max(
                0,
                int((resolved_at - created_at_for_diagnostic).total_seconds()),
            )

        payload = _event_payload_from_diagnostic(document)
        payload["resolved_at"] = resolved_at
        payload["time_to_fix_seconds"] = time_to_fix_seconds

        events.append(
            build_learning_event_document(
                user_id,
                learning_session_id,
                component="code_coach",
                event_type="diagnostic_resolved",
                concept_tag=document["conceptTag"],
                occurred_at=resolved_at,
                payload=payload,
            )
        )

    return events


def _safe_last_seen(document: dict[str, Any]) -> datetime:
    candidate = document.get("resolvedAt") or document.get("createdAt")
    if isinstance(candidate, datetime):
        return candidate
    return datetime.now(timezone.utc)


def build_diagnostic_summary(
    user_id: str,
    diagnostics: Iterable[dict[str, Any]],
    *,
    limit: int = 5,
) -> DiagnosticSummaryResponse:
    diagnostic_list = list(diagnostics)
    error_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "active_count": 0,
            "last_seen_at": datetime.min.replace(tzinfo=timezone.utc),
        },
    )
    concept_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "repeat_count": 0,
            "unresolved_count": 0,
            "last_seen_at": datetime.min.replace(tzinfo=timezone.utc),
        },
    )

    for document in diagnostic_list:
        last_seen_at = _safe_last_seen(document)

        error_bucket = error_stats[document["errorType"]]
        error_bucket["count"] += 1
        if document.get("status") == "active":
            error_bucket["active_count"] += 1
        error_bucket["last_seen_at"] = max(error_bucket["last_seen_at"], last_seen_at)

        concept_bucket = concept_stats[document["conceptTag"]]
        concept_bucket["repeat_count"] += 1
        if document.get("status") == "active":
            concept_bucket["unresolved_count"] += 1
        concept_bucket["last_seen_at"] = max(concept_bucket["last_seen_at"], last_seen_at)

    top_error_types = sorted(
        (
            ErrorTypeSummaryView(
                error_type=error_type,
                count=values["count"],
                active_count=values["active_count"],
                last_seen_at=values["last_seen_at"],
            )
            for error_type, values in error_stats.items()
        ),
        key=lambda item: (item.count, item.active_count, item.last_seen_at),
        reverse=True,
    )[:limit]

    top_concepts = sorted(
        (
            ConceptSummaryView(
                concept_tag=concept_tag,
                repeat_count=values["repeat_count"],
                unresolved_count=values["unresolved_count"],
                last_seen_at=values["last_seen_at"],
            )
            for concept_tag, values in concept_stats.items()
        ),
        key=lambda item: (item.repeat_count, item.unresolved_count, item.last_seen_at),
        reverse=True,
    )[:limit]

    return DiagnosticSummaryResponse(
        status="ok",
        user_id=user_id,
        total_diagnostics=len(diagnostic_list),
        top_error_types=top_error_types,
        top_concepts=top_concepts,
    )


def _calculate_struggle_score(
    *,
    repeat_count: int,
    active_count: int,
    unique_learning_sessions: int,
) -> float:
    score = 0.0
    score += min(0.45, repeat_count * 0.18)
    score += min(0.35, active_count * 0.18)
    score += min(0.12, max(0, unique_learning_sessions - 1) * 0.06)
    if repeat_count >= 3:
        score += 0.08
    if active_count >= 2:
        score += 0.08
    return round(min(0.99, score), 2)


def _struggle_level_for_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _recommended_action_for_level(level: str) -> str:
    if level == "high":
        return "trigger_study_guider"
    if level == "medium":
        return "assign_targeted_practice"
    return "monitor"


def build_concept_struggles(
    user_id: str,
    diagnostics: Iterable[dict[str, Any]],
    *,
    limit: int = 10,
) -> ConceptStruggleResponse:
    diagnostic_list = list(diagnostics)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for document in diagnostic_list:
        grouped[document["conceptTag"]].append(document)

    struggles: list[ConceptStruggleView] = []

    for concept_tag, concept_documents in grouped.items():
        repeat_count = len(concept_documents)
        active_count = sum(1 for item in concept_documents if item.get("status") == "active")
        resolved_count = sum(1 for item in concept_documents if item.get("status") == "resolved")
        unique_learning_sessions = len(
            {item["learningSessionId"] for item in concept_documents if item.get("learningSessionId")}
        )
        last_seen_at = max(_safe_last_seen(item) for item in concept_documents)
        dominant_error_type = Counter(
            item["errorType"] for item in concept_documents
        ).most_common(1)[0][0]

        struggle_score = _calculate_struggle_score(
            repeat_count=repeat_count,
            active_count=active_count,
            unique_learning_sessions=unique_learning_sessions,
        )
        struggle_level = _struggle_level_for_score(struggle_score)

        struggles.append(
            ConceptStruggleView(
                concept_tag=concept_tag,
                error_type=dominant_error_type,
                repeat_count=repeat_count,
                active_count=active_count,
                resolved_count=resolved_count,
                unique_learning_sessions=unique_learning_sessions,
                last_seen_at=last_seen_at,
                struggle_score=struggle_score,
                struggle_level=struggle_level,
                recommended_action=_recommended_action_for_level(struggle_level),
            )
        )

    struggles.sort(
        key=lambda item: (
            item.struggle_score,
            item.repeat_count,
            item.active_count,
            item.last_seen_at,
        ),
        reverse=True,
    )

    return ConceptStruggleResponse(
        status="ok",
        user_id=user_id,
        total_concepts=len(struggles),
        struggles=struggles[:limit],
    )
