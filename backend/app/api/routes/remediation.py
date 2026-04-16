from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.models import RemediationTriggerListResponse, RemediationTriggerView

router = APIRouter(prefix="/api/v1/remediation", tags=["remediation"])


def _serialize_trigger(document: dict[str, Any]) -> RemediationTriggerView:
    return RemediationTriggerView(
        trigger_id=document["triggerId"],
        user_id=document["userId"],
        learning_session_id=document["learningSessionId"],
        trigger_source=document["triggerSource"],
        concept_tag=document["conceptTag"],
        error_type=document["errorType"],
        reason=document["reason"],
        struggle_level=document["struggleLevel"],
        recommended_action=document["recommendedAction"],
        repeat_count=document["repeatCount"],
        active_count=document["activeCount"],
        resolved_count=document["resolvedCount"],
        unique_learning_sessions=document["uniqueLearningSessions"],
        struggle_score=document["struggleScore"],
        hint_dependency_score=document.get("hintDependencyScore", 0.0),
        hint_dependency_level=document.get("hintDependencyLevel", "low"),
        status=document["status"],
        created_at=document["createdAt"],
        updated_at=document["updatedAt"],
        resolved_at=document.get("resolvedAt"),
    )


@router.get("/me/triggers", response_model=RemediationTriggerListResponse)
def get_my_remediation_triggers(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
    status: Optional[str] = Query(default=None),
    trigger_source: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> RemediationTriggerListResponse:
    documents = storage.list_remediation_triggers_for_user(
        auth.user_id,
        status=status,
        trigger_source=trigger_source,
        limit=limit,
    )
    triggers = [_serialize_trigger(document) for document in documents]
    return RemediationTriggerListResponse(
        status="ok",
        message="Remediation triggers loaded for the authenticated user.",
        total=len(triggers),
        triggers=triggers,
    )
