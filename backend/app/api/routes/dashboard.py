from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.cache import TTLCache
from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import DashboardOverviewResponse, DashboardTimelineResponse
from app.services.dashboard_service import build_dashboard_overview, build_dashboard_timeline
from app.services.learning_signal_service import build_concept_struggles, build_diagnostic_summary

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

# These two endpoints are by far the most expensive reads in the service, and
# they are also the most repeated.
#
# Each one fans out to four per-user collection scans. The `limit` on those
# storage calls is applied in Python AFTER the documents arrive, so the database
# bills for every diagnostic, learning event, mastery record and trigger the
# student has ever had - not for the 300 that get kept. A student with a few
# hundred of each therefore costs over a thousand billed reads per call.
#
# That was survivable while only Study Guider's Analytics tab used it. The
# portal's Home page now calls it too, on every sign-in and every return to
# Home, and the free-tier daily read quota did not survive the combination.
#
# Caching the assembled response per student collapses the repeats. Sixty
# seconds is invisible on a dashboard - the numbers are not live telemetry -
# and it turns "every page load" back into "at most once a minute".
#
# This is a mitigation, not the fix. The fix is to push order_by + limit into
# the database queries so the database returns 300 documents instead of all of
# them, which needs a composite index per collection (userId ==, createdAt
# desc) created on the collection.
_OVERVIEW_CACHE = TTLCache(ttl_seconds=60.0, max_entries=512)
_TIMELINE_CACHE = TTLCache(ttl_seconds=60.0, max_entries=512)


@router.get("/me/overview", response_model=DashboardOverviewResponse)
def get_my_dashboard_overview(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    concept_limit: int = Query(default=6, ge=1, le=20),
    timeline_limit: int = Query(default=12, ge=1, le=50),
    sample_size: int = Query(default=300, ge=1, le=1000),
) -> DashboardOverviewResponse:
    cache_key = f"{auth.user_id}:{concept_limit}:{timeline_limit}:{sample_size}"
    cached = _OVERVIEW_CACHE.get(cache_key)
    if cached is not None:
        return cached

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
    overview = build_dashboard_overview(
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
    _OVERVIEW_CACHE.set(cache_key, overview)
    return overview


@router.get("/me/timeline", response_model=DashboardTimelineResponse)
def get_my_dashboard_timeline(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    limit: int = Query(default=25, ge=1, le=100),
    sample_size: int = Query(default=300, ge=1, le=1000),
) -> DashboardTimelineResponse:
    cache_key = f"{auth.user_id}:{limit}:{sample_size}"
    cached = _TIMELINE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    learning_events = storage.list_learning_events_for_user(
        auth.user_id,
        limit=sample_size,
    )
    timeline = build_dashboard_timeline(
        auth.user_id,
        learning_events,
        limit=limit,
    )
    _TIMELINE_CACHE.set(cache_key, timeline)
    return timeline
