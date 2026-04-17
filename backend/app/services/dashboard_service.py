from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.models import (
    ConceptMasteryView,
    ConceptStruggleView,
    DashboardConceptTrendView,
    DashboardCountsView,
    DashboardMasterySummaryView,
    DashboardOverviewResponse,
    DashboardTimelineItemView,
    DashboardTimelineResponse,
)
from app.services.mastery_service import build_concept_mastery_view


def _safe_event_time(document: dict[str, Any]) -> datetime:
    candidate = document.get("occurredAt") or document.get("createdAt")
    if isinstance(candidate, datetime):
        return candidate
    return datetime.now(timezone.utc)


def _timeline_title_and_summary(document: dict[str, Any]) -> tuple[str, str]:
    event_type = document.get("eventType")
    payload = document.get("payload", {})
    concept_tag = document.get("conceptTag") or payload.get("concept_tag")

    if event_type == "code_diagnostic_detected":
        return (
            "Code Coach detected an issue",
            f"{payload.get('error_type', 'Unknown issue')} in {concept_tag or 'this concept'}.",
        )
    if event_type == "diagnostic_resolved":
        return (
            "Issue resolved",
            f"{payload.get('error_type', 'Issue')} was resolved after {payload.get('time_to_fix_seconds', 0)} second(s).",
        )
    if event_type == "hint_shown":
        return (
            "Hint shown",
            f"A {payload.get('hint_level', 'concept')} hint was shown for {concept_tag or 'the current concept'}.",
        )
    if event_type == "struggle_signal_created":
        return (
            "Struggle signal created",
            f"{concept_tag or 'A concept'} escalated to {payload.get('struggle_level', 'high')} struggle.",
        )
    if event_type == "micro_lesson_viewed":
        return (
            "Micro-lesson opened",
            f"The lesson {payload.get('lesson_id', 'lesson')} was opened for {concept_tag or 'the current concept'}.",
        )
    if event_type == "quiz_completed":
        return (
            "Quiz completed",
            f"Quiz {payload.get('quiz_id', 'quiz')} finished with {payload.get('score_percent', 0)}%.",
        )
    if event_type == "mastery_updated":
        return (
            "Mastery updated",
            f"{concept_tag or 'A concept'} mastery is now {payload.get('mastery_score', 0)}.",
        )
    if event_type == "game_adaptation_decision_created":
        return (
            "Game assigned",
            f"{payload.get('assigned_game_type', 'game')} assigned at {payload.get('assigned_difficulty', 'beginner')} difficulty.",
        )
    if event_type == "game_session_completed":
        return (
            "Game completed",
            f"{payload.get('game_type', 'game')} finished with {payload.get('score_percent', 0)}%.",
        )
    if event_type == "pair_session_started":
        return (
            "Pair session started",
            f"Pair programming session started for task {payload.get('task_id', 'current task')}.",
        )
    if event_type == "collaboration_prompt_shown":
        return (
            "Collaboration prompt shown",
            f"{payload.get('prompt_type', 'prompt')} shown for {concept_tag or 'the current concept'}.",
        )
    if event_type == "peer_review_submitted":
        return (
            "Peer review submitted",
            f"Peer review recorded with rubric score {payload.get('rubric_score', '-')}.",
        )

    return (
        event_type.replace("_", " ").title() if event_type else "Learning event",
        f"Activity recorded for {concept_tag or 'the user'}.",
    )


def build_dashboard_timeline(
    user_id: str,
    learning_events: list[dict[str, Any]],
    *,
    limit: int = 20,
) -> DashboardTimelineResponse:
    sorted_events = sorted(
        learning_events,
        key=_safe_event_time,
        reverse=True,
    )
    items = [
        DashboardTimelineItemView(
            event_id=document["eventId"],
            component=document["component"],
            event_type=document["eventType"],
            title=_timeline_title_and_summary(document)[0],
            summary=_timeline_title_and_summary(document)[1],
            concept_tag=document.get("conceptTag"),
            occurred_at=_safe_event_time(document),
        )
        for document in sorted_events[:limit]
    ]
    return DashboardTimelineResponse(
        status="ok",
        user_id=user_id,
        total=len(items),
        events=items,
    )


