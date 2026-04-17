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
    hint_event_count: int = 0
    hint_shown_count: int = 0
    hint_request_count: int = 0
    hint_navigation_count: int = 0
    hint_dependency_score: float = 0.0
    hint_dependency_level: str = "low"
    last_hint_at: Optional[datetime] = None


class DiagnosticSummaryResponse(BaseModel):
    status: str
    user_id: str
    total_diagnostics: int
    total_hint_events: int = 0
    concepts_with_hint_usage: int = 0
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
    hint_event_count: int = 0
    hint_shown_count: int = 0
    hint_request_count: int = 0
    hint_navigation_count: int = 0
    hint_dependency_score: float = 0.0
    hint_dependency_level: str = "low"
    last_hint_at: Optional[datetime] = None
    struggle_score: float
    struggle_level: str
    recommended_action: str


class ConceptStruggleResponse(BaseModel):
    status: str
    user_id: str
    total_concepts: int
    struggles: List[ConceptStruggleView]


class ConceptMasteryView(BaseModel):
    concept_tag: str
    mastery_score: float
    struggle_score: float
    mastery_level: str
    update_source: str
    last_learning_session_id: str
    last_error_type: Optional[str] = None
    last_trigger_id: Optional[str] = None
    last_quiz_id: Optional[str] = None
    last_quiz_score_percent: Optional[int] = None
    last_quiz_passed: Optional[bool] = None
    last_game_id: Optional[str] = None
    last_game_type: Optional[str] = None
    last_game_score_percent: Optional[int] = None
    last_game_difficulty_level: Optional[str] = None
    last_updated_at: datetime


class ConceptMasteryListResponse(BaseModel):
    status: str
    user_id: str
    total_concepts: int
    concepts: List[ConceptMasteryView]


class RemediationTriggerView(BaseModel):
    trigger_id: str
    user_id: str
    learning_session_id: str
    trigger_source: str
    concept_tag: str
    error_type: str
    reason: str
    struggle_level: str
    recommended_action: str
    repeat_count: int
    active_count: int
    resolved_count: int
    unique_learning_sessions: int
    struggle_score: float
    hint_dependency_score: float = 0.0
    hint_dependency_level: str = "low"
    status: str
    intervention_status: str = "pending"
    lesson_id: Optional[str] = None
    lesson_opened_at: Optional[datetime] = None
    quiz_id: Optional[str] = None
    quiz_completed_at: Optional[datetime] = None
    quiz_score_percent: Optional[int] = None
    quiz_passed: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class RemediationTriggerListResponse(BaseModel):
    status: str
    message: str
    total: int
    triggers: List[RemediationTriggerView]


class QuizRecommendationView(BaseModel):
    quiz_id: str
    title: str
    question_count: int
    passing_score_percent: int
    focus_points: List[str]


class MicroLessonRecommendationView(BaseModel):
    lesson_id: str
    title: str
    summary: str
    estimated_duration_minutes: int
    learning_objectives: List[str]
    recommended_steps: List[str]


class StudyGuiderRecommendationView(BaseModel):
    recommendation_id: str
    trigger_id: str
    trigger_source: str
    learning_session_id: str
    concept_tag: str
    error_type: str
    struggle_level: str
    recommended_action: str
    lesson: MicroLessonRecommendationView
    quiz: QuizRecommendationView
    rationale: str
    priority: str


class StudyGuiderRecommendationListResponse(BaseModel):
    status: str
    message: str
    total: int
    recommendations: List[StudyGuiderRecommendationView]


class GamificationRecommendationView(BaseModel):
    recommendation_id: str
    concept_tag: str
    error_type: Optional[str] = None
    recommendation_source: str
    adaptation_goal: str
    based_on_mastery_level: Optional[str] = None
    based_on_struggle_level: Optional[str] = None
    game_id: str
    game_type: str
    title: str
    difficulty_level: str
    support_level: str
    estimated_duration_minutes: int
    focus_points: List[str]
    rationale: str
    priority: str


class GamificationRecommendationListResponse(BaseModel):
    status: str
    message: str
    total: int
    recommendations: List[GamificationRecommendationView]


class GamificationAdaptationDecisionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    learning_session_id: str = Field(
        alias="learningSessionId",
        min_length=3,
        max_length=80,
    )
    concept_tag: str = Field(min_length=3, max_length=64)
    recommendation_id: Optional[str] = Field(default=None, max_length=80)
    game_id: str = Field(min_length=3, max_length=80)
    game_type: str = Field(min_length=3, max_length=64)
    difficulty_level: str = Field(min_length=3, max_length=32)
    support_level: str = Field(min_length=3, max_length=32)
    rationale: str = Field(min_length=5, max_length=400)
    based_on_mastery_level: Optional[str] = Field(default=None, max_length=32)
    based_on_struggle_level: Optional[str] = Field(default=None, max_length=32)
    occurred_at: Optional[datetime] = None


class GamificationSessionCompletedRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    learning_session_id: str = Field(
        alias="learningSessionId",
        min_length=3,
        max_length=80,
    )
    concept_tag: str = Field(min_length=3, max_length=64)
    recommendation_id: Optional[str] = Field(default=None, max_length=80)
    game_id: str = Field(min_length=3, max_length=80)
    game_type: str = Field(min_length=3, max_length=64)
    difficulty_level: str = Field(min_length=3, max_length=32)
    support_level: Optional[str] = Field(default=None, max_length=32)
    score_percent: int = Field(ge=0, le=100)
    error_count: int = Field(ge=0, le=100)
    attempt_count: int = Field(ge=1, le=20)
    hint_usage: int = Field(ge=0, le=100)
    time_taken_seconds: int = Field(ge=0, le=7200)
    passed: Optional[bool] = None
    occurred_at: Optional[datetime] = None


