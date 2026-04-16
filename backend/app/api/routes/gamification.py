from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import (
    GamificationActionResponse,
    GamificationAdaptationDecisionRequest,
    GamificationRecommendationListResponse,
    GamificationSessionCompletedRequest,
)
from app.services.gamification_service import (
    build_gamification_recommendations,
    record_gamification_adaptation_decision,
    record_gamification_session_completed,
)
from app.services.learning_signal_service import build_concept_struggles

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])


def _get_owned_learning_session_or_404(
    storage: Any,
    *,
    user_id: str,
    learning_session_id: str,
) -> dict[str, Any]:
    learning_session = storage.find_learning_session_by_id(learning_session_id)
    if learning_session is None or learning_session.get("userId") != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found.",
        )
    return learning_session


@router.get("/me/recommendations", response_model=GamificationRecommendationListResponse)
def get_my_gamification_recommendations(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=10, ge=1, le=25),
    sample_size: int = Query(default=200, ge=1, le=1000),
) -> GamificationRecommendationListResponse:
    diagnostics = storage.list_diagnostics_for_user(
        auth.user_id,
        limit=sample_size,
    )
    learning_events = storage.list_learning_events_for_user(
        auth.user_id,
        limit=sample_size,
    )
    mastery_documents = storage.list_concept_mastery_for_user(
        auth.user_id,
        limit=sample_size,
    )
    struggle_response = build_concept_struggles(
        auth.user_id,
        diagnostics,
        learning_events,
        limit=limit,
    )
    return build_gamification_recommendations(
        struggle_response.struggles,
        mastery_documents,
        limit=limit,
    )


@router.post("/me/adaptation-decisions", response_model=GamificationActionResponse)
def create_my_gamification_adaptation_decision(
    payload: GamificationAdaptationDecisionRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> GamificationActionResponse:
    _get_owned_learning_session_or_404(
        storage,
        user_id=auth.user_id,
        learning_session_id=payload.learning_session_id,
    )
    events = record_gamification_adaptation_decision(
        storage,
        user_id=auth.user_id,
        learning_session_id=payload.learning_session_id,
        recommendation_id=payload.recommendation_id,
        concept_tag=payload.concept_tag,
        game_id=payload.game_id,
        game_type=payload.game_type,
        difficulty_level=payload.difficulty_level,
        support_level=payload.support_level,
        rationale=payload.rationale,
        based_on_mastery_level=payload.based_on_mastery_level,
        based_on_struggle_level=payload.based_on_struggle_level,
        occurred_at=payload.occurred_at,
    )
    return GamificationActionResponse(
        status="ok",
        message="Gamification adaptation decision recorded.",
        created_event_types=[event["eventType"] for event in events],
        mastery=None,
    )


@router.post("/me/session-results", response_model=GamificationActionResponse)
def create_my_gamification_session_result(
    payload: GamificationSessionCompletedRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> GamificationActionResponse:
    _get_owned_learning_session_or_404(
        storage,
        user_id=auth.user_id,
        learning_session_id=payload.learning_session_id,
    )
    passed = payload.passed if payload.passed is not None else payload.score_percent >= 70
    mastery, events = record_gamification_session_completed(
        storage,
        user_id=auth.user_id,
        learning_session_id=payload.learning_session_id,
        recommendation_id=payload.recommendation_id,
        concept_tag=payload.concept_tag,
        game_id=payload.game_id,
        game_type=payload.game_type,
        difficulty_level=payload.difficulty_level,
        support_level=payload.support_level,
        score_percent=payload.score_percent,
        error_count=payload.error_count,
        attempt_count=payload.attempt_count,
        hint_usage=payload.hint_usage,
        time_taken_seconds=payload.time_taken_seconds,
        passed=passed,
        occurred_at=payload.occurred_at,
    )
    return GamificationActionResponse(
        status="ok",
        message="Gamification session result recorded.",
        created_event_types=[event["eventType"] for event in events],
        mastery=mastery,
    )
