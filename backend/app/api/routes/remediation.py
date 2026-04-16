from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import (
    LessonOpenedRequest,
    QuizCompletedRequest,
    RemediationActionResponse,
    RemediationTriggerListResponse,
    RemediationTriggerView,
    StudyGuiderRecommendationListResponse,
)
from app.services.remediation_service import (
    record_micro_lesson_opened,
    record_quiz_completed,
)
from app.services.study_guider_service import build_study_guider_recommendations

router = APIRouter(prefix="/api/v1/remediation", tags=["remediation"])


def _serialize_trigger(document: dict[str, Any]) -> RemediationTriggerView:
    return RemediationTriggerView(
        trigger_id=document["triggerId"],
        user_id=document["userId"],
        learning_session_id=document["learningSessionId"],
        trigger_source=document["triggerSource"],
        concept_tag=document["conceptTag"],
        error_type=document["errorType"],
        reason=document["reason"],
        struggle_level=document["struggleLevel"],
        recommended_action=document["recommendedAction"],
        repeat_count=document["repeatCount"],
        active_count=document["activeCount"],
        resolved_count=document["resolvedCount"],
        unique_learning_sessions=document["uniqueLearningSessions"],
        struggle_score=document["struggleScore"],
        hint_dependency_score=document.get("hintDependencyScore", 0.0),
        hint_dependency_level=document.get("hintDependencyLevel", "low"),
        status=document["status"],
        intervention_status=document.get("interventionStatus", "pending"),
        lesson_id=document.get("lessonId"),
        lesson_opened_at=document.get("lessonOpenedAt"),
        quiz_id=document.get("quizId"),
        quiz_completed_at=document.get("quizCompletedAt"),
        quiz_score_percent=document.get("quizScorePercent"),
        quiz_passed=document.get("quizPassed"),
        created_at=document["createdAt"],
        updated_at=document["updatedAt"],
        resolved_at=document.get("resolvedAt"),
    )


def _get_owned_trigger_or_404(
    storage: Any,
    *,
    user_id: str,
    trigger_id: str,
) -> dict[str, Any]:
    trigger_document = storage.find_remediation_trigger_by_id(trigger_id)
    if trigger_document is None or trigger_document.get("userId") != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remediation trigger not found.",
        )
    return trigger_document


@router.get("/me/triggers", response_model=RemediationTriggerListResponse)
def get_my_remediation_triggers(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    status: Optional[str] = Query(default=None),
    trigger_source: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> RemediationTriggerListResponse:
    documents = storage.list_remediation_triggers_for_user(
        auth.user_id,
        status=status,
        trigger_source=trigger_source,
        limit=limit,
    )
    triggers = [_serialize_trigger(document) for document in documents]
    return RemediationTriggerListResponse(
        status="ok",
        message="Remediation triggers loaded for the authenticated user.",
        total=len(triggers),
        triggers=triggers,
    )


@router.get(
    "/me/recommendations",
    response_model=StudyGuiderRecommendationListResponse,
)
def get_my_study_guider_recommendations(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=50, ge=1, le=200),
) -> StudyGuiderRecommendationListResponse:
    documents = storage.list_remediation_triggers_for_user(
        auth.user_id,
        status="active",
        trigger_source="code_coach",
        limit=limit,
    )
    return build_study_guider_recommendations(documents)


@router.post(
    "/me/triggers/{trigger_id}/lesson-opened",
    response_model=RemediationActionResponse,
)
def mark_lesson_opened(
    trigger_id: str,
    payload: LessonOpenedRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> RemediationActionResponse:
    trigger_document = _get_owned_trigger_or_404(
        storage,
        user_id=auth.user_id,
        trigger_id=trigger_id,
    )
    if trigger_document.get("status") == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The remediation trigger is already completed.",
        )

    updated_trigger, events = record_micro_lesson_opened(
        storage,
        trigger_document=trigger_document,
        lesson_id=payload.lesson_id,
        occurred_at=payload.occurred_at,
    )
    return RemediationActionResponse(
        status="ok",
        message="Micro-lesson opening recorded.",
        trigger=_serialize_trigger(updated_trigger),
        created_event_types=[event["eventType"] for event in events],
    )


@router.post(
    "/me/triggers/{trigger_id}/quiz-completed",
    response_model=RemediationActionResponse,
)
def mark_quiz_completed(
    trigger_id: str,
    payload: QuizCompletedRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> RemediationActionResponse:
    trigger_document = _get_owned_trigger_or_404(
        storage,
        user_id=auth.user_id,
        trigger_id=trigger_id,
    )
    if trigger_document.get("status") == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The remediation trigger is already completed.",
        )

    passed = payload.passed if payload.passed is not None else payload.score_percent >= 70
    updated_trigger, events = record_quiz_completed(
        storage,
        trigger_document=trigger_document,
        quiz_id=payload.quiz_id,
        score_percent=payload.score_percent,
        passed=passed,
        occurred_at=payload.occurred_at,
    )
    return RemediationActionResponse(
        status="ok",
        message="Quiz completion recorded.",
        trigger=_serialize_trigger(updated_trigger),
        created_event_types=[event["eventType"] for event in events],
    )
