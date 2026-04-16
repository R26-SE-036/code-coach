from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import (
    CollaborationActionResponse,
    CollaborationPromptListResponse,
    CollaborationPromptShownRequest,
    CollaborationSessionCreateRequest,
    CollaborationSessionCreateResponse,
    PeerReviewSubmittedRequest,
)
from app.services.collaboration_service import (
    build_collaboration_prompts,
    build_collaboration_session_view,
    create_collaboration_session_document,
    record_collaboration_prompt_shown,
    record_pair_session_started,
    record_peer_review_submitted,
)
from app.services.learning_signal_service import build_concept_struggles

router = APIRouter(prefix="/api/v1/collaboration", tags=["collaboration"])


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


def _get_owned_collaboration_session_or_404(
    storage: Any,
    *,
    user_id: str,
    pair_session_id: str,
) -> dict[str, Any]:
    collaboration_session = storage.find_collaboration_session_by_id(pair_session_id)
    if collaboration_session is None or collaboration_session.get("userId") != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaboration session not found.",
        )
    return collaboration_session


def _validate_linked_diagnostic(
    storage: Any,
    *,
    user_id: str,
    linked_diagnostic_id: str | None,
    linked_learning_session_id: str | None,
) -> dict[str, Any] | None:
    if linked_learning_session_id:
        _get_owned_learning_session_or_404(
            storage,
            user_id=user_id,
            learning_session_id=linked_learning_session_id,
        )

    if not linked_diagnostic_id:
        return None

    diagnostic = storage.find_diagnostic_by_id(user_id, linked_diagnostic_id)
    if diagnostic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked diagnostic not found.",
        )
    if (
        linked_learning_session_id is not None
        and diagnostic.get("learningSessionId") != linked_learning_session_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Linked diagnostic does not belong to the provided learning session.",
        )
    return diagnostic


@router.get("/me/prompts", response_model=CollaborationPromptListResponse)
def get_my_collaboration_prompts(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=10, ge=1, le=25),
    sample_size: int = Query(default=200, ge=1, le=1000),
) -> CollaborationPromptListResponse:
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
    return build_collaboration_prompts(
        diagnostics,
        struggle_response.struggles,
        mastery_documents,
        limit=limit,
    )


@router.post("/me/pair-sessions", response_model=CollaborationSessionCreateResponse)
def create_my_pair_session(
    payload: CollaborationSessionCreateRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> CollaborationSessionCreateResponse:
    _get_owned_learning_session_or_404(
        storage,
        user_id=auth.user_id,
        learning_session_id=payload.learning_session_id,
    )
    if payload.linked_learning_session_id:
        _get_owned_learning_session_or_404(
            storage,
            user_id=auth.user_id,
            learning_session_id=payload.linked_learning_session_id,
        )

    session_document = create_collaboration_session_document(
        auth.user_id,
        payload.learning_session_id,
        collaboration_mode=payload.collaboration_mode,
        partner_user_id=payload.partner_user_id,
        task_id=payload.task_id,
        linked_learning_session_id=payload.linked_learning_session_id,
    )
    stored_session, events = record_pair_session_started(
        storage,
        session_document=session_document,
    )
    return CollaborationSessionCreateResponse(
        status="ok",
        message="Pair collaboration session created.",
        session=build_collaboration_session_view(stored_session),
        created_event_types=[event["eventType"] for event in events],
    )


@router.post("/me/prompts/shown", response_model=CollaborationActionResponse)
def mark_my_collaboration_prompt_shown(
    payload: CollaborationPromptShownRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> CollaborationActionResponse:
    _get_owned_learning_session_or_404(
        storage,
        user_id=auth.user_id,
        learning_session_id=payload.learning_session_id,
    )
    collaboration_session = _get_owned_collaboration_session_or_404(
        storage,
        user_id=auth.user_id,
        pair_session_id=payload.pair_session_id,
    )
    _validate_linked_diagnostic(
        storage,
        user_id=auth.user_id,
        linked_diagnostic_id=payload.linked_diagnostic_id,
        linked_learning_session_id=payload.linked_learning_session_id,
    )

    events = record_collaboration_prompt_shown(
        storage,
        session_document=collaboration_session,
        prompt_id=payload.prompt_id,
        prompt_type=payload.prompt_type,
        concept_tag=payload.concept_tag,
        linked_diagnostic_id=payload.linked_diagnostic_id,
        linked_learning_session_id=payload.linked_learning_session_id,
        target_role=payload.target_role,
        occurred_at=payload.occurred_at,
    )
    return CollaborationActionResponse(
        status="ok",
        message="Collaboration prompt display recorded.",
        pair_session_id=payload.pair_session_id,
        created_event_types=[event["eventType"] for event in events],
    )


@router.post("/me/peer-reviews", response_model=CollaborationActionResponse)
def submit_my_peer_review(
    payload: PeerReviewSubmittedRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> CollaborationActionResponse:
    _get_owned_learning_session_or_404(
        storage,
        user_id=auth.user_id,
        learning_session_id=payload.learning_session_id,
    )
    collaboration_session = _get_owned_collaboration_session_or_404(
        storage,
        user_id=auth.user_id,
        pair_session_id=payload.pair_session_id,
    )
    _validate_linked_diagnostic(
        storage,
        user_id=auth.user_id,
        linked_diagnostic_id=payload.linked_diagnostic_id,
        linked_learning_session_id=payload.linked_learning_session_id,
    )

    events = record_peer_review_submitted(
        storage,
        session_document=collaboration_session,
        concept_tag=payload.concept_tag,
        linked_diagnostic_id=payload.linked_diagnostic_id,
        linked_learning_session_id=payload.linked_learning_session_id,
        rubric_score=payload.rubric_score,
        feedback_quality_score=payload.feedback_quality_score,
        review_comment=payload.review_comment,
        occurred_at=payload.occurred_at,
    )
    return CollaborationActionResponse(
        status="ok",
        message="Peer review submission recorded.",
        pair_session_id=payload.pair_session_id,
        created_event_types=[event["eventType"] for event in events],
    )
