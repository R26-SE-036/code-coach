"""Mutation operators for the thirteen types moved onto per-site models.

Same contract as mutators.py: take a parsed CORRECT program, return every
Mutation of one kind - the new source and where the mutated site is in it.
Whether a mutant is a real bug is decided by running it (build_mutation_corpus),
except for the few types labelled by construction there.

Where an edit lands away from the site it breaks - deleting the zero check at
the top of a method breaks the division further down - the Mutation's span is
the DIVISION's position in the new source, because that is where the
candidate (and the student's underline) is.
"""

from __future__ import annotations

import random
import re
from typing import Callable, Dict, List, Tuple

from app.analysis import java_facts as jf
from app.analysis.promoted_candidates import Types, _init_node
from app.dev_tools.mutation.mutators import Mutation, _b, _for_loops, _mutation
from app.models import ParseResult


def _op_node(binary):
    return binary.child_by_field_name("operator") or binary.children[1]


def _shift(position: int, edits: List[Tuple[int, int, bytes]]) -> int:
    """Where old byte `position` (outside every edit) is after the edits."""
    return position + sum(len(new) - (end - start) for start, end, new in edits if end <= position)


def _at(pr: ParseResult, edits: List[Tuple[int, int, bytes]], site: Tuple[int, int], note: str) -> Mutation:
    """A mutation whose span is `site` (old bytes, outside the edits) moved into the new source."""
    mutation = _mutation(pr, edits, note)
    start, end = _shift(site[0], edits), _shift(site[1], edits)
    mutation.spans = [(start, max(end, start + 1))]
    return mutation


