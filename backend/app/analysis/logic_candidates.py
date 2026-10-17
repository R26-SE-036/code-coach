"""Candidate proposers for the logic errors that need a model to judge.

Each proposer walks the tree and returns every SITE that might be its kind of
mistake - deliberately too many. `i < a.length - 1` is a bug in a loop that
sums the array and exactly right in one that compares a[i] with a[i + 1]; a
rule has to pick one answer for both. So the proposer only says "this could
be it" and describes the site in numbers (its features), and a per-type model
trained on executed code decides (ml_engine.score_candidates).

Every feature is about the site and its immediate surroundings - the loop it
sits in, the statement it belongs to, the method it is in - never the size or
shape of the whole file. That keeps a 300-line assignment and a 10-line
exercise on the same footing.

The labels the models learn from do NOT come from these proposers. They come
from dev_tools/mutation: correct code is mutated at a known site and both
versions are run on the same inputs; a site is a positive only if the change
alters what the program does. A proposer firing on correct code is exactly
the hard negative the model needs to see.

Each Candidate carries the finding to show (line, message, details for the
targeted hint) and `spans`: the byte ranges a mutation at this site would
touch, which is how the corpus builder matches a mutation to a candidate.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from app.analysis import java_facts as jf
from app.analysis.issue_locators import _result
from app.models import DetectionResult, ParseResult


@dataclass
class Candidate:
    finding: DetectionResult
    features: Dict[str, float]
    spans: List[Tuple[int, int]] = field(default_factory=list)


ProposerFn = Callable[[ParseResult], List[Candidate]]

_NEIGHBOUR_WORDS = ["pair", "pairs", "adjacent", "neighbour", "neighbor", "next", "rise", "rises", "jump",
                    "sorted", "increasing", "decreasing", "diff", "difference", "consecutive", "gap", "step", "steps"]
_ACC_WORDS = ["sum", "total", "count", "counter", "product", "result", "acc", "score", "points", "tally", "num"]
_RESET_WORDS = ["streak", "run", "current", "curr", "row", "col", "column", "temp", "tmp", "local", "line", "word"]
_EXTREME_WORDS = ["max", "min", "largest", "smallest", "highest", "lowest", "best", "worst", "longest",
                  "shortest", "biggest", "greatest", "least", "top", "peak"]


def _root(parse_result: ParseResult):
    return parse_result.tree.root_node


def _first_line(value: str) -> str:
    lines = value.strip().splitlines()
    return lines[0].strip() if lines else value.strip()


def _header(node, source: bytes) -> str:
    body = node.child_by_field_name("body") or node.child_by_field_name("consequence")
    if body is None:
        return _first_line(jf.text(node, source))
    return " ".join(source[node.start_byte:body.start_byte].decode("utf-8", errors="replace").split())


def _statement_of(node):
    current = node
    while current is not None and current.parent is not None:
        if current.type.endswith("_statement") or current.type in ("local_variable_declaration",):
            return current
        current = current.parent
    return node


# ═════════════════════════════════ 1. LOOP_SKIPS_LAST_ELEMENT ═════════════════
# `for (i = 0; i < a.length - 1; i++)` never reaches the last element - a bug
# when the body handles a[i] on its own, correct when it pairs a[i] with
# a[i + 1]. The mirror image: counting down with `i > 0` never reaches a[0].

def propose_loop_skips_last_element(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "for_statement"):
        var = jf.for_loop_var(loop, source)
        condition = jf.unwrap(loop.child_by_field_name("condition"))
        updates = jf.for_updates(loop)
        if not var or condition is None or condition.type != "binary_expression" or not updates:
            continue
        op = jf.operator(condition)
        left = jf.unwrap(condition.child_by_field_name("left"))
        right = jf.unwrap(condition.child_by_field_name("right"))
        if left is None or left.type != "identifier" or jf.text(left, source) != var:
            continue
        direction = jf.update_direction(updates[0], var, source)

        target, ascending = None, True
        k_right = jf.length_minus(right, source)
        if direction == 1 and k_right[0] and ((op == "<" and k_right[1] == 1) or (op == "<=" and k_right[1] == 2)):
            target = k_right[0]
        elif direction == -1 and ((op == ">" and jf.text(right, source).strip() == "0") or (op == ">=" and jf.text(right, source).strip() == "1")):
            init_target, init_k = jf.length_minus(_init_value_node(loop), source)
            if init_target and init_k == 1:
                target, ascending = init_target, False
        if target is None:
            continue

        body = jf.loop_body(loop)
        accesses = [(node, coll, jf.index_offset(index, var, source)) for node, coll, index in jf.indexed_accesses(body, source)]
        offsets = [off for _, _, off in accesses if off is not None]
        method = jf.method_of(loop)
        method_name = jf.text(method.child_by_field_name("name"), source) if method is not None else ""
        features = {
            "ascending": jf.flag(ascending),
            "cond_leq": jf.flag(op in ("<=", ">=")),
            "init_is_zero": jf.flag(jf.for_init_value(loop, source) == "0"),
            "body_uses_next": jf.flag((1 in offsets) if ascending else (-1 in offsets)),
            "body_uses_prev": jf.flag((-1 in offsets) if ascending else (1 in offsets)),
            "body_uses_far_offset": jf.flag(any(abs(off) >= 2 for off in offsets)),
            "body_indexes_target_at_var": jf.flag(any(coll == target and off == 0 for _, coll, off in accesses)),
            "body_indexes_other_at_var": jf.flag(any(coll != target and off == 0 for _, coll, off in accesses)),
            "body_accesses_target": jf.flag(any(coll == target for _, coll, _ in accesses)),
            "compares_neighbours": jf.flag(_compares_neighbours(body, var, source)),
            "body_has_compound_update": jf.flag(_has_compound_update(body, source)),
            "body_has_return": jf.flag(bool(jf.descendants(body, "return_statement"))),
            "body_has_break": jf.flag(bool(jf.descendants(body, "break_statement"))),
            "nested_in_loop": jf.flag(bool(jf.enclosing_loops(loop))),
            "method_returns_boolean": jf.flag(jf.method_return_type(method, source) == "boolean"),
            "method_name_neighbour": jf.has_token(method_name, _NEIGHBOUR_WORDS),
            "body_statement_count": float(len(jf.statements(body))),
            "var_uses_in_body": float(jf.uses(body, var, source)),
            "target_is_string": jf.flag(".length()" in jf.text(right, source) or "charAt" in jf.text(body, source)),
            # `for (j = i + 1; ...)` inside: a pairs loop. The last i has no
            # partner left, so stopping one early is exactly right (two-sum,
            # bubble sort, counting duplicate pairs).
            "inner_loop_starts_after_var": jf.flag(_inner_starts_after(body, var, source)),
            # The counter only bounds an inner loop (`j < n - 1 - pass`): a
            # pass counter, as in bubble sort, where n - 1 passes are enough.
            "var_only_in_inner_bounds": jf.flag(_only_in_inner_bounds(body, var, source)),
        }
        finding = _result(
            "LOOP_SKIPS_LAST_ELEMENT", condition, source, 0.8,
            "This loop may stop one element early, so an element at the end is never visited.",
            context_node=loop,
            details={"condition": jf.text(condition, source), "collection": target},
        )
        found.append(Candidate(finding, features, [jf.span(condition), jf.span(loop.child_by_field_name("init") or condition)]))
    return found


def _inner_starts_after(body, var: str, source: bytes) -> bool:
    for inner in jf.descendants(body, "for_statement"):
        start = jf.for_init_value(inner, source).replace(" ", "")
        if start in (f"{var}+1", f"1+{var}"):
            return True
    return False


def _only_in_inner_bounds(body, var: str, source: bytes) -> bool:
    uses = [n for n in jf.descendants(body, "identifier") if jf.text(n, source) == var]
    if not uses:
        return False
    for use in uses:
        inner = jf.enclosing(use, {"for_statement"})
        if inner is None or not jf.is_inside(inner, body):
            return False
        header = [inner.child_by_field_name("condition"), inner.child_by_field_name("init")]
        if not any(part is not None and jf.is_inside(use, part) for part in header):
            return False
    return True


def _init_value_node(for_node):
    init = for_node.child_by_field_name("init")
    if init is None:
        return None
    if init.type == "local_variable_declaration":
        declarator = init.child_by_field_name("declarator")
        return declarator.child_by_field_name("value") if declarator is not None else None
    if init.type == "assignment_expression":
        return init.child_by_field_name("right")
    return None


def _compares_neighbours(body, var: str, source: bytes) -> bool:
    for comparison in jf.descendants(body, "binary_expression"):
        if jf.operator(comparison) not in ("<", ">", "<=", ">=", "==", "!=", "-"):
            continue
        offsets = set()
        for _, _, index in jf.indexed_accesses(comparison, source):
            off = jf.index_offset(index, var, source)
            if off is not None:
                offsets.add(off)
        if len(offsets) >= 2:
            return True
    return False


def _has_compound_update(node, source: bytes) -> bool:
    for assignment in jf.descendants(node, "assignment_expression"):
        if jf.operator(assignment) in ("+=", "-=", "*="):
            return True
    return False


# ══════════════════════════ 2. INDEX_PLUS_ONE_OUT_OF_BOUNDS ═══════════════════
# `a[i + 1]` inside `for (i = 0; i < a.length; i++)` reads past the end on the
# last pass. Correct when the loop stops one sooner, when the access is guarded,
# or when the array read is longer (prefix sums: p[i + 1] = p[i] + a[i]).

def propose_index_plus_one_out_of_bounds(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "for_statement"):
        var = jf.for_loop_var(loop, source)
        condition = jf.unwrap(loop.child_by_field_name("condition"))
        updates = jf.for_updates(loop)
        if not var or condition is None or not updates:
            continue
        direction = jf.update_direction(updates[0], var, source)
        if direction == 0:
            continue
        op = jf.operator(condition) if condition.type == "binary_expression" else ""
        right = jf.unwrap(condition.child_by_field_name("right")) if condition.type == "binary_expression" else None
        bound_target, bound_k = jf.length_minus(right, source) if right is not None else (None, 0)
        # `i + 1 < a.length` is `i < a.length - 1` written the other way: the
        # guard every correct neighbour loop needs, not the missing one.
        left_shift = _left_shift(condition, var, source)
        if left_shift is None:
            bound_target = None
        else:
            bound_k += left_shift
        init_text = jf.for_init_value(loop, source)
        method = jf.method_of(loop)
        body = jf.loop_body(loop)

        for access, coll, index in jf.indexed_accesses(body, source):
            offset = jf.index_offset(index, var, source)
            if not offset:
                continue
            same = coll == bound_target
            if offset > 0:
                slack = (bound_k if op == "<" else bound_k - 1) - offset if same and op in ("<", "<=") else None
            else:
                start = int(init_text) if init_text.isdigit() else None
                slack = (start + offset) if (start is not None and direction == 1) else None
            features = {
                "offset_positive": jf.flag(offset > 0),
                "offset_size": float(abs(offset)),
                "same_collection_as_bound": jf.flag(same),
                "bound_minus_k": float(bound_k) if same else -1.0,
                "slack_known": jf.flag(slack is not None),
                "slack_negative": jf.flag(slack is not None and slack < 0),
                "cond_leq": jf.flag(op in ("<=", ">=")),
                "ascending": jf.flag(direction == 1),
                "init_is_zero": jf.flag(init_text == "0"),
                "init_is_one": jf.flag(init_text == "1"),
                "guarded": jf.flag(_guarded(access, body, var, coll, source)),
                "access_is_write": jf.flag(_is_write_target(access)),
                "collection_declared_longer": jf.flag(_declared_longer(method, coll, source)),
                "collection_is_string": jf.flag(access.type == "method_invocation" and "charAt" in jf.text(access, source)),
                "nested_in_loop": jf.flag(bool(jf.enclosing_loops(loop))),
                "body_has_break": jf.flag(bool(jf.descendants(body, "break_statement"))),
                "body_also_uses_var_plain": jf.flag(any(jf.index_offset(i, var, source) == 0 for _, _, i in jf.indexed_accesses(body, source))),
                "condition_adds_to_var": jf.flag(bool(left_shift)),
                # a[i - 1] on the very first pass of a loop that starts at 0.
                "first_pass_below_zero": jf.flag(offset < 0 and init_text.isdigit() and int(init_text) + offset < 0 and direction == 1),
            }
            finding = _result(
                "INDEX_PLUS_ONE_OUT_OF_BOUNDS", access, source, 0.8,
                "This index may run past the end of the collection on the loop's last pass.",
                context_node=_statement_of(access),
                details={"access": jf.text(access, source), "condition": jf.text(condition, source), "collection": coll},
            )
            # Only the part of the header that can push THIS access out of
            # range: the bound for a + offset, the start for a - offset.
            spans = [jf.span(access)]
            if offset > 0 and same:
                spans.append(jf.span(condition))
            init = loop.child_by_field_name("init")
            if offset < 0 and init is not None:
                spans.append(jf.span(init))
            found.append(Candidate(finding, features, spans))
    return found


def _left_shift(condition, var: str, source: bytes) -> Optional[int]:
    """How much the condition adds to the counter before comparing: 0 for
    `i < n`, 1 for `i + 1 < n`, None when the left side is not the counter."""
    if condition is None or condition.type != "binary_expression":
        return None
    left = jf.unwrap(condition.child_by_field_name("left"))
    if left is None:
        return None
    if left.type == "identifier":
        return 0 if jf.text(left, source) == var else None
    if left.type == "binary_expression" and jf.operator(left) == "+":
        a, b = jf.unwrap(left.child_by_field_name("left")), jf.unwrap(left.child_by_field_name("right"))
        for name, number in ((a, b), (b, a)):
            if name is not None and number is not None and name.type == "identifier" and jf.text(name, source) == var and jf.text(number, source).strip().isdigit():
                return int(jf.text(number, source))
    return None


def _guarded(access, body, var: str, coll: str, source: bytes) -> bool:
    current = access.parent
    while current is not None and current != body:
        if current.type in ("if_statement", "while_statement", "ternary_expression"):
            condition = current.child_by_field_name("condition")
            if condition is not None and not jf.is_inside(access, condition):
                names = set(jf.identifiers(condition, source))
                if var in names and (coll in names or "length" in jf.text(condition, source) or "size" in jf.text(condition, source)):
                    return True
        if current.type == "binary_expression" and jf.operator(current) in ("&&", "||"):
            left = current.child_by_field_name("left")
            if left is not None and not jf.is_inside(access, left):
                names = set(jf.identifiers(left, source))
                if var in names:
                    return True
        current = current.parent
    return False


def _is_write_target(access) -> bool:
    parent = access.parent
    return parent is not None and parent.type == "assignment_expression" and parent.child_by_field_name("left") == access


def _declared_longer(method, coll: str, source: bytes) -> bool:
    if method is None:
        return False
    for declarator in jf.descendants(method, "variable_declarator"):
        name = declarator.child_by_field_name("name")
        value = declarator.child_by_field_name("value")
        if name is not None and jf.text(name, source) == coll and value is not None:
            if re.search(r"\[\s*[\w.()]+\s*\+\s*\d+\s*\]", jf.text(value, source)):
                return True
    return False


# ═══════════════════════════ 3. WRONG_LOOP_VARIABLE_IN_INDEX ══════════════════
# Inside `for (j ...)` nested in `for (i ...)`, `grid[i][i]` or `b[i]` where the
# inner counter was meant. Correct when the outer element is really wanted on
# every inner pass (pair sums a[i] + a[j], comparing a[i] with each a[j]).

def propose_wrong_loop_variable_in_index(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for inner in jf.descendants(_root(parse_result), "for_statement"):
        j = jf.for_loop_var(inner, source)
        outers = [loop for loop in jf.enclosing_loops(inner) if loop.type in ("for_statement",)]
        outer_vars = [jf.for_loop_var(loop, source) for loop in outers]
        outer_vars = [v for v in outer_vars if v and v != j]
        if not j or not outer_vars:
            continue
        i = outer_vars[0]
        body = jf.loop_body(inner)
        inner_condition = inner.child_by_field_name("condition")
        inner_init = jf.for_init_value(inner, source)
        bound_target = jf.length_minus(jf.unwrap(inner_condition.child_by_field_name("right")) if inner_condition is not None and inner_condition.type == "binary_expression" else None, source)[0]

        for access, coll, index in jf.indexed_accesses(body, source):
            if jf.enclosing(access, {"for_statement"}) != inner:
                continue
            # The row part of grid[i][j] is meant to use the outer counter.
            holder = access.parent
            if holder is not None and holder.type == "array_access" and holder.child_by_field_name("array") == access:
                continue
            idx = jf.unwrap(index)
            kind = None
            if idx is not None and idx.type == "identifier" and jf.text(idx, source) == i:
                kind = "outer"
            parent_array = access.child_by_field_name("array") if access.type == "array_access" else None
            if parent_array is not None and parent_array.type == "array_access":
                first = jf.unwrap(parent_array.child_by_field_name("index"))
                if first is not None and idx is not None and jf.text(first, source) == jf.text(idx, source) and jf.text(idx, source) in (i, j):
                    kind = "repeated"
                    coll = jf.text(parent_array.child_by_field_name("array"), source)
            if kind is None:
                continue
            statement = _statement_of(access)
            same_coll_with_j = any(
                (c == coll or c.startswith(coll + "[")) and jf.text(jf.unwrap(ix), source) == j
                for _, c, ix in jf.indexed_accesses(body, source)
            )
            features = {
                "kind_outer_index": jf.flag(kind == "outer"),
                "kind_repeated_2d": jf.flag(kind == "repeated"),
                "inner_var_used_in_body": jf.flag(jf.uses(body, j, source) > 0),
                "inner_var_used_in_statement": jf.flag(jf.uses(statement, j, source) > 0),
                "same_collection_indexed_with_inner": jf.flag(same_coll_with_j),
                "inner_bound_is_this_collection": jf.flag(bound_target is not None and (bound_target == coll or bound_target.startswith(coll + "["))),
                "inner_init_uses_outer": jf.flag(i in re.findall(r"[A-Za-z_]\w*", inner_init)),
                "access_is_write": jf.flag(_is_write_target(access)),
                "outer_uses_in_inner_body": float(jf.uses(body, i, source)),
                "inner_uses_in_inner_body": float(jf.uses(body, j, source)),
                "statement_is_comparison": jf.flag(bool([b for b in jf.descendants(statement, "binary_expression") if jf.operator(b) in ("==", "!=", "<", ">", "<=", ">=")])),
                "loop_depth": float(len(jf.enclosing_loops(access))),
            }
            finding = _result(
                "WRONG_LOOP_VARIABLE_IN_INDEX", access, source, 0.8,
                "This index uses the outer loop's counter inside the inner loop; check which counter was meant.",
                context_node=statement,
                details={"access": jf.text(access, source), "inner": j, "outer": i},
            )
            found.append(Candidate(finding, features, [jf.span(access)]))
    return found


# ═══════════════════════════ 4. NESTED_LOOP_WRONG_COUNTER ═════════════════════
# `for (int j = 0; j < n; i++)` - the header tests or steps a different counter
# from the one it declares, usually the outer loop's. The inner loop then never
# ends, or the outer one skips. Correct for some deliberate two-counter loops.

def propose_nested_loop_wrong_counter(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "for_statement"):
        var = jf.for_loop_var(loop, source)
        condition = loop.child_by_field_name("condition")
        updates = jf.for_updates(loop)
        if not var or condition is None or not updates:
            continue
        declared = set(jf.for_declared_vars(loop, source)) or {var}
        cond_ids = set(jf.identifiers(condition, source))
        update_writes = set()
        for update in updates:
            update_writes |= jf.written_vars(update, source)
        if not update_writes:
            continue
        update_misses = not (declared & update_writes)
        cond_misses = not (declared & cond_ids)
        if not (update_misses or cond_misses):
            continue
        outer_vars = {jf.loop_var_of(o, source) for o in jf.enclosing_loops(loop)} - {None}
        body = jf.loop_body(loop)
        features = {
            "update_misses_own_var": jf.flag(update_misses),
            "cond_misses_own_var": jf.flag(cond_misses),
            "update_writes_outer_var": jf.flag(bool(update_writes & outer_vars)),
            "cond_uses_outer_var": jf.flag(bool(cond_ids & outer_vars)),
            "nested": jf.flag(bool(outer_vars)),
            "own_var_written_in_body": jf.flag(bool(jf.writes_of(body, var, source))),
            "own_var_used_in_body": jf.flag(jf.uses(body, var, source) > 0),
            "cond_has_call": jf.flag(bool(jf.descendants(condition, "method_invocation"))),
            "cond_single_identifier": jf.flag(jf.unwrap(condition).type == "identifier" if jf.unwrap(condition) is not None else False),
            "multi_var_init": jf.flag(len(declared) > 1),
            "update_count": float(len(updates)),
            "body_has_break": jf.flag(bool(jf.descendants(body, "break_statement", "return_statement"))),
        }
        wrong = sorted((update_writes - declared) if update_misses else (cond_ids & outer_vars) or (cond_ids - declared))
        finding = _result(
            "NESTED_LOOP_WRONG_COUNTER", condition if cond_misses else updates[0], source, 0.8,
            "This loop's header tests or changes a different counter from the one it declares.",
            context_node=loop,
            details={"header": _header(loop, source), "counter": var, "other": ", ".join(wrong)},
        )
        found.append(Candidate(finding, features, [jf.span(condition), *[jf.span(u) for u in updates]]))
    return found


# ═══════════════════════════ 5. LOOP_COUNTER_CHANGED_IN_BODY ══════════════════
# The header already steps `i`, and the body changes it again - so elements get
# skipped. Correct when the skip is the point (jumping over a run, a pair, an
# escape character), which is the judgment the model makes.

def propose_loop_counter_changed_in_body(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "for_statement"):
        var = jf.for_loop_var(loop, source)
        updates = jf.for_updates(loop)
        if not var or not updates:
            continue
        loop_direction = jf.update_direction(updates[0], var, source)
        body = jf.loop_body(loop)
        top = jf.statements(body)
        for write in jf.writes_of(body, var, source):
            # A nested loop's own header belongs to that loop, not this body.
            holder = jf.enclosing(write, {"for_statement"})
            if holder is not None and holder != loop and any(jf.is_inside(write, u) for u in jf.for_updates(holder)):
                continue
            statement = _statement_of(write)
            inner_loops = [l for l in jf.enclosing_loops(write) if jf.is_inside(l, body)]
            ifs = [p for p in jf.ancestors(write) if p.type == "if_statement" and jf.is_inside(p, body)]
            direction = jf.update_direction(write, var, source)
            features = {
                "write_conditional": jf.flag(bool(ifs)),
                "write_in_inner_loop": jf.flag(bool(inner_loops)),
                "write_is_last_statement": jf.flag(bool(top) and jf.is_inside(write, top[-1]) and not ifs),
                "write_is_first_statement": jf.flag(bool(top) and jf.is_inside(write, top[0]) and not ifs),
                "same_direction": jf.flag(direction == loop_direction and direction != 0),
                "opposite_direction": jf.flag(direction == -loop_direction and direction != 0),
                "write_is_reset": jf.flag(write.type == "assignment_expression" and jf.operator(write) == "="),
                "body_looks_ahead": jf.flag(any((jf.index_offset(ix, var, source) or 0) > 0 for _, _, ix in jf.indexed_accesses(body, source))),
                "if_condition_looks_ahead": jf.flag(any("+ 1" in jf.text(p.child_by_field_name("condition"), source) or "+1" in jf.text(p.child_by_field_name("condition"), source) for p in ifs)),
                "followed_by_continue": jf.flag(any(jf.descendants(p, "continue_statement") for p in ifs)),
                "body_has_break": jf.flag(bool(jf.descendants(body, "break_statement"))),
                "body_statement_count": float(len(top)),
                "loop_update_is_step_one": jf.flag(jf.text(updates[0], source).replace(" ", "") in (f"{var}++", f"++{var}", f"{var}--", f"--{var}")),
                # A deliberate skip moves the counter to consume the next
                # element and then READS it (`i++; c = text.charAt(i);`). An
                # extra step added by mistake leaves the new value unread
                # until the header moves it again.
                "reads_var_after_write": jf.flag(_read_after_in_block(write, statement, var, source)),
            }
            finding = _result(
                "LOOP_COUNTER_CHANGED_IN_BODY", write, source, 0.8,
                "The loop counter is changed inside the body as well as in the loop header, so some passes may be skipped.",
                context_node=statement,
                details={"change": jf.text(write, source), "counter": var},
            )
            found.append(Candidate(finding, features, [jf.span(statement)]))
    return found


def _read_after_in_block(write, statement, var: str, source: bytes) -> bool:
    """Is `var` read by a later statement of the block that holds the write?"""
    block = statement.parent
    if block is None:
        return False
    after = [s for s in jf.statements(block) if s.start_byte > statement.end_byte] if block.type == "block" else []
    return any(jf.uses(s, var, source) > 0 for s in after)


# ═══════════════════════════ 6. ACCUMULATOR_RESET_INSIDE_LOOP ═════════════════
# `total = 0;` inside the loop that adds to total throws the running total away
# on every pass. Correct when the reset belongs to an OUTER pass (a row total
# reset per row) or is conditional (a streak that restarts on a mismatch).

def propose_accumulator_reset_inside_loop(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    root = _root(parse_result)
    for statement in jf.descendants(root, "expression_statement", "local_variable_declaration"):
        loops = jf.enclosing_loops(statement)
        if not loops or (statement.parent is not None and statement.parent.type == "for_statement"):
            continue
        loop = loops[0]
        acc, value_node, is_declaration = _literal_assignment(statement, source)
        if acc is None:
            continue
        updates = [w for w in jf.writes_of(loop, acc, source) if not jf.is_inside(w, statement) and jf.is_compound_update(w, acc, source)]
        if not updates:
            continue
        body = jf.loop_body(loop)
        top = jf.statements(body)
        same_loop = any(jf.enclosing_loops(u)[:1] == [loop] for u in updates)
        reads_in_loop = jf.uses(loop, acc, source) - len(updates) - 1
        # Java scope, not the name: two loops that each declare their own
        # `int total = 0;` are two variables, and the second must not count
        # as "declared before" its loop, nor the first as "read after" it.
        scope = statement.parent if is_declaration else _declaring_scope(statement, acc, source)
        declared_outside = scope is not None and not is_declaration and jf.is_inside(loop, scope)
        read_after = declared_outside and _reads_from(scope, loop.end_byte, acc, source) > 0
        features = {
            "is_declaration": jf.flag(is_declaration),
            "update_in_same_loop": jf.flag(same_loop),
            "update_only_in_nested_loop": jf.flag(not same_loop),
            "reset_conditional": jf.flag(any(p.type == "if_statement" and jf.is_inside(p, loop) for p in jf.ancestors(statement))),
            "reset_is_first_statement": jf.flag(bool(top) and top[0] == statement),
            "read_after_loop": jf.flag(read_after),
            "declared_before_loop": jf.flag(declared_outside),
            "read_inside_loop": jf.flag(reads_in_loop > 0),
            "printed_in_loop": jf.flag(any(acc in jf.text(c, source) for c in jf.descendants(loop, "method_invocation") if "print" in jf.text(c.child_by_field_name("name"), source))),
            "name_accumulator": jf.has_token(acc, _ACC_WORDS),
            "name_resettable": jf.has_token(acc, _RESET_WORDS),
            "literal_zero": jf.flag(jf.text(value_node, source).strip() in ("0", "0.0", "0L")),
            "literal_string": jf.flag(jf.literal_kind(jf.text(value_node, source)) == "string"),
            "loop_depth": float(len(loops)),
            "loop_is_for": jf.flag(loop.type in ("for_statement", "enhanced_for_statement")),
            "update_count": float(len(updates)),
        }
        finding = _result(
            "ACCUMULATOR_RESET_INSIDE_LOOP", statement, source, 0.8,
            "This value is set back to its starting value on every pass of the loop that builds it up.",
            context_node=statement,
            details={"reset": _first_line(jf.text(statement, source)), "variable": acc},
        )
        found.append(Candidate(finding, features, [jf.span(statement)]))
    return found


def _declaring_scope(node, name: str, source: bytes):
    """The block (or method, for a parameter) whose declaration of `name` is
    the one `node` sees; None when it is a field or undeclared."""
    for parent in jf.ancestors(node):
        if parent.type in ("block", "switch_block_statement_group"):
            for child in parent.named_children:
                if child.start_byte >= node.start_byte:
                    break
                if child.type == "local_variable_declaration" and any(
                    jf.text(d.child_by_field_name("name"), source) == name
                    for d in child.named_children if d.type == "variable_declarator"
                ):
                    return parent
        if parent.type in ("for_statement", "enhanced_for_statement"):
            if name in jf.for_declared_vars(parent, source) or jf.loop_var_of(parent, source) == name and parent.type == "enhanced_for_statement":
                return parent
        if parent.type in ("method_declaration", "constructor_declaration"):
            for parameter in jf.descendants(parent.child_by_field_name("parameters"), "formal_parameter"):
                if jf.text(parameter.child_by_field_name("name"), source) == name:
                    return parent
            return None
    return None


def _reads_from(scope, position: int, name: str, source: bytes) -> int:
    count = 0
    for identifier in jf.descendants(scope, "identifier"):
        if identifier.start_byte < position or jf.text(identifier, source) != name:
            continue
        parent = identifier.parent
        if parent is not None and parent.type == "assignment_expression" and parent.child_by_field_name("left") == identifier:
            continue
        count += 1
    return count


def _literal_assignment(statement, source: bytes):
    """`x = <literal>;` or `T x = <literal>;` -> (name, value node, is_declaration)."""
    if statement.type == "expression_statement":
        assignment = statement.named_children[0] if statement.named_children else None
        if assignment is None or assignment.type != "assignment_expression" or jf.operator(assignment) != "=":
            return None, None, False
        left = assignment.child_by_field_name("left")
        right = jf.unwrap(assignment.child_by_field_name("right"))
        if left is None or left.type != "identifier" or right is None:
            return None, None, False
        if jf.literal_kind(jf.text(right, source)) == "other":
            return None, None, False
        return jf.text(left, source), right, False
    declarator = statement.child_by_field_name("declarator")
    if declarator is None:
        return None, None, False
    name = declarator.child_by_field_name("name")
    value = declarator.child_by_field_name("value")
    if name is None or value is None or jf.literal_kind(jf.text(value, source)) == "other":
        return None, None, False
    return jf.text(name, source), value, True


# ═══════════════════════════ 7. WRONG_EXTREME_INITIAL_VALUE ═══════════════════
# `int max = 0;` before a search for the largest value gives 0 for an array of
# negatives; `int min = 0;` gives 0 for an array of positives. Correct when the
# values cannot go below 0 (lengths, counts) - the model weighs that.

def propose_wrong_extreme_initial_value(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for method in jf.descendants(_root(parse_result), "method_declaration", "constructor_declaration"):
        for declarator in jf.descendants(method, "variable_declarator"):
            name_node = declarator.child_by_field_name("name")
            value = declarator.child_by_field_name("value")
            if name_node is None or value is None:
                continue
            var = jf.text(name_node, source)
            pattern = _extreme_update(method, var, declarator.end_byte, source)
            if pattern is None:
                continue
            direction, compared, loop = pattern
            init = jf.text(value, source).strip()
            kind = _init_kind(init)
            features = {
                "direction_max": jf.flag(direction == "max"),
                "init_zero": jf.flag(kind == "zero"),
                "init_one_or_minus_one": jf.flag(kind in ("one", "minus_one")),
                "init_min_constant": jf.flag(kind == "min_const"),
                "init_max_constant": jf.flag(kind == "max_const"),
                "init_element": jf.flag(kind == "element"),
                "init_other": jf.flag(kind == "other"),
                "constant_mismatch": jf.flag((direction == "max" and kind == "max_const") or (direction == "min" and kind == "min_const")),
                "compared_nonnegative": jf.flag(_nonnegative(compared, source)),
                "compared_from_collection": jf.flag(bool(jf.indexed_accesses(compared, source)) or compared.type == "identifier"),
                # What is being compared decides whether 0 is a safe start:
                # an element of the data can be negative; a counter (a run
                # length, a streak) is built up from 0 and cannot.
                "compared_is_element": jf.flag(_is_element(compared, loop, source)),
                "compared_is_counter": jf.flag(_is_counter(method, compared, source)),
                "name_extreme": jf.has_token(var, _EXTREME_WORDS),
                "name_matches_direction": jf.has_token(var, ["max", "largest", "highest", "biggest", "greatest", "longest", "top", "peak"] if direction == "max" else ["min", "smallest", "lowest", "least", "shortest"]),
                "loop_starts_at_one": jf.flag(loop.type == "for_statement" and jf.for_init_value(loop, source) == "1"),
                "decimal_type": jf.flag(jf.declared_type(method, var, source) in ("double", "float", "Double")),
            }
            finding = _result(
                "WRONG_EXTREME_INITIAL_VALUE", value, source, 0.8,
                f"The starting value of {var} may win the comparison before any real value is seen.",
                context_node=_statement_of(declarator),
                details={"declaration": _first_line(jf.text(_statement_of(declarator), source)), "variable": var, "value": init},
            )
            found.append(Candidate(finding, features, [jf.span(value)]))
    return found


def _init_kind(init: str) -> str:
    compact = init.replace(" ", "")
    if compact in ("0", "0.0", "0L", "0.0d", "0d"):
        return "zero"
    if compact in ("1", "1.0"):
        return "one"
    if compact in ("-1", "-1.0"):
        return "minus_one"
    if compact.endswith("MIN_VALUE") or compact in ("-Double.MAX_VALUE", "Double.NEGATIVE_INFINITY"):
        return "min_const"
    if compact.endswith("MAX_VALUE") or compact == "Double.POSITIVE_INFINITY":
        return "max_const"
    if re.fullmatch(r"\w+\[0\]|\w+\.get\(0\)|\w+\.charAt\(0\)|\w+\[0\]\.length\(\)|\w+\[0\]\[0\]", compact):
        return "element"
    return "other"


def _extreme_update(method, var: str, after: int, source: bytes):
    """("max"|"min", compared expression, loop) when a loop keeps the extreme in `var`."""
    for loop in jf.descendants(method, *jf.LOOP_TYPES):
        if loop.start_byte < after:
            continue
        for if_node in jf.descendants(loop, "if_statement"):
            condition = jf.unwrap(if_node.child_by_field_name("condition"))
            if condition is None or condition.type != "binary_expression" or jf.operator(condition) not in ("<", ">", "<=", ">="):
                continue
            left = jf.unwrap(condition.child_by_field_name("left"))
            right = jf.unwrap(condition.child_by_field_name("right"))
            op = jf.operator(condition)
            if left is not None and jf.text(left, source) == var:
                compared, var_on_left = right, True
            elif right is not None and jf.text(right, source) == var:
                compared, var_on_left = left, False
            else:
                continue
            consequence = if_node.child_by_field_name("consequence")
            assigned = [w for w in jf.writes_of(consequence, var, source) if w.type == "assignment_expression" and jf.operator(w) == "="]
            if not assigned:
                continue
            greater = op in (">", ">=")
            # compared > var  or  var < compared  -> keeping the max
            keeps_max = (greater and not var_on_left) or (not greater and var_on_left)
            return ("max" if keeps_max else "min"), compared, loop
        for call in jf.descendants(loop, "method_invocation"):
            name = jf.text(call.child_by_field_name("name"), source)
            obj = jf.text(call.child_by_field_name("object"), source)
            parent = call.parent
            if obj == "Math" and name in ("max", "min") and parent is not None and parent.type == "assignment_expression":
                left = parent.child_by_field_name("left")
                args = call.child_by_field_name("arguments")
                if left is not None and jf.text(left, source) == var and args is not None:
                    others = [a for a in args.named_children if jf.text(a, source) != var]
                    if others:
                        return name, others[0], loop
    return None


def _is_element(compared, loop, source: bytes) -> bool:
    if jf.indexed_accesses(compared, source) or jf.unwrap(compared).type in ("array_access",):
        return True
    if compared.type == "identifier" and loop.type == "enhanced_for_statement":
        name = loop.child_by_field_name("name")
        return name is not None and jf.text(name, source) == jf.text(compared, source)
    return False


def _is_counter(method, compared, source: bytes) -> bool:
    if compared.type != "identifier":
        return False
    var = jf.text(compared, source)
    writes = jf.writes_of(method, var, source)
    return bool(writes) and all(
        w.type == "update_expression" or jf.operator(w) in ("+=",) or
        (jf.operator(w) == "=" and jf.literal_kind(jf.text(w.child_by_field_name("right"), source)) == "int")
        for w in writes
    )


def _nonnegative(node, source: bytes) -> bool:
    value = jf.text(node, source)
    return bool(re.search(r"\.length\b|\.length\(\)|\.size\(\)|Math\.abs|count", value))


# ═══════════════════════════ 8. EARLY_RETURN_IN_LOOP ══════════════════════════
# `for (...) { if (a[i] == t) return true; else return false; }` decides on the
# first element. A return inside a loop is fine on a hit; leaving on BOTH
# branches, or unconditionally, ends the loop after one pass.

def propose_early_return_in_loop(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), *jf.LOOP_TYPES):
        body = jf.loop_body(loop)
        top = jf.statements(body)
        method = jf.method_of(loop)
        var = jf.loop_var_of(loop, source)
        following = loop.next_named_sibling
        while following is not None and following.type in jf.COMMENT_TYPES:
            following = following.next_named_sibling
        for statement in top:
            both = False
            unconditional = False
            if statement.type == "if_statement" and statement.child_by_field_name("alternative") is not None:
                both = _exits(statement.child_by_field_name("consequence")) and _exits(statement.child_by_field_name("alternative"))
            elif statement.type in ("return_statement",) and statement is top[-1] and len(top) >= 1:
                unconditional = True
            if not (both or unconditional):
                continue
            returns = [r for r in jf.descendants(statement, "return_statement")]
            values = {jf.text(r, source).replace("return", "").strip(" ;") for r in returns}
            features = {
                "both_branches_exit": jf.flag(both),
                "unconditional_return": jf.flag(unconditional),
                "opposite_booleans": jf.flag(values == {"true", "false"}),
                "returns_literals": jf.flag(bool(values) and all(jf.literal_kind(v) != "other" for v in values)),
                "uses_break": jf.flag(bool(jf.descendants(statement, "break_statement"))),
                "method_returns_boolean": jf.flag(jf.method_return_type(method, source) == "boolean"),
                "return_after_loop": jf.flag(following is not None and following.type == "return_statement"),
                "loop_var_in_condition": jf.flag(var is not None and statement.type == "if_statement" and var in jf.identifiers(statement.child_by_field_name("condition"), source)),
                "statements_before_in_body": float(top.index(statement)),
                "body_statement_count": float(len(top)),
                "loop_is_while": jf.flag(loop.type in ("while_statement", "do_statement")),
                "returns_loop_var": jf.flag(var is not None and any(jf.text(r, source).replace(" ", "") == f"return{var};" for r in returns)),
            }
            finding = _result(
                "EARLY_RETURN_IN_LOOP", statement, source, 0.8,
                "Every path through this part of the loop leaves the method, so the loop can only ever look at one element.",
                context_node=statement,
                details={"statement": _first_line(jf.text(statement, source))},
            )
            found.append(Candidate(finding, features, [jf.span(statement)]))
    return found


def _exits(node) -> bool:
    if node is None:
        return False
    if node.type in ("return_statement", "break_statement", "throw_statement"):
        return True
    if node.type == "block":
        inner = jf.statements(node)
        return bool(inner) and _exits(inner[-1])
    if node.type == "if_statement":
        alternative = node.child_by_field_name("alternative")
        return alternative is not None and _exits(node.child_by_field_name("consequence")) and _exits(alternative)
    return False


# ═══════════════════════════ 9. UNREACHABLE_ELSE_IF_ORDER ═════════════════════
# `if (score >= 50) ... else if (score >= 75)` - every score that reaches the
# second test already passed the first, so that branch never runs. Swapping
# two branches is harmless when the ranges do not overlap; the model learns
# which chains are which.

_COMPARISON = {"<", ">", "<=", ">=", "=="}


def propose_unreachable_else_if_order(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for head in jf.descendants(_root(parse_result), "if_statement"):
        parent = head.parent
        if parent is not None and parent.type == "if_statement" and parent.child_by_field_name("alternative") == head:
            continue
        branches = []
        current = head
        while current is not None and current.type == "if_statement":
            branches.append(current)
            current = current.child_by_field_name("alternative")
        if len(branches) < 2:
            continue
        parsed = [_condition_interval(jf.unwrap(b.child_by_field_name("condition")), source) for b in branches]
        variables = [p[0] for p in parsed if p is not None]
        if len(variables) < 2:
            continue
        main_var = max(set(variables), key=variables.count)
        same_var = [p for p in parsed if p is not None and p[0] == main_var]
        if len(same_var) < 2:
            continue
        # A test repeated word for word is DUPLICATE_IF_ELSE_CONDITION's to
        # report; saying it twice under two names helps nobody.
        conditions = [" ".join(jf.text(jf.unwrap(b.child_by_field_name("condition")), source).split()) for b in branches]
        if len(set(conditions)) < len(conditions):
            continue
        unreachable_index = None
        earlier: List[Tuple[float, float]] = []
        for index, item in enumerate(parsed):
            if item is None or item[0] != main_var:
                continue
            if earlier and _covered(item[1], earlier):
                unreachable_index = index
                break
            earlier.append(item[1])
        ops = [p[2] for p in same_var]
        thresholds = [p[3] for p in same_var if p[3] is not None]
        features = {
            "branch_count": float(len(branches)),
            "same_var_share": len(same_var) / len(branches),
            "has_unreachable_branch": jf.flag(unreachable_index is not None),
            "unreachable_position": float(unreachable_index or 0),
            "uses_ranges": jf.flag(any(p[2] == "range" for p in same_var)),
            "all_greater": jf.flag(all(op in (">", ">=") for op in ops)),
            "all_less": jf.flag(all(op in ("<", "<=") for op in ops)),
            "mixed_directions": jf.flag(len({op[0] for op in ops if op in ("<", ">", "<=", ">=")}) > 1),
            "thresholds_ascending": jf.flag(len(thresholds) > 1 and thresholds == sorted(thresholds)),
            "thresholds_descending": jf.flag(len(thresholds) > 1 and thresholds == sorted(thresholds, reverse=True)),
            # Whether the order suits the comparison: >= tests go from the
            # highest threshold down, < tests from the lowest up.
            "order_consistent": jf.flag(len(thresholds) > 1 and (
                (all(op in (">", ">=") for op in ops) and thresholds == sorted(thresholds, reverse=True))
                or (all(op in ("<", "<=") for op in ops) and thresholds == sorted(thresholds)))),
            "order_reversed": jf.flag(len(thresholds) > 1 and (
                (all(op in (">", ">=") for op in ops) and thresholds == sorted(thresholds))
                or (all(op in ("<", "<=") for op in ops) and thresholds == sorted(thresholds, reverse=True)))),
            "has_final_else": jf.flag(current is not None),
            "has_equality_branch": jf.flag("==" in ops),
        }
        anchor = branches[unreachable_index] if unreachable_index is not None else branches[1]
        anchor_condition = anchor.child_by_field_name("condition")
        earlier_text = ""
        if unreachable_index is not None:
            for b, p in zip(branches[:unreachable_index], parsed[:unreachable_index]):
                if p is not None and p[0] == main_var and _covered(parsed[unreachable_index][1], [p[1]]):
                    earlier_text = jf.text(jf.unwrap(b.child_by_field_name("condition")), source)
                    break
        finding = _result(
            "UNREACHABLE_ELSE_IF_ORDER", anchor_condition or anchor, source, 0.8,
            "A later branch of this if / else if chain may never run, because an earlier test already catches every value it would.",
            context_node=anchor,
            details={"later": jf.text(jf.unwrap(anchor_condition), source) if anchor_condition is not None else "",
                     "earlier": earlier_text or jf.text(jf.unwrap(head.child_by_field_name("condition")), source)},
        )
        found.append(Candidate(finding, features, [jf.span(head)]))
    return found


def _number(node, source: bytes) -> Optional[float]:
    value = jf.text(node, source).strip().rstrip("dDfFlL")
    try:
        return float(value)
    except ValueError:
        return None


def _simple_interval(node, source: bytes):
    """`x >= 5` -> ("x", (5, inf), ">=", 5)."""
    if node is None or node.type != "binary_expression":
        return None
    op = jf.operator(node)
    if op not in _COMPARISON:
        return None
    left = jf.unwrap(node.child_by_field_name("left"))
    right = jf.unwrap(node.child_by_field_name("right"))
    eps = 1e-9
    if left is not None and left.type in ("identifier", "field_access", "method_invocation") and _number(right, source) is not None:
        name, c = jf.text(left, source), _number(right, source)
    elif right is not None and right.type in ("identifier", "field_access", "method_invocation") and _number(left, source) is not None:
        name, c = jf.text(right, source), _number(left, source)
        op = {"<": ">", ">": "<", "<=": ">=", ">=": "<=", "==": "=="}[op]
    else:
        return None
    interval = {
        ">": (c + eps, math.inf), ">=": (c, math.inf),
        "<": (-math.inf, c - eps), "<=": (-math.inf, c), "==": (c, c),
    }[op]
    return name, interval, op, c


def _condition_interval(node, source: bytes):
    simple = _simple_interval(node, source)
    if simple is not None:
        return simple
    if node is not None and node.type == "binary_expression" and jf.operator(node) == "&&":
        a = _simple_interval(jf.unwrap(node.child_by_field_name("left")), source)
        b = _simple_interval(jf.unwrap(node.child_by_field_name("right")), source)
        if a and b and a[0] == b[0]:
            lo, hi = max(a[1][0], b[1][0]), min(a[1][1], b[1][1])
            return a[0], (lo, hi), "range", None
    return None


def _covered(interval: Tuple[float, float], earlier: List[Tuple[float, float]]) -> bool:
    lo, hi = interval
    if lo > hi:
        return True
    point = lo
    for start, end in sorted(earlier):
        if start > point + 1e-12:
            break
        point = max(point, end + 1e-9)
        if point >= hi:
            return True
    return point >= hi


# ═══════════════════════ 10. MISLEADING_INDENTATION_NO_BRACES ═════════════════
# if (x > max)
#     max = x;
#     index = i;      <- indented as if inside, but runs every time
# Without braces only the first statement belongs to the if. Harmless when the
# extra line would be right either way; the model judges.

def propose_misleading_indentation_no_braces(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    targets = []
    for node in jf.descendants(_root(parse_result), "if_statement", "for_statement", "while_statement", "enhanced_for_statement"):
        if node.type == "if_statement":
            consequence = node.child_by_field_name("consequence")
            alternative = node.child_by_field_name("alternative")
            if alternative is None:
                targets.append((node, consequence, "if"))
            elif alternative.type not in ("if_statement", "block"):
                targets.append((node, alternative, "else"))
        else:
            targets.append((node, node.child_by_field_name("body"), "loop"))
    for owner, body, kind in targets:
        if body is None or body.type in ("block", ";"):
            continue
        following = owner.next_named_sibling
        while following is not None and following.type in jf.COMMENT_TYPES:
            following = following.next_named_sibling
        header_row = owner.start_point[0]
        header_indent = jf.line_indent(source, header_row)
        body_row = body.start_point[0]
        body_indent = jf.line_indent(source, body_row)
        features = {
            "kind_if": jf.flag(kind == "if"),
            "kind_else": jf.flag(kind == "else"),
            "kind_loop": jf.flag(kind == "loop"),
            "body_on_own_line": jf.flag(body_row > header_row),
            "next_exists": jf.flag(following is not None),
            "next_indent_deeper": 0.0,
            "next_indent_equals_body": 0.0,
            "next_on_body_line": 0.0,
            "blank_line_before_next": 0.0,
            "next_uses_body_writes": 0.0,
            "next_is_exit": 0.0,
            "next_is_closing": jf.flag(following is None),
        }
        anchor = body
        if following is not None:
            next_row = following.start_point[0]
            next_indent = jf.line_indent(source, next_row)
            features["next_indent_deeper"] = jf.flag(next_row > body.end_point[0] and next_indent > header_indent)
            features["next_indent_equals_body"] = jf.flag(next_row > body.end_point[0] and body_row > header_row and next_indent == body_indent)
            features["next_on_body_line"] = jf.flag(next_row == body.end_point[0])
            features["blank_line_before_next"] = jf.flag(next_row > body.end_point[0] + 1)
            written = jf.written_vars(body, source)
            features["next_uses_body_writes"] = jf.flag(bool(written & set(jf.identifiers(following, source))))
            features["next_is_exit"] = jf.flag(following.type in ("return_statement", "break_statement", "continue_statement"))
            if features["next_indent_deeper"] or features["next_on_body_line"]:
                anchor = following
        finding = _result(
            "MISLEADING_INDENTATION_NO_BRACES", anchor, source, 0.8,
            "Without braces only the first statement belongs to this " + ("else" if kind == "else" else "if" if kind == "if" else "loop") + ", even if the next line is indented to look like it does.",
            context_node=anchor,
            details={"header": _header(owner, source) if kind != "else" else "else", "statement": _first_line(jf.text(following, source)) if following is not None else ""},
        )
        end = following.end_byte if following is not None else body.end_byte
        found.append(Candidate(finding, features, [(owner.start_byte, end)]))
    return found


# ═══════════════════════════ 11. NON_SHORT_CIRCUIT_OPERATOR ═══════════════════
# `s != null & s.length() > 0` evaluates BOTH sides, so a null s still throws.
# `&` and `|` on two plain comparisons give the same answer as && and ||; the
# difference only bites when the right side depends on the left being true.

_BOOLEAN_CALLS = {"equals", "equalsIgnoreCase", "isEmpty", "isBlank", "contains", "startsWith", "endsWith",
                  "hasNext", "isDigit", "isLetter", "isLetterOrDigit", "isUpperCase", "isLowerCase", "isWhitespace",
                  "containsKey", "matches"}


def propose_non_short_circuit_operator(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for node in jf.descendants(_root(parse_result), "binary_expression"):
        op = jf.operator(node)
        if op not in ("&", "|"):
            continue
        method = jf.method_of(node)
        left = jf.unwrap(node.child_by_field_name("left"))
        right = jf.unwrap(node.child_by_field_name("right"))
        if not (_booleanish(left, method, source) and _booleanish(right, method, source)):
            continue
        left_text = jf.text(left, source)
        left_ids = set(jf.identifiers(left, source))
        null_checked = {m.group(1) for m in re.finditer(r"(\w+)\s*!=\s*null|null\s*!=\s*(\w+)", left_text) if m.group(1)}
        null_checked |= {m.group(1) for m in re.finditer(r"null\s*!=\s*(\w+)", left_text)}
        null_checked |= {m.group(1) for m in re.finditer(r"(\w+)\s*==\s*null", left_text)}
        right_derefs = {jf.text(c.child_by_field_name("object"), source) for c in jf.descendants(right, "method_invocation", "field_access") if c.child_by_field_name("object") is not None}
        right_index_vars = {name for _, _, ix in jf.indexed_accesses(right, source) for name in jf.identifiers(ix, source)}
        right_divisors = {jf.text(b.child_by_field_name("right"), source).strip() for b in jf.descendants(right, "binary_expression") if jf.operator(b) in ("/", "%")}
        features = {
            "op_and": jf.flag(op == "&"),
            "left_null_check": jf.flag(bool(null_checked)),
            "left_bounds_check": jf.flag(bool(re.search(r"\.length|\.size\(\)|\.isEmpty\(\)|>=\s*0|>\s*0", left_text))),
            "left_nonzero_check": jf.flag(bool(re.search(r"!=\s*0\b", left_text))),
            "right_derefs_checked_var": jf.flag(bool(null_checked & right_derefs)),
            "right_indexes_with_left_var": jf.flag(bool(right_index_vars & left_ids)),
            "right_divides_by_left_var": jf.flag(bool(right_divisors & left_ids)),
            "right_has_call": jf.flag(bool(jf.descendants(right, "method_invocation"))),
            "right_has_side_effect": jf.flag(bool(jf.descendants(right, "update_expression", "assignment_expression"))),
            "right_has_index": jf.flag(bool(jf.indexed_accesses(right, source))),
            "shared_identifiers": float(len(left_ids & set(jf.identifiers(right, source)))),
            "both_simple_comparisons": jf.flag(all(n is not None and n.type == "binary_expression" and jf.operator(n) in ("<", ">", "<=", ">=", "==", "!=") and not jf.descendants(n, "method_invocation", "array_access") for n in (left, right))),
            "in_condition": jf.flag(jf.enclosing(node, {"if_statement", "while_statement", "for_statement"}) is not None),
            # The same variable was already checked for null earlier in the
            # method (`if (s == null) return 0;`): then evaluating both sides
            # here is harmless, which is what most equivalent mutants were.
            "checked_var_guarded_before": jf.flag(_guarded_earlier(method, null_checked, node.start_byte, source)),
        }
        intended = "&&" if op == "&" else "||"
        finding = _result(
            "NON_SHORT_CIRCUIT_OPERATOR", node, source, 0.8,
            f"`{op}` evaluates both sides even when the left side already decides the answer; `{intended}` stops early.",
            context_node=_statement_of(node),
            details={"expression": jf.text(node, source), "operator": op, "intended": intended},
        )
        found.append(Candidate(finding, features, [jf.span(node)]))
    return found


def _guarded_earlier(method, names: set, before: int, source: bytes) -> bool:
    if method is None or not names:
        return False
    earlier = source[method.start_byte:before].decode("utf-8", errors="replace")
    return any(re.search(rf"\b{re.escape(name)}\s*[=!]=\s*null\b|\bnull\s*[=!]=\s*{re.escape(name)}\b", earlier) for name in names)


def _booleanish(node, method, source: bytes) -> bool:
    node = jf.unwrap(node)
    if node is None:
        return False
    if node.type in ("true", "false"):
        return True
    if node.type == "unary_expression" and jf.text(node, source).lstrip().startswith("!"):
        return True
    if node.type == "binary_expression":
        op = jf.operator(node)
        if op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
            return True
        if op in ("&", "|", "^"):
            return _booleanish(node.child_by_field_name("left"), method, source) and _booleanish(node.child_by_field_name("right"), method, source)
        return False
    if node.type == "instanceof_expression":
        return True
    if node.type == "method_invocation":
        name = jf.text(node.child_by_field_name("name"), source)
        return name in _BOOLEAN_CALLS or bool(re.match(r"(is|has|can|should)[A-Z]", name))
    if node.type == "identifier":
        return jf.declared_type(method, jf.text(node, source), source) in ("boolean", "Boolean")
    return False


# ── registry: error type -> proposer ──

PROPOSERS: Dict[str, ProposerFn] = {
    "LOOP_SKIPS_LAST_ELEMENT": propose_loop_skips_last_element,
    "INDEX_PLUS_ONE_OUT_OF_BOUNDS": propose_index_plus_one_out_of_bounds,
    "WRONG_LOOP_VARIABLE_IN_INDEX": propose_wrong_loop_variable_in_index,
    "NESTED_LOOP_WRONG_COUNTER": propose_nested_loop_wrong_counter,
    "LOOP_COUNTER_CHANGED_IN_BODY": propose_loop_counter_changed_in_body,
    "ACCUMULATOR_RESET_INSIDE_LOOP": propose_accumulator_reset_inside_loop,
    "WRONG_EXTREME_INITIAL_VALUE": propose_wrong_extreme_initial_value,
    "EARLY_RETURN_IN_LOOP": propose_early_return_in_loop,
    "UNREACHABLE_ELSE_IF_ORDER": propose_unreachable_else_if_order,
    "MISLEADING_INDENTATION_NO_BRACES": propose_misleading_indentation_no_braces,
    "NON_SHORT_CIRCUIT_OPERATOR": propose_non_short_circuit_operator,
}


def located(proposer: ProposerFn) -> Callable[[ParseResult], List[DetectionResult]]:
    """Every site a proposer offers, as plain findings (no model applied)."""
    def locate(parse_result: ParseResult) -> List[DetectionResult]:
        return [candidate.finding for candidate in proposer(parse_result)]
    locate.__name__ = f"locate_{proposer.__name__.removeprefix('propose_')}"
    return locate
