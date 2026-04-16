from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.dependencies import AuthContext, get_current_auth, get_storage
from app.learning_signal_service import (
    build_concept_struggles,
    build_diagnostic_summary,
)
from app.models import ConceptStruggleResponse, DiagnosticSummaryResponse

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
    return build_diagnostic_summary(
        auth.user_id,
        diagnostics,
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
    return build_concept_struggles(
        auth.user_id,
        diagnostics,
        limit=limit,
    )
