"""Candidate-level feature extraction: one feature row PER SITE, not per file.

Where file-level features (feature_extractor.py) aggregate the whole file and
answer "is this bug type probably SOMEWHERE in here?", a candidate row
describes ONE candidate site — here, one for-loop — and lets a model answer
"is THIS loop buggy?". The flagged candidate IS the location, so detection and
localization merge, and file size stops being an input entirely (see
docs/learning-sessions/10_candidate_level_features.md for the motivation and
the demonstrated file-level failure this eliminates).

Every feature is deliberately SITE-LOCAL: nothing about the rest of the file
leaks in. That is the property that makes candidate scoring immune to the
out-of-distribution file-shape drift documented in Session 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.analysis.issue_locators import collect_nodes_by_type
from app.models import ParseResult


@dataclass
class CandidateSite:
    """One scoreable site, anchored to editor coordinates."""
    line: int        # 1-based first line of the candidate (for_statement)
    end_line: int    # 1-based last line — used to match locator findings
    column: int
    features: Dict[str, float]


def _text(node, source_bytes: bytes) -> str:
    if node is None:
        return ""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _first_identifier(node, source_bytes: bytes) -> Optional[str]:
    if node is None:
        return None
    if node.type == "identifier":
        return _text(node, source_bytes)
    for child in node.children:
        found = _first_identifier(child, source_bytes)
        if found is not None:
            return found
    return None


def _count_type(node, wanted: str) -> int:
    if node is None:
        return 0
    total = 1 if node.type == wanted else 0
    for child in node.children:
        total += _count_type(child, wanted)
    return total


def extract_off_by_one_candidates(parse_result: ParseResult) -> List[CandidateSite]:
    """One candidate per for-statement, described only by its own parts."""
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    candidates: List[CandidateSite] = []

    for for_node in collect_nodes_by_type(root, "for_statement"):
        init_node = for_node.child_by_field_name("init")
        condition_node = for_node.child_by_field_name("condition")
        update_node = for_node.child_by_field_name("update")
        body_node = for_node.child_by_field_name("body")

        init_text = _text(init_node, source_bytes)
        condition_text = _text(condition_node, source_bytes)
        update_text = _text(update_node, source_bytes)
        body_text = _text(body_node, source_bytes)

        # The structural heart: what exactly is on the right of the comparison?
        right_is_bare_length = 0.0
        right_is_length_arithmetic = 0.0
        if condition_node is not None and condition_node.type == "binary_expression":
            right_node = condition_node.child_by_field_name("right")
            if right_node is not None:
                right_text = _text(right_node, source_bytes)
                if right_node.type == "field_access" and right_text.endswith(".length"):
                    right_is_bare_length = 1.0
                elif ".length" in right_text and right_node.type == "binary_expression":
                    right_is_length_arithmetic = 1.0

        loop_var = _first_identifier(init_node, source_bytes) or _first_identifier(condition_node, source_bytes)

        body_array_access_count = float(_count_type(body_node, "array_access"))
        loop_var_indexes_array = 0.0
        loop_var_body_uses = 0.0
        if loop_var and body_node is not None:
            loop_var_body_uses = float(body_text.count(loop_var))
            for access in collect_nodes_by_type(body_node, "array_access"):
                index_node = access.child_by_field_name("index")
                if _text(index_node, source_bytes).strip() == loop_var:
                    loop_var_indexes_array = 1.0

        features: Dict[str, float] = {
            "cond_uses_leq": 1.0 if "<=" in condition_text else 0.0,
            "cond_uses_lt": 1.0 if ("<" in condition_text and "<=" not in condition_text) else 0.0,
            "cond_uses_gt_or_geq": 1.0 if (">" in condition_text) else 0.0,
            "cond_contains_length": 1.0 if ".length" in condition_text else 0.0,
            "cond_crude_off_by_one": 1.0 if ("<=" in condition_text and ".length" in condition_text) else 0.0,
            "right_is_bare_length": right_is_bare_length,
            "right_is_length_arithmetic": right_is_length_arithmetic,
            "init_starts_at_zero": 1.0 if "= 0" in init_text.replace("=0", "= 0") else 0.0,
            "init_starts_at_one": 1.0 if "= 1" in init_text.replace("=1", "= 1") else 0.0,
            "update_is_increment": 1.0 if "++" in update_text else 0.0,
            "update_is_decrement": 1.0 if "--" in update_text else 0.0,
            "body_statement_count": float(_count_type(body_node, "expression_statement")),
            "body_array_access_count": body_array_access_count,
            "loop_var_indexes_array": loop_var_indexes_array,
            "loop_var_body_uses": loop_var_body_uses,
            "cond_char_count": float(len(condition_text)),
        }

        candidates.append(
            CandidateSite(
                line=for_node.start_point[0] + 1,
                end_line=for_node.end_point[0] + 1,
                column=for_node.start_point[1] + 1,
                features=features,
            )
        )

    return candidates


# Registry so the analyzer and dataset builder agree on which extractor serves
# which target. Extending candidate gating to another type = one entry here
# plus its extractor function above.
CANDIDATE_EXTRACTORS = {
    "has_off_by_one": extract_off_by_one_candidates,
}
