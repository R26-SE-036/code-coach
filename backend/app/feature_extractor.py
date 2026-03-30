from typing import Any, Dict, List, Optional

from app.parser_utils import (
    parse_java_code_safe,
    collect_nodes_by_type,
    get_node_text,
    find_first_descendant_by_type,
)


def _count_lines(code: str) -> int:
    if not code.strip():
        return 0
    return len(code.splitlines())


def _safe_text(node, source_bytes: bytes) -> str:
    if node is None:
        return ""
    return get_node_text(node, source_bytes).strip()


def _max_tree_depth(node, current_depth: int = 0) -> int:
    if node is None or not node.children:
        return current_depth
    return max(_max_tree_depth(child, current_depth + 1) for child in node.children)


def _count_descendants(node) -> int:
    if node is None:
        return 0

    total = 1
    for child in node.children:
        total += _count_descendants(child)
    return total


def _has_assignment_inside_condition(condition_node) -> int:
    if condition_node is None:
        return 0

    assignment_node = find_first_descendant_by_type(
        condition_node,
        "assignment_expression",
    )
    return 1 if assignment_node is not None else 0


def _count_logical_operators(text: str) -> int:
    return text.count("&&") + text.count("||")


def _extract_for_loop_features(root_node, source_bytes: bytes) -> Dict[str, Any]:
    for_nodes = collect_nodes_by_type(root_node, "for_statement")

    loop_condition_contains_lt = 0
    loop_condition_contains_leq = 0
    loop_condition_contains_gt = 0
    loop_condition_contains_geq = 0
    loop_condition_contains_length = 0
    loop_condition_off_by_one_pattern_count = 0

    for_node_with_array_access_count = 0
    max_for_loop_body_size = 0

    for for_node in for_nodes:
        condition_node = for_node.child_by_field_name("condition")
        body_node = for_node.child_by_field_name("body")

        condition_text = _safe_text(condition_node, source_bytes)

        if "<=" in condition_text:
            loop_condition_contains_leq += 1
        if "<" in condition_text:
            loop_condition_contains_lt += 1
        if ">=" in condition_text:
            loop_condition_contains_geq += 1
        if ">" in condition_text:
            loop_condition_contains_gt += 1
        if ".length" in condition_text:
            loop_condition_contains_length += 1
        if "<=" in condition_text and ".length" in condition_text:
            loop_condition_off_by_one_pattern_count += 1

        if body_node is not None:
            array_accesses_in_body = collect_nodes_by_type(body_node, "array_access")
            if array_accesses_in_body:
                for_node_with_array_access_count += 1

            body_size = _count_descendants(body_node)
            if body_size > max_for_loop_body_size:
                max_for_loop_body_size = body_size

    return {
        "for_statement_count": len(for_nodes),
        "loop_condition_contains_lt": loop_condition_contains_lt,
        "loop_condition_contains_leq": loop_condition_contains_leq,
        "loop_condition_contains_gt": loop_condition_contains_gt,
        "loop_condition_contains_geq": loop_condition_contains_geq,
        "loop_condition_contains_length": loop_condition_contains_length,
        "loop_condition_off_by_one_pattern_count": loop_condition_off_by_one_pattern_count,
        "for_node_with_array_access_count": for_node_with_array_access_count,
        "max_for_loop_body_size": max_for_loop_body_size,
    }


