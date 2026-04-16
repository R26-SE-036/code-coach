from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.code_coach_service import (
    build_analyze_response,
    build_diagnostic_records,
    run_analysis,
)
from app.dependencies import AuthContext, get_current_auth, get_storage
from app.evaluation_logger import log_analysis_event
from app.learning_signal_service import build_code_coach_learning_events
from app.models import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/api/v1/code-coach", tags=["code-coach"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_for_authenticated_user(
    payload: AnalyzeRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> AnalyzeResponse:
    learning_session_id = payload.resolved_session_id
    if not learning_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="learning_session_id is required for authenticated analysis.",
        )

    learning_session = storage.find_learning_session_by_id(learning_session_id)
    if learning_session is None or learning_session.get("userId") != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning session not found.",
        )

    if learning_session.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The learning session is not active.",
        )

    diagnostics, analysis_duration_ms = run_analysis(payload)
    diagnostic_documents = build_diagnostic_records(
        auth.user_id,
        learning_session_id,
        diagnostics,
    )
    sync_result = storage.sync_code_diagnostics(
        auth.user_id,
        learning_session_id,
        diagnostic_documents,
    )
    learning_events = build_code_coach_learning_events(
        auth.user_id,
        learning_session_id,
        sync_result,
    )
    if learning_events:
        storage.create_learning_events(learning_events)
    storage.touch_learning_session(learning_session_id)
    log_analysis_event(
        payload,
        diagnostics,
        user_id=auth.user_id,
        learning_session_id=learning_session_id,
    )

    return build_analyze_response(
        diagnostics,
        analysis_duration_ms,
        learning_session_id=learning_session_id,
    )
