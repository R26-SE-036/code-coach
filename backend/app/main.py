from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.analysis.error_catalog import validate_catalog
from app.analysis.parser_utils import parse_java_code
from app.models import AnalyzeRequest, AnalyzeResponse
from app.api.routes.auth import router as auth_router
from app.api.routes.collaboration import router as collaboration_router
from app.api.routes.code_coach import router as code_coach_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.events import router as events_router
from app.api.routes.gamification import router as gamification_router
from app.api.routes.learning_sessions import router as learning_session_router
from app.api.routes.remediation import router as remediation_router
from app.api.routes.users import router as users_router
from app.db.storage import build_storage
from app.services.code_coach_service import build_analyze_response, run_analysis
from app.services.evaluation_logger import log_analysis_event


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

    # registered routes
    app.include_router(auth_router)
    app.include_router(learning_session_router)
    app.include_router(collaboration_router)
    app.include_router(code_coach_router)
    app.include_router(dashboard_router)
    app.include_router(diagnostics_router)
    app.include_router(events_router)
    app.include_router(gamification_router)
    app.include_router(remediation_router)
    app.include_router(users_router)


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
