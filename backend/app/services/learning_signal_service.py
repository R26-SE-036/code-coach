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

HINT_EVENT_TYPES = {
    "hint_shown",
    "hint_level_requested",
    "hint_navigation_used",
}


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


def _safe_event_time(document: dict[str, Any]) -> datetime:
    candidate = document.get("occurredAt") or document.get("createdAt")
    if isinstance(candidate, datetime):
        return candidate
    return datetime.now(timezone.utc)


def _hint_dependency_level_for_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _calculate_hint_dependency_score(
    *,
    repeat_count: int,
    hint_shown_count: int,
    hint_request_count: int,
    hint_navigation_count: int,
) -> float:
    if repeat_count <= 0:
        return 0.0

    weighted_support = (
        hint_shown_count * 1.0
        + hint_request_count * 1.5
        + hint_navigation_count * 1.2
    )
    score = weighted_support / max(4.0, repeat_count * 3.5)
    return round(min(0.99, score), 2)


def _build_hint_usage_by_concept(
    learning_events: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    hint_usage: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "hint_event_count": 0,
            "hint_shown_count": 0,
            "hint_request_count": 0,
            "hint_navigation_count": 0,
            "last_hint_at": None,
        },
    )

    for document in learning_events:
        if document.get("component") != "code_coach":
            continue

        event_type = document.get("eventType")
        if event_type not in HINT_EVENT_TYPES:
            continue

        concept_tag = document.get("conceptTag")
        if not concept_tag:
            continue

        bucket = hint_usage[concept_tag]
        bucket["hint_event_count"] += 1
        if event_type == "hint_shown":
            bucket["hint_shown_count"] += 1
        elif event_type == "hint_level_requested":
            bucket["hint_request_count"] += 1
        elif event_type == "hint_navigation_used":
            bucket["hint_navigation_count"] += 1

        event_time = _safe_event_time(document)
        last_hint_at = bucket["last_hint_at"]
        if last_hint_at is None or event_time > last_hint_at:
            bucket["last_hint_at"] = event_time

    return hint_usage


def build_diagnostic_summary(
    user_id: str,
    diagnostics: Iterable[dict[str, Any]],
    learning_events: Iterable[dict[str, Any]],
    *,
    limit: int = 5,
) -> DiagnosticSummaryResponse:
    diagnostic_list = list(diagnostics)
    hint_usage = _build_hint_usage_by_concept(learning_events)
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
                hint_event_count=hint_usage.get(concept_tag, {}).get("hint_event_count", 0),
                hint_shown_count=hint_usage.get(concept_tag, {}).get("hint_shown_count", 0),
                hint_request_count=hint_usage.get(concept_tag, {}).get("hint_request_count", 0),
                hint_navigation_count=hint_usage.get(concept_tag, {}).get("hint_navigation_count", 0),
                hint_dependency_score=_calculate_hint_dependency_score(
                    repeat_count=values["repeat_count"],
                    hint_shown_count=hint_usage.get(concept_tag, {}).get("hint_shown_count", 0),
                    hint_request_count=hint_usage.get(concept_tag, {}).get("hint_request_count", 0),
                    hint_navigation_count=hint_usage.get(concept_tag, {}).get("hint_navigation_count", 0),
                ),
                hint_dependency_level=_hint_dependency_level_for_score(
                    _calculate_hint_dependency_score(
                        repeat_count=values["repeat_count"],
                        hint_shown_count=hint_usage.get(concept_tag, {}).get("hint_shown_count", 0),
                        hint_request_count=hint_usage.get(concept_tag, {}).get("hint_request_count", 0),
                        hint_navigation_count=hint_usage.get(concept_tag, {}).get("hint_navigation_count", 0),
                    )
                ),
                last_hint_at=hint_usage.get(concept_tag, {}).get("last_hint_at"),
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
        total_hint_events=sum(
            bucket["hint_event_count"] for bucket in hint_usage.values()
        ),
        concepts_with_hint_usage=sum(
            1 for bucket in hint_usage.values() if bucket["hint_event_count"] > 0
        ),
        top_error_types=top_error_types,
        top_concepts=top_concepts,
    )


def _calculate_struggle_score(
    *,
    repeat_count: int,
    active_count: int,
    unique_learning_sessions: int,
    hint_dependency_score: float,
) -> float:
    score = 0.0
    score += min(0.45, repeat_count * 0.18)
    score += min(0.35, active_count * 0.18)
    score += min(0.12, max(0, unique_learning_sessions - 1) * 0.06)
    score += min(0.2, hint_dependency_score * 0.2)
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
    learning_events: Iterable[dict[str, Any]],
    *,
    limit: int = 10,
) -> ConceptStruggleResponse:
    diagnostic_list = list(diagnostics)
    hint_usage = _build_hint_usage_by_concept(learning_events)
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
        concept_hint_usage = hint_usage.get(concept_tag, {})
        hint_dependency_score = _calculate_hint_dependency_score(
            repeat_count=repeat_count,
            hint_shown_count=concept_hint_usage.get("hint_shown_count", 0),
            hint_request_count=concept_hint_usage.get("hint_request_count", 0),
            hint_navigation_count=concept_hint_usage.get("hint_navigation_count", 0),
        )
        hint_dependency_level = _hint_dependency_level_for_score(
            hint_dependency_score,
        )

        struggle_score = _calculate_struggle_score(
            repeat_count=repeat_count,
            active_count=active_count,
            unique_learning_sessions=unique_learning_sessions,
            hint_dependency_score=hint_dependency_score,
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
                hint_event_count=concept_hint_usage.get("hint_event_count", 0),
                hint_shown_count=concept_hint_usage.get("hint_shown_count", 0),
                hint_request_count=concept_hint_usage.get("hint_request_count", 0),
                hint_navigation_count=concept_hint_usage.get("hint_navigation_count", 0),
                hint_dependency_score=hint_dependency_score,
                hint_dependency_level=hint_dependency_level,
                last_hint_at=concept_hint_usage.get("last_hint_at"),
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
