from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    language: str
    code: str
    session_id: Optional[str] = None
    learning_session_id: Optional[str] = Field(
        default=None,
        alias="learningSessionId",
    )
    enable_logging: bool = False

    @property
    def resolved_session_id(self) -> Optional[str]:
        return self.learning_session_id or self.session_id


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
    learning_session_id: Optional[str] = None
    diagnostics: List[Diagnostic]


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    student_number: str = Field(min_length=4, max_length=40)
    password: str = Field(min_length=8, max_length=128)
    client_name: str = Field(default="code-coach-vscode", min_length=2, max_length=80)


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    client_name: str = Field(default="code-coach-vscode", min_length=2, max_length=80)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=256)


class AuthUser(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr
    student_number: str
    role: str
    status: str
    created_at: datetime


class AuthSessionView(BaseModel):
    auth_session_id: str
    client_name: str
    status: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime


class TokenBundle(BaseModel):
    token_type: str = "Bearer"
    access_token: str
    refresh_token: str
    expires_in: int


class AuthResponse(BaseModel):
    status: str
    message: str
    user: AuthUser
    auth_session: AuthSessionView
    tokens: TokenBundle


class MeResponse(BaseModel):
    status: str
    user: AuthUser
    auth_session: AuthSessionView


class StatusResponse(BaseModel):
    status: str
    message: str


class LearningSessionCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source_component: str = Field(default="code_coach", min_length=2, max_length=64)
    language: str = Field(default="java", min_length=2, max_length=32)
    task_id: Optional[str] = Field(default=None, max_length=120)


class LearningSessionResponse(BaseModel):
    status: str
    message: str
    learning_session_id: str
    user_id: str
    source_component: str
    language: str
    task_id: Optional[str] = None
    learning_session_status: str
    started_at: datetime
    last_analysis_at: Optional[datetime] = None
    reused_existing: bool = False


class PersistedDiagnosticView(BaseModel):
    diagnostic_record_id: str
    diagnostic_id: str
    user_id: str
    learning_session_id: str
    error_type: str
    concept_tag: str
    explanation_key: str
    line: int
    column: int
    severity: str
    confidence: float
    ml_probability: Optional[float] = None
    locator_confidence: Optional[float] = None
    detection_engine: str
    status: str
    code_context_hash: str
    created_at: datetime
    resolved_at: Optional[datetime] = None


class DiagnosticListResponse(BaseModel):
    status: str
    message: str
    total: int
    diagnostics: List[PersistedDiagnosticView]


class LearningEventView(BaseModel):
    event_id: str
    user_id: str
    learning_session_id: str
    component: str
    event_type: str
    concept_tag: Optional[str] = None
    occurred_at: datetime
    created_at: datetime
    payload: dict[str, Any]


class LearningEventListResponse(BaseModel):
    status: str
    message: str
    total: int
    events: List[LearningEventView]


class LearningEventCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    learning_session_id: str = Field(
        alias="learningSessionId",
        min_length=3,
        max_length=80,
    )
    component: str = Field(default="code_coach", min_length=2, max_length=64)
    event_type: str = Field(min_length=3, max_length=64)
    concept_tag: Optional[str] = Field(default=None, max_length=64)
    occurred_at: Optional[datetime] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class LearningEventCreateResponse(BaseModel):
    status: str
    message: str
    event_id: str


class ErrorTypeSummaryView(BaseModel):
    error_type: str
    count: int
    active_count: int
    last_seen_at: datetime


class ConceptSummaryView(BaseModel):
    concept_tag: str
    repeat_count: int
    unresolved_count: int
    last_seen_at: datetime


class DiagnosticSummaryResponse(BaseModel):
    status: str
    user_id: str
    total_diagnostics: int
    top_error_types: List[ErrorTypeSummaryView]
    top_concepts: List[ConceptSummaryView]


class ConceptStruggleView(BaseModel):
    concept_tag: str
    error_type: str
    repeat_count: int
    active_count: int
    resolved_count: int
    unique_learning_sessions: int
    last_seen_at: datetime
    struggle_score: float
    struggle_level: str
    recommended_action: str


class ConceptStruggleResponse(BaseModel):
    status: str
    user_id: str
    total_concepts: int
    struggles: List[ConceptStruggleView]


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
class DiagnosticSyncResult:
    active_documents: list[dict[str, Any]] = field(default_factory=list)
    newly_detected_documents: list[dict[str, Any]] = field(default_factory=list)
    resolved_documents: list[dict[str, Any]] = field(default_factory=list)


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
