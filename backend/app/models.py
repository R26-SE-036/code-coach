from dataclasses import dataclass, field
from typing import Any, List, Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    language: str
    code: str
    student_id: Optional[str] = None
    session_id: Optional[str] = None
    enable_logging: bool = False


class HintSet(BaseModel):
    concept: str
    guidance: str
    targeted: str


class DetectionResult(BaseModel):
    error_type: str
    line: int
    column: int
    confidence: float
    severity: str = "warning"
    message: str
    code_context: str
    detection_engine: str = "ml_gated_ast_locator"
    ml_probability: Optional[float] = None
    locator_confidence: Optional[float] = None


class Diagnostic(BaseModel):
    diagnostic_id: str
    error_type: str
    severity: str
    line: int
    column: int
    confidence: float
    message: str
    code_context: str
    concept_tag: str
    explanation_key: str
    status: str
    detection_engine: str
    ml_probability: Optional[float] = None
    locator_confidence: Optional[float] = None
    hints: HintSet


class AnalyzeResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    analysis_duration_ms: float
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
