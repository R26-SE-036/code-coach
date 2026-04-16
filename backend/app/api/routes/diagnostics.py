from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import DiagnosticListResponse, PersistedDiagnosticView

router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])


def _serialize_persisted_diagnostic(document: dict[str, Any]) -> PersistedDiagnosticView:
    return PersistedDiagnosticView(
        diagnostic_record_id=document["diagnosticRecordId"],
        diagnostic_id=document["diagnosticId"],
        user_id=document["userId"],
        learning_session_id=document["learningSessionId"],
        error_type=document["errorType"],
        concept_tag=document["conceptTag"],
        explanation_key=document["explanationKey"],
        line=document["line"],
        column=document["column"],
        severity=document["severity"],
        confidence=document["confidence"],
        ml_probability=document.get("mlProbability"),
        locator_confidence=document.get("locatorConfidence"),
        detection_engine=document["detectionEngine"],
        status=document["status"],
        code_context_hash=document["codeContextHash"],
        created_at=document["createdAt"],
        resolved_at=document.get("resolvedAt"),
    )


@router.get("/me", response_model=DiagnosticListResponse)
def get_my_diagnostics(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    learning_session_id: Optional[str] = Query(default=None),
    error_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> DiagnosticListResponse:
    documents = storage.list_diagnostics_for_user(
        auth.user_id,
        learning_session_id=learning_session_id,
        error_type=error_type,
        status=status,
        limit=limit,
    )
    diagnostics = [_serialize_persisted_diagnostic(document) for document in documents]
    return DiagnosticListResponse(
        status="ok",
        message="Diagnostics loaded for the authenticated user.",
        total=len(diagnostics),
        diagnostics=diagnostics,
    )
