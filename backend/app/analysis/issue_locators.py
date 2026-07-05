from typing import List

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


def _binary_operator(node) -> str:
    operator_node = node.child_by_field_name("operator")
    if operator_node is not None:
        return operator_node.type
    return node.children[1].type if len(node.children) >= 2 else ""


def _unwrap_parentheses(node):
    while node is not None and node.type == "parenthesized_expression":
        inner = None
        for child in node.named_children:
            inner = child
            break
        if inner is None:
            return node
        node = inner
    return node


def _collect_string_variable_names(root, source_bytes: bytes) -> set[str]:
    names: set[str] = set()
    declaration_types = (
        "local_variable_declaration",
        "formal_parameter",
        "field_declaration",
    )

    for declaration_type in declaration_types:
        for declaration in collect_nodes_by_type(root, declaration_type):
            type_node = declaration.child_by_field_name("type")
            if type_node is None or _node_text(type_node, source_bytes) != "String":
                continue

            for declarator in collect_nodes_by_type(declaration, "variable_declarator"):
                name_node = declarator.child_by_field_name("name")
                if name_node is not None:
                    names.add(_node_text(name_node, source_bytes))

            if declaration_type == "formal_parameter":
                name_node = declaration.child_by_field_name("name")
                if name_node is not None:
                    names.add(_node_text(name_node, source_bytes))

    return names


