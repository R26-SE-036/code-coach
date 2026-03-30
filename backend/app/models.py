from dataclasses import dataclass, field
from typing import Any, List, Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    language: str
    code: str


class HintSet(BaseModel):
    concept: str
    guidance: str
    targeted: str


class DetectionResult(BaseModel):
    error_type: str
    line: int
    column: int
    confidence: float
    message: str
    code_context: str


class Diagnostic(BaseModel):
    error_type: str
    line: int
    column: int
    confidence: float
    message: str
    code_context: str
    concept_tag: str
    explanation_key: str
    hints: HintSet


class AnalyzeResponse(BaseModel):
    status: str
    message: str
    diagnostics: List[Diagnostic]


@dataclass
class Span:
    start_line: int
    start_col: int
    end_line: int
    end_col: int


@dataclass
class ParseHealth:
    has_error_nodes: bool = False
    error_node_count: int = 0
    missing_node_count: int = 0
    unstable_spans: list[Span] = field(default_factory=list)
    completeness_score: float = 1.0


@dataclass
class ParseResult:
    tree: Optional[Any]
    source_bytes: bytes
    health: ParseHealth
    crashed: bool = False


@dataclass
class DetectionCandidate:
    error_type: str
    line: int
    column: int
    base_confidence: float
    message: str
    code_context: str
    source_span: Span
    requires_stable_region: bool = True