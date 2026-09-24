"""Storage for research: consent decisions, and the code kept with consent.

    researchConsents   append-only; a student's current decision is their latest.
                       Keyed by the real user id, because the student must be
                       able to see and change their own decision.
    codeSnapshots      one document per distinct file per participant. Keyed by
                       the PARTICIPANT code (a keyed hash of the user id), never
                       the user id, name or email - the research copy of the
                       code does not say whose it is.

A file analysed again unchanged is not stored twice: the second time only
bumps `timesAnalysed` and `lastSeenAt`. Students re-run analysis constantly as
they type, and a thousand copies of one file would outweigh every other file
in any training set.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from pymongo import ASCENDING, DESCENDING
except ImportError:  # pragma: no cover
    ASCENDING, DESCENDING = 1, -1


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryResearchStorage:
    def _research(self) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
        if not hasattr(self, "research_consents"):
            self.research_consents = []
            self.code_snapshots = {}
        return self.research_consents, self.code_snapshots

    def record_research_consent(self, document: dict[str, Any]) -> None:
        self._research()[0].append(deepcopy(document))

    def latest_research_consent(self, user_id: str) -> Optional[dict[str, Any]]:
        mine = [d for d in self._research()[0] if d["userId"] == user_id]
        return deepcopy(max(mine, key=lambda d: d["decidedAt"])) if mine else None

    def save_code_snapshot(self, document: dict[str, Any]) -> None:
        snapshots = self._research()[1]
        key = (document["participant"], document["codeHash"])
        existing = snapshots.get(key)
        if existing is None:
            snapshots[key] = deepcopy(document)
        else:
            existing["lastSeenAt"] = document["lastSeenAt"]
            existing["timesAnalysed"] += 1
            existing["findings"] = deepcopy(document["findings"])

    def delete_code_snapshots(self, participant: str) -> int:
        snapshots = self._research()[1]
        doomed = [key for key in snapshots if key[0] == participant]
        for key in doomed:
            del snapshots[key]
        return len(doomed)

    def count_code_snapshots(self, participant: str) -> int:
        return sum(1 for key in self._research()[1] if key[0] == participant)

    def list_code_snapshots(self, limit: int = 10_000) -> list[dict[str, Any]]:
        documents = sorted(self._research()[1].values(), key=lambda d: d["firstSeenAt"])
        return [deepcopy(d) for d in documents[:limit]]

    def list_latest_research_consents(self) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for document in self._research()[0]:
            current = latest.get(document["userId"])
            if current is None or document["decidedAt"] > current["decidedAt"]:
                latest[document["userId"]] = document
        return [deepcopy(d) for d in latest.values()]


class MongoResearchStorage:
    def create_research_indexes(self) -> None:
        self.db.researchConsents.create_index([("userId", ASCENDING), ("decidedAt", DESCENDING)])
        self.db.codeSnapshots.create_index(
            [("participant", ASCENDING), ("codeHash", ASCENDING)], unique=True
        )
        self.db.codeSnapshots.create_index([("firstSeenAt", ASCENDING)])

    def record_research_consent(self, document: dict[str, Any]) -> None:
        self.db.researchConsents.insert_one(deepcopy(document))

    def latest_research_consent(self, user_id: str) -> Optional[dict[str, Any]]:
        document = self.db.researchConsents.find_one(
            {"userId": user_id}, sort=[("decidedAt", DESCENDING)]
        )
        if document is not None:
            document.pop("_id", None)
        return document

    def save_code_snapshot(self, document: dict[str, Any]) -> None:
        fresh = {k: v for k, v in document.items() if k not in {"lastSeenAt", "timesAnalysed", "findings"}}
        self.db.codeSnapshots.update_one(
            {"participant": document["participant"], "codeHash": document["codeHash"]},
            {
                "$setOnInsert": fresh,
                "$set": {"lastSeenAt": document["lastSeenAt"], "findings": document["findings"]},
                "$inc": {"timesAnalysed": 1},
            },
            upsert=True,
        )

    def delete_code_snapshots(self, participant: str) -> int:
        return self.db.codeSnapshots.delete_many({"participant": participant}).deleted_count

    def count_code_snapshots(self, participant: str) -> int:
        return self.db.codeSnapshots.count_documents({"participant": participant})

    def list_code_snapshots(self, limit: int = 10_000) -> list[dict[str, Any]]:
        cursor = self.db.codeSnapshots.find({}, {"_id": 0}).sort("firstSeenAt", ASCENDING).limit(limit)
        return list(cursor)

    def list_latest_research_consents(self) -> list[dict[str, Any]]:
        pipeline = [
            {"$sort": {"decidedAt": -1}},
            {"$group": {"_id": "$userId", "latest": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$latest"}},
            {"$project": {"_id": 0}},
        ]
        return list(self.db.researchConsents.aggregate(pipeline))
