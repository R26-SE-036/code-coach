from __future__ import annotations

from typing import Any

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
    DiagnosticSummaryResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me/diagnostic-summary", response_model=DiagnosticSummaryResponse)
def get_my_diagnostic_summary(
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


@router.get("/me/concept-struggles", response_model=ConceptStruggleResponse)
def get_my_concept_struggles(
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


@router.get("/me/mastery", response_model=ConceptMasteryListResponse)
def get_my_mastery_summary(
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
