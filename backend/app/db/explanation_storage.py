"""Storage for the language-model explanations: the daily allowance and the cache.

    llmUsage            one document per (student, UTC day): how many
                        explanations the model wrote for them that day. The
                        allowance (settings.llm_daily_limit) is checked against
                        it; a cached answer does not count.
    explanationCache    one document per explained piece of code, keyed by a
                        hash of the kind of explanation, the mistake and the
                        lines around it - so asking again, or a classmate
                        asking about the same exercise, costs nothing.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    from pymongo import ASCENDING, ReturnDocument
except ImportError:  # pragma: no cover
    ASCENDING = 1
    ReturnDocument = None  # type: ignore[assignment]


class InMemoryExplanationStorage:
    def _explanations(self) -> dict[str, Any]:
        if not hasattr(self, "explanation_tables"):
            self.explanation_tables = {"usage": {}, "cache": {}}
        return self.explanation_tables

    def llm_uses_on(self, user_id: str, day: str) -> int:
        return self._explanations()["usage"].get((user_id, day), 0)

    def add_llm_use(self, user_id: str, day: str) -> int:
        usage = self._explanations()["usage"]
        usage[(user_id, day)] = usage.get((user_id, day), 0) + 1
        return usage[(user_id, day)]

    def get_cached_explanation(self, key: str) -> Optional[dict[str, Any]]:
        cached = self._explanations()["cache"].get(key)
        return dict(cached) if cached else None

    def save_cached_explanation(self, key: str, document: dict[str, Any]) -> None:
        self._explanations()["cache"][key] = dict(document)


class MongoExplanationStorage:
    def create_explanation_indexes(self) -> None:
        self.db.llmUsage.create_index([("userId", ASCENDING), ("day", ASCENDING)], unique=True)
        self.db.explanationCache.create_index([("key", ASCENDING)], unique=True)

    def llm_uses_on(self, user_id: str, day: str) -> int:
        document = self.db.llmUsage.find_one({"userId": user_id, "day": day})
        return int(document.get("count", 0)) if document else 0

    def add_llm_use(self, user_id: str, day: str) -> int:
        document = self.db.llmUsage.find_one_and_update(
            {"userId": user_id, "day": day},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(document.get("count", 1)) if document else 1

    def get_cached_explanation(self, key: str) -> Optional[dict[str, Any]]:
        document = self.db.explanationCache.find_one({"key": key})
        if document is None:
            return None
        document = dict(document)
        document.pop("_id", None)
        return document

    def save_cached_explanation(self, key: str, document: dict[str, Any]) -> None:
        self.db.explanationCache.update_one({"key": key}, {"$set": {**document, "key": key}}, upsert=True)
