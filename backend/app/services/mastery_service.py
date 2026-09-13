from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from app.core.common import generate_prefixed_id, utcnow
from app.models import ConceptMasteryListResponse, ConceptMasteryView


def _mastery_level_for_score(score: float) -> str:
    if score >= 0.75:
        return "strong"
    if score >= 0.45:
        return "developing"
    return "at_risk"


def build_concept_mastery_document(
    user_id: str,
    learning_session_id: str,
    *,
    concept_tag: str,
    error_type: str | None,
    trigger_id: str | None,
    mastery_score: float,
    struggle_score: float,
    update_source: str,
    quiz_id: str | None = None,
    score_percent: int | None = None,
    passed: bool | None = None,
    source_component: str = "study_guider",
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    created_at = utcnow()
    last_updated_at = occurred_at or created_at
    return {
        "masteryId": generate_prefixed_id("mst"),
        "userId": user_id,
        "conceptTag": concept_tag,
        "masteryScore": mastery_score,
        "struggleScore": struggle_score,
        "masteryLevel": _mastery_level_for_score(mastery_score),
        "updateSource": update_source,
        "sourceComponent": source_component,
        "lastLearningSessionId": learning_session_id,
        "lastErrorType": error_type,
        "lastTriggerId": trigger_id,
        "lastQuizId": quiz_id,
        "lastQuizScorePercent": score_percent,
        "lastQuizPassed": passed,
        "createdAt": created_at,
        "lastUpdatedAt": last_updated_at,
    }


def _safe_last_updated(document: dict[str, Any]) -> datetime:
    candidate = document.get("lastUpdatedAt") or document.get("createdAt")
    if isinstance(candidate, datetime):
        return candidate
    return datetime.now(timezone.utc)


def build_concept_mastery_view(document: dict[str, Any]) -> ConceptMasteryView:
    return ConceptMasteryView(
        concept_tag=document["conceptTag"],
        mastery_score=document["masteryScore"],
        struggle_score=document["struggleScore"],
        mastery_level=document.get("masteryLevel") or _mastery_level_for_score(document["masteryScore"]),
        update_source=document.get("updateSource", "unknown"),
        last_learning_session_id=document["lastLearningSessionId"],
        last_error_type=document.get("lastErrorType"),
        last_trigger_id=document.get("lastTriggerId"),
        last_quiz_id=document.get("lastQuizId"),
        last_quiz_score_percent=document.get("lastQuizScorePercent"),
        last_quiz_passed=document.get("lastQuizPassed"),
        last_game_id=document.get("lastGameId"),
        last_game_type=document.get("lastGameType"),
        last_game_score_percent=document.get("lastGameScorePercent"),
        last_game_difficulty_level=document.get("lastGameDifficultyLevel"),
        last_updated_at=_safe_last_updated(document),
    )


def build_concept_mastery_response(
    user_id: str,
    documents: Iterable[dict[str, Any]],
    *,
    limit: int = 20,
) -> ConceptMasteryListResponse:
    mastery_views = sorted(
        (build_concept_mastery_view(document) for document in documents),
        key=lambda item: (item.struggle_score, item.last_updated_at),
        reverse=True,
    )[:limit]

    return ConceptMasteryListResponse(
        status="ok",
        user_id=user_id,
        total_concepts=len(mastery_views),
        concepts=mastery_views,
    )


def practice_mastery_scores(
    *,
    score_percent: int,
    error_count: int,
    attempt_count: int,
    hint_usage: int,
    passed: bool,
) -> tuple[float, float]:
    """Observed mastery and struggle from one finished practice attempt.

    Moved here from gamification_service, unchanged, when PairPath became the
    second component to report finished attempts. Both use it, so a mastery
    score of 0.6 means the same thing whichever of them wrote it.
    """
    mastery_score = score_percent / 100
    mastery_score -= min(0.2, error_count * 0.05)
    mastery_score -= min(0.12, max(0, attempt_count - 1) * 0.04)
    mastery_score -= min(0.12, hint_usage * 0.03)
    if passed:
        mastery_score += 0.05

    mastery_score = round(max(0.0, min(0.99, mastery_score)), 2)
    if passed:
        struggle_score = round(max(0.0, 1 - mastery_score), 2)
    else:
        struggle_score = round(min(0.99, max(0.35, 1 - mastery_score + 0.08)), 2)
    return mastery_score, struggle_score


def blend_mastery_scores(
    existing_mastery_document: dict[str, Any] | None,
    *,
    mastery_score: float,
    struggle_score: float,
) -> tuple[float, float]:
    """Fold a new observation into the stored scores: 65% history, 35% new."""
    if existing_mastery_document is None:
        return mastery_score, struggle_score

    blended_mastery = round(
        min(
            0.99,
            max(
                0.0,
                existing_mastery_document["masteryScore"] * 0.65 + mastery_score * 0.35,
            ),
        ),
        2,
    )
    blended_struggle = round(
        min(
            0.99,
            max(
                0.0,
                existing_mastery_document["struggleScore"] * 0.65 + struggle_score * 0.35,
            ),
        ),
        2,
    )
    return blended_mastery, blended_struggle
