"""The model cards, as the editor and anyone curious read them.

Written by dev_tools/mutation/model_cards.py from the training and test
results and shipped with the models; this only reads them. `in_use` is added
here, from the live catalogue, because a type can be switched back to its old
detector (LEGACY_DETECTORS) without a new build - and then its card describes
a model that is not deciding anything.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Dict, List, Optional

from app.analysis.error_catalog import ERROR_CATALOG, MODELS_DIR

CARDS_PATH = MODELS_DIR / "model_cards_v1.json"


@lru_cache(maxsize=1)
def _cards() -> Dict[str, dict]:
    if not CARDS_PATH.exists():
        return {}
    return json.loads(CARDS_PATH.read_text(encoding="utf-8")).get("cards", {})


def _in_use(error_type: str) -> bool:
    spec = ERROR_CATALOG.get(error_type)
    return spec is not None and spec.detection_mode == "candidate_ml"


def model_card(error_type: str) -> Optional[dict]:
    card = _cards().get(error_type)
    return None if card is None else {**card, "in_use": _in_use(error_type)}


def model_card_index() -> List[dict]:
    return [
        {
            "error_type": error_type,
            "title": card["title"],
            "concept_tag": card["concept_tag"],
            "model": card["model"]["family_name"],
            "f1": (card["performance"].get("test") or {}).get("f1"),
            "in_use": _in_use(error_type),
        }
        for error_type, card in _cards().items()
    ]
