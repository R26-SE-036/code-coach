from typing import Optional

from app.models import DetectionResult, ParseResult
from app.parser_utils import (
    collect_nodes_by_type,
    find_first_descendant_by_type,
    get_node_text,
)


def locate_off_by_one_loop_boundary(parse_result: ParseResult) -> Optional[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes

    for_nodes = collect_nodes_by_type(root, "for_statement")

    for for_node in for_nodes:
        condition_node = for_node.child_by_field_name("condition")
        if condition_node is None:
            continue

        condition_text = get_node_text(condition_node, source_bytes).strip()

        if "<=" in condition_text and ".length" in condition_text:
            return DetectionResult(
                error_type="OFF_BY_ONE_LOOP_BOUNDARY",
                line=condition_node.start_point[0] + 1,
                column=condition_node.start_point[1] + 1,
                confidence=0.0,
                message="Possible off-by-one loop boundary issue detected.",
                code_context=get_node_text(for_node, source_bytes).splitlines()[0].strip(),
            )

    return None


def locate_incorrect_conditional_operator(parse_result: ParseResult) -> Optional[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes

    if_nodes = collect_nodes_by_type(root, "if_statement")

    for if_node in if_nodes:
        condition_node = if_node.child_by_field_name("condition")
        if condition_node is None:
            continue

        assignment_node = find_first_descendant_by_type(
            condition_node,
            "assignment_expression",
        )

        if assignment_node is not None:
            return DetectionResult(
                error_type="INCORRECT_CONDITIONAL_OPERATOR",
                line=assignment_node.start_point[0] + 1,
                column=assignment_node.start_point[1] + 1,
                confidence=0.0,
                message="Possible assignment used inside an if condition.",
                code_context=get_node_text(if_node, source_bytes).splitlines()[0].strip(),
            )

    return None


def locate_array_length_index_misuse(parse_result: ParseResult) -> Optional[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes

    array_access_nodes = collect_nodes_by_type(root, "array_access")

    for array_access_node in array_access_nodes:
        array_node = array_access_node.child_by_field_name("array")
        index_node = array_access_node.child_by_field_name("index")

        if array_node is None or index_node is None:
            continue

        array_text = get_node_text(array_node, source_bytes).strip()
        index_text = get_node_text(index_node, source_bytes).strip()

        if index_text == f"{array_text}.length":
            return DetectionResult(
                error_type="ARRAY_LENGTH_INDEX_MISUSE",
                line=index_node.start_point[0] + 1,
                column=index_node.start_point[1] + 1,
                confidence=0.0,
                message="Possible array index out-of-bounds issue detected.",
                code_context=get_node_text(array_access_node, source_bytes).strip(),
            )

    return None