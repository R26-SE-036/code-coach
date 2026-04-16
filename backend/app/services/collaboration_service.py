from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.common import generate_prefixed_id, utcnow
from app.models import (
    CollaborationPromptListResponse,
    CollaborationPromptView,
    CollaborationSessionView,
    ConceptMasteryView,
    ConceptStruggleView,
)
from app.services.learning_signal_service import build_learning_event_document
from app.services.mastery_service import build_concept_mastery_view


class CollaborationPromptTemplate(BaseModel):
    prompt_type: str
    collaboration_mode: str
    title: str
    prompt_text: str
    target_role: str


class CollaborationPromptContentItem(BaseModel):
    pair_prompt: CollaborationPromptTemplate
    peer_review_prompt: CollaborationPromptTemplate


EMBEDDED_COLLABORATION_CONTENT: dict[str, CollaborationPromptContentItem] = {
    "array_indexing": CollaborationPromptContentItem(
        pair_prompt=CollaborationPromptTemplate(
            prompt_type="reasoning_prompt",
            collaboration_mode="pair_programming",
            title="Reason About the Last Valid Index",
            prompt_text="Ask the driver to explain why array.length is the number of elements and what the last valid index should be for the current array.",
            target_role="navigator",
        ),
        peer_review_prompt=CollaborationPromptTemplate(
            prompt_type="peer_review_focus",
            collaboration_mode="peer_review",
            title="Review the Array Access Fix",
            prompt_text="Check whether the fix uses a safe array index and whether the explanation clearly distinguishes array length from the last valid index.",
            target_role="reviewer",
        ),
    ),
    "loop_boundaries": CollaborationPromptContentItem(
        pair_prompt=CollaborationPromptTemplate(
            prompt_type="reasoning_prompt",
            collaboration_mode="pair_programming",
            title="Trace the Final Loop Iteration",
            prompt_text="Have the driver trace the final loop iteration aloud and compare the stopping condition with the last valid array index.",
            target_role="navigator",
        ),
        peer_review_prompt=CollaborationPromptTemplate(
            prompt_type="peer_review_focus",
            collaboration_mode="peer_review",
            title="Review the Loop Boundary Choice",
            prompt_text="Review whether the stopping condition avoids one extra iteration and whether the explanation matches the valid index range.",
            target_role="reviewer",
        ),
    ),
    "conditional_logic": CollaborationPromptContentItem(
        pair_prompt=CollaborationPromptTemplate(
            prompt_type="reasoning_prompt",
            collaboration_mode="pair_programming",
            title="Explain the Condition in Plain English",
            prompt_text="Ask the driver to read the condition in plain English and explain whether it is checking a value or accidentally assigning one.",
            target_role="navigator",
        ),
        peer_review_prompt=CollaborationPromptTemplate(
            prompt_type="peer_review_focus",
            collaboration_mode="peer_review",
            title="Review the Conditional Operator",
            prompt_text="Check whether the condition uses the correct operator and whether the reviewer comment explains why that operator is appropriate.",
            target_role="reviewer",
        ),
    ),
}

