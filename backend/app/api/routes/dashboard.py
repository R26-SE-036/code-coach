from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import DashboardOverviewResponse, DashboardTimelineResponse
from app.services.dashboard_service import build_dashboard_overview, build_dashboard_timeline
from app.services.learning_signal_service import build_concept_struggles, build_diagnostic_summary

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/me/overview", response_model=DashboardOverviewResponse)
def get_my_dashboard_overview(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    concept_limit: int = Query(default=6, ge=1, le=20),
    timeline_limit: int = Query(default=12, ge=1, le=50),
    sample_size: int = Query(default=300, ge=1, le=1000),
) -> DashboardOverviewResponse:
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
    remediation_triggers = storage.list_remediation_triggers_for_user(
        auth.user_id,
        limit=sample_size,
    )
    concept_struggles = build_concept_struggles(
        auth.user_id,
        diagnostics,
        learning_events,
        limit=concept_limit,
    ).struggles
    diagnostic_summary = build_diagnostic_summary(
        auth.user_id,
        diagnostics,
        learning_events,
        limit=concept_limit,
    )
    return build_dashboard_overview(
        auth.user_id,
        diagnostics,
        learning_events,
        mastery_documents,
        remediation_triggers,
        concept_struggles,
        concept_limit=concept_limit,
        timeline_limit=timeline_limit,
        total_hint_events=diagnostic_summary.total_hint_events,
    )


@router.get("/me/timeline", response_model=DashboardTimelineResponse)
def get_my_dashboard_timeline(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=25, ge=1, le=100),
    sample_size: int = Query(default=300, ge=1, le=1000),
) -> DashboardTimelineResponse:
    learning_events = storage.list_learning_events_for_user(
        auth.user_id,
        limit=sample_size,
    )
    return build_dashboard_timeline(
        auth.user_id,
        learning_events,
        limit=limit,
    )
