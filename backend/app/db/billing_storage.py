"""Storage for subscriptions: who has Pro, what they paid, and the free quota.

    subscriptions   one document per student who has ever had Pro. A student
                    with no document is on Free. Kept rather than deleted when
                    Pro ends, so the history of a subscription survives it.
    checkouts       one per "Upgrade" press: the order PayHere is asked to
                    charge. A notification is only honoured for an order that
                    exists here and belongs to the student it names.
    payments        append-only, one per payment PayHere reports - including
                    failures, so a failed renewal is visible afterwards. No card
                    details are stored; PayHere's masked card number and the
                    card holder's name are dropped before anything is written.
    lessonUnlocks   the Study Guider lessons a Free student has opened this
                    month, one per (student, month, trigger). Opening the same
                    lesson again in the same month does not use up another.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

try:
    from pymongo import ASCENDING, DESCENDING
    from pymongo.errors import DuplicateKeyError
except ImportError:  # pragma: no cover
    ASCENDING, DESCENDING = 1, -1
    DuplicateKeyError = Exception  # type: ignore[misc,assignment]


def _clean(document: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if document is None:
        return None
    document = dict(document)
    document.pop("_id", None)
    return document


class InMemoryBillingStorage:
    def _billing(self) -> dict[str, Any]:
        if not hasattr(self, "billing_tables"):
            self.billing_tables = {
                "subscriptions": {},
                "checkouts": {},
                "payments": [],
                "lessonUnlocks": {},
            }
        return self.billing_tables

    def get_subscription(self, user_id: str) -> Optional[dict[str, Any]]:
        return deepcopy(self._billing()["subscriptions"].get(user_id))

    def save_subscription(self, document: dict[str, Any]) -> None:
        self._billing()["subscriptions"][document["userId"]] = deepcopy(document)

    def delete_subscription(self, user_id: str) -> None:
        self._billing()["subscriptions"].pop(user_id, None)

    def find_subscription_by_provider_id(self, provider_subscription_id: str) -> Optional[dict[str, Any]]:
        for document in self._billing()["subscriptions"].values():
            if document.get("providerSubscriptionId") == provider_subscription_id:
                return deepcopy(document)
        return None

    def create_checkout(self, document: dict[str, Any]) -> None:
        self._billing()["checkouts"][document["orderId"]] = deepcopy(document)

    def find_checkout(self, order_id: str) -> Optional[dict[str, Any]]:
        return deepcopy(self._billing()["checkouts"].get(order_id))

    def update_checkout(self, order_id: str, fields: dict[str, Any]) -> None:
        checkout = self._billing()["checkouts"].get(order_id)
        if checkout is not None:
            checkout.update(deepcopy(fields))

    def record_payment(self, document: dict[str, Any]) -> bool:
        """False when this provider payment was already recorded (a retried notify)."""
        payments = self._billing()["payments"]
        key = document.get("providerPaymentId")
        if key and any(p.get("providerPaymentId") == key and p.get("status") == document.get("status") for p in payments):
            return False
        payments.append(deepcopy(document))
        return True

    def list_payments(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        mine = [p for p in self._billing()["payments"] if p["userId"] == user_id]
        mine.sort(key=lambda p: p["createdAt"], reverse=True)
        return [deepcopy(p) for p in mine[:limit]]

    def add_lesson_unlock(self, document: dict[str, Any]) -> bool:
        """False when this lesson was already unlocked this month."""
        key = (document["userId"], document["month"], document["triggerId"])
        unlocks = self._billing()["lessonUnlocks"]
        if key in unlocks:
            return False
        unlocks[key] = deepcopy(document)
        return True

    def list_lesson_unlocks(self, user_id: str, month: str) -> list[dict[str, Any]]:
        return [
            deepcopy(d)
            for (uid, m, _), d in self._billing()["lessonUnlocks"].items()
            if uid == user_id and m == month
        ]

    def delete_lesson_unlocks(self, user_id: str, month: str) -> None:
        unlocks = self._billing()["lessonUnlocks"]
        for key in [k for k in unlocks if k[0] == user_id and k[1] == month]:
            del unlocks[key]


class MongoBillingStorage:
    def create_billing_indexes(self) -> None:
        self.db.subscriptions.create_index([("userId", ASCENDING)], unique=True)
        self.db.subscriptions.create_index([("providerSubscriptionId", ASCENDING)], sparse=True)
        self.db.checkouts.create_index([("orderId", ASCENDING)], unique=True)
        self.db.payments.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)])
        self.db.payments.create_index([("providerPaymentId", ASCENDING), ("status", ASCENDING)], sparse=True)
        self.db.lessonUnlocks.create_index(
            [("userId", ASCENDING), ("month", ASCENDING), ("triggerId", ASCENDING)], unique=True
        )

    def get_subscription(self, user_id: str) -> Optional[dict[str, Any]]:
        return _clean(self.db.subscriptions.find_one({"userId": user_id}))

    def save_subscription(self, document: dict[str, Any]) -> None:
        self.db.subscriptions.replace_one({"userId": document["userId"]}, deepcopy(document), upsert=True)

    def delete_subscription(self, user_id: str) -> None:
        self.db.subscriptions.delete_one({"userId": user_id})

    def find_subscription_by_provider_id(self, provider_subscription_id: str) -> Optional[dict[str, Any]]:
        return _clean(self.db.subscriptions.find_one({"providerSubscriptionId": provider_subscription_id}))

    def create_checkout(self, document: dict[str, Any]) -> None:
        self.db.checkouts.insert_one(deepcopy(document))

    def find_checkout(self, order_id: str) -> Optional[dict[str, Any]]:
        return _clean(self.db.checkouts.find_one({"orderId": order_id}))

    def update_checkout(self, order_id: str, fields: dict[str, Any]) -> None:
        self.db.checkouts.update_one({"orderId": order_id}, {"$set": deepcopy(fields)})

    def record_payment(self, document: dict[str, Any]) -> bool:
        key = document.get("providerPaymentId")
        if key and self.db.payments.find_one({"providerPaymentId": key, "status": document.get("status")}):
            return False
        self.db.payments.insert_one(deepcopy(document))
        return True

    def list_payments(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.db.payments.find({"userId": user_id}, {"_id": 0}).sort("createdAt", DESCENDING).limit(limit)
        return list(cursor)

    def add_lesson_unlock(self, document: dict[str, Any]) -> bool:
        try:
            self.db.lessonUnlocks.insert_one(deepcopy(document))
            return True
        except DuplicateKeyError:
            return False

    def list_lesson_unlocks(self, user_id: str, month: str) -> list[dict[str, Any]]:
        return list(self.db.lessonUnlocks.find({"userId": user_id, "month": month}, {"_id": 0}))

    def delete_lesson_unlocks(self, user_id: str, month: str) -> None:
        self.db.lessonUnlocks.delete_many({"userId": user_id, "month": month})
