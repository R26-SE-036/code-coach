from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from app.models import (
    ConceptMasteryView,
    ConceptStruggleView,
    GamificationRecommendationListResponse,
    GamificationRecommendationView,
)
from app.core.common import utcnow
from app.services.learning_signal_service import build_learning_event_document
from app.services.mastery_service import build_concept_mastery_document, build_concept_mastery_view


class GamificationContentItem(BaseModel):
    game_id: str
    game_type: str
    title: str
    estimated_duration_minutes: int
    focus_points: list[str]


EMBEDDED_GAMIFICATION_CONTENT: dict[str, GamificationContentItem] = {
    "array_indexing": GamificationContentItem(
        game_id="game_arrays_bug_hunt_01",
        game_type="bug_hunt",
        title="Array Index Bug Hunt",
        estimated_duration_minutes=8,
        focus_points=[
            "zero-based indexing",
            "last valid index",
            "safe array access",
        ],
    ),
    "loop_boundaries": GamificationContentItem(
        game_id="game_loops_trace_01",
        game_type="loop_tracer",
        title="Loop Boundary Trace",
        estimated_duration_minutes=9,
        focus_points=[
            "loop stopping conditions",
            "off-by-one reasoning",
            "array traversal",
        ],
    ),
    "conditional_logic": GamificationContentItem(
        game_id="game_conditions_fix_01",
        game_type="condition_debug",
        title="Conditional Logic Fix-Up",
        estimated_duration_minutes=7,
        focus_points=[
            "assignment vs comparison",
            "boolean conditions",
            "branch reasoning",
        ],
    ),
}

