"""Everything about the authenticated student, under one predictable prefix.

/api/v1/students/me/...  is the read surface downstream components consume:
    diagnostics           the student's persisted error history
    diagnostics/summary   aggregated top error types + hint usage
    struggling-concepts   concepts the student repeatedly gets wrong
    concept-mastery       per-concept mastery scores

`me` always means "the user identified by the bearer token" — services acting
for a student forward the student's own token (see docs/api-integration-guide.md).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.services.learning_signal_service import (
    build_concept_struggles,
    build_diagnostic_summary,
)
from app.services.mastery_service import build_concept_mastery_response
from app.models import (
    ConceptMasteryListResponse,
    ConceptStruggleResponse,
    DiagnosticListResponse,
    DiagnosticSummaryResponse,
    PersistedDiagnosticView,
)

router = APIRouter(prefix="/api/v1/students", tags=["students"])


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


@router.get("/me/diagnostics", response_model=DiagnosticListResponse)
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


@router.get("/me/diagnostics/summary", response_model=DiagnosticSummaryResponse)
def get_my_diagnostics_summary(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=5, ge=1, le=20),
    sample_size: int = Query(default=200, ge=1, le=1000),
) -> DiagnosticSummaryResponse:
    diagnostics = storage.list_diagnostics_for_user(
        auth.user_id,
        limit=sample_size,
    )
    learning_events = storage.list_learning_events_for_user(
        auth.user_id,
        limit=sample_size,
    )
    return build_diagnostic_summary(
        auth.user_id,
        diagnostics,
        learning_events,
        limit=limit,
    )


@router.get("/me/struggling-concepts", response_model=ConceptStruggleResponse)
def get_my_struggling_concepts(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=10, ge=1, le=20),
    sample_size: int = Query(default=200, ge=1, le=1000),
) -> ConceptStruggleResponse:
    diagnostics = storage.list_diagnostics_for_user(
        auth.user_id,
        limit=sample_size,
    )
    learning_events = storage.list_learning_events_for_user(
        auth.user_id,
        limit=sample_size,
    )
    return build_concept_struggles(
        auth.user_id,
        diagnostics,
        learning_events,
        limit=limit,
    )


@router.get("/me/concept-mastery", response_model=ConceptMasteryListResponse)
def get_my_concept_mastery(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=20, ge=1, le=50),
) -> ConceptMasteryListResponse:
    mastery_documents = storage.list_concept_mastery_for_user(
        auth.user_id,
        limit=limit,
    )
    return build_concept_mastery_response(
        auth.user_id,
        mastery_documents,
        limit=limit,
    )
