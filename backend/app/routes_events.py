from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import AuthContext, get_current_auth, get_storage
from app.models import LearningEventListResponse, LearningEventView

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
