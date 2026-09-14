"""A student's "this is not a mistake" - recorded, and acted on.

The extension has always let a student report a finding as a false positive,
and has always sent the report: a diagnostic_disputed learning event. Nothing
read it. The finding stayed in the editor and went on counting - towards the
concept's repeat count, the student's mastery, and the struggle score that
opens a Study Guider lesson - so a student who told us we were wrong could
then be sent the lesson for the mistake they had not made.

A dispute is now kept per student and diagnostic id, and:

  * every stored record of that finding is marked "disputed", which
    list_diagnostics_for_user leaves out, so no count sees it;
  * later analyses leave it out of the response and out of storage, in every
    session - the id no longer changes when the rest of the file does.

It is the student's word, not a verdict on the detector. An evaluation that
wants a false-positive rate reads the disputes themselves.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.cache import TTLCache
from app.core.common import utcnow

DISPUTE_EVENT_TYPE = "diagnostic_disputed"
DISPUTED_STATUS = "disputed"

# Read on every analysis, and disputes are rare. Recording one invalidates the
# entry in the process that recorded it; another process can go on showing the
# finding for up to this long. That is why what gets STORED is filtered with a
# fresh read instead - see routes/code_coach.py.
_DISPUTED_IDS = TTLCache(ttl_seconds=60.0)

_MAX_ID_LENGTH = 64


def disputed_ids_for(storage: Any, user_id: str, *, fresh: bool = False) -> set[str]:
    if not fresh:
        cached = _DISPUTED_IDS.get(user_id)
        if cached is not None:
            return cached

    ids = set(storage.list_disputed_diagnostic_ids(user_id))
    _DISPUTED_IDS.set(user_id, ids)
    return ids


def _text(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()[:_MAX_ID_LENGTH]


def _probability(value: Any) -> Optional[float]:
    # bool is an int in Python, and True is not a probability.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def record_dispute(
    storage: Any,
    *,
    user_id: str,
    learning_session_id: str,
    concept_tag: Optional[str],
    payload: Any,
) -> bool:
    """Record a dispute from a diagnostic_disputed event. False if it names no finding."""
    if not isinstance(payload, dict):
        return False

    diagnostic_id = _text(payload.get("diagnostic_id"))
    if diagnostic_id is None:
        return False

    disputed_at = utcnow()
    storage.record_diagnostic_dispute(
        {
            "userId": user_id,
            "diagnosticId": diagnostic_id,
            "learningSessionId": learning_session_id,
            "errorType": _text(payload.get("error_type")),
            "conceptTag": concept_tag,
            "detectionEngine": _text(payload.get("detection_engine")),
            "mlProbability": _probability(payload.get("ml_probability")),
            "reason": _text(payload.get("dispute_reason")) or "false_positive",
            "disputedAt": disputed_at,
        }
    )
    storage.mark_diagnostics_disputed(user_id, diagnostic_id, disputed_at=disputed_at)
    _DISPUTED_IDS.invalidate(user_id)
    return True
