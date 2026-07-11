"""The locators: find the EXACT line/column of each error by walking the tree.

Pipeline position: this is where a bug's precise location is decided. Every
`locate_*` function takes a ParseResult (the tree from parser_utils) and returns
a list of DetectionResult — one per spot in the code that matches its pattern.

How these get called: error_catalog.py points each error type at one locator
here (spec.locator = locate_...). analyzer._detect_for_spec() then runs it:
  - rule_only types  -> locator runs directly (deterministic, no ML involved),
  - ml_gated types   -> locator runs ONLY after the ML model said "likely present".
So the same kind of function serves both modes; the catalog decides the mode.

What each locator does NOT do: it does not attach hints, ids, or final
confidence. It reports a raw DetectionResult (error_type, line, column, a
locator_confidence, a message). analyzer refines the confidence and hint_engine
adds the hints afterwards.

Shape of every locator (they all follow this template):
    root = parse_result.tree.root_node
    for node in collect_nodes_by_type(root, "<some_node_type>"):
        if <this node matches the buggy pattern>:
            findings.append(_result(...))
    return _deduplicate(findings)
"""

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


# Shared factory: build one DetectionResult from the node that pinpoints the bug.
# `node` decides the reported line/column (via node_to_span logic); `context_node`
# (if given) supplies the human-readable code snippet shown in the editor.
# locator_confidence is how sure the RULE is (hand-set per pattern, e.g. 0.95);
# analyzer later blends it with any ML probability into the final confidence.
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


# Same physical bug can be reached by more than one tree walk; this drops
# repeats keyed on (error_type, line, column, snippet). Every locator returns
# its findings through here so VS Code never shows two underlines on one spot.
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


# [ml_gated] Matches: a for-loop whose condition uses "<=" together with
# ".length" (e.g. i <= a.length), which runs one iteration too far. Only
# reached when the OFF_BY_ONE model has already flagged the file.
def locate_off_by_one_loop_boundaries(parse_result: ParseResult) -> List[DetectionResult]:
    root = parse_result.tree.root_node
    source_bytes = parse_result.source_bytes
    findings: List[DetectionResult] = []

    for_nodes = collect_nodes_by_type(root, "for_statement") # 1. every for-loop

    for for_node in for_nodes:
        condition_node = for_node.child_by_field_name("condition") # 2. its condition slot
        if condition_node is None:
            continue

        condition_text = _node_text(condition_node, source_bytes) # 3. the TEXT of it

        if "<=" in condition_text and ".length" in condition_text: # 4. crude string check
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


# [ml_gated] Matches: an assignment ("=") used inside an if/while condition
# where "==" was meant (e.g. if(ready = true)). Only reached when the
# INCORRECT_CONDITIONAL model has flagged the file.
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


# [ml_gated] Matches: indexing an array with its own .length (e.g. a[a.length]),
# always one past the last valid index. Only reached when the
# ARRAY_LENGTH_INDEX model has flagged the file. (This is the type whose file-
# level ML gate can suppress a real bug the locator would otherwise catch.)
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


# Shared helper: read the operator symbol ("==", "<=", "/", "||", "=") out of a
# binary_expression or assignment node. Many rule-only locators branch on this.
def _binary_operator(node) -> str:
    operator_node = node.child_by_field_name("operator")
    if operator_node is not None:
        return operator_node.type
    return node.children[1].type if len(node.children) >= 2 else ""


# Shared helper: strip surrounding parentheses so ((x != 1)) is treated the same
# as x != 1. Lets locators match the real inner expression regardless of how the
# student wrapped it.
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


# Shared helper for the string-equality locator: find every variable declared as
# a String (locals, parameters, fields). Comparing two of those with == is the
# classic beginner bug, so this builds the set of names to watch for.
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


# [rule_only] Matches: comparing strings with == or != (a string literal, or two
# known String variables) instead of .equals(). Skips comparisons against null.
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


# [rule_only] Matches: a for-loop that counts the wrong way for its condition
# (i < 10 but i-- , or i > 0 but i++), so it never reaches the bound.
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


# [rule_only] Matches: any statement that sits after a return in the same block,
# so it can never execute. Walks each block and flags the statement following
# the first return.
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

# [rule_only] Matches: a switch case (other than the last) whose body does not
# end in break/return/throw/continue/yield, so it falls through. Empty stacked
# labels (case 1: case 2:) are intentionally skipped.
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


# [rule_only] Matches: a stray semicolon right after an if/while/for header
# (e.g. if(x > 0); ), which makes the body empty so the condition controls
# nothing.
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


# [rule_only] Matches: assigning a variable to itself (x = x), where the left and
# right text are identical, so the statement does nothing.
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


# [rule_only] Matches: x != A || x != B where A and B are different constants —
# always true because a value can't equal both, so the guard is meaningless
# (the classic "|| should have been &&" bug).
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


# [rule_only] Matches: calling an immutable-String method (toUpperCase, trim,
# substring, replace, ...) as a standalone statement, throwing away the new
# string it returns. Strings never change in place, so the call has no effect.
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


# [rule_only] Matches: dividing or modding by the literal 0 (x / 0, x % 0),
# which throws ArithmeticException at runtime. Severity could be raised to
# "error" here since it always crashes.
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


# [rule_only] Matches: a for-loop whose counter starts at a literal that already
# fails the condition (e.g. for(i=10; i<5; i++)), so the body never runs. Uses
# _COMPARISON_CHECKS above to actually evaluate the first check.
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


# [rule_only] Matches: an else-if that repeats a condition already tested earlier
# in the same if/else-if chain, so that branch can never run. Walks each chain
# from its head and remembers conditions it has seen (whitespace-normalized).
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


# [rule_only] Matches: a while-loop whose condition variables are never changed
# in the body and which has no break/return/throw — a likely infinite loop.
# Deliberately skips conditions that call methods or read fields (those could
# change in ways this simple check can't see), to avoid false alarms.
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
