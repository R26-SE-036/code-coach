"""Turn a Java file into a flat dict of numbers (the ML feature vector).

Pipeline position: sits between parser_utils (below) and ml_engine (above).
The ML models cannot read source code or a tree — they only understand a fixed
row of numbers. This file produces that row.

Data flow:
    code (str)
      -> parse_java_code_safe()        (from parser_utils; note it re-parses
                                         here, independently of analyzer's parse)
      -> count AST constructs           (for-loops, if-conditions, array access,
                                         node depth, "<=" with ".length", etc.)
      -> feature_dict {name: number}    (returned)

Who consumes the output: analyzer.analyze_code() passes this dict to
ml_engine.predict_issue_types(), which lines the keys up against the exact
feature columns each trained model expects. So the feature NAMES here must stay
in sync with the columns the models were trained on (train_baselines.py).
Only the ml_gated error types use these features; rule_only types ignore them.

Adding NEW features is always safe for already-trained models: ml_engine's
_build_feature_frame reindexes to each model's feature_names_in_, so columns a
model never saw during training are simply ignored. New features only take
effect for models trained AFTER they were added.
"""

from typing import Any, Dict, List, Optional

from app.analysis.parser_utils import (
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


# Features about for-loops. These are the signals the OFF_BY_ONE model leans on
# most: does a loop condition use "<=" together with ".length"? how big is the
# loop body? does the body index into an array? Each returned key becomes one
# column in the feature row.
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


# Features about if-conditions. The key signal for the INCORRECT_CONDITIONAL
# model is assignment_inside_if_condition_count (a "=" where "==" was meant,
# e.g. if(ready = true)). Also counts equality operators, boolean literals,
# and &&/|| usage in conditions.
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


# Features about array indexing. The key signal for the ARRAY_LENGTH_INDEX
# model is array_index_uses_length_directly_count: writing a[a.length], which is
# always one past the last valid index. Also counts how many distinct arrays
# are touched.
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


# Statement types that legitimately end a switch case (mirrors the
# _SWITCH_EXIT_STATEMENTS set used by the MISSING_BREAK locator).
_SWITCH_EXIT_STATEMENT_TYPES = {
    "break_statement",
    "return_statement",
    "throw_statement",
    "continue_statement",
    "yield_statement",
}


# Features about switch statements. The key signal for the MISSING_BREAK model
# is switch_fallthrough_case_count (a non-last case whose body does not end in
# break/return/throw/continue/yield) — the same pattern the rule locator flags.
# The context features are what let the model judge INTENT, which the rule
# cannot: intentional fall-through is usually marked with a comment
# (switch_comment_count) or written as stacked empty labels
# (switch_empty_stacked_label_count).
def _extract_switch_features(root_node, source_bytes: bytes) -> Dict[str, Any]:
    switch_blocks = collect_nodes_by_type(root_node, "switch_block")

    switch_case_group_count = 0
    switch_case_ends_with_terminator_count = 0
    switch_fallthrough_case_count = 0
    switch_empty_stacked_label_count = 0
    switch_default_label_count = 0
    switch_comment_count = 0
    max_switch_case_body_size = 0

    for switch_block in switch_blocks:
        switch_comment_count += len(collect_nodes_by_type(switch_block, "line_comment"))
        switch_comment_count += len(collect_nodes_by_type(switch_block, "block_comment"))

        for label in collect_nodes_by_type(switch_block, "switch_label"):
            if _safe_text(label, source_bytes).startswith("default"):
                switch_default_label_count += 1

        groups = [
            child
            for child in switch_block.named_children
            if child.type == "switch_block_statement_group"
        ]
        switch_case_group_count += len(groups)

        for position, group in enumerate(groups):
            statements = [
                child
                for child in group.named_children
                if child.type != "switch_label"
            ]
            if not statements:
                # Labels stacked with no body (case 1: case 2:) — an
                # intentional grouping idiom, not a missing break.
                switch_empty_stacked_label_count += 1
                continue

            case_body_size = sum(_count_descendants(s) for s in statements)
            if case_body_size > max_switch_case_body_size:
                max_switch_case_body_size = case_body_size

            if statements[-1].type in _SWITCH_EXIT_STATEMENT_TYPES:
                switch_case_ends_with_terminator_count += 1
            elif position < len(groups) - 1:
                # Same condition the rule locator fires on: a non-last case
                # with a body that does not end in an exit statement.
                switch_fallthrough_case_count += 1

    return {
        "switch_block_count": len(switch_blocks),
        "switch_case_group_count": switch_case_group_count,
        "switch_case_ends_with_terminator_count": switch_case_ends_with_terminator_count,
        "switch_fallthrough_case_count": switch_fallthrough_case_count,
        "switch_empty_stacked_label_count": switch_empty_stacked_label_count,
        "switch_default_label_count": switch_default_label_count,
        "switch_comment_count": switch_comment_count,
        "max_switch_case_body_size": max_switch_case_body_size,
    }


# Features about while-loops. The key signal for the WHILE_NOT_UPDATED model is
# while_condition_var_not_updated_count — same conditions the rule locator uses
# (plain-variable condition, no early exit, no condition variable assigned or
# incremented in the body). The context features capture what the rule is blind
# to: method calls in the body (side effects could update state), method-call /
# field-access conditions (which the rule skips), and while(true)+break idioms.
def _extract_while_features(root_node, source_bytes: bytes) -> Dict[str, Any]:
    while_nodes = collect_nodes_by_type(root_node, "while_statement")

    while_condition_with_method_call_count = 0
    while_condition_with_field_access_count = 0
    while_condition_true_literal_count = 0
    while_body_with_exit_count = 0
    while_body_method_call_count = 0
    while_condition_var_updated_count = 0
    while_condition_var_not_updated_count = 0
    max_while_body_size = 0

    for while_node in while_nodes:
        condition_node = while_node.child_by_field_name("condition")
        body_node = while_node.child_by_field_name("body")
        condition_text = _safe_text(condition_node, source_bytes)

        condition_has_method_call = (
            condition_node is not None
            and find_first_descendant_by_type(condition_node, "method_invocation") is not None
        )
        condition_has_field_access = (
            condition_node is not None
            and find_first_descendant_by_type(condition_node, "field_access") is not None
        )

        if condition_has_method_call:
            while_condition_with_method_call_count += 1
        if condition_has_field_access:
            while_condition_with_field_access_count += 1
        if condition_text in {"(true)", "true"}:
            while_condition_true_literal_count += 1

        exits_early = False
        if body_node is not None:
            body_size = _count_descendants(body_node)
            if body_size > max_while_body_size:
                max_while_body_size = body_size

            while_body_method_call_count += len(
                collect_nodes_by_type(body_node, "method_invocation")
            )

            exits_early = any(
                find_first_descendant_by_type(body_node, exit_type) is not None
                for exit_type in ("break_statement", "return_statement", "throw_statement")
            )
            if exits_early:
                while_body_with_exit_count += 1

        if condition_node is None or body_node is None:
            continue

        condition_variables = {
            _safe_text(identifier, source_bytes)
            for identifier in collect_nodes_by_type(condition_node, "identifier")
        }
        if not condition_variables:
            continue

        updated_variables = set()
        for assignment in collect_nodes_by_type(body_node, "assignment_expression"):
            left = assignment.child_by_field_name("left")
            if left is not None:
                updated_variables.add(_safe_text(left, source_bytes))
        for update in collect_nodes_by_type(body_node, "update_expression"):
            for identifier in collect_nodes_by_type(update, "identifier"):
                updated_variables.add(_safe_text(identifier, source_bytes))

        if condition_variables & updated_variables:
            while_condition_var_updated_count += 1
        elif not condition_has_method_call and not condition_has_field_access and not exits_early:
            # Same condition the rule locator fires on.
            while_condition_var_not_updated_count += 1

    return {
        "while_condition_with_method_call_count": while_condition_with_method_call_count,
        "while_condition_with_field_access_count": while_condition_with_field_access_count,
        "while_condition_true_literal_count": while_condition_true_literal_count,
        "while_body_with_exit_count": while_body_with_exit_count,
        "while_body_method_call_count": while_body_method_call_count,
        "while_condition_var_updated_count": while_condition_var_updated_count,
        "while_condition_var_not_updated_count": while_condition_var_not_updated_count,
        "max_while_body_size": max_while_body_size,
    }


# Broad "shape of the code" features: how many classes/methods/loops/returns,
# how deep the tree is, how many nodes total. These give the models context
# (a tiny snippet vs. a large method) that sharpens the specific signals above.
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


# THE public entry point. Parses the code, then merges the four feature groups
# above with some base counts (lines, chars, parse health) into ONE flat dict.
# If parsing crashed it returns only the base features. The returned dict is
# what ml_engine.predict_issue_types() scores against each model.
#
# Note: this parses independently of analyzer's own parse_java_code_safe() call.
# Same input code, so same tree — just computed a second time here for features.
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
    feature_groups.update(_extract_switch_features(root_node, source_bytes))
    feature_groups.update(_extract_while_features(root_node, source_bytes))

    base_features.update(feature_groups)
    return base_features