# 1. i < a.length  ->  i <= a.length ;  i = a.length - 1 (counting down)  ->  i = a.length
def mutate_off_by_one_loop_boundary(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for loop in _for_loops(pr):
        var = jf.for_loop_var(loop, source)
        condition = jf.unwrap(loop.child_by_field_name("condition"))
        updates = jf.for_updates(loop)
        if not var or condition is None or condition.type != "binary_expression" or not updates:
            continue
        left, right = jf.unwrap(condition.child_by_field_name("left")), jf.unwrap(condition.child_by_field_name("right"))
        if left is None or jf.text(left, source) != var or right is None:
            continue
        op, direction = jf.operator(condition), jf.update_direction(updates[0], var, source)
        target, k = jf.length_minus(right, source)
        if direction == 1 and op == "<" and ((target and k == 0) or right.type == "identifier"):
            node = _op_node(condition)
            out.append(_mutation(pr, [(node.start_byte, node.end_byte, b"<=")], "< becomes <="))
        init = jf.unwrap(_init_node(loop))
        init_target, init_k = jf.length_minus(init, source)
        if direction == -1 and op in (">=", ">") and init_target and init_k == 1 and init.type == "binary_expression":
            length = jf.unwrap(init.child_by_field_name("left"))
            out.append(_mutation(pr, [(init.start_byte, init.end_byte, _b(jf.text(length, source)))], "count down from the length"))
    return out


# 2. if (flag) -> if (flag = true) ; if (!flag) -> if (flag = false) ; done == false -> done = false
def mutate_incorrect_conditional_operator(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    types = Types(pr)
    out = []
    for statement in jf.descendants(pr.tree.root_node, "if_statement", "while_statement", "do_statement", "for_statement"):
        condition = statement.child_by_field_name("condition")
        if condition is None:
            continue
        inner = jf.unwrap(condition)
        if inner is not None and inner.type == "identifier" and types.kind(inner) == "boolean":
            out.append(_mutation(pr, [(inner.start_byte, inner.end_byte, _b(jf.text(inner, source) + " = true"))], "flag -> flag = true"))
        if inner is not None and inner.type == "unary_expression" and jf.text(inner, source).lstrip().startswith("!"):
            operand = jf.unwrap(inner.child_by_field_name("operand"))
            if operand is not None and operand.type == "identifier" and types.kind(operand) == "boolean":
                out.append(_mutation(pr, [(inner.start_byte, inner.end_byte, _b(jf.text(operand, source) + " = false"))], "!flag -> flag = false"))
        for binary in jf.descendants(condition, "binary_expression"):
            if jf.operator(binary) != "==":
                continue
            left, right = jf.unwrap(binary.child_by_field_name("left")), jf.unwrap(binary.child_by_field_name("right"))
            if left is not None and left.type == "identifier" and types.kind(left) == "boolean" and types.kind(right) == "boolean":
                node = _op_node(binary)
                out.append(_mutation(pr, [(node.start_byte, node.end_byte, b"=")], "== -> ="))
    return out


# 3. a[a.length - 1] -> a[a.length] ; s.charAt(s.length() - 1) -> s.charAt(s.length())
def mutate_array_length_index_misuse(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for _, collection, index in jf.indexed_accesses(pr.tree.root_node, source):
        node = jf.unwrap(index)
        target, k = jf.length_minus(node, source)
        if target == collection and k == 1 and node.type == "binary_expression":
            length = jf.unwrap(node.child_by_field_name("left"))
            out.append(_mutation(pr, [(node.start_byte, node.end_byte, _b(jf.text(length, source)))], "index the length itself"))
    return out


# 4. delete the break at the end of a case
def mutate_missing_break_in_switch(pr: ParseResult) -> List[Mutation]:
    out = []
    for switch_block in jf.descendants(pr.tree.root_node, "switch_block"):
        groups = [child for child in switch_block.named_children if child.type == "switch_block_statement_group"]
        for group in groups[:-1]:
            statements = [c for c in group.named_children if c.type != "switch_label" and c.type not in jf.COMMENT_TYPES]
            if len(statements) >= 2 and statements[-1].type == "break_statement":
                brk = statements[-1]
                out.append(_mutation(pr, [(brk.start_byte, brk.end_byte, b"")], "break removed"))
    return out


# 5. delete a statement that moves the while condition along
def mutate_while_variable_not_updated(pr: ParseResult, rng: random.Random) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for loop in jf.descendants(pr.tree.root_node, "while_statement", "do_statement"):
        condition, body = loop.child_by_field_name("condition"), loop.child_by_field_name("body")
        if condition is None or body is None or body.type != "block":
            continue
        names = set(jf.identifiers(condition, source))
        steps = [s for s in jf.statements(body) if s.type == "expression_statement" and jf.written_vars(s, source) & names]
        rng.shuffle(steps)
        for step in steps[:2]:
            out.append(_mutation(pr, [(step.start_byte, step.end_byte, b"")], "condition update removed"))
    return out


# 6. a.equals(b) -> a == b ; !a.equals(b) -> a != b
def mutate_string_equality_with_operator(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    types = Types(pr)
    out = []
    for call in jf.descendants(pr.tree.root_node, "method_invocation"):
        name = jf.text(call.child_by_field_name("name"), source)
        receiver, args = call.child_by_field_name("object"), call.child_by_field_name("arguments")
        if name not in ("equals", "equalsIgnoreCase") or receiver is None or args is None or len(args.named_children) != 1:
            continue
        argument = args.named_children[0]
        if "string" not in (types.kind(receiver), types.kind(argument)):
            continue
        left, right = jf.text(receiver, source), jf.text(argument, source)
        parent = call.parent
        if parent is not None and parent.type == "unary_expression" and jf.text(parent, source).lstrip().startswith("!"):
            node, text = parent, f"{left} != {right}"
        else:
            node, text = call, f"{left} == {right}"
        holder = node.parent
        bare = holder is not None and (holder.type in ("parenthesized_expression", "return_statement", "variable_declarator", "assignment_expression", "argument_list")
                                       or (holder.type == "binary_expression" and jf.operator(holder) in ("&&", "||")))
        out.append(_mutation(pr, [(node.start_byte, node.end_byte, _b(text if bare else f"({text})"))], f"{name} -> =="))
    return out


# 7. i++ -> i-- (and back) in a for update
def mutate_loop_update_wrong_direction(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for loop in _for_loops(pr):
        var = jf.for_loop_var(loop, source)
        update = loop.child_by_field_name("update")
        condition = jf.unwrap(loop.child_by_field_name("condition"))
        if not var or update is None or condition is None or condition.type != "binary_expression":
            continue
        text = jf.text(update, source)
        flipped = (text.replace("++", "\0").replace("--", "++").replace("\0", "--")
                   .replace("+=", "\1").replace("-=", "+=").replace("\1", "-="))
        flipped = re.sub(rf"({re.escape(var)}\s*=\s*{re.escape(var)}\s*)([+-])", lambda m: m.group(1) + ("-" if m.group(2) == "+" else "+"), flipped)
        if flipped != text and jf.update_direction(update, var, source) != 0:
            out.append(_mutation(pr, [(update.start_byte, update.end_byte, _b(flipped))], "update reversed"))
    return out


# 8. i < n -> i > n (the loop never starts) ; or the start and the bound swapped
def mutate_constant_false_loop_condition(pr: ParseResult, rng: random.Random) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    flips = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}
    for loop in _for_loops(pr):
        var = jf.for_loop_var(loop, source)
        condition = jf.unwrap(loop.child_by_field_name("condition"))
        init = jf.unwrap(_init_node(loop))
        updates = jf.for_updates(loop)
        if not var or condition is None or condition.type != "binary_expression" or init is None or not updates:
            continue
        left, right = jf.unwrap(condition.child_by_field_name("left")), jf.unwrap(condition.child_by_field_name("right"))
        op = jf.operator(condition)
        if left is None or right is None or jf.text(left, source) != var or op not in flips:
            continue
        direction = jf.update_direction(updates[0], var, source)
        if (direction == 1 and op in ("<", "<=")) or (direction == -1 and op in (">", ">=")):
            node = _op_node(condition)
            out.append(_mutation(pr, [(node.start_byte, node.end_byte, _b(flips[op]))], "comparison flipped"))
            simple = {"identifier", "decimal_integer_literal", "field_access", "method_invocation"}
            if init.type in simple and right.type in simple and rng.random() < 0.6:
                out.append(_mutation(pr, [(init.start_byte, init.end_byte, source[right.start_byte:right.end_byte]),
                                          (right.start_byte, right.end_byte, source[init.start_byte:init.end_byte])], "start and bound swapped"))
    return out


# 9. s = s.trim();  ->  s.trim();
def mutate_ignored_string_method_result(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    types = Types(pr)
    out = []
    for statement in jf.descendants(pr.tree.root_node, "expression_statement"):
        assignment = next((c for c in statement.named_children if c.type not in jf.COMMENT_TYPES), None)
        if assignment is None or assignment.type != "assignment_expression" or jf.operator(assignment) != "=":
            continue
        left, right = assignment.child_by_field_name("left"), jf.unwrap(assignment.child_by_field_name("right"))
        if left is None or left.type != "identifier" or right is None or right.type != "method_invocation":
            continue
        receiver = right.child_by_field_name("object")
        while receiver is not None and receiver.type == "method_invocation":
            receiver = receiver.child_by_field_name("object")
        if receiver is None or jf.text(receiver, source) != jf.text(left, source) or types.kind(left) != "string":
            continue
        out.append(_mutation(pr, [(left.start_byte, right.start_byte, b"")], "result not stored"))
    return out


# 10. the zero check removed: a guard return, a ternary, or the if around it
_ZERO_TEST = re.compile(r"(==|<=)\s*0\b|\.isEmpty\(\)|\b0\s*==|<\s*1\b")
_NONZERO_TEST = re.compile(r"(!=|>)\s*0\b|>=\s*1\b|!\s*\w+\.isEmpty\(\)")


def _divisions(node, source: bytes) -> List:
    return [d for d in jf.descendants(node, "binary_expression", "assignment_expression") if jf.operator(d) in ("/", "%", "/=", "%=")
            and jf.literal_kind(jf.text(jf.unwrap(d.child_by_field_name("right")), source)) not in ("int", "decimal")]


def _divisor_names(division, source: bytes) -> List[str]:
    divisor = jf.unwrap(division.child_by_field_name("right"))
    target, _ = jf.length_minus(divisor, source)
    return [target] if target else [jf.text(divisor, source).strip()]


def mutate_division_by_zero(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for method in jf.descendants(pr.tree.root_node, "method_declaration"):
        divisions = _divisions(method, source)
        if not divisions:
            continue
        for guard in jf.descendants(method, "if_statement"):
            condition = guard.child_by_field_name("condition")
            consequence = guard.child_by_field_name("consequence")
            if condition is None or consequence is None:
                continue
            text = jf.text(condition, source)
            after = [d for d in divisions if d.start_byte > guard.end_byte and any(re.search(rf"\b{re.escape(n)}\b", text) for n in _divisor_names(d, source))]
            inside = [d for d in divisions if jf.is_inside(d, consequence) and any(re.search(rf"\b{re.escape(n)}\b", text) for n in _divisor_names(d, source))]
            exits = any(s.type in ("return_statement", "throw_statement") for s in jf.statements(consequence))
            if after and exits and _ZERO_TEST.search(text) and guard.child_by_field_name("alternative") is None:
                inner = jf.unwrap(condition)
                if "null" in text:
                    # Keep the null half: removing it would crash on null, not on zero.
                    if inner is not None and inner.type == "binary_expression" and jf.operator(inner) == "||":
                        keep = next((side for side in (inner.child_by_field_name("left"), inner.child_by_field_name("right")) if "null" in jf.text(side, source)), None)
                        if keep is not None and not _ZERO_TEST.search(jf.text(keep, source)):
                            edits = [(inner.start_byte, inner.end_byte, source[keep.start_byte:keep.end_byte])]
                            out.append(_at(pr, edits, jf.span(after[0]), "zero half of the guard removed"))
                    continue
                edits = [(guard.start_byte, guard.end_byte, b"")]
                out.append(_at(pr, edits, jf.span(after[0]), "zero guard removed"))
            if inside and _NONZERO_TEST.search(text) and "null" not in text and guard.child_by_field_name("alternative") is None:
                body = consequence
                if body.type == "block":
                    inner_start, inner_end = body.children[0].end_byte, body.children[-1].start_byte
                else:
                    inner_start, inner_end = body.start_byte, body.end_byte
                replacement = source[inner_start:inner_end].strip()
                lead = len(source[inner_start:inner_end]) - len(source[inner_start:inner_end].lstrip())
                edits = [(guard.start_byte, guard.end_byte, replacement)]
                division = inside[0]
                mutation = _mutation(pr, edits, "if around the division removed")
                new_start = guard.start_byte + (division.start_byte - inner_start - lead)
                mutation.spans = [(new_start, new_start + (division.end_byte - division.start_byte))]
                out.append(mutation)
        for ternary in jf.descendants(method, "ternary_expression"):
            condition = ternary.child_by_field_name("condition")
            text = jf.text(condition, source)
            for branch_name, test in (("alternative", _ZERO_TEST), ("consequence", _NONZERO_TEST)):
                branch = ternary.child_by_field_name(branch_name)
                hits = [d for d in _divisions(branch, source) if any(re.search(rf"\b{re.escape(n)}\b", text) for n in _divisor_names(d, source))]
                if branch is not None and hits and test.search(text) and "null" not in text:
                    edits = [(ternary.start_byte, ternary.end_byte, b"(" + source[branch.start_byte:branch.end_byte] + b")")]
                    mutation = _mutation(pr, edits, "ternary guard removed")
                    new_start = ternary.start_byte + 1 + (hits[0].start_byte - branch.start_byte)
                    mutation.spans = [(new_start, new_start + (hits[0].end_byte - hits[0].start_byte))]
                    out.append(mutation)
    return out


# 11. (double) total / count -> total / count ; total / 2.0 -> total / 2 ; 100.0 * a / b -> 100 * a / b
def mutate_integer_division_in_decimal_context(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    types = Types(pr)
    out = []
    for division in jf.descendants(pr.tree.root_node, "binary_expression"):
        if jf.operator(division) != "/":
            continue
        for side_name in ("left", "right"):
            side = division.child_by_field_name(side_name)
            other = division.child_by_field_name("right" if side_name == "left" else "left")
            inner = jf.unwrap(side)
            if inner is None:
                continue
            if inner.type == "cast_expression" and jf.text(inner.child_by_field_name("type"), source).strip() in ("double", "float"):
                value = inner.child_by_field_name("value")
                if types.kind(value) in ("int", "char") and types.kind(other) in ("int", "char"):
                    out.append(_mutation(pr, [(inner.start_byte, value.start_byte, b"")], "cast removed"))
            if inner.type == "decimal_floating_point_literal" and types.kind(other) in ("int", "char"):
                value = jf.text(inner, source).rstrip("dDfF")
                if re.fullmatch(r"\d+\.0*", value):
                    out.append(_mutation(pr, [(inner.start_byte, inner.end_byte, _b(value.split(".")[0]))], "decimal literal made whole"))
            if inner.type == "binary_expression" and jf.operator(inner) == "*" and side_name == "left":
                for factor_name in ("left", "right"):
                    factor = jf.unwrap(inner.child_by_field_name(factor_name))
                    rest = inner.child_by_field_name("right" if factor_name == "left" else "left")
                    if factor is not None and factor.type == "decimal_floating_point_literal" and types.kind(rest) in ("int", "char") and types.kind(other) in ("int", "char"):
                        whole = jf.text(factor, source).rstrip("dDfF").split(".")[0]
                        if whole == "1":
                            out.append(_mutation(pr, [(inner.start_byte, inner.end_byte, source[rest.start_byte:rest.end_byte])], "* 1.0 removed"))
                        elif re.fullmatch(r"\d+\.0*", jf.text(factor, source).rstrip("dDfF")):
                            out.append(_mutation(pr, [(factor.start_byte, factor.end_byte, _b(whole))], "decimal factor made whole"))
    return out


# 12. Math.abs(a - b) < EPS -> a == b ;  >= EPS -> a != b
def mutate_decimal_equality_comparison(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for comparison in jf.descendants(pr.tree.root_node, "binary_expression"):
        op = jf.operator(comparison)
        if op not in ("<", "<=", ">", ">="):
            continue
        call = jf.unwrap(comparison.child_by_field_name("left"))
        if call is None or call.type != "method_invocation" or jf.text(call, source).replace(" ", "")[:9] != "Math.abs(":
            continue
        args = call.child_by_field_name("arguments")
        difference = jf.unwrap(args.named_children[0]) if args is not None and args.named_children else None
        if difference is None or difference.type != "binary_expression" or jf.operator(difference) != "-":
            continue
        a, b = jf.text(difference.child_by_field_name("left"), source).strip(), jf.text(difference.child_by_field_name("right"), source).strip()
        text = f"{a} == {b}" if op in ("<", "<=") else f"{a} != {b}"
        out.append(_mutation(pr, [(comparison.start_byte, comparison.end_byte, _b(text))], "tolerance replaced by =="))
    return out


# 13. if (x > 0) { ... }  ->  if (x > 0); { ... }
def mutate_empty_conditional_body(pr: ParseResult, rng: random.Random) -> List[Mutation]:
    out = []
    for statement in jf.descendants(pr.tree.root_node, "if_statement", "while_statement", "for_statement"):
        if statement.type == "if_statement" and statement.child_by_field_name("alternative") is not None:
            continue
        body = statement.child_by_field_name("consequence" if statement.type == "if_statement" else "body")
        if body is None or body.type != "block" or not jf.statements(body):
            continue
        closing = [c for c in statement.children if c.type == ")" and c.end_byte <= body.start_byte]
        if statement.type == "for_statement":
            position = closing[-1].end_byte if closing else None
        else:
            condition = statement.child_by_field_name("condition")
            position = condition.end_byte if condition is not None else None
        if position is None or rng.random() > 0.7:
            continue
        mutation = _mutation(pr, [(position, position, b";")], "semicolon after the condition")
        mutation.spans = [(statement.start_byte, statement.end_byte + 1)]
        out.append(mutation)
    return out


PROMOTED_MUTATORS: Dict[str, Callable[..., List[Mutation]]] = {
    "OFF_BY_ONE_LOOP_BOUNDARY": mutate_off_by_one_loop_boundary,
    "INCORRECT_CONDITIONAL_OPERATOR": mutate_incorrect_conditional_operator,
    "ARRAY_LENGTH_INDEX_MISUSE": mutate_array_length_index_misuse,
    "MISSING_BREAK_IN_SWITCH": mutate_missing_break_in_switch,
    "WHILE_VARIABLE_NOT_UPDATED": mutate_while_variable_not_updated,
    "STRING_EQUALITY_WITH_OPERATOR": mutate_string_equality_with_operator,
    "LOOP_UPDATE_WRONG_DIRECTION": mutate_loop_update_wrong_direction,
    "CONSTANT_FALSE_LOOP_CONDITION": mutate_constant_false_loop_condition,
    "IGNORED_STRING_METHOD_RESULT": mutate_ignored_string_method_result,
    "DIVISION_BY_ZERO_LITERAL": mutate_division_by_zero,
    "INTEGER_DIVISION_IN_DECIMAL_CONTEXT": mutate_integer_division_in_decimal_context,
    "DECIMAL_EQUALITY_COMPARISON": mutate_decimal_equality_comparison,
    "EMPTY_CONDITIONAL_BODY": mutate_empty_conditional_body,
}

PROMOTED_NEEDS_RNG = {"WHILE_VARIABLE_NOT_UPDATED", "CONSTANT_FALSE_LOOP_CONDITION", "EMPTY_CONDITIONAL_BODY"}
