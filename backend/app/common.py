from datetime import datetime, timezone
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_prefixed_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
