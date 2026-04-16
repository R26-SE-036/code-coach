from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from app.models import (
    MicroLessonRecommendationView,
    QuizRecommendationView,
    StudyGuiderRecommendationListResponse,
    StudyGuiderRecommendationView,
)


class StudyGuiderContentItem(BaseModel):
    lesson: MicroLessonRecommendationView
    quiz: QuizRecommendationView


EMBEDDED_STUDY_GUIDER_CONTENT: dict[str, StudyGuiderContentItem] = {
    "array_indexing": StudyGuiderContentItem(
        lesson=MicroLessonRecommendationView(
            lesson_id="lesson_arrays_01",
            title="Array Indexing Basics",
            summary="Explains the difference between array length and the last valid index, with examples of safe access patterns.",
            estimated_duration_minutes=8,
            learning_objectives=[
                "Understand how Java array indexes start at 0.",
                "Differentiate between array length and last valid index.",
                "Apply safe indexing rules when reading and writing array elements.",
            ],
            recommended_steps=[
                "Review the meaning of array length and last index.",
                "Trace a few example arrays by hand.",
                "Rewrite the failing line using a safe final index.",
            ],
        ),
        quiz=QuizRecommendationView(
            quiz_id="quiz_arrays_01",
            title="Array Index Quiz",
            question_count=5,
            passing_score_percent=70,
            focus_points=[
                "zero-based indexing",
                "last valid index",
                "safe array access",
            ],
        ),
    ),
    "loop_boundaries": StudyGuiderContentItem(
        lesson=MicroLessonRecommendationView(
            lesson_id="lesson_loops_01",
            title="Loop Boundaries and Off-by-One Errors",
            summary="Shows how loop conditions interact with array sizes and why one extra iteration can break a program.",
            estimated_duration_minutes=9,
            learning_objectives=[
                "Recognize common off-by-one loop patterns.",
                "Choose a correct stopping condition for array iteration.",
                "Check loop boundaries against the valid index range.",
            ],
            recommended_steps=[
                "Inspect the loop start, condition, and update together.",
                "Compare the final loop value with the array's last valid index.",
                "Test the corrected loop with a small example array.",
            ],
        ),
        quiz=QuizRecommendationView(
            quiz_id="quiz_loops_01",
            title="Loop Boundary Quiz",
            question_count=5,
            passing_score_percent=70,
            focus_points=[
                "loop stopping conditions",
                "off-by-one reasoning",
                "array traversal",
            ],
        ),
    ),
    "conditional_logic": StudyGuiderContentItem(
        lesson=MicroLessonRecommendationView(
            lesson_id="lesson_conditions_01",
            title="Conditions, Comparison, and Assignment",
            summary="Covers the difference between assigning a value and checking a condition, with beginner-friendly Java examples.",
            estimated_duration_minutes=7,
            learning_objectives=[
                "Distinguish between assignment and comparison operators.",
                "Recognize valid boolean conditions in Java.",
                "Correct accidental assignment inside conditions.",
            ],
            recommended_steps=[
                "Review the purpose of =, ==, and boolean expressions.",
                "Rewrite the condition in plain English.",
                "Replace the operator and re-check the condition logic.",
            ],
        ),
        quiz=QuizRecommendationView(
            quiz_id="quiz_conditions_01",
            title="Conditional Logic Quiz",
            question_count=5,
            passing_score_percent=70,
            focus_points=[
                "assignment vs comparison",
                "boolean conditions",
                "if statement correctness",
            ],
        ),
    ),
}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STUDY_GUIDER_CONTENT_PATH = PROJECT_ROOT / "knowledge_base" / "study_guider_lessons.json"


def _load_study_guider_content() -> dict[str, StudyGuiderContentItem]:
    if not STUDY_GUIDER_CONTENT_PATH.exists():
        return EMBEDDED_STUDY_GUIDER_CONTENT

    try:
        raw_items = json.loads(STUDY_GUIDER_CONTENT_PATH.read_text(encoding="utf-8"))
        return {
            concept_tag: StudyGuiderContentItem(**content)
            for concept_tag, content in raw_items.items()
        }
    except (OSError, json.JSONDecodeError, TypeError, ValidationError):
        return EMBEDDED_STUDY_GUIDER_CONTENT


