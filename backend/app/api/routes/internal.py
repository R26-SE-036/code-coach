"""Routes for other Code Guru services, not for a browser or the extension.

Every other route takes a student's bearer token. These are called by another
service's server with a key shared between the two (`X-Internal-Key`), because
the caller is not acting as any one student.

They run the detector and nothing else: no learning session, no diagnostic
records, no evaluation log, no research snapshot. Code a pair wrote together in
PairPath is not one student's work, so it must not count against either of
them here.
"""

from __future__ import annotations

import hmac
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models import AnalyzeRequest
from app.services.code_coach_service import run_analysis

router = APIRouter(prefix="/api/v1/internal", tags=["internal"])


def require_internal_caller(x_internal_key: Optional[str] = Header(default=None)) -> None:
    """A request with no key is always a 401, whatever the configuration.

    That keeps these routes inside the rule tests/test_api_surface.py holds
    every endpoint to, and it is the honest answer: the caller did not say
    who it was.
    """
    if not x_internal_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This endpoint is for other Code Guru services, and needs X-Internal-Key.",
        )

    expected = get_settings().internal_service_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INTERNAL_SERVICE_KEY is not set on Code Coach, so service calls are refused.",
        )

    # Constant-time, so the key cannot be recovered one character at a time.
    if not hmac.compare_digest(x_internal_key.encode(), expected.encode()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong X-Internal-Key.")


class ConceptsRequest(BaseModel):
    code: str = Field(max_length=50_000)


class ConceptsResponse(BaseModel):
    # Most confident finding first, each concept once.
    concept_tags: list[str]
    error_types: list[str]


@router.post(
    "/concepts",
    response_model=ConceptsResponse,
    dependencies=[Depends(require_internal_caller)],
)
def concepts_in_code(payload: ConceptsRequest) -> ConceptsResponse:
    """The platform concepts the detector finds in a piece of Java.

    PairPath's free-coding sessions have no exercise, so there are no concept
    tags to choose course notes by. This gives it the same vocabulary a
    finding in the editor would carry.
    """
    if not payload.code.strip():
        return ConceptsResponse(concept_tags=[], error_types=[])

    diagnostics, _ = run_analysis(AnalyzeRequest(language="java", code=payload.code))
    ranked = sorted(diagnostics, key=lambda d: d.confidence, reverse=True)

    def unique(values: list[str]) -> list[str]:
        seen: set[str] = set()
        return [v for v in values if v and not (v in seen or seen.add(v))]

    return ConceptsResponse(
        concept_tags=unique([d.concept_tag for d in ranked]),
        error_types=unique([d.error_type for d in ranked]),
    )