DEFAULT_GAMIFICATION_CONTENT = GamificationContentItem(
    game_id="game_general_debug_01",
    game_type="debug_challenge",
    title="General Debugging Challenge",
    estimated_duration_minutes=7,
    focus_points=[
        "trace logic",
        "check assumptions",
        "find one focused fix",
    ],
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GAMIFICATION_CONTENT_PATH = PROJECT_ROOT / "knowledge_base" / "gamification_catalog.json"


def _load_gamification_content() -> dict[str, GamificationContentItem]:
    if not GAMIFICATION_CONTENT_PATH.exists():
        return EMBEDDED_GAMIFICATION_CONTENT

    try:
        raw_items = json.loads(GAMIFICATION_CONTENT_PATH.read_text(encoding="utf-8"))
        return {
            concept_tag: GamificationContentItem(**content)
            for concept_tag, content in raw_items.items()
        }
    except (OSError, json.JSONDecodeError, TypeError, ValidationError):
        return EMBEDDED_GAMIFICATION_CONTENT


GAMIFICATION_CONTENT = _load_gamification_content()


def _content_for_concept(concept_tag: str) -> GamificationContentItem:
    return GAMIFICATION_CONTENT.get(concept_tag, DEFAULT_GAMIFICATION_CONTENT)


def _recommendation_id(seed: str, concept_tag: str) -> str:
    digest = hashlib.sha1(f"{seed}|{concept_tag}".encode("utf-8")).hexdigest()[:12]
    return f"grec_{digest}"


def _priority_rank(priority: str) -> int:
    if priority == "high":
        return 2
    if priority == "medium":
        return 1
    return 0


def _difficulty_from_signals(
    *,
    mastery_level: str | None,
    struggle_level: str | None,
) -> str:
    if mastery_level == "strong" and struggle_level not in {"high", "medium"}:
        return "intermediate"
    return "beginner"


def _support_from_signals(
    *,
    mastery_level: str | None,
    struggle_level: str | None,
    hint_dependency_level: str | None,
) -> str:
    if struggle_level == "high" or hint_dependency_level == "high":
        return "high"
    if mastery_level in {"at_risk", "developing"} or struggle_level == "medium":
        return "guided"
    return "light"


def _priority_for_struggle(struggle: ConceptStruggleView) -> str:
    if struggle.struggle_level == "high" or struggle.hint_dependency_level == "high":
        return "high"
    if struggle.struggle_level == "medium":
        return "medium"
    return "low"


def _priority_for_mastery(mastery: ConceptMasteryView) -> str:
    if mastery.mastery_level == "at_risk":
        return "high"
    if mastery.mastery_level == "developing":
        return "medium"
    return "low"


def _adaptation_goal_for_struggle(struggle: ConceptStruggleView) -> str:
    if struggle.struggle_level == "high":
        return "remediation"
    return "targeted_practice"


def _adaptation_goal_for_mastery(mastery: ConceptMasteryView) -> str:
    if mastery.mastery_level == "strong":
        return "reinforcement"
    return "targeted_practice"


def _rationale_for_struggle(
    struggle: ConceptStruggleView,
    mastery: ConceptMasteryView | None,
) -> str:
    mastery_phrase = (
        f" The latest mastery level for this concept is {mastery.mastery_level}."
        if mastery is not None
        else ""
    )
    return (
        f"The student has repeated {struggle.concept_tag} issues {struggle.repeat_count} time(s), "
        f"still has {struggle.active_count} active issue(s), and shows "
        f"{struggle.hint_dependency_level} hint dependence.{mastery_phrase}"
    )


def _rationale_for_mastery(mastery: ConceptMasteryView) -> str:
    return (
        f"The latest mastery snapshot for {mastery.concept_tag} is {mastery.mastery_level} "
        f"(mastery score {mastery.mastery_score:.2f}, struggle score {mastery.struggle_score:.2f}), "
        "so the game can reinforce the concept at an appropriate difficulty."
    )


def build_gamification_recommendations(
    concept_struggles: list[ConceptStruggleView],
    mastery_documents: list[dict[str, Any]],
    *,
    limit: int = 10,
) -> GamificationRecommendationListResponse:
    mastery_views: dict[str, ConceptMasteryView] = {}
    for document in mastery_documents:
        mastery_view = ConceptMasteryView(
            concept_tag=document["conceptTag"],
            mastery_score=document["masteryScore"],
            struggle_score=document["struggleScore"],
            mastery_level=document.get("masteryLevel", "developing"),
            update_source=document.get("updateSource", "unknown"),
            last_learning_session_id=document["lastLearningSessionId"],
            last_error_type=document.get("lastErrorType"),
            last_trigger_id=document.get("lastTriggerId"),
            last_quiz_id=document.get("lastQuizId"),
            last_quiz_score_percent=document.get("lastQuizScorePercent"),
            last_quiz_passed=document.get("lastQuizPassed"),
            last_updated_at=document["lastUpdatedAt"],
        )
        mastery_views[mastery_view.concept_tag] = mastery_view

    recommendations: list[GamificationRecommendationView] = []
    seen_concepts: set[str] = set()

    for struggle in concept_struggles:
        content = _content_for_concept(struggle.concept_tag)
        mastery = mastery_views.get(struggle.concept_tag)
        if (
            struggle.active_count <= 0
            and mastery is not None
            and mastery.mastery_level == "strong"
        ):
            continue

        priority = _priority_for_struggle(struggle)
        recommendations.append(
            GamificationRecommendationView(
                recommendation_id=_recommendation_id(
                    f"struggle|{struggle.concept_tag}|{struggle.error_type}",
                    struggle.concept_tag,
                ),
                concept_tag=struggle.concept_tag,
                error_type=struggle.error_type,
                recommendation_source="concept_struggle",
                adaptation_goal=_adaptation_goal_for_struggle(struggle),
                based_on_mastery_level=mastery.mastery_level if mastery is not None else None,
                based_on_struggle_level=struggle.struggle_level,
                game_id=content.game_id,
                game_type=content.game_type,
                title=content.title,
                difficulty_level=_difficulty_from_signals(
                    mastery_level=mastery.mastery_level if mastery is not None else None,
                    struggle_level=struggle.struggle_level,
                ),
                support_level=_support_from_signals(
                    mastery_level=mastery.mastery_level if mastery is not None else None,
                    struggle_level=struggle.struggle_level,
                    hint_dependency_level=struggle.hint_dependency_level,
                ),
                estimated_duration_minutes=content.estimated_duration_minutes,
                focus_points=content.focus_points,
                rationale=_rationale_for_struggle(struggle, mastery),
                priority=priority,
            )
        )
        seen_concepts.add(struggle.concept_tag)

    for concept_tag, mastery in mastery_views.items():
        if concept_tag in seen_concepts:
            continue

        content = _content_for_concept(concept_tag)
        priority = _priority_for_mastery(mastery)
        recommendations.append(
            GamificationRecommendationView(
                recommendation_id=_recommendation_id(
                    f"mastery|{concept_tag}|{mastery.update_source}",
                    concept_tag,
                ),
                concept_tag=concept_tag,
                error_type=mastery.last_error_type,
                recommendation_source="mastery_summary",
                adaptation_goal=_adaptation_goal_for_mastery(mastery),
                based_on_mastery_level=mastery.mastery_level,
                based_on_struggle_level=None,
                game_id=content.game_id,
                game_type=content.game_type,
                title=content.title,
                difficulty_level=_difficulty_from_signals(
                    mastery_level=mastery.mastery_level,
                    struggle_level=None,
                ),
                support_level=_support_from_signals(
                    mastery_level=mastery.mastery_level,
                    struggle_level=None,
                    hint_dependency_level=None,
                ),
                estimated_duration_minutes=content.estimated_duration_minutes,
                focus_points=content.focus_points,
                rationale=_rationale_for_mastery(mastery),
                priority=priority,
            )
        )

    recommendations.sort(
        key=lambda item: (
            _priority_rank(item.priority),
            1 if item.recommendation_source == "concept_struggle" else 0,
            1 if item.adaptation_goal == "remediation" else 0,
        ),
        reverse=True,
    )

    return GamificationRecommendationListResponse(
        status="ok",
        message="Adaptive gamification recommendations generated from Code Coach struggle and mastery signals.",
        total=min(len(recommendations), limit),
        recommendations=recommendations[:limit],
    )


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _game_mastery_scores(
    *,
    score_percent: int,
    error_count: int,
    attempt_count: int,
    hint_usage: int,
    passed: bool,
) -> tuple[float, float]:
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


def _blend_mastery_scores(
    existing_mastery_document: dict[str, Any] | None,
    *,
    mastery_score: float,
    struggle_score: float,
) -> tuple[float, float]:
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


def record_gamification_adaptation_decision(
    storage: Any,
    *,
    user_id: str,
    learning_session_id: str,
    recommendation_id: str | None,
    concept_tag: str,
    game_id: str,
    game_type: str,
    difficulty_level: str,
    support_level: str,
    rationale: str,
    based_on_mastery_level: str | None,
    based_on_struggle_level: str | None,
    occurred_at=None,
) -> list[dict[str, Any]]:
    event_time = occurred_at or utcnow()
    event = build_learning_event_document(
        user_id,
        learning_session_id,
        component="adaptive_gamification",
        event_type="game_adaptation_decision_created",
        concept_tag=_normalize_token(concept_tag),
        occurred_at=event_time,
        payload={
            "recommendation_id": recommendation_id,
            "assigned_game_id": game_id,
            "assigned_game_type": _normalize_token(game_type),
            "assigned_difficulty": _normalize_token(difficulty_level),
            "assigned_support_level": _normalize_token(support_level),
            "reason": rationale,
            "based_on_mastery_level": _normalize_token(based_on_mastery_level)
            if based_on_mastery_level
            else None,
            "based_on_struggle_level": _normalize_token(based_on_struggle_level)
            if based_on_struggle_level
            else None,
        },
    )
    storage.create_learning_events([event])
    return [event]


def record_gamification_session_completed(
    storage: Any,
    *,
    user_id: str,
    learning_session_id: str,
    recommendation_id: str | None,
    concept_tag: str,
    game_id: str,
    game_type: str,
    difficulty_level: str,
    support_level: str | None,
    score_percent: int,
    error_count: int,
    attempt_count: int,
    hint_usage: int,
    time_taken_seconds: int,
    passed: bool,
    occurred_at=None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    event_time = occurred_at or utcnow()
    normalized_concept_tag = _normalize_token(concept_tag)
    normalized_game_type = _normalize_token(game_type)
    normalized_difficulty = _normalize_token(difficulty_level)
    normalized_support = _normalize_token(support_level) if support_level else None

    observed_mastery_score, observed_struggle_score = _game_mastery_scores(
        score_percent=score_percent,
        error_count=error_count,
        attempt_count=attempt_count,
        hint_usage=hint_usage,
        passed=passed,
    )
    existing_mastery = next(
        iter(storage.list_concept_mastery_for_user(user_id, concept_tag=normalized_concept_tag, limit=1)),
        None,
    )
    mastery_score, struggle_score = _blend_mastery_scores(
        existing_mastery,
        mastery_score=observed_mastery_score,
        struggle_score=observed_struggle_score,
    )
    mastery_document = build_concept_mastery_document(
        user_id,
        learning_session_id,
        concept_tag=normalized_concept_tag,
        error_type=existing_mastery.get("lastErrorType") if existing_mastery else None,
        trigger_id=existing_mastery.get("lastTriggerId") if existing_mastery else None,
        mastery_score=mastery_score,
        struggle_score=struggle_score,
        update_source="game_session_completed",
        source_component="adaptive_gamification",
        occurred_at=event_time,
    )
    mastery_document["lastGameId"] = game_id
    mastery_document["lastGameType"] = normalized_game_type
    mastery_document["lastGameScorePercent"] = score_percent
    mastery_document["lastGameDifficultyLevel"] = normalized_difficulty

    game_event = build_learning_event_document(
        user_id,
        learning_session_id,
        component="adaptive_gamification",
        event_type="game_session_completed",
        concept_tag=normalized_concept_tag,
        occurred_at=event_time,
        payload={
            "recommendation_id": recommendation_id,
            "game_id": game_id,
            "game_type": normalized_game_type,
            "difficulty_level": normalized_difficulty,
            "support_level": normalized_support,
            "score_percent": score_percent,
            "error_count": error_count,
            "attempt_count": attempt_count,
            "hint_usage": hint_usage,
            "time_taken_seconds": time_taken_seconds,
            "passed": passed,
            "observed_mastery_score": observed_mastery_score,
            "observed_struggle_score": observed_struggle_score,
            "blended_mastery_score": mastery_score,
            "blended_struggle_score": struggle_score,
        },
    )
    mastery_event = build_learning_event_document(
        user_id,
        learning_session_id,
        component="adaptive_gamification",
        event_type="mastery_updated",
        concept_tag=normalized_concept_tag,
        occurred_at=event_time,
        payload={
            "concept_tag": normalized_concept_tag,
            "mastery_score": mastery_score,
            "struggle_score": struggle_score,
            "observed_mastery_score": observed_mastery_score,
            "observed_struggle_score": observed_struggle_score,
            "update_source": "game_session_completed",
            "game_id": game_id,
            "game_type": normalized_game_type,
            "difficulty_level": normalized_difficulty,
            "score_percent": score_percent,
            "passed": passed,
        },
    )

    stored_mastery = storage.upsert_concept_mastery(mastery_document)
    storage.create_learning_events([game_event, mastery_event])
    return build_concept_mastery_view(stored_mastery).model_dump(), [game_event, mastery_event]
