from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.cache import TTLCache
from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import AnalyzeRequest, AnalyzeResponse
from app.services.code_coach_service import (
    build_analyze_response,
    build_diagnostic_records,
    run_analysis,
)
from app.services.evaluation_logger import log_analysis_event
from app.services.learning_signal_service import build_code_coach_learning_events
from app.services.remediation_service import sync_code_coach_remediation_triggers

router = APIRouter(prefix="/api/v1/code-coach", tags=["code-coach"])

logger = logging.getLogger(__name__)

# Learning sessions are validated on every analysis but change rarely; caching
# the ownership/active check removes another database round trip from the
# path the student waits on.
_SESSION_CACHE = TTLCache(ttl_seconds=60.0)


def _persist_analysis(
    storage: Any,
    *,
    user_id: str,
    learning_session_id: str,
    diagnostic_documents: list[dict],
) -> None:
    """All database writes for one analysis.

    Runs AFTER the response is sent (FastAPI background task). The student is
    waiting for underlines, not for persistence: every write here is a
    ~network-round-trip, and together they dominated request latency. Nothing
    in the response depends on their result, and a failure must not break the
    editor experience — so failures are logged, not raised.
    """
    try:
        sync_result = storage.sync_code_diagnostics(
            user_id, learning_session_id, diagnostic_documents,
        )
        learning_events = build_code_coach_learning_events(
            user_id, learning_session_id, sync_result,
        )
        if learning_events:
            storage.create_learning_events(learning_events)
        sync_code_coach_remediation_triggers(
            storage, user_id=user_id, learning_session_id=learning_session_id,
        )
        storage.touch_learning_session(learning_session_id)
    except Exception:
        logger.exception(
            "Background persistence failed for learning session %s",
            learning_session_id,
        )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_for_authenticated_user(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> AnalyzeResponse:
    learning_session_id = payload.resolved_session_id
    if not learning_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="learning_session_id is required for authenticated analysis.",
        )

    session_key = f"{auth.user_id}:{learning_session_id}"
    if _SESSION_CACHE.get(session_key) is None:
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
        _SESSION_CACHE.set(session_key, True)

    # Calls code_coach_service.py — pure computation, no database.
    diagnostics, analysis_duration_ms = run_analysis(payload)
    diagnostic_documents = build_diagnostic_records(
        auth.user_id,
        learning_session_id,
        diagnostics,
    )

    # Everything that touches the database happens after the response is sent.
    background_tasks.add_task(
        _persist_analysis,
        storage,
        user_id=auth.user_id,
        learning_session_id=learning_session_id,
        diagnostic_documents=diagnostic_documents,
    )

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
