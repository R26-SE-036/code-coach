"""Keeping the code Code Coach analyses, for students who agreed.

Three conditions, all required, checked every time:

  1. The deployment has collection switched on (RESEARCH_COLLECTION_ENABLED),
     which should happen only once the ethics application is approved.
  2. It has a participant salt (RESEARCH_ID_SALT) to pseudonymise with.
  3. The student's LATEST decision is GRANTED, under the CURRENT consent
     version - an agreement to older wording does not count.

Runs as a background task after the analysis response is sent, like the rest
of Code Coach's persistence, so it adds nothing to the time a student waits
for underlines - and never raises, so it cannot break the editor either.

What is kept is the file, the detector's findings in it, and whether the
student had disputed each finding: a dispute is the student saying "this is
wrong", which is exactly the evidence a false-positive rate needs. Who the
student is, is not kept - see participant_id.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Optional

from app.core.common import generate_prefixed_id, utcnow
from app.core.config import get_settings
from app.core.research_consent import RESEARCH_CONSENT_VERSION

logger = logging.getLogger(__name__)


def participant_id(user_id: str) -> Optional[str]:
    """A stable code for one student that cannot be turned back into their id.

    A keyed hash (HMAC-SHA256) rather than a plain one: without the salt, a
    plain hash of an id could be reversed by hashing every known id and
    comparing. None when no salt is configured, which keeps collection off.
    """
    salt = get_settings().research_id_salt
    if not salt:
        return None
    digest = hmac.new(salt.encode("utf-8"), user_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"p_{digest[:24]}"


def collection_active() -> bool:
    settings = get_settings()
    return bool(settings.research_collection_enabled and settings.research_id_salt)


def consent_is_current(consent: Optional[dict[str, Any]]) -> bool:
    return bool(
        consent
        and consent.get("decision") == "GRANTED"
        and consent.get("version") == RESEARCH_CONSENT_VERSION
    )


def collect_code_snapshot(
    storage: Any,
    *,
    user_id: str,
    language: str,
    code: str,
    findings: list[Any],
    disputed_ids: set[str],
) -> bool:
    """Keep this file if every condition holds. True when something was saved."""
    try:
        if not collection_active():
            return False
        if not code.strip() or len(code) > get_settings().research_max_code_chars:
            return False
        if not consent_is_current(storage.latest_research_consent(user_id)):
            return False

        participant = participant_id(user_id)
        now = utcnow()
        storage.save_code_snapshot(
            {
                "snapshotId": generate_prefixed_id("snap"),
                "participant": participant,
                "consentVersion": RESEARCH_CONSENT_VERSION,
                "language": language,
                "code": code,
                "codeHash": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                "lineCount": code.count("\n") + 1,
                "findings": [
                    {
                        "errorType": finding.error_type,
                        "line": finding.line,
                        "detectionEngine": finding.detection_engine,
                        "confidence": finding.confidence,
                        "mlProbability": finding.ml_probability,
                        "disputed": finding.diagnostic_id in disputed_ids,
                    }
                    for finding in findings
                ],
                "firstSeenAt": now,
                "lastSeenAt": now,
                "timesAnalysed": 1,
            }
        )
        return True
    except Exception:
        logger.exception("Could not keep a research snapshot")
        return False
