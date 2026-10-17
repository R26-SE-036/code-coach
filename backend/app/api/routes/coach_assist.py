"""On-demand help in the editor: explanations, compiler errors, worked examples.

All under /api/v1/code-coach next to /analyze. The three POST routes need a
signed-in student, because the daily allowance is per student; the catalogue
is public - it is the list of mistakes Code Coach knows, with their names - and
so are the model cards, which say how each model was trained and tested.
"""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.dependencies import AuthContext, get_current_auth, get_storage
from app.services.explanation_service import (
    MAX_CODE_CHARS,
    catalogue,
    explain_compiler_error,
    explain_diagnostic,
    similar_example,
)
from app.services.model_cards import model_card, model_card_index

router = APIRouter(prefix="/api/v1/code-coach", tags=["code-coach"])


class ExplainRequest(BaseModel):
    error_type: str = Field(min_length=3, max_length=80)
    code: str = Field(max_length=MAX_CODE_CHARS * 5)
    line: int = Field(ge=1, le=100_000)
    message: Optional[str] = Field(default=None, max_length=400)
    diagnostic_id: Optional[str] = Field(default=None, max_length=40)


class CompilerErrorRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    code: str = Field(max_length=MAX_CODE_CHARS * 5)
    line: int = Field(ge=1, le=100_000)


class SimilarExampleRequest(BaseModel):
    error_type: str = Field(min_length=3, max_length=80)
    code: str = Field(default="", max_length=MAX_CODE_CHARS * 5)
    line: int = Field(default=1, ge=1, le=100_000)


class ExplanationResponse(BaseModel):
    status: str = "ok"
    explanation: str
    source: str
    remaining_today: int
    daily_limit: int
    limit_reached: bool = False


class CatalogueEntry(BaseModel):
    error_type: str
    title: str
    concept_tag: str
    detection_mode: str
    course_path: str


def _response(result) -> ExplanationResponse:
    return ExplanationResponse(
        explanation=result.text,
        source=result.source,
        remaining_today=result.remaining_today,
        daily_limit=result.limit,
        limit_reached=result.limit_reached,
    )


@router.get("/catalog", response_model=List[CatalogueEntry])
def list_catalogue() -> List[CatalogueEntry]:
    return [CatalogueEntry(**entry) for entry in catalogue()]


@router.get("/model-cards")
def list_model_cards() -> List[dict]:
    return model_card_index()


@router.get("/model-cards/{error_type}")
def get_model_card(error_type: str) -> dict:
    card = model_card(error_type.upper())
    if card is None:
        raise HTTPException(status_code=404, detail=f"{error_type} is decided by a rule, not a model, or is not a known error type.")
    return card


@router.post("/explain", response_model=ExplanationResponse)
def explain(
    payload: ExplainRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> ExplanationResponse:
    return _response(explain_diagnostic(
        storage, auth.user_id, error_type=payload.error_type.upper(), code=payload.code,
        line=payload.line, message=payload.message or "",
    ))


@router.post("/explain-compiler-error", response_model=ExplanationResponse)
def explain_compiler(
    payload: CompilerErrorRequest,
    auth: AuthContext = Depends(get_current_auth),
    storage: Any = Depends(get_storage),
) -> ExplanationResponse:
    return _response(explain_compiler_error(
        storage, auth.user_id, message=payload.message, code=payload.code, line=payload.line,
    ))


@router.post("/similar-example")
def worked_example(
    payload: SimilarExampleRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    return similar_example(error_type=payload.error_type.upper(), code=payload.code, line=payload.line)