STUDY_GUIDER_CONTENT = _load_study_guider_content()
DEFAULT_STUDY_GUIDER_CONTENT = StudyGuiderContentItem(
    lesson=MicroLessonRecommendationView(
        lesson_id="lesson_general_01",
        title="Beginner Debugging Review",
        summary="A short fallback lesson that helps the student inspect logic, values, and structure more carefully.",
        estimated_duration_minutes=6,
        learning_objectives=[
            "Review the current code more systematically.",
            "Check values, conditions, and structure step by step.",
            "Build a habit of tracing logic before changing code.",
        ],
        recommended_steps=[
            "Read the code aloud in plain English.",
            "Trace one sample input through the logic.",
            "Make one focused correction and test again.",
        ],
    ),
    quiz=QuizRecommendationView(
        quiz_id="quiz_general_01",
        title="General Debugging Quiz",
        question_count=4,
        passing_score_percent=70,
        focus_points=[
            "step-by-step reasoning",
            "logic checking",
            "debugging habits",
        ],
    ),
)


def _content_for_concept(concept_tag: str) -> StudyGuiderContentItem:
    return STUDY_GUIDER_CONTENT.get(concept_tag, DEFAULT_STUDY_GUIDER_CONTENT)


def _priority_for_trigger(trigger: dict[str, Any]) -> str:
    if trigger.get("hintDependencyLevel") == "high":
        return "high"
    if trigger.get("struggleLevel") == "high":
        return "high"
    return "medium"


def _priority_rank(priority: str) -> int:
    if priority == "high":
        return 2
    if priority == "medium":
        return 1
    return 0


def _recommendation_id(trigger_id: str, lesson_id: str) -> str:
    digest = hashlib.sha1(f"{trigger_id}|{lesson_id}".encode("utf-8")).hexdigest()[:12]
    return f"sgrec_{digest}"


def _rationale_for_trigger(trigger: dict[str, Any]) -> str:
    repeat_count = trigger.get("repeatCount", 0)
    active_count = trigger.get("activeCount", 0)
    hint_dependency_level = trigger.get("hintDependencyLevel", "low")
    concept_tag = trigger.get("conceptTag", "this concept")
    return (
        f"The student has repeated {concept_tag} errors {repeat_count} time(s), "
        f"still has {active_count} active issue(s), and shows {hint_dependency_level} hint dependence."
    )


def build_study_guider_recommendations(
    trigger_documents: list[dict[str, Any]],
) -> StudyGuiderRecommendationListResponse:
    recommendations: list[StudyGuiderRecommendationView] = []

    for trigger in trigger_documents:
        content = _content_for_concept(trigger["conceptTag"])
        priority = _priority_for_trigger(trigger)
        recommendations.append(
            StudyGuiderRecommendationView(
                recommendation_id=_recommendation_id(
                    trigger["triggerId"],
                    content.lesson.lesson_id,
                ),
                trigger_id=trigger["triggerId"],
                trigger_source=trigger["triggerSource"],
                learning_session_id=trigger["learningSessionId"],
                concept_tag=trigger["conceptTag"],
                error_type=trigger["errorType"],
                struggle_level=trigger["struggleLevel"],
                recommended_action=trigger["recommendedAction"],
                lesson=content.lesson,
                quiz=content.quiz,
                rationale=_rationale_for_trigger(trigger),
                priority=priority,
            )
        )

    recommendations.sort(
        key=lambda item: (
            _priority_rank(item.priority),
            1 if item.struggle_level == "high" else 0,
            -item.lesson.estimated_duration_minutes,
        ),
        reverse=True,
    )

    return StudyGuiderRecommendationListResponse(
        status="ok",
        message="Study Guider recommendations generated from active remediation triggers.",
        total=len(recommendations),
        recommendations=recommendations,
    )