def _recommended_focus(
    *,
    active_count: int,
    struggle_level: str | None,
    mastery_level: str | None,
) -> str:
    if active_count > 0 and struggle_level == "high":
        return "study_guider_and_collaboration"
    if active_count > 0 or struggle_level == "medium":
        return "gamification_and_practice"
    if mastery_level == "at_risk":
        return "targeted_practice"
    if mastery_level == "strong":
        return "reinforcement"
    return "monitor"


def build_dashboard_overview(
    user_id: str,
    diagnostics: list[dict[str, Any]],
    learning_events: list[dict[str, Any]],
    mastery_documents: list[dict[str, Any]],
    remediation_triggers: list[dict[str, Any]],
    concept_struggles: list[ConceptStruggleView],
    *,
    concept_limit: int = 6,
    timeline_limit: int = 12,
    total_hint_events: int = 0,
) -> DashboardOverviewResponse:
    mastery_views = [build_concept_mastery_view(document) for document in mastery_documents]
    mastery_by_concept: dict[str, ConceptMasteryView] = {
        item.concept_tag: item for item in mastery_views
    }
    struggle_by_concept = {item.concept_tag: item for item in concept_struggles}
    concept_tags = set(struggle_by_concept.keys()) | set(mastery_by_concept.keys())

    concept_trends: list[DashboardConceptTrendView] = []
    for concept_tag in concept_tags:
        struggle = struggle_by_concept.get(concept_tag)
        mastery = mastery_by_concept.get(concept_tag)
        last_activity_at = max(
            [
                candidate
                for candidate in [
                    struggle.last_seen_at if struggle is not None else None,
                    mastery.last_updated_at if mastery is not None else None,
                ]
                if candidate is not None
            ],
            default=datetime.now(timezone.utc),
        )
        concept_trends.append(
            DashboardConceptTrendView(
                concept_tag=concept_tag,
                repeat_count=struggle.repeat_count if struggle is not None else 0,
                active_count=struggle.active_count if struggle is not None else 0,
                struggle_level=struggle.struggle_level if struggle is not None else None,
                mastery_level=mastery.mastery_level if mastery is not None else None,
                mastery_score=mastery.mastery_score if mastery is not None else None,
                hint_dependency_level=struggle.hint_dependency_level if struggle is not None else None,
                last_activity_at=last_activity_at,
                recommended_focus=_recommended_focus(
                    active_count=struggle.active_count if struggle is not None else 0,
                    struggle_level=struggle.struggle_level if struggle is not None else None,
                    mastery_level=mastery.mastery_level if mastery is not None else None,
                ),
            )
        )

    concept_trends.sort(
        key=lambda item: (
            item.active_count,
            1 if item.struggle_level == "high" else 0,
            item.last_activity_at,
        ),
        reverse=True,
    )

    event_counts = Counter(document["eventType"] for document in learning_events)
    mastery_levels = Counter(item.mastery_level for item in mastery_views)
    timeline = build_dashboard_timeline(
        user_id,
        learning_events,
        limit=timeline_limit,
    )

    return DashboardOverviewResponse(
        status="ok",
        user_id=user_id,
        counts=DashboardCountsView(
            total_diagnostics=len(diagnostics),
            active_diagnostics=sum(1 for item in diagnostics if item.get("status") == "active"),
            resolved_diagnostics=sum(1 for item in diagnostics if item.get("status") == "resolved"),
            total_hint_events=total_hint_events,
            active_remediation_triggers=sum(
                1 for item in remediation_triggers if item.get("status") == "active"
            ),
            completed_remediation_triggers=sum(
                1 for item in remediation_triggers if item.get("status") == "completed"
            ),
            total_game_sessions=event_counts.get("game_session_completed", 0),
            total_pair_sessions=event_counts.get("pair_session_started", 0),
            total_peer_reviews=event_counts.get("peer_review_submitted", 0),
            total_lessons_viewed=event_counts.get("micro_lesson_viewed", 0),
            total_quizzes_completed=event_counts.get("quiz_completed", 0),
        ),
        mastery=DashboardMasterySummaryView(
            total_concepts=len(mastery_views),
            strong_count=mastery_levels.get("strong", 0),
            developing_count=mastery_levels.get("developing", 0),
            at_risk_count=mastery_levels.get("at_risk", 0),
        ),
        concept_trends=concept_trends[:concept_limit],
        recent_timeline=timeline.events,
    )