def locate_string_equality_with_operator(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    string_variables = _collect_string_variable_names(root, source_bytes)

    for binary_node in collect_nodes_by_type(root, "binary_expression"):
        if _binary_operator(binary_node) not in {"==", "!="}:
            continue

        left = _unwrap_parentheses(binary_node.child_by_field_name("left"))
        right = _unwrap_parentheses(binary_node.child_by_field_name("right"))
        if left is None or right is None:
            continue

        operand_types = {left.type, right.type}
        if "null_literal" in operand_types:
            continue

        is_string_comparison = "string_literal" in operand_types or (
            left.type == "identifier"
            and right.type == "identifier"
            and _node_text(left, source_bytes) in string_variables
            and _node_text(right, source_bytes) in string_variables
        )

        if is_string_comparison:
            findings.append(
                _result(
                    "STRING_EQUALITY_WITH_OPERATOR",
                    binary_node,
                    source_bytes,
                    0.93,
                    "Possible string comparison using == or != instead of .equals().",
                )
            )

    return _deduplicate(findings)


def locate_loop_update_wrong_directions(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for for_node in collect_nodes_by_type(root, "for_statement"):
        condition_node = for_node.child_by_field_name("condition")
        update_node = for_node.child_by_field_name("update")
        if condition_node is None or update_node is None:
            continue

        condition = _unwrap_parentheses(condition_node)
        if condition is None or condition.type != "binary_expression":
            continue

        operator = _binary_operator(condition)
        update_text = _node_text(update_node, source_bytes)

        moves_down = "--" in update_text or "-=" in update_text
        moves_up = "++" in update_text or "+=" in update_text

        if (operator in {"<", "<="} and moves_down and not moves_up) or (
            operator in {">", ">="} and moves_up and not moves_down
        ):
            findings.append(
                _result(
                    "LOOP_UPDATE_WRONG_DIRECTION",
                    condition,
                    source_bytes,
                    0.94,
                    "Loop update moves the counter away from the loop bound, so the loop may never finish.",
                    context_node=for_node,
                )
            )

    return _deduplicate(findings)


def locate_unreachable_code_after_return(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for block_node in collect_nodes_by_type(root, "block"):
        statements = [
            child
            for child in block_node.named_children
            if child.type not in {"line_comment", "block_comment"}
        ]
        for index, statement in enumerate(statements[:-1]):
            if statement.type == "return_statement":
                findings.append(
                    _result(
                        "UNREACHABLE_CODE_AFTER_RETURN",
                        statements[index + 1],
                        source_bytes,
                        0.97,
                        "This statement can never run because the method returns before it.",
                    )
                )
                break

    return _deduplicate(findings)


_SWITCH_EXIT_STATEMENTS = {
    "break_statement",
    "return_statement",
    "throw_statement",
    "continue_statement",
    "yield_statement",
}


def locate_missing_breaks_in_switch(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for switch_block in collect_nodes_by_type(root, "switch_block"):
        groups = [
            child
            for child in switch_block.named_children
            if child.type == "switch_block_statement_group"
        ]

        for group in groups[:-1]:
            statements = [
                child
                for child in group.named_children
                if child.type != "switch_label"
            ]
            # Empty groups stack labels intentionally (case 1: case 2: ...).
            if not statements:
                continue

            if statements[-1].type not in _SWITCH_EXIT_STATEMENTS:
                findings.append(
                    _result(
                        "MISSING_BREAK_IN_SWITCH",
                        group,
                        source_bytes,
                        0.85,
                        "This case may fall through into the next case because it does not end with break.",
                    )
                )

    return _deduplicate(findings)


def locate_empty_conditional_bodies(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    checks = (
        ("if_statement", "consequence"),
        ("while_statement", "body"),
        ("for_statement", "body"),
    )

    for statement_type, body_field in checks:
        for statement_node in collect_nodes_by_type(root, statement_type):
            body_node = statement_node.child_by_field_name(body_field)
            if body_node is not None and body_node.type == ";":
                findings.append(
                    _result(
                        "EMPTY_CONDITIONAL_BODY",
                        statement_node,
                        source_bytes,
                        0.93,
                        "A semicolon right after the condition makes the body empty, so the condition controls nothing.",
                    )
                )

    return _deduplicate(findings)


def locate_self_assignments(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for assignment_node in collect_nodes_by_type(root, "assignment_expression"):
        if _binary_operator(assignment_node) != "=":
            continue

        left = assignment_node.child_by_field_name("left")
        right = assignment_node.child_by_field_name("right")
        if left is None or right is None:
            continue

        if _node_text(left, source_bytes) == _node_text(right, source_bytes):
            findings.append(
                _result(
                    "SELF_ASSIGNMENT",
                    assignment_node,
                    source_bytes,
                    0.96,
                    "This assigns a variable to itself, so nothing changes.",
                )
            )

    return _deduplicate(findings)


def locate_always_true_or_conditions(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    literal_types = {
        "decimal_integer_literal",
        "string_literal",
        "character_literal",
        "true",
        "false",
    }

    for binary_node in collect_nodes_by_type(root, "binary_expression"):
        if _binary_operator(binary_node) != "||":
            continue

        left = _unwrap_parentheses(binary_node.child_by_field_name("left"))
        right = _unwrap_parentheses(binary_node.child_by_field_name("right"))
        if left is None or right is None:
            continue
        if left.type != "binary_expression" or right.type != "binary_expression":
            continue
        if _binary_operator(left) != "!=" or _binary_operator(right) != "!=":
            continue

        left_var = left.child_by_field_name("left")
        right_var = right.child_by_field_name("left")
        left_value = left.child_by_field_name("right")
        right_value = right.child_by_field_name("right")
        if None in (left_var, right_var, left_value, right_value):
            continue

        same_variable = (
            left_var.type == "identifier"
            and right_var.type == "identifier"
            and _node_text(left_var, source_bytes) == _node_text(right_var, source_bytes)
        )
        different_literals = (
            left_value.type in literal_types
            and right_value.type in literal_types
            and _node_text(left_value, source_bytes) != _node_text(right_value, source_bytes)
        )

        if same_variable and different_literals:
            findings.append(
                _result(
                    "ALWAYS_TRUE_OR_CONDITION",
                    binary_node,
                    source_bytes,
                    0.9,
                    "This condition is always true: a value always differs from at least one of two different constants.",
                )
            )

    return _deduplicate(findings)


_IMMUTABLE_STRING_METHODS = {
    "toUpperCase",
    "toLowerCase",
    "trim",
    "strip",
    "substring",
    "replace",
    "replaceAll",
    "replaceFirst",
    "concat",
    "repeat",
}


def locate_ignored_string_method_results(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for statement_node in collect_nodes_by_type(root, "expression_statement"):
        invocation = None
        for child in statement_node.named_children:
            invocation = child
            break

        if invocation is None or invocation.type != "method_invocation":
            continue

        object_node = invocation.child_by_field_name("object")
        name_node = invocation.child_by_field_name("name")
        if object_node is None or name_node is None:
            continue

        if _node_text(name_node, source_bytes) in _IMMUTABLE_STRING_METHODS:
            findings.append(
                _result(
                    "IGNORED_STRING_METHOD_RESULT",
                    invocation,
                    source_bytes,
                    0.88,
                    "This String method returns a new value that is thrown away; strings are never changed in place.",
                )
            )

    return _deduplicate(findings)


def locate_division_by_zero_literals(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for binary_node in collect_nodes_by_type(root, "binary_expression"):
        if _binary_operator(binary_node) not in {"/", "%"}:
            continue

        right = _unwrap_parentheses(binary_node.child_by_field_name("right"))
        if right is None:
            continue

        if (
            right.type == "decimal_integer_literal"
            and _node_text(right, source_bytes) == "0"
        ):
            findings.append(
                _result(
                    "DIVISION_BY_ZERO_LITERAL",
                    binary_node,
                    source_bytes,
                    0.97,
                    "Dividing by the literal 0 will crash the program with an ArithmeticException.",
                )
            )

    return _deduplicate(findings)


_COMPARISON_CHECKS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def locate_constant_false_loop_conditions(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for for_node in collect_nodes_by_type(root, "for_statement"):
        init_node = for_node.child_by_field_name("init")
        condition_node = for_node.child_by_field_name("condition")
        if init_node is None or condition_node is None:
            continue

        declarator = find_first_descendant_by_type(init_node, "variable_declarator")
        if declarator is None:
            continue

        name_node = declarator.child_by_field_name("name")
        value_node = declarator.child_by_field_name("value")
        if name_node is None or value_node is None:
            continue
        if value_node.type != "decimal_integer_literal":
            continue

        condition = _unwrap_parentheses(condition_node)
        if condition is None or condition.type != "binary_expression":
            continue

        operator = _binary_operator(condition)
        check = _COMPARISON_CHECKS.get(operator)
        if check is None:
            continue

        cond_left = condition.child_by_field_name("left")
        cond_right = condition.child_by_field_name("right")
        if cond_left is None or cond_right is None:
            continue
        if cond_left.type != "identifier" or cond_right.type != "decimal_integer_literal":
            continue
        if _node_text(cond_left, source_bytes) != _node_text(name_node, source_bytes):
            continue

        initial_value = int(_node_text(value_node, source_bytes))
        bound_value = int(_node_text(cond_right, source_bytes))

        if not check(initial_value, bound_value):
            findings.append(
                _result(
                    "CONSTANT_FALSE_LOOP_CONDITION",
                    condition,
                    source_bytes,
                    0.95,
                    "The loop condition is already false at the first check, so the loop body never runs.",
                    context_node=for_node,
                )
            )

    return _deduplicate(findings)


def locate_duplicate_if_else_conditions(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    def _is_chain_head(if_node) -> bool:
        parent = if_node.parent
        if parent is None or parent.type != "if_statement":
            return True
        return parent.child_by_field_name("alternative") != if_node

    def _normalized_condition(if_node) -> str:
        condition_node = if_node.child_by_field_name("condition")
        if condition_node is None:
            return ""
        return "".join(_node_text(condition_node, source_bytes).split())

    for if_node in collect_nodes_by_type(root, "if_statement"):
        if not _is_chain_head(if_node):
            continue

        seen_conditions: set[str] = set()
        current = if_node
        while current is not None and current.type == "if_statement":
            condition_text = _normalized_condition(current)
            if condition_text and condition_text in seen_conditions:
                findings.append(
                    _result(
                        "DUPLICATE_IF_ELSE_CONDITION",
                        current.child_by_field_name("condition") or current,
                        source_bytes,
                        0.95,
                        "This else-if repeats an earlier condition, so this branch can never run.",
                        context_node=current,
                    )
                )
            seen_conditions.add(condition_text)
            current = current.child_by_field_name("alternative")

    return _deduplicate(findings)


def locate_while_variables_not_updated(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for while_node in collect_nodes_by_type(root, "while_statement"):
        condition_node = while_node.child_by_field_name("condition")
        body_node = while_node.child_by_field_name("body")
        if condition_node is None or body_node is None:
            continue

        # Conditions calling methods or reading fields may change between
        # iterations in ways we cannot see, so only plain-variable
        # conditions are checked.
        if find_first_descendant_by_type(condition_node, "method_invocation") is not None:
            continue
        if find_first_descendant_by_type(condition_node, "field_access") is not None:
            continue

        condition_variables = {
            _node_text(identifier, source_bytes)
            for identifier in collect_nodes_by_type(condition_node, "identifier")
        }
        if not condition_variables:
            continue

        exits_early = any(
            find_first_descendant_by_type(body_node, exit_type) is not None
            for exit_type in ("break_statement", "return_statement", "throw_statement")
        )
        if exits_early:
            continue

        updated_variables: set[str] = set()
        for assignment in collect_nodes_by_type(body_node, "assignment_expression"):
            left = assignment.child_by_field_name("left")
            if left is not None:
                updated_variables.add(_node_text(left, source_bytes))
        for update in collect_nodes_by_type(body_node, "update_expression"):
            for identifier in collect_nodes_by_type(update, "identifier"):
                updated_variables.add(_node_text(identifier, source_bytes))

        if not (condition_variables & updated_variables):
            findings.append(
                _result(
                    "WHILE_VARIABLE_NOT_UPDATED",
                    condition_node,
                    source_bytes,
                    0.86,
                    "No variable used in this while condition changes inside the loop, so the loop may never end.",
                    context_node=while_node,
                )
            )

    return _deduplicate(findings)
