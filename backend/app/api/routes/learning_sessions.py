from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.routes.diagnostics import _serialize_persisted_diagnostic
from app.core.common import generate_prefixed_id, utcnow
from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import (
    DiagnosticListResponse,
    LearningSessionCreateRequest,
    LearningSessionResponse,
)

router = APIRouter(prefix="/api/v1/learning-sessions", tags=["learning-sessions"])


def _normalize_source_component(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _serialize_learning_session(
    document: dict[str, Any],
    *,
    message: str,
    reused_existing: bool,
) -> LearningSessionResponse:
    return LearningSessionResponse(
        status="ok",
        message=message,
        learning_session_id=document["learningSessionId"],
        user_id=document["userId"],
        source_component=document["sourceComponent"],
        language=document["language"],
        task_id=document.get("taskId"),
        learning_session_status=document["status"],
        started_at=document["startedAt"],
        last_analysis_at=document.get("lastAnalysisAt"),
        reused_existing=reused_existing,
    )


@router.post("", response_model=LearningSessionResponse)
def create_or_resume_learning_session(
    payload: LearningSessionCreateRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> LearningSessionResponse:
    source_component = _normalize_source_component(payload.source_component)
    task_id = payload.task_id.strip() if payload.task_id else None
    language = payload.language.strip().lower()

    existing = storage.find_active_learning_session(
        auth.user_id,
        source_component,
        task_id=task_id,
    )
    if existing is not None and existing.get("language") == language:
        return _serialize_learning_session(
            existing,
            message="Reused the active learning session.",
            reused_existing=True,
        )

    started_at = utcnow()
    session_document = {
        "learningSessionId": generate_prefixed_id("ls"),
        "userId": auth.user_id,
        "sourceComponent": source_component,
        "taskId": task_id,
        "language": language,
        "status": "active",
        "startedAt": started_at,
        "lastAnalysisAt": None,
    }
    storage.create_learning_session(session_document)

    return _serialize_learning_session(
        session_document,
        message="Created a new learning session.",
        reused_existing=False,
    )


@router.get("/{learning_session_id}", response_model=LearningSessionResponse)
def get_learning_session(
    learning_session_id: str,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> LearningSessionResponse:
    session_document = storage.find_learning_session_by_id(learning_session_id)

    if session_document is None or session_document.get("userId") != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found.",
        )

    return _serialize_learning_session(
        session_document,
        message="Learning session loaded.",
        reused_existing=False,
    )


@router.get("/{learning_session_id}/diagnostics", response_model=DiagnosticListResponse)
def get_learning_session_diagnostics(
    learning_session_id: str,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> DiagnosticListResponse:
    session_document = storage.find_learning_session_by_id(learning_session_id)

    if session_document is None or session_document.get("userId") != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found.",
        )

    documents = storage.list_diagnostics_for_session(
        learning_session_id,
        user_id=auth.user_id,
    )
    diagnostics = [_serialize_persisted_diagnostic(document) for document in documents]
    return DiagnosticListResponse(
        status="ok",
        message="Diagnostics loaded for the learning session.",
        total=len(diagnostics),
        diagnostics=diagnostics,
    )