def _extract_if_features(root_node, source_bytes: bytes) -> Dict[str, Any]:
    if_nodes = collect_nodes_by_type(root_node, "if_statement")

    assignment_inside_if_condition_count = 0
    equality_in_if_condition_count = 0
    boolean_literal_in_if_condition_count = 0
    logical_operator_in_if_condition_count = 0

    for if_node in if_nodes:
        condition_node = if_node.child_by_field_name("condition")
        condition_text = _safe_text(condition_node, source_bytes)

        assignment_inside_if_condition_count += _has_assignment_inside_condition(condition_node)

        if "==" in condition_text or "!=" in condition_text:
            equality_in_if_condition_count += 1

        if "true" in condition_text or "false" in condition_text:
            boolean_literal_in_if_condition_count += 1

        if _count_logical_operators(condition_text) > 0:
            logical_operator_in_if_condition_count += 1

    return {
        "if_statement_count": len(if_nodes),
        "assignment_inside_if_condition_count": assignment_inside_if_condition_count,
        "equality_in_if_condition_count": equality_in_if_condition_count,
        "boolean_literal_in_if_condition_count": boolean_literal_in_if_condition_count,
        "logical_operator_in_if_condition_count": logical_operator_in_if_condition_count,
    }


def _extract_array_access_features(root_node, source_bytes: bytes) -> Dict[str, Any]:
    array_access_nodes = collect_nodes_by_type(root_node, "array_access")

    array_index_uses_length_directly_count = 0
    array_index_uses_length_expression_count = 0
    unique_arrays_accessed = set()

    for array_access_node in array_access_nodes:
        array_node = array_access_node.child_by_field_name("array")
        index_node = array_access_node.child_by_field_name("index")

        array_text = _safe_text(array_node, source_bytes)
        index_text = _safe_text(index_node, source_bytes)

        if array_text:
            unique_arrays_accessed.add(array_text)

        if array_text and index_text == f"{array_text}.length":
            array_index_uses_length_directly_count += 1

        if ".length" in index_text:
            array_index_uses_length_expression_count += 1

    return {
        "array_access_count": len(array_access_nodes),
        "array_index_uses_length_directly_count": array_index_uses_length_directly_count,
        "array_index_uses_length_expression_count": array_index_uses_length_expression_count,
        "unique_arrays_accessed_count": len(unique_arrays_accessed),
    }


def _extract_general_ast_features(root_node) -> Dict[str, Any]:
    method_nodes = collect_nodes_by_type(root_node, "method_declaration")
    class_nodes = collect_nodes_by_type(root_node, "class_declaration")
    local_var_nodes = collect_nodes_by_type(root_node, "local_variable_declaration")
    return_nodes = collect_nodes_by_type(root_node, "return_statement")
    while_nodes = collect_nodes_by_type(root_node, "while_statement")
    assignment_nodes = collect_nodes_by_type(root_node, "assignment_expression")
    binary_expression_nodes = collect_nodes_by_type(root_node, "binary_expression")

    return {
        "class_declaration_count": len(class_nodes),
        "method_declaration_count": len(method_nodes),
        "local_variable_declaration_count": len(local_var_nodes),
        "return_statement_count": len(return_nodes),
        "while_statement_count": len(while_nodes),
        "assignment_expression_count": len(assignment_nodes),
        "binary_expression_count": len(binary_expression_nodes),
        "max_ast_depth": _max_tree_depth(root_node, 0),
        "ast_node_count": _count_descendants(root_node),
    }


def extract_features(code: str) -> Dict[str, Any]:
    parse_result = parse_java_code_safe(code)

    base_features: Dict[str, Any] = {
        "line_count": _count_lines(code),
        "char_count": len(code),
        "parse_crashed": 1 if parse_result.crashed else 0,
        "parse_completeness": parse_result.health.completeness_score,
        "has_error_nodes": 1 if parse_result.health.has_error_nodes else 0,
        "error_node_count": parse_result.health.error_node_count,
        "missing_node_count": parse_result.health.missing_node_count,
        "unstable_span_count": len(parse_result.health.unstable_spans),
    }

    if parse_result.crashed or parse_result.tree is None:
        return base_features

    root_node = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes

    feature_groups = {}
    feature_groups.update(_extract_general_ast_features(root_node))
    feature_groups.update(_extract_for_loop_features(root_node, source_bytes))
    feature_groups.update(_extract_if_features(root_node, source_bytes))
    feature_groups.update(_extract_array_access_features(root_node, source_bytes))

    base_features.update(feature_groups)
    return base_features