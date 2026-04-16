from typing import Callable, List, Optional

from app.models import DetectionResult, ParseResult
from app.analysis.parser_utils import (
    collect_nodes_by_type,
    find_first_descendant_by_type,
    get_node_text,
)


def _node_line(node) -> int:
    return node.start_point[0] + 1


def _node_column(node) -> int:
    return node.start_point[1] + 1


def _first_line(text: str) -> str:
    lines = text.strip().splitlines()
    return lines[0].strip() if lines else text.strip()


def _node_text(node, source_bytes: bytes) -> str:
    return get_node_text(node, source_bytes).strip()


def _node_context(node, source_bytes: bytes) -> str:
    return _first_line(get_node_text(node, source_bytes))


def _result(
    error_type: str,
    node,
    source_bytes: bytes,
    locator_confidence: float,
    message: str,
    *,
    context_node=None,
    severity: str = "warning",
) -> DetectionResult:
    return DetectionResult(
        error_type=error_type,
        line=_node_line(node),
        column=_node_column(node),
        confidence=locator_confidence,
        severity=severity,
        message=message,
        code_context=_node_context(context_node or node, source_bytes),
        locator_confidence=locator_confidence,
    )


def _deduplicate(results: List[DetectionResult]) -> List[DetectionResult]:
    deduplicated: List[DetectionResult] = []
    seen: set[tuple[str, int, int, str]] = set()

    for result in results:
        key = (
            result.error_type,
            result.line,
            result.column,
            result.code_context,
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(result)

    return deduplicated


def locate_off_by_one_loop_boundaries(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for_nodes = collect_nodes_by_type(root, "for_statement")

    for for_node in for_nodes:
        condition_node = for_node.child_by_field_name("condition")
        if condition_node is None:
            continue

        condition_text = _node_text(condition_node, source_bytes)

        if "<=" in condition_text and ".length" in condition_text:
            findings.append(
                _result(
                    "OFF_BY_ONE_LOOP_BOUNDARY",
                    condition_node,
                    source_bytes,
                    0.95,
                    "Possible off-by-one loop boundary issue detected.",
                    context_node=for_node,
                )
            )

    return _deduplicate(findings)


def locate_incorrect_conditional_operators(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    conditional_nodes = collect_nodes_by_type(root, "if_statement")
    conditional_nodes.extend(collect_nodes_by_type(root, "while_statement"))

    for conditional_node in conditional_nodes:
        condition_node = conditional_node.child_by_field_name("condition")
        if condition_node is None:
            continue

        assignment_node = find_first_descendant_by_type(
            condition_node,
            "assignment_expression",
        )

        if assignment_node is None:
            continue

        findings.append(
            _result(
                "INCORRECT_CONDITIONAL_OPERATOR",
                assignment_node,
                source_bytes,
                0.92,
                "Possible assignment used inside a condition.",
                context_node=conditional_node,
            )
        )

    return _deduplicate(findings)


def locate_array_length_index_misuses(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for array_access_node in collect_nodes_by_type(root, "array_access"):
        array_node = array_access_node.child_by_field_name("array")
        index_node = array_access_node.child_by_field_name("index")

        if array_node is None or index_node is None:
            continue

        array_text = _node_text(array_node, source_bytes)
        index_text = _node_text(index_node, source_bytes)

        if index_text == f"{array_text}.length":
            findings.append(
                _result(
                    "ARRAY_LENGTH_INDEX_MISUSE",
                    index_node,
                    source_bytes,
                    0.94,
                    "Possible array index out-of-bounds issue detected.",
                    context_node=array_access_node,
                )
            )

    return _deduplicate(findings)


TARGET_LOCATORS: dict[str, Callable[[ParseResult], List[DetectionResult]]] = {
    "OFF_BY_ONE_LOOP_BOUNDARY": locate_off_by_one_loop_boundaries,
    "INCORRECT_CONDITIONAL_OPERATOR": locate_incorrect_conditional_operators,
    "ARRAY_LENGTH_INDEX_MISUSE": locate_array_length_index_misuses,
}


def _first_or_none(results: List[DetectionResult]) -> Optional[DetectionResult]:
    return results[0] if results else None


def locate_off_by_one_loop_boundary(parse_result: ParseResult) -> Optional[DetectionResult]:
    return _first_or_none(locate_off_by_one_loop_boundaries(parse_result))


def locate_incorrect_conditional_operator(parse_result: ParseResult) -> Optional[DetectionResult]:
    return _first_or_none(locate_incorrect_conditional_operators(parse_result))


def locate_array_length_index_misuse(parse_result: ParseResult) -> Optional[DetectionResult]:
    return _first_or_none(locate_array_length_index_misuses(parse_result))
