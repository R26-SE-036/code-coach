from __future__ import annotations

from typing import Any

from app.core.common import generate_prefixed_id, utcnow
from app.services.learning_signal_service import (
    build_concept_struggles,
    build_learning_event_document,
)
from app.services.mastery_service import build_concept_mastery_document


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
        "interventionStatus": "pending",
        "lessonId": None,
        "lessonOpenedAt": None,
        "quizId": None,
        "quizCompletedAt": None,
        "quizScorePercent": None,
        "quizPassed": None,
        "createdAt": now,
        "updatedAt": now,
        "resolvedAt": None,
    }


def _mastery_scores_for_quiz(score_percent: int, passed: bool) -> tuple[float, float]:
    mastery_score = round(score_percent / 100, 2)
    if passed:
        struggle_score = round(max(0.0, 1 - mastery_score), 2)
    else:
        struggle_score = round(min(0.99, max(0.45, 1 - mastery_score + 0.1)), 2)
    return mastery_score, struggle_score


def record_micro_lesson_opened(
    storage: Any,
    *,
    trigger_document: dict[str, Any],
    lesson_id: str,
    occurred_at=None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    event_time = occurred_at or utcnow()
    updated_trigger = storage.update_remediation_trigger(
        trigger_document["triggerId"],
        {
            "lessonId": lesson_id,
            "lessonOpenedAt": event_time,
            "interventionStatus": "lesson_opened",
            "updatedAt": utcnow(),
        },
    )
    if updated_trigger is None:
        raise ValueError("Remediation trigger not found for lesson update.")

    event = build_learning_event_document(
        trigger_document["userId"],
        trigger_document["learningSessionId"],
        component="study_guider",
        event_type="micro_lesson_viewed",
        concept_tag=trigger_document["conceptTag"],
        occurred_at=event_time,
        payload={
            "trigger_id": trigger_document["triggerId"],
            "trigger_source": trigger_document["triggerSource"],
            "lesson_id": lesson_id,
            "concept_tag": trigger_document["conceptTag"],
            "error_type": trigger_document["errorType"],
        },
    )
    storage.create_learning_events([event])
    return updated_trigger, [event]


def record_quiz_completed(
    storage: Any,
    *,
    trigger_document: dict[str, Any],
    quiz_id: str,
    score_percent: int,
    passed: bool,
    occurred_at=None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    event_time = occurred_at or utcnow()
    mastery_score, struggle_score = _mastery_scores_for_quiz(score_percent, passed)
    mastery_document = build_concept_mastery_document(
        trigger_document["userId"],
        trigger_document["learningSessionId"],
        concept_tag=trigger_document["conceptTag"],
        error_type=trigger_document["errorType"],
        trigger_id=trigger_document["triggerId"],
        mastery_score=mastery_score,
        struggle_score=struggle_score,
        update_source="quiz_completed",
        quiz_id=quiz_id,
        score_percent=score_percent,
        passed=passed,
        occurred_at=event_time,
    )
    updates = {
        "quizId": quiz_id,
        "quizCompletedAt": event_time,
        "quizScorePercent": score_percent,
        "quizPassed": passed,
        "interventionStatus": "quiz_completed_passed" if passed else "quiz_completed_failed",
        "updatedAt": utcnow(),
    }
    if passed:
        updates["status"] = "completed"
        updates["resolvedAt"] = event_time

    updated_trigger = storage.update_remediation_trigger(
        trigger_document["triggerId"],
        updates,
    )
    if updated_trigger is None:
        raise ValueError("Remediation trigger not found for quiz update.")

    quiz_event = build_learning_event_document(
        trigger_document["userId"],
        trigger_document["learningSessionId"],
        component="study_guider",
        event_type="quiz_completed",
        concept_tag=trigger_document["conceptTag"],
        occurred_at=event_time,
        payload={
            "trigger_id": trigger_document["triggerId"],
            "trigger_source": trigger_document["triggerSource"],
            "quiz_id": quiz_id,
            "score_percent": score_percent,
            "passed": passed,
            "concept_tag": trigger_document["conceptTag"],
            "error_type": trigger_document["errorType"],
        },
    )
    mastery_event = build_learning_event_document(
        trigger_document["userId"],
        trigger_document["learningSessionId"],
        component="study_guider",
        event_type="mastery_updated",
        concept_tag=trigger_document["conceptTag"],
        occurred_at=event_time,
        payload={
            "trigger_id": trigger_document["triggerId"],
            "trigger_source": trigger_document["triggerSource"],
            "concept_tag": trigger_document["conceptTag"],
            "mastery_score": mastery_score,
            "struggle_score": struggle_score,
            "update_source": "quiz_completed",
            "quiz_id": quiz_id,
            "score_percent": score_percent,
            "passed": passed,
        },
    )
    storage.upsert_concept_mastery(mastery_document)
    storage.create_learning_events([quiz_event, mastery_event])
    return updated_trigger, [quiz_event, mastery_event]


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
