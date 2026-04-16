from __future__ import annotations

from typing import Any

from app.core.common import generate_prefixed_id, utcnow
from app.services.learning_signal_service import (
    build_concept_struggles,
    build_learning_event_document,
)


def _reason_for_struggle(struggle) -> str:
    if (
        struggle.repeat_count >= 3
        and struggle.active_count >= 2
        and struggle.hint_dependency_level in {"medium", "high"}
    ):
        return "repeated_unresolved_errors_with_hint_dependence"
    if struggle.repeat_count >= 3 and struggle.active_count >= 2:
        return "repeated_unresolved_errors"
    if struggle.hint_dependency_level == "high":
        return "high_hint_dependence"
    return "high_concept_struggle"


def build_remediation_trigger_document(
    user_id: str,
    learning_session_id: str,
    *,
    trigger_source: str,
    struggle,
) -> dict[str, Any]:
    now = utcnow()
    return {
        "triggerId": generate_prefixed_id("rt"),
        "userId": user_id,
        "learningSessionId": learning_session_id,
        "triggerSource": trigger_source,
        "conceptTag": struggle.concept_tag,
        "errorType": struggle.error_type,
        "reason": _reason_for_struggle(struggle),
        "struggleLevel": struggle.struggle_level,
        "recommendedAction": struggle.recommended_action,
        "repeatCount": struggle.repeat_count,
        "activeCount": struggle.active_count,
        "resolvedCount": struggle.resolved_count,
        "uniqueLearningSessions": struggle.unique_learning_sessions,
        "struggleScore": struggle.struggle_score,
        "hintDependencyScore": struggle.hint_dependency_score,
        "hintDependencyLevel": struggle.hint_dependency_level,
        "status": "active",
        "createdAt": now,
        "updatedAt": now,
        "resolvedAt": None,
    }


def sync_code_coach_remediation_triggers(
    storage: Any,
    *,
    user_id: str,
    learning_session_id: str,
    sample_size: int = 500,
) -> list[dict[str, Any]]:
    diagnostics = storage.list_diagnostics_for_user(
        user_id,
        limit=sample_size,
    )
    learning_events = storage.list_learning_events_for_user(
        user_id,
        limit=sample_size,
    )
    struggle_response = build_concept_struggles(
        user_id,
        diagnostics,
        learning_events,
        limit=25,
    )

    created_triggers: list[dict[str, Any]] = []
    trigger_events: list[dict[str, Any]] = []

    for struggle in struggle_response.struggles:
        if struggle.recommended_action != "trigger_study_guider":
            continue

        trigger_document = build_remediation_trigger_document(
            user_id,
            learning_session_id,
            trigger_source="code_coach",
            struggle=struggle,
        )
        stored_trigger, created = storage.upsert_remediation_trigger(
            trigger_document,
        )
        if not created:
            continue

        created_triggers.append(stored_trigger)
        trigger_events.append(
            build_learning_event_document(
                user_id,
                learning_session_id,
                component="code_coach",
                event_type="struggle_signal_created",
                concept_tag=struggle.concept_tag,
                payload={
                    "trigger_id": stored_trigger["triggerId"],
                    "trigger_source": "code_coach",
                    "concept_tag": struggle.concept_tag,
                    "error_type": struggle.error_type,
                    "reason": stored_trigger["reason"],
                    "repeat_count": struggle.repeat_count,
                    "active_count": struggle.active_count,
                    "resolved_count": struggle.resolved_count,
                    "unique_learning_sessions": struggle.unique_learning_sessions,
                    "struggle_score": struggle.struggle_score,
                    "struggle_level": struggle.struggle_level,
                    "hint_dependency_score": struggle.hint_dependency_score,
                    "hint_dependency_level": struggle.hint_dependency_level,
                    "recommended_action": struggle.recommended_action,
                },
            )
        )

    if trigger_events:
        storage.create_learning_events(trigger_events)

    return created_triggers