class GamificationActionResponse(BaseModel):
    status: str
    message: str
    created_event_types: List[str]
    mastery: Optional[ConceptMasteryView] = None


class CollaborationPromptView(BaseModel):
    prompt_id: str
    prompt_type: str
    collaboration_mode: str
    concept_tag: str
    error_type: Optional[str] = None
    linked_diagnostic_id: Optional[str] = None
    linked_learning_session_id: Optional[str] = None
    title: str
    prompt_text: str
    target_role: str
    based_on_struggle_level: Optional[str] = None
    based_on_mastery_level: Optional[str] = None
    priority: str
    rationale: str


class CollaborationPromptListResponse(BaseModel):
    status: str
    message: str
    total: int
    prompts: List[CollaborationPromptView]


class CollaborationSessionView(BaseModel):
    pair_session_id: str
    user_id: str
    learning_session_id: str
    collaboration_mode: str
    partner_user_id: Optional[str] = None
    task_id: Optional[str] = None
    linked_learning_session_id: Optional[str] = None
    status: str
    started_at: datetime
    last_activity_at: datetime


class CollaborationSessionCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    learning_session_id: str = Field(
        alias="learningSessionId",
        min_length=3,
        max_length=80,
    )
    collaboration_mode: str = Field(default="pair_programming", min_length=3, max_length=40)
    partner_user_id: Optional[str] = Field(default=None, max_length=80)
    task_id: Optional[str] = Field(default=None, max_length=120)
    linked_learning_session_id: Optional[str] = Field(
        default=None,
        alias="linkedLearningSessionId",
        max_length=80,
    )


class CollaborationSessionCreateResponse(BaseModel):
    status: str
    message: str
    session: CollaborationSessionView
    created_event_types: List[str]


class CollaborationPromptShownRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    learning_session_id: str = Field(
        alias="learningSessionId",
        min_length=3,
        max_length=80,
    )
    pair_session_id: str = Field(min_length=3, max_length=80)
    prompt_id: str = Field(min_length=3, max_length=80)
    prompt_type: str = Field(min_length=3, max_length=40)
    concept_tag: str = Field(min_length=3, max_length=64)
    linked_diagnostic_id: Optional[str] = Field(default=None, max_length=120)
    linked_learning_session_id: Optional[str] = Field(
        default=None,
        alias="linkedLearningSessionId",
        max_length=80,
    )
    target_role: Optional[str] = Field(default=None, max_length=40)
    occurred_at: Optional[datetime] = None


class PeerReviewSubmittedRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    learning_session_id: str = Field(
        alias="learningSessionId",
        min_length=3,
        max_length=80,
    )
    pair_session_id: str = Field(min_length=3, max_length=80)
    concept_tag: str = Field(min_length=3, max_length=64)
    linked_diagnostic_id: Optional[str] = Field(default=None, max_length=120)
    linked_learning_session_id: Optional[str] = Field(
        default=None,
        alias="linkedLearningSessionId",
        max_length=80,
    )
    rubric_score: int = Field(ge=1, le=5)
    feedback_quality_score: float = Field(ge=0.0, le=1.0)
    review_comment: Optional[str] = Field(default=None, max_length=1000)
    occurred_at: Optional[datetime] = None


class CollaborationActionResponse(BaseModel):
    status: str
    message: str
    pair_session_id: str
    created_event_types: List[str]


class DashboardCountsView(BaseModel):
    total_diagnostics: int
    active_diagnostics: int
    resolved_diagnostics: int
    total_hint_events: int
    active_remediation_triggers: int
    completed_remediation_triggers: int
    total_game_sessions: int
    total_pair_sessions: int
    total_peer_reviews: int
    total_lessons_viewed: int
    total_quizzes_completed: int


class DashboardMasterySummaryView(BaseModel):
    total_concepts: int
    strong_count: int
    developing_count: int
    at_risk_count: int


class DashboardConceptTrendView(BaseModel):
    concept_tag: str
    repeat_count: int = 0
    active_count: int = 0
    struggle_level: Optional[str] = None
    mastery_level: Optional[str] = None
    mastery_score: Optional[float] = None
    hint_dependency_level: Optional[str] = None
    last_activity_at: datetime
    recommended_focus: str


class DashboardTimelineItemView(BaseModel):
    event_id: str
    component: str
    event_type: str
    title: str
    summary: str
    concept_tag: Optional[str] = None
    occurred_at: datetime


class DashboardOverviewResponse(BaseModel):
    status: str
    user_id: str
    counts: DashboardCountsView
    mastery: DashboardMasterySummaryView
    concept_trends: List[DashboardConceptTrendView]
    recent_timeline: List[DashboardTimelineItemView]


class DashboardTimelineResponse(BaseModel):
    status: str
    user_id: str
    total: int
    events: List[DashboardTimelineItemView]


class LessonOpenedRequest(BaseModel):
    lesson_id: str = Field(min_length=3, max_length=80)
    occurred_at: Optional[datetime] = None


class QuizCompletedRequest(BaseModel):
    quiz_id: str = Field(min_length=3, max_length=80)
    score_percent: int = Field(ge=0, le=100)
    passed: Optional[bool] = None
    occurred_at: Optional[datetime] = None


class RemediationActionResponse(BaseModel):
    status: str
    message: str
    trigger: RemediationTriggerView
    created_event_types: List[str]


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
