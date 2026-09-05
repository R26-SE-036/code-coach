import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure

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

    # The database being unreachable is not a bug in the request, and it should
    # not look like one. Unhandled, it surfaces as a 500 behind a long driver
    # traceback, which reads like a crash - and 500 is ambiguous to the sibling
    # services, where 401 means "sign in again" and 503 means "we could not
    # reach the platform store, keep your session".
    #
    # These replace two google.api_core handlers (ResourceExhausted and
    # ServiceUnavailable) that outlived the move off Firestore. The import at
    # the top of this file survived because the development virtualenv still had
    # google-cloud-firestore installed, while requirements-prod.txt no longer
    # does - so the service ran fine on a laptop and died on import in the
    # container, the first time one was ever built.
    #
    # There is no replacement for the quota handler. Firestore's
    # RESOURCE_EXHAUSTED was a daily read limit with a real "come back later"
    # meaning; Atlas has no daily read quota, so inventing an equivalent would
    # be describing a failure mode this deployment does not have.
    #
    # ConnectionFailure is the base of AutoReconnect, NetworkTimeout and
    # ServerSelectionTimeoutError - every way the driver says "I could not
    # reach a server". OperationFailure is deliberately NOT caught: a rejected
    # query is usually a bug in this service, and mapping it to 503 would tell
    # the caller to retry something that will never succeed.
    @app.exception_handler(ConnectionFailure)
    def handle_storage_unavailable(request: Request, exc: ConnectionFailure):
        logger.error("MongoDB unreachable on %s: %s", request.url.path, exc)
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
