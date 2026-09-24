"""The student's research consent for Code Coach.

    GET  /api/v1/research/consent   the statement, and this student's decision
    POST /api/v1/research/consent   record GRANTED or DECLINED

Decisions are appended, never edited: the history of what someone agreed to,
and when, is itself something an ethics review can ask for.

Declining - including withdrawing an earlier agreement - deletes every file
already kept from this student, at once. "Withdrawing keeps your future work
out" is weaker than what the statement promises.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.common import generate_prefixed_id, utcnow
from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.core.research_consent import RESEARCH_CONSENT_STATEMENT, RESEARCH_CONSENT_VERSION
from app.services.research_collection import collection_active, participant_id

router = APIRouter(prefix="/api/v1/research", tags=["research"])


class ConsentDecisionRequest(BaseModel):
    decision: Literal["GRANTED", "DECLINED"]


def _state(storage: Any, user_id: str) -> dict[str, Any]:
    latest = storage.latest_research_consent(user_id)
    current = latest if latest and latest.get("version") == RESEARCH_CONSENT_VERSION else None
    participant = participant_id(user_id)
    return {
        "version": RESEARCH_CONSENT_VERSION,
        "statement": RESEARCH_CONSENT_STATEMENT,
        # Null when they have not decided under THIS wording - the page asks.
        "decision": current["decision"] if current else None,
        "decided_at": current["decidedAt"] if current else None,
        # Whether agreeing would keep anything today. False until the ethics
        # application is approved and the deployment switches collection on.
        "collecting": collection_active(),
        "files_kept": storage.count_code_snapshots(participant) if participant else 0,
    }


@router.get("/consent")
def get_consent(
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> dict[str, Any]:
    return _state(storage, auth.user_id)


@router.post("/consent")
def decide(
    payload: ConsentDecisionRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> dict[str, Any]:
    storage.record_research_consent(
        {
            "consentId": generate_prefixed_id("consent"),
            "userId": auth.user_id,
            "decision": payload.decision,
            "version": RESEARCH_CONSENT_VERSION,
            "decidedAt": utcnow(),
        }
    )

    if payload.decision == "DECLINED":
        participant = participant_id(auth.user_id)
        if participant:
            storage.delete_code_snapshots(participant)

    return _state(storage, auth.user_id)
