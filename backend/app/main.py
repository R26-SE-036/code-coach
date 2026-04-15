from datetime import datetime, timezone
from time import perf_counter

from fastapi import FastAPI

from app.analyzer import analyze_code
from app.evaluation_logger import log_analysis_event
from app.models import AnalyzeRequest, AnalyzeResponse
from app.parser_utils import parse_java_code

app = FastAPI(title="Code Coach Backend")


@app.get("/")
def root():
    return {"message": "Code Coach backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    started_at = perf_counter()
    diagnostics = []

    if payload.language.lower() == "java":
        diagnostics = analyze_code(payload.code)

    log_analysis_event(payload, diagnostics)

    return AnalyzeResponse(
        status="ok",
        message="Analysis completed.",
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis_duration_ms=round((perf_counter() - started_at) * 1000, 2),
        diagnostics=diagnostics,
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
