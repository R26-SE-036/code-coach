import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from app.core.config import get_settings
from app.core.rate_limit import SlidingWindowLimiter
from app.analysis.error_catalog import validate_catalog
from app.analysis.parser_utils import parse_java_code
from app.models import AnalyzeRequest, AnalyzeResponse
from app.api.routes.auth import router as auth_router
from app.api.routes.collaboration import router as collaboration_router
from app.api.routes.code_coach import router as code_coach_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.students import router as students_router
from app.api.routes.events import router as events_router
from app.api.routes.gamification import router as gamification_router
from app.api.routes.learning_sessions import router as learning_session_router
from app.api.routes.remediation import router as remediation_router
from app.db.storage import build_storage
from app.services.code_coach_service import build_analyze_response, run_analysis
from app.services.evaluation_logger import log_analysis_event

logger = logging.getLogger(__name__)


def create_app(*, storage=None) -> FastAPI:
    # Fail at startup if any error-catalog entry is half registered
    # (missing model file, locator, or knowledge-base hints).
    validate_catalog()

    @asynccontextmanager
    async def lifespan(lifespan_app: FastAPI):
        if storage is not None:
            lifespan_app.state.storage = storage
        elif getattr(lifespan_app.state, "storage", None) is None:
            lifespan_app.state.storage = build_storage()

        try:
            yield
        finally:
            current_storage = getattr(lifespan_app.state, "storage", None)
            close = getattr(current_storage, "close", None)
            if callable(close):
                close()

    app = FastAPI(title="Code Coach Backend", lifespan=lifespan)
    if storage is not None:
        app.state.storage = storage

    settings = get_settings()
    app.state.auth_limiter = SlidingWindowLimiter(
        settings.auth_rate_limit_attempts,
        settings.auth_rate_limit_window_seconds,
    )

    # Browser-based clients (the CodeGuru website, teammates' frontends) are
    # blocked by the browser without this. Origins come from settings so the
    # deployed service can allow the real website URL via an env var.
    allowed_origins = [
        origin.strip()
        for origin in get_settings().cors_allowed_origins.split(",")
        if origin.strip()
    ]
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["*"],
            allow_headers=["Authorization", "Content-Type"],
        )

    # registered routes
    app.include_router(auth_router)
    app.include_router(learning_session_router)
    app.include_router(collaboration_router)
    app.include_router(code_coach_router)
    app.include_router(dashboard_router)
    app.include_router(students_router)
    app.include_router(events_router)
    app.include_router(gamification_router)
    app.include_router(remediation_router)

    # Firestore refusing work is not a bug in the request, and it should not
    # look like one. Unhandled, a quota or availability failure surfaces as a
    # 500 behind a 200-line gRPC traceback, which reads like a crash - and 500
    # is ambiguous to the sibling services, where 401 means "sign in again" and
    # 503 means "we could not reach Code Coach, keep your session".
    #
    # RESOURCE_EXHAUSTED in particular is the free-tier daily read quota, and
    # the honest answer to it is "come back later", not "something broke".
    @app.exception_handler(ResourceExhausted)
    def handle_quota_exhausted(request: Request, exc: ResourceExhausted):
        logger.error("Firestore quota exhausted on %s", request.url.path)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Code Coach's database is over its daily read quota. "
                          "Your session is fine - try again later, or raise the "
                          "quota in the Firebase console.",
            },
        )

    @app.exception_handler(ServiceUnavailable)
    def handle_storage_unavailable(request: Request, exc: ServiceUnavailable):
        logger.error("Firestore unavailable on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Code Coach cannot reach its database right now. "
                               "Your session is fine - please try again."},
        )


    @app.get("/")
    def root():
        return {"message": "Code Coach backend is running"}


    @app.get("/health")
    def health():
        return {"status": "ok"}


    @app.post("/analyze", response_model=AnalyzeResponse)
    def analyze(payload: AnalyzeRequest):
        diagnostics, analysis_duration_ms = run_analysis(payload)
        log_analysis_event(payload, diagnostics)
        return build_analyze_response(
            diagnostics,
            analysis_duration_ms,
            learning_session_id=payload.resolved_session_id,
        )


    @app.post("/debug-ast")
    def debug_ast(payload: AnalyzeRequest):
        if payload.language.lower() != "java":
            return {"status": "unsupported_language"}

        tree, _ = parse_java_code(payload.code)

        return {
            "status": "ok",
            "root_type": tree.root_node.type,
            "tree": str(tree.root_node),
        }

    return app


app = create_app()
