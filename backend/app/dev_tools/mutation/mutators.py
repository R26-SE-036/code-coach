"""Mutation operators: plant one kind of mistake into correct code, at a known
site, the way a student would make it.

Each operator takes a parsed CORRECT program and returns every Mutation it can
make: the new source, and the byte range in the NEW source that the edit
covers. Whether the mutation is actually a bug is not decided here - the
corpus builder runs both versions and compares (a mutation that changes
nothing the program does is an "equivalent mutant" and becomes a hard
negative). Operators work on bytes, because tree-sitter positions are bytes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from app.analysis import java_facts as jf
from app.analysis.logic_candidates import (
    _booleanish,
    _condition_interval,
    _init_kind,
    _literal_assignment,
    propose_wrong_extreme_initial_value,
)
from app.models import ParseResult


@dataclass
class Mutation:
    source: str
    # Where each edit landed in the NEW source. A candidate is "the mutated
    # site" when one of its spans overlaps one of these - each edit on its
    # own, so removing two braces does not also claim everything between.
    spans: List[Tuple[int, int]]
    note: str


def _splice(source: bytes, edits: List[Tuple[int, int, bytes]]) -> Tuple[bytes, List[Tuple[int, int]]]:
    """Apply non-overlapping (start, end, replacement) edits; return the new
    bytes and where each edit is in them (at least one byte wide)."""
    edits = sorted(edits)
    out = bytearray()
    cursor = 0
    spans: List[Tuple[int, int]] = []
    for start, end, replacement in edits:
        out += source[cursor:start]
        new_start = len(out)
        out += replacement
        spans.append((new_start, max(len(out), new_start + 1)))
        cursor = end
    out += source[cursor:]
    return bytes(out), spans


def _mutation(parse_result: ParseResult, edits: List[Tuple[int, int, bytes]], note: str) -> Mutation:
    new, spans = _splice(parse_result.source_bytes, edits)
    return Mutation(new.decode("utf-8", errors="replace"), spans, note)


def _b(value: str) -> bytes:
    return value.encode("utf-8")


def _indent_at(source: bytes, node) -> str:
    return " " * jf.line_indent(source, node.start_point[0])


def _for_loops(parse_result: ParseResult):
    return jf.descendants(parse_result.tree.root_node, "for_statement")


# 1. i < a.length  ->  i < a.length - 1   (and counting down: i >= 0 -> i > 0)
def mutate_loop_skips_last_element(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for loop in _for_loops(pr):
        var = jf.for_loop_var(loop, source)
        condition = jf.unwrap(loop.child_by_field_name("condition"))
        updates = jf.for_updates(loop)
        if not var or condition is None or condition.type != "binary_expression" or not updates:
            continue
        left = jf.unwrap(condition.child_by_field_name("left"))
        right = jf.unwrap(condition.child_by_field_name("right"))
        if left is None or jf.text(left, source) != var:
            continue
        op = jf.operator(condition)
        direction = jf.update_direction(updates[0], var, source)
        target, k = jf.length_minus(right, source)
        body = jf.loop_body(loop)
        if direction == 1 and target and op == "<" and k == 0:
            uses_target = any(c == target and jf.index_offset(ix, var, source) == 0 for _, c, ix in jf.indexed_accesses(body, source))
            if uses_target:
                out.append(_mutation(pr, [(right.start_byte, right.end_byte, _b(jf.text(right, source) + " - 1"))], "stop one early"))
        elif direction == 1 and target and op == "<=" and k == 1:
            out.append(_mutation(pr, [(right.start_byte, right.end_byte, _b(jf.text(right, source)[:-1] + "2"))], "stop one early (<=)"))
        elif direction == -1 and op == ">=" and jf.text(right, source).strip() == "0":
            operator_node = condition.child_by_field_name("operator") or condition.children[1]
            out.append(_mutation(pr, [(operator_node.start_byte, operator_node.end_byte, b">")], "skip index 0 counting down"))
    return out


# 2. i < a.length - 1 with a[i + 1]  ->  i < a.length ;  i = 1 with a[i - 1]  ->  i = 0
def mutate_index_plus_one_out_of_bounds(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for loop in _for_loops(pr):
        var = jf.for_loop_var(loop, source)
        condition = jf.unwrap(loop.child_by_field_name("condition"))
        if not var or condition is None or condition.type != "binary_expression":
            continue
        body = jf.loop_body(loop)
        offsets = {(c, jf.index_offset(ix, var, source)) for _, c, ix in jf.indexed_accesses(body, source)}
        right = jf.unwrap(condition.child_by_field_name("right"))
        target, k = jf.length_minus(right, source)
        if target and jf.operator(condition) == "<" and k == 1 and (target, 1) in offsets:
            length_node = jf.unwrap(right.child_by_field_name("left"))
            out.append(_mutation(pr, [(right.start_byte, right.end_byte, _b(jf.text(length_node, source)))], "loop to the end with a[i + 1]"))
        # i + 1 < a.length  ->  i < a.length : the guard written on the left side, dropped
        left = jf.unwrap(condition.child_by_field_name("left"))
        if target and k == 0 and jf.operator(condition) == "<" and left is not None and left.type == "binary_expression" \
                and jf.text(left, source).replace(" ", "") == f"{var}+1" and (target, 1) in offsets:
            out.append(_mutation(pr, [(left.start_byte, left.end_byte, _b(var))], "i + 1 < n loses its + 1"))
        init_value = None
        init = loop.child_by_field_name("init")
        if init is not None and init.type == "local_variable_declaration":
            declarator = init.child_by_field_name("declarator")
            init_value = declarator.child_by_field_name("value") if declarator is not None else None
        if init_value is not None and jf.text(init_value, source).strip() == "1" and any(off == -1 for _, off in offsets):
            out.append(_mutation(pr, [(init_value.start_byte, init_value.end_byte, b"0")], "start at 0 with a[i - 1]"))
    return out


# 3. grid[i][j] -> grid[i][i] ; b[j] -> b[i]   (inside the inner loop)
def mutate_wrong_loop_variable_in_index(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for inner in _for_loops(pr):
        j = jf.for_loop_var(inner, source)
        outers = [jf.for_loop_var(l, source) for l in jf.enclosing_loops(inner) if l.type == "for_statement"]
        outers = [v for v in outers if v and v != j]
        if not j or not outers:
            continue
        i = outers[0]
        for access, _, index in jf.indexed_accesses(jf.loop_body(inner), source):
            idx = jf.unwrap(index)
            if idx is not None and idx.type == "identifier" and jf.text(idx, source) == j:
                out.append(_mutation(pr, [(idx.start_byte, idx.end_byte, _b(i))], f"index {j} -> {i}"))
    return out


# 4. for (int j = 0; j < m; j++) inside an i loop -> j < m; i++   (or i < m)
def mutate_nested_loop_wrong_counter(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for inner in _for_loops(pr):
        j = jf.for_loop_var(inner, source)
        outers = [jf.loop_var_of(l, source) for l in jf.enclosing_loops(inner) if l.type == "for_statement"]
        outers = [v for v in outers if v and v != j]
        if not j or not outers:
            continue
        i = outers[0]
        for update in jf.for_updates(inner):
            for identifier in jf.descendants(update, "identifier"):
                if jf.text(identifier, source) == j:
                    out.append(_mutation(pr, [(identifier.start_byte, identifier.end_byte, _b(i))], "inner update steps the outer counter"))
                    break
        condition = jf.unwrap(inner.child_by_field_name("condition"))
        if condition is not None and condition.type == "binary_expression":
            left = jf.unwrap(condition.child_by_field_name("left"))
            if left is not None and left.type == "identifier" and jf.text(left, source) == j:
                out.append(_mutation(pr, [(left.start_byte, left.end_byte, _b(i))], "inner condition tests the outer counter"))
    return out


# 5. an extra i++ inside a for body that already steps i
def mutate_loop_counter_changed_in_body(pr: ParseResult, rng: random.Random) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for loop in _for_loops(pr):
        var = jf.for_loop_var(loop, source)
        updates = jf.for_updates(loop)
        body = jf.loop_body(loop)
        if not var or not updates or body is None or body.type != "block":
            continue
        direction = jf.update_direction(updates[0], var, source)
        if direction == 0:
            continue
        top = jf.statements(body)
        if not top:
            continue
        step = rng.choice([f"{var}++;", f"{var} += 1;"]) if direction == 1 else rng.choice([f"{var}--;", f"{var} -= 1;"])
        anchor = rng.choice(top)
        insert = _b("\n" + _indent_at(source, anchor) + step)
        out.append(_mutation(pr, [(anchor.end_byte, anchor.end_byte, insert)], "extra counter step in the body"))
        # The same step inside an if in the body: a skip that only happens
        # sometimes. Without these, every conditional change of the counter
        # in the corpus was a correct one, and the model could not learn when
        # a conditional skip is the mistake.
        guarded = [
            node.child_by_field_name("consequence") for node in jf.descendants(body, "if_statement")
            if jf.enclosing(node, {"for_statement"}) == loop
        ]
        guarded = [block for block in guarded if block is not None and block.type == "block" and jf.statements(block)]
        if guarded:
            inner = jf.statements(rng.choice(guarded))[-1]
            insert = _b("\n" + _indent_at(source, inner) + step)
            out.append(_mutation(pr, [(inner.end_byte, inner.end_byte, insert)], "extra counter step inside an if"))
    return out


# 6. total declared before the loop -> also reset at the top of the loop
def mutate_accumulator_reset_inside_loop(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for declaration in jf.descendants(pr.tree.root_node, "local_variable_declaration"):
        if declaration.parent is not None and declaration.parent.type == "for_statement":
            continue
        acc, value, _ = _literal_assignment(declaration, source)
        if acc is None:
            continue
        block = declaration.parent
        if block is None:
            continue
        for loop in jf.descendants(block, *jf.LOOP_TYPES):
            if loop.start_byte < declaration.end_byte:
                continue
            updates = [w for w in jf.writes_of(loop, acc, source) if jf.is_compound_update(w, acc, source)]
            if not updates:
                continue
            innermost = jf.enclosing_loops(updates[0])[0]
            body = jf.loop_body(innermost)
            if body is None or body.type != "block":
                continue
            top = jf.statements(body)
            if not top:
                continue
            insert = _b(f"{acc} = {jf.text(value, source)};\n" + _indent_at(source, top[0]))
            out.append(_mutation(pr, [(top[0].start_byte, top[0].start_byte, insert)], "reset inside the loop"))
            break
    return out


# 7. int max = a[0]  ->  int max = 0  (and the MIN/MAX constants swapped)
def mutate_wrong_extreme_initial_value(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for candidate in propose_wrong_extreme_initial_value(pr):
        f = candidate.features
        start, end = candidate.spans[0]
        value = source[start:end].decode("utf-8", errors="replace").strip()
        kind = _init_kind(value)
        good = kind == "element" or (f["direction_max"] and kind == "min_const") or (not f["direction_max"] and kind == "max_const")
        if not good:
            continue
        out.append(_mutation(pr, [(start, end, b"0")], "start the extreme at 0"))
        if kind in ("min_const", "max_const"):
            swapped = value.replace("MIN_VALUE", "TMP").replace("MAX_VALUE", "MIN_VALUE").replace("TMP", "MAX_VALUE")
            out.append(_mutation(pr, [(start, end, _b(swapped))], "the opposite constant"))
    return out


# 8. if (hit) return true;  ...  return false;   ->  if (hit) return true; else return false;
def mutate_early_return_in_loop(pr: ParseResult, rng: random.Random) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for loop in jf.descendants(pr.tree.root_node, *jf.LOOP_TYPES):
        following = loop.next_named_sibling
        while following is not None and following.type in jf.COMMENT_TYPES:
            following = following.next_named_sibling
        if following is None or following.type != "return_statement":
            continue
        final = jf.text(following, source).strip()
        body = jf.loop_body(loop)
        for statement in jf.statements(body):
            if statement.type == "if_statement" and statement.child_by_field_name("alternative") is None:
                consequence = statement.child_by_field_name("consequence")
                if consequence is not None and jf.descendants(consequence, "return_statement"):
                    out.append(_mutation(pr, [(consequence.end_byte, consequence.end_byte, _b(" else " + final))], "else return inside the loop"))
        top = jf.statements(body)
        if body is not None and body.type == "block" and top and rng.random() < 0.4:
            out.append(_mutation(pr, [(top[-1].end_byte, top[-1].end_byte, _b("\n" + _indent_at(source, top[-1]) + final))], "unconditional return in the loop"))
    return out


# 9. swap two neighbouring branches of an if / else if chain
def mutate_unreachable_else_if_order(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    for head in jf.descendants(pr.tree.root_node, "if_statement"):
        parent = head.parent
        if parent is not None and parent.type == "if_statement" and parent.child_by_field_name("alternative") == head:
            continue
        branches = []
        current = head
        while current is not None and current.type == "if_statement":
            branches.append(current)
            current = current.child_by_field_name("alternative")
        for k in range(len(branches) - 1):
            a, b = branches[k], branches[k + 1]
            ca, cb = a.child_by_field_name("condition"), b.child_by_field_name("condition")
            qa, qb = a.child_by_field_name("consequence"), b.child_by_field_name("consequence")
            if None in (ca, cb, qa, qb):
                continue
            if _condition_interval(jf.unwrap(ca), source) is None or _condition_interval(jf.unwrap(cb), source) is None:
                continue
            edits = [
                (ca.start_byte, ca.end_byte, source[cb.start_byte:cb.end_byte]),
                (qa.start_byte, qa.end_byte, source[qb.start_byte:qb.end_byte]),
                (cb.start_byte, cb.end_byte, source[ca.start_byte:ca.end_byte]),
                (qb.start_byte, qb.end_byte, source[qa.start_byte:qa.end_byte]),
            ]
            out.append(_mutation(pr, edits, f"swap branches {k} and {k + 1}"))
        # The whole chain in reverse: the classic "lowest grade first" order.
        pairs = [(b.child_by_field_name("condition"), b.child_by_field_name("consequence")) for b in branches]
        if len(pairs) >= 3 and all(c is not None and q is not None and _condition_interval(jf.unwrap(c), source) is not None for c, q in pairs):
            edits = []
            for (c, q), (rc, rq) in zip(pairs, reversed(pairs)):
                if c == rc:
                    continue
                edits.append((c.start_byte, c.end_byte, source[rc.start_byte:rc.end_byte]))
                edits.append((q.start_byte, q.end_byte, source[rq.start_byte:rq.end_byte]))
            out.append(_mutation(pr, edits, "reverse the chain"))
    return out


# 10. remove the braces from a two-statement body, keeping the indentation
def mutate_misleading_indentation_no_braces(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    bodies = []
    for node in jf.descendants(pr.tree.root_node, "if_statement", "for_statement", "while_statement", "enhanced_for_statement"):
        if node.type == "if_statement":
            alternative = node.child_by_field_name("alternative")
            if alternative is None:
                bodies.append(node.child_by_field_name("consequence"))
            elif alternative.type == "block":
                bodies.append(alternative)
        else:
            bodies.append(node.child_by_field_name("body"))
    for body in bodies:
        if body is None or body.type != "block":
            continue
        top = jf.statements(body)
        if len(top) < 2 or top[0].type == "local_variable_declaration":
            continue
        if any(child.type in jf.COMMENT_TYPES for child in body.named_children):
            continue
        # Only bodies already laid out one statement per line - that layout
        # is what makes the missing braces misleading.
        if top[0].start_point[0] == body.start_point[0] or top[1].start_point[0] == top[0].start_point[0]:
            continue
        open_brace = body.children[0]
        close_brace = body.children[-1]
        if open_brace.type != "{" or close_brace.type != "}":
            continue
        out.append(_mutation(pr, [(open_brace.start_byte, open_brace.end_byte, b""), (close_brace.start_byte, close_brace.end_byte, b"")], "braces removed"))
    return out


# 11. && -> &   and   || -> |
def mutate_non_short_circuit_operator(pr: ParseResult) -> List[Mutation]:
    source = pr.source_bytes
    out = []
    logical = ("&&", "||")
    for node in jf.descendants(pr.tree.root_node, "binary_expression"):
        op = jf.operator(node)
        if op not in logical:
            continue
        parent = node.parent
        if parent is not None and parent.type == "binary_expression" and jf.operator(parent) in logical + ("&", "|"):
            continue
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")
        if any(child is not None and child.type == "binary_expression" and jf.operator(child) in logical for child in (left, right)):
            continue
        method = jf.method_of(node)
        if not (_booleanish(left, method, source) and _booleanish(right, method, source)):
            continue
        operator_node = node.child_by_field_name("operator") or node.children[1]
        out.append(_mutation(pr, [(operator_node.start_byte, operator_node.end_byte, b"&" if op == "&&" else b"|")], f"{op} -> {op[0]}"))
    return out


MUTATORS: Dict[str, Callable[..., List[Mutation]]] = {
    "LOOP_SKIPS_LAST_ELEMENT": mutate_loop_skips_last_element,
    "INDEX_PLUS_ONE_OUT_OF_BOUNDS": mutate_index_plus_one_out_of_bounds,
    "WRONG_LOOP_VARIABLE_IN_INDEX": mutate_wrong_loop_variable_in_index,
    "NESTED_LOOP_WRONG_COUNTER": mutate_nested_loop_wrong_counter,
    "LOOP_COUNTER_CHANGED_IN_BODY": mutate_loop_counter_changed_in_body,
    "ACCUMULATOR_RESET_INSIDE_LOOP": mutate_accumulator_reset_inside_loop,
    "WRONG_EXTREME_INITIAL_VALUE": mutate_wrong_extreme_initial_value,
    "EARLY_RETURN_IN_LOOP": mutate_early_return_in_loop,
    "UNREACHABLE_ELSE_IF_ORDER": mutate_unreachable_else_if_order,
    "MISLEADING_INDENTATION_NO_BRACES": mutate_misleading_indentation_no_braces,
    "NON_SHORT_CIRCUIT_OPERATOR": mutate_non_short_circuit_operator,
}

# Operators that make a random choice take the corpus RNG as well.
NEEDS_RNG = {"LOOP_COUNTER_CHANGED_IN_BODY", "EARLY_RETURN_IN_LOOP"}


def mutate(error_type: str, parse_result: ParseResult, rng: random.Random) -> List[Mutation]:
    # The operators for the types moved off rules and file-level gates live
    # in promoted_mutators.py, which builds on the helpers above.
    from app.dev_tools.mutation.promoted_mutators import PROMOTED_MUTATORS, PROMOTED_NEEDS_RNG

    operator_fn = MUTATORS.get(error_type) or PROMOTED_MUTATORS[error_type]
    if error_type in NEEDS_RNG or error_type in PROMOTED_NEEDS_RNG:
        return operator_fn(parse_result, rng)
    return operator_fn(parse_result)