DEFAULT_COLLABORATION_CONTENT = CollaborationPromptContentItem(
    pair_prompt=CollaborationPromptTemplate(
        prompt_type="reasoning_prompt",
        collaboration_mode="pair_programming",
        title="Explain the Bug Out Loud",
        prompt_text="Ask one student to explain the problem in plain English while the partner checks each part of the explanation against the code.",
        target_role="navigator",
    ),
    peer_review_prompt=CollaborationPromptTemplate(
        prompt_type="peer_review_focus",
        collaboration_mode="peer_review",
        title="Review the Reasoning",
        prompt_text="Review whether the explanation identifies the bug clearly, justifies the fix, and shows how the correction was verified.",
        target_role="reviewer",
    ),
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
COLLABORATION_CONTENT_PATH = PROJECT_ROOT / "knowledge_base" / "collaboration_prompts.json"


def _load_collaboration_content() -> dict[str, CollaborationPromptContentItem]:
    if not COLLABORATION_CONTENT_PATH.exists():
        return EMBEDDED_COLLABORATION_CONTENT

    try:
        raw_items = json.loads(COLLABORATION_CONTENT_PATH.read_text(encoding="utf-8"))
        return {
            concept_tag: CollaborationPromptContentItem(**content)
            for concept_tag, content in raw_items.items()
        }
    except (OSError, json.JSONDecodeError, TypeError, ValidationError):
        return EMBEDDED_COLLABORATION_CONTENT


COLLABORATION_CONTENT = _load_collaboration_content()


def _content_for_concept(concept_tag: str) -> CollaborationPromptContentItem:
    return COLLABORATION_CONTENT.get(concept_tag, DEFAULT_COLLABORATION_CONTENT)


def _priority_rank(priority: str) -> int:
    if priority == "high":
        return 2
    if priority == "medium":
        return 1
    return 0


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _prompt_id(seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"cpr_{digest}"


def _priority_for_prompt(
    *,
    struggle_level: str | None,
    mastery_level: str | None,
    active_count: int,
) -> str:
    if active_count > 0 or struggle_level == "high":
        return "high"
    if struggle_level == "medium" or mastery_level in {"at_risk", "developing"}:
        return "medium"
    return "low"


def _rationale_for_prompt(
    *,
    concept_tag: str,
    error_type: str | None,
    struggle_level: str | None,
    mastery_level: str | None,
    active_count: int,
) -> str:
    parts = [f"The pair is working around the concept {concept_tag}."]
    if error_type:
        parts.append(f"The linked error type is {error_type}.")
    if active_count > 0:
        parts.append(f"There are currently {active_count} active diagnostic(s) for this concept.")
    if struggle_level:
        parts.append(f"The latest struggle level is {struggle_level}.")
    if mastery_level:
        parts.append(f"The latest mastery level is {mastery_level}.")
    return " ".join(parts)


def _mastery_by_concept(
    mastery_documents: list[dict[str, Any]],
) -> dict[str, ConceptMasteryView]:
    mastery_views: dict[str, ConceptMasteryView] = {}
    for document in mastery_documents:
        mastery_view = build_concept_mastery_view(document)
        mastery_views[mastery_view.concept_tag] = mastery_view
    return mastery_views


def build_collaboration_prompts(
    diagnostics: list[dict[str, Any]],
    concept_struggles: list[ConceptStruggleView],
    mastery_documents: list[dict[str, Any]],
    *,
    limit: int = 10,
) -> CollaborationPromptListResponse:
    mastery_views = _mastery_by_concept(mastery_documents)
    active_diagnostics = [item for item in diagnostics if item.get("status") == "active"]
    latest_active_by_concept: dict[str, dict[str, Any]] = {}
    for diagnostic in active_diagnostics:
        concept_tag = diagnostic["conceptTag"]
        if concept_tag not in latest_active_by_concept:
            latest_active_by_concept[concept_tag] = diagnostic

    struggle_by_concept = {item.concept_tag: item for item in concept_struggles}
    prompts: list[CollaborationPromptView] = []

    for concept_tag, diagnostic in latest_active_by_concept.items():
        content = _content_for_concept(concept_tag)
        struggle = struggle_by_concept.get(concept_tag)
        mastery = mastery_views.get(concept_tag)
        active_count = struggle.active_count if struggle is not None else 1
        priority = _priority_for_prompt(
            struggle_level=struggle.struggle_level if struggle is not None else None,
            mastery_level=mastery.mastery_level if mastery is not None else None,
            active_count=active_count,
        )
        prompts.append(
            CollaborationPromptView(
                prompt_id=_prompt_id(f"pair|{diagnostic['diagnosticId']}|{concept_tag}"),
                prompt_type=content.pair_prompt.prompt_type,
                collaboration_mode=content.pair_prompt.collaboration_mode,
                concept_tag=concept_tag,
                error_type=diagnostic["errorType"],
                linked_diagnostic_id=diagnostic["diagnosticId"],
                linked_learning_session_id=diagnostic["learningSessionId"],
                title=content.pair_prompt.title,
                prompt_text=content.pair_prompt.prompt_text,
                target_role=content.pair_prompt.target_role,
                based_on_struggle_level=struggle.struggle_level if struggle is not None else None,
                based_on_mastery_level=mastery.mastery_level if mastery is not None else None,
                priority=priority,
                rationale=_rationale_for_prompt(
                    concept_tag=concept_tag,
                    error_type=diagnostic["errorType"],
                    struggle_level=struggle.struggle_level if struggle is not None else None,
                    mastery_level=mastery.mastery_level if mastery is not None else None,
                    active_count=active_count,
                ),
            )
        )

    for struggle in concept_struggles:
        content = _content_for_concept(struggle.concept_tag)
        mastery = mastery_views.get(struggle.concept_tag)
        linked_diagnostic = latest_active_by_concept.get(struggle.concept_tag)
        priority = _priority_for_prompt(
            struggle_level=struggle.struggle_level,
            mastery_level=mastery.mastery_level if mastery is not None else None,
            active_count=struggle.active_count,
        )
        prompts.append(
            CollaborationPromptView(
                prompt_id=_prompt_id(f"review|{struggle.concept_tag}|{struggle.error_type}"),
                prompt_type=content.peer_review_prompt.prompt_type,
                collaboration_mode=content.peer_review_prompt.collaboration_mode,
                concept_tag=struggle.concept_tag,
                error_type=struggle.error_type,
                linked_diagnostic_id=linked_diagnostic["diagnosticId"] if linked_diagnostic else None,
                linked_learning_session_id=linked_diagnostic["learningSessionId"] if linked_diagnostic else None,
                title=content.peer_review_prompt.title,
                prompt_text=content.peer_review_prompt.prompt_text,
                target_role=content.peer_review_prompt.target_role,
                based_on_struggle_level=struggle.struggle_level,
                based_on_mastery_level=mastery.mastery_level if mastery is not None else None,
                priority=priority,
                rationale=_rationale_for_prompt(
                    concept_tag=struggle.concept_tag,
                    error_type=struggle.error_type,
                    struggle_level=struggle.struggle_level,
                    mastery_level=mastery.mastery_level if mastery is not None else None,
                    active_count=struggle.active_count,
                ),
            )
        )

    prompts.sort(
        key=lambda item: (
            _priority_rank(item.priority),
            1 if item.collaboration_mode == "pair_programming" else 0,
        ),
        reverse=True,
    )

    unique_prompts: list[CollaborationPromptView] = []
    seen_ids: set[str] = set()
    for prompt in prompts:
        if prompt.prompt_id in seen_ids:
            continue
        seen_ids.add(prompt.prompt_id)
        unique_prompts.append(prompt)

    return CollaborationPromptListResponse(
        status="ok",
        message="Collaborative prompts generated from Code Coach diagnostics, struggles, and mastery signals.",
        total=min(len(unique_prompts), limit),
        prompts=unique_prompts[:limit],
    )


def create_collaboration_session_document(
    user_id: str,
    learning_session_id: str,
    *,
    collaboration_mode: str,
    partner_user_id: str | None,
    task_id: str | None,
    linked_learning_session_id: str | None,
) -> dict[str, Any]:
    now = utcnow()
    return {
        "pairSessionId": generate_prefixed_id("collab"),
        "userId": user_id,
        "learningSessionId": learning_session_id,
        "collaborationMode": _normalize_token(collaboration_mode),
        "partnerUserId": partner_user_id,
        "taskId": task_id,
        "linkedLearningSessionId": linked_learning_session_id,
        "status": "active",
        "startedAt": now,
        "lastActivityAt": now,
    }


def build_collaboration_session_view(document: dict[str, Any]) -> CollaborationSessionView:
    return CollaborationSessionView(
        pair_session_id=document["pairSessionId"],
        user_id=document["userId"],
        learning_session_id=document["learningSessionId"],
        collaboration_mode=document["collaborationMode"],
        partner_user_id=document.get("partnerUserId"),
        task_id=document.get("taskId"),
        linked_learning_session_id=document.get("linkedLearningSessionId"),
        status=document["status"],
        started_at=document["startedAt"],
        last_activity_at=document["lastActivityAt"],
    )


def record_pair_session_started(
    storage: Any,
    *,
    session_document: dict[str, Any],
    occurred_at=None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    event_time = occurred_at or session_document["startedAt"]
    stored_session = storage.create_collaboration_session(session_document)
    event = build_learning_event_document(
        session_document["userId"],
        session_document["learningSessionId"],
        component="collaborative_studio",
        event_type="pair_session_started",
        concept_tag=None,
        occurred_at=event_time,
        payload={
            "pair_session_id": session_document["pairSessionId"],
            "partner_user_id": session_document.get("partnerUserId"),
            "task_id": session_document.get("taskId"),
            "collaboration_mode": session_document["collaborationMode"],
            "linked_learning_session_id": session_document.get("linkedLearningSessionId"),
        },
    )
    storage.create_learning_events([event])
    return stored_session, [event]


def record_collaboration_prompt_shown(
    storage: Any,
    *,
    session_document: dict[str, Any],
    prompt_id: str,
    prompt_type: str,
    concept_tag: str,
    linked_diagnostic_id: str | None,
    linked_learning_session_id: str | None,
    target_role: str | None,
    occurred_at=None,
) -> list[dict[str, Any]]:
    event_time = occurred_at or utcnow()
    storage.update_collaboration_session(
        session_document["pairSessionId"],
        {"lastActivityAt": utcnow()},
    )
    event = build_learning_event_document(
        session_document["userId"],
        session_document["learningSessionId"],
        component="collaborative_studio",
        event_type="collaboration_prompt_shown",
        concept_tag=_normalize_token(concept_tag),
        occurred_at=event_time,
        payload={
            "pair_session_id": session_document["pairSessionId"],
            "prompt_id": prompt_id,
            "prompt_type": _normalize_token(prompt_type),
            "linked_diagnostic_id": linked_diagnostic_id,
            "linked_learning_session_id": linked_learning_session_id,
            "target_role": _normalize_token(target_role) if target_role else None,
        },
    )
    storage.create_learning_events([event])
    return [event]


def record_peer_review_submitted(
    storage: Any,
    *,
    session_document: dict[str, Any],
    concept_tag: str,
    linked_diagnostic_id: str | None,
    linked_learning_session_id: str | None,
    rubric_score: int,
    feedback_quality_score: float,
    review_comment: str | None,
    occurred_at=None,
) -> list[dict[str, Any]]:
    event_time = occurred_at or utcnow()
    storage.update_collaboration_session(
        session_document["pairSessionId"],
        {"lastActivityAt": utcnow()},
    )
    event = build_learning_event_document(
        session_document["userId"],
        session_document["learningSessionId"],
        component="collaborative_studio",
        event_type="peer_review_submitted",
        concept_tag=_normalize_token(concept_tag),
        occurred_at=event_time,
        payload={
            "pair_session_id": session_document["pairSessionId"],
            "linked_diagnostic_id": linked_diagnostic_id,
            "linked_learning_session_id": linked_learning_session_id,
            "rubric_score": rubric_score,
            "feedback_quality_score": feedback_quality_score,
            "review_comment": review_comment,
        },
    )
    storage.create_learning_events([event])
    return [event]
