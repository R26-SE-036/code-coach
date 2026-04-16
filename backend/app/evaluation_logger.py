import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models import AnalyzeRequest, Diagnostic

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"
EVENT_LOG_PATH = LOGS_DIR / "code_coach_events.jsonl"


def _hash_identifier(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _context_hash(diagnostic: Diagnostic) -> str:
    return hashlib.sha256(diagnostic.code_context.encode("utf-8")).hexdigest()[:16]
def log_analysis_event(
    payload: AnalyzeRequest,
    diagnostics: list[Diagnostic],
    *,
    user_id: Optional[str] = None,
    learning_session_id: Optional[str] = None,
) -> None:
    if not payload.enable_logging:
        return

    LOGS_DIR.mkdir(exist_ok=True)
    resolved_session_id = learning_session_id or payload.resolved_session_id
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_hash": _hash_identifier(user_id),
        "learning_session_hash": _hash_identifier(resolved_session_id),
        "language": payload.language,
        "diagnostic_count": len(diagnostics),
        "diagnostics": [
            {
                "diagnostic_id": diagnostic.diagnostic_id,
                "error_type": diagnostic.error_type,
                "severity": diagnostic.severity,
                "confidence": diagnostic.confidence,
                "detection_engine": diagnostic.detection_engine,
                "ml_probability": diagnostic.ml_probability,
                "locator_confidence": diagnostic.locator_confidence,
                "line": diagnostic.line,
                "column": diagnostic.column,
                "concept_tag": diagnostic.concept_tag,
                "explanation_key": diagnostic.explanation_key,
                "status": diagnostic.status,
                "code_context_hash": _context_hash(diagnostic),
            }
            for diagnostic in diagnostics
        ],
    }

    with EVENT_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(event, separators=(",", ":")) + "\n")
