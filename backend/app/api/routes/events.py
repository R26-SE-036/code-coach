from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import (
    LearningEventCreateRequest,
    LearningEventCreateResponse,
    LearningEventListResponse,
    LearningEventView,
)
from app.services.learning_signal_service import build_learning_event_document
from app.services.remediation_service import sync_code_coach_remediation_triggers

router = APIRouter(prefix="/api/v1/events", tags=["events"])


def _serialize_learning_event(document: dict[str, Any]) -> LearningEventView:
    return LearningEventView(
        event_id=document["eventId"],
        user_id=document["userId"],
        learning_session_id=document["learningSessionId"],
        component=document["component"],
        event_type=document["eventType"],
        concept_tag=document.get("conceptTag"),
        occurred_at=document["occurredAt"],
        created_at=document["createdAt"],
        payload=document["payload"],
    )


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


@router.post("", response_model=LearningEventCreateResponse)
def create_learning_event(
    payload: LearningEventCreateRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> LearningEventCreateResponse:
    learning_session = storage.find_learning_session_by_id(payload.learning_session_id)
    if learning_session is None or learning_session.get("userId") != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found.",
        )

    component = _normalize_token(payload.component)
    event_type = _normalize_token(payload.event_type)
    concept_tag = _normalize_token(payload.concept_tag) if payload.concept_tag else None
    document = build_learning_event_document(
        auth.user_id,
        payload.learning_session_id,
        component=component,
        event_type=event_type,
        concept_tag=concept_tag,
        occurred_at=payload.occurred_at,
        payload=payload.payload,
    )
    storage.create_learning_events([document])
    if component == "code_coach":
        sync_code_coach_remediation_triggers(
            storage,
            user_id=auth.user_id,
            learning_session_id=payload.learning_session_id,
        )
    return LearningEventCreateResponse(
        status="ok",
        message="Learning event recorded.",
        event_id=document["eventId"],
    )


@router.get("/me", response_model=LearningEventListResponse)
def get_my_learning_events(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    learning_session_id: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> LearningEventListResponse:
    documents = storage.list_learning_events_for_user(
        auth.user_id,
        learning_session_id=learning_session_id,
        event_type=event_type,
        limit=limit,
    )
    events = [_serialize_learning_event(document) for document in documents]
    return LearningEventListResponse(
        status="ok",
        message="Learning events loaded for the authenticated user.",
        total=len(events),
        events=events,
    )
