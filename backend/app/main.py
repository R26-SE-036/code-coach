from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.code_coach_service import build_analyze_response, run_analysis
from app.evaluation_logger import log_analysis_event
from app.models import AnalyzeRequest, AnalyzeResponse
from app.parser_utils import parse_java_code
from app.routes_auth import router as auth_router
from app.routes_code_coach import router as code_coach_router
from app.routes_learning_sessions import router as learning_session_router
from app.storage import build_storage


def create_app(*, storage=None) -> FastAPI:
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

    app.include_router(auth_router)
    app.include_router(learning_session_router)
    app.include_router(code_coach_router)


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
