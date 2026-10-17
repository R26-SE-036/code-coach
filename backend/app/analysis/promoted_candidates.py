"""Candidate proposers for the thirteen types moved onto per-site models.

Five of these used to be "ml_gated": one model looked at a whole file's
numbers and said "this mistake is probably in here", and then a rule flagged
EVERY match in the file, right or wrong. Eight were pure rules. All thirteen
now work like the logic errors in logic_candidates.py: the proposer offers
every site that might be the mistake - including the look-alikes the old rule
had to either flag or skip wholesale - with numbers that describe that site
alone, and the type's own model, trained on mutated and executed code
(dev_tools/mutation), decides each one.

What each proposer reports keeps the line, column, message and `details` keys
of the locator it replaces, so the targeted hints, the stored diagnostics and
everything downstream see the same shape as before.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from app.analysis import java_facts as jf
from app.analysis.issue_locators import _IMMUTABLE_STRING_METHODS, _result
from app.analysis.logic_candidates import _BOOLEAN_CALLS, Candidate, ProposerFn
from app.models import ParseResult

# ═════════════════════════════════ what an expression holds ═════════════════
# Several types turn on what kind of value an operand is - a String compared
# with ==, two ints divided where a double was wanted. The old rules only knew
# the types of plain variables; this follows literals, fields, array elements,
# casts, arithmetic and the return types of common methods too, and says
# "unknown" rather than guess.

_STRING_TYPES = {"String"}
_CHAR_TYPES = {"char", "Character"}
_INT_TYPES = {"int", "long", "short", "byte", "Integer", "Long", "Short", "Byte"}
_DECIMAL_TYPES = {"double", "float", "Double", "Float"}
_BOOLEAN_TYPES = {"boolean", "Boolean"}
_BUILDER_TYPES = {"StringBuilder", "StringBuffer"}

_STRING_METHODS = {"substring", "trim", "strip", "stripLeading", "stripTrailing", "toUpperCase", "toLowerCase",
                   "replace", "replaceAll", "replaceFirst", "concat", "repeat", "toString", "nextLine", "next",
                   "valueOf", "join", "format", "intern"}
_INT_METHODS = {"length", "size", "indexOf", "lastIndexOf", "compareTo", "compareToIgnoreCase", "parseInt",
                "nextInt", "hashCode", "getNumericValue", "round", "floorDiv", "floorMod", "signum"}
_DECIMAL_METHODS = {"sqrt", "pow", "random", "parseDouble", "nextDouble", "ceil", "floor", "cbrt", "log", "exp",
                    "sin", "cos", "hypot"}
_CHAR_METHODS = {"charAt", "toUpperCaseChar"}
_BUILDER_METHODS = {"append", "reverse", "insert", "deleteCharAt", "delete", "setLength", "setCharAt"}
_NUMBER_KINDS = {"int", "char", "decimal"}


def _kind_of_type(type_text: str) -> str:
    t = (type_text or "").strip()
    if not t:
        return "unknown"
    if t in _STRING_TYPES:
        return "string"
    if t in _CHAR_TYPES:
        return "char"
    if t in _INT_TYPES:
        return "int"
    if t in _DECIMAL_TYPES:
        return "decimal"
    if t in _BOOLEAN_TYPES:
        return "boolean"
    if t in _BUILDER_TYPES:
        return "builder"
    if t.endswith("]"):
        return "array"
    if re.match(r"(Array)?List\b|List<", t):
        return "list"
    return "object"


class Types:
    """Answers "what kind of value is this?" for one parsed file."""

    def __init__(self, parse_result: ParseResult):
        self.source = parse_result.source_bytes
        root = parse_result.tree.root_node
        self.fields: Dict[str, str] = {}
        for field in jf.descendants(root, "field_declaration"):
            type_text = jf.text(field.child_by_field_name("type"), self.source)
            for declarator in field.named_children:
                if declarator.type == "variable_declarator":
                    self.fields[jf.text(declarator.child_by_field_name("name"), self.source)] = type_text
        self.returns: Dict[str, str] = {}
        for method in jf.descendants(root, "method_declaration"):
            name = jf.text(method.child_by_field_name("name"), self.source)
            self.returns.setdefault(name, jf.method_return_type(method, self.source))

    def declared(self, node, name: str) -> str:
        for loop in jf.ancestors(node):
            if loop.type == "enhanced_for_statement" and jf.text(loop.child_by_field_name("name"), self.source) == name:
                return jf.text(loop.child_by_field_name("type"), self.source)
            if loop.type == "catch_clause":
                break
        return jf.declared_type(jf.method_of(node), name, self.source) or self.fields.get(name, "")

    def kind(self, node) -> str:
        node = jf.unwrap(node)
        if node is None:
            return "unknown"
        t = node.type
        if t == "string_literal" or t == "text_block":
            return "string"
        if t == "character_literal":
            return "char"
        if t in ("decimal_integer_literal", "hex_integer_literal", "octal_integer_literal", "binary_integer_literal"):
            return "int"
        if t == "decimal_floating_point_literal":
            return "decimal"
        if t in ("true", "false"):
            return "boolean"
        if t == "null_literal":
            return "null"
        if t == "identifier":
            name = jf.text(node, self.source)
            declared = self.declared(node, name)
            if declared:
                return _kind_of_type(declared)
            return "constant" if re.fullmatch(r"[A-Z][A-Z0-9_]+", name) else "unknown"
        if t == "field_access":
            field = jf.text(node.child_by_field_name("field"), self.source)
            owner = jf.text(node.child_by_field_name("object"), self.source)
            if field == "length":
                return "int"
            if owner in ("Integer", "Long", "Short", "Byte"):
                return "int"
            if owner in ("Double", "Float") or (owner == "Math" and field in ("PI", "E")):
                return "decimal"
            if owner == "this":
                return _kind_of_type(self.fields.get(field, ""))
            return "unknown"
        if t == "array_access":
            base, depth = node, 0
            while base is not None and base.type == "array_access":
                base, depth = jf.unwrap(base.child_by_field_name("array")), depth + 1
            if base is not None and base.type == "identifier":
                declared = self.declared(base, jf.text(base, self.source)).replace(" ", "")
                for _ in range(depth):
                    if declared.endswith("[]"):
                        declared = declared[:-2]
                return _kind_of_type(declared) if declared else "unknown"
            return "unknown"
        if t == "method_invocation":
            return self._call_kind(node)
        if t == "cast_expression":
            return _kind_of_type(jf.text(node.child_by_field_name("type"), self.source))
        if t == "object_creation_expression":
            return _kind_of_type(jf.text(node.child_by_field_name("type"), self.source))
        if t == "array_creation_expression":
            return "array"
        if t in ("update_expression",):
            return "int"
        if t == "assignment_expression":
            return self.kind(node.child_by_field_name("left"))
        if t == "ternary_expression":
            kind = self.kind(node.child_by_field_name("consequence"))
            return kind if kind not in ("unknown", "null") else self.kind(node.child_by_field_name("alternative"))
        if t == "unary_expression":
            if jf.text(node, self.source).lstrip().startswith("!"):
                return "boolean"
            return self.kind(node.child_by_field_name("operand"))
        if t == "instanceof_expression":
            return "boolean"
        if t == "binary_expression":
            op = jf.operator(node)
            if op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                return "boolean"
            left, right = self.kind(node.child_by_field_name("left")), self.kind(node.child_by_field_name("right"))
            if op == "+" and "string" in (left, right):
                return "string"
            if op in ("&", "|", "^") and left == right == "boolean":
                return "boolean"
            if op in ("+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>", ">>>"):
                if "decimal" in (left, right) and {left, right} <= _NUMBER_KINDS:
                    return "decimal"
                if {left, right} <= {"int", "char"}:
                    return "int"
            return "unknown"
        return "unknown"

    def _call_kind(self, node) -> str:
        name = jf.text(node.child_by_field_name("name"), self.source)
        owner_node = node.child_by_field_name("object")
        owner = jf.text(owner_node, self.source) if owner_node is not None else ""
        args = node.child_by_field_name("arguments")
        arg_nodes = [a for a in (args.named_children if args is not None else []) if a.type not in jf.COMMENT_TYPES]
        if owner == "Math":
            if name in ("abs", "max", "min"):
                kinds = {self.kind(a) for a in arg_nodes}
                return "int" if kinds <= {"int", "char"} and kinds else "decimal" if kinds <= _NUMBER_KINDS and kinds else "unknown"
            if name == "round":
                return "int"
            if name in _DECIMAL_METHODS:
                return "decimal"
        if owner == "Character":
            if name.startswith("is"):
                return "boolean"
            if name in ("toUpperCase", "toLowerCase"):
                return "char"
            if name == "getNumericValue":
                return "int"
            if name == "toString":
                return "string"
        if owner in ("Integer", "Long") and name in ("parseInt", "parseLong", "max", "min", "sum", "compare", "abs"):
            return "int"
        if owner in ("Integer", "Long", "Double") and name == "toString":
            return "string"
        if owner == "Double" and name == "parseDouble":
            return "decimal"
        if owner == "String" and name in ("valueOf", "join", "format"):
            return "string"
        owner_kind = self.kind(owner_node) if owner_node is not None else "unknown"
        if owner_kind == "builder":
            if name in _BUILDER_METHODS:
                return "builder"
            if name == "toString":
                return "string"
            if name in ("length", "indexOf"):
                return "int"
            if name == "charAt":
                return "char"
        if owner_kind == "list" and name == "get":
            return "unknown"
        if name in _BOOLEAN_CALLS or re.match(r"(is|has|can|should)[A-Z]", name):
            return "boolean"
        if name in _CHAR_METHODS:
            return "char"
        if name in _INT_METHODS:
            return "int"
        if name in _STRING_METHODS:
            return "string"
        if owner_node is None and name in self.returns:
            return _kind_of_type(self.returns[name])
        if name in _DECIMAL_METHODS:
            return "decimal"
        return "unknown"


# ═══════════════════════════════════ shared small facts ═════════════════════

_EXIT_TYPES = {"break_statement", "return_statement", "throw_statement", "continue_statement", "yield_statement"}
_COUNT_WORDS = ["n", "count", "size", "num", "limit", "max", "times", "rows", "cols", "steps", "total", "number", "len", "length", "end", "last", "high", "hi"]
_AVERAGE_WORDS = ["avg", "average", "mean", "percent", "percentage", "pct", "ratio", "rate", "share", "fraction", "score", "grade", "gpa"]
_MONEY_WORDS = ["price", "total", "cost", "amount", "balance", "sum", "pay", "fee", "change", "money", "cash"]


def _root(parse_result: ParseResult):
    return parse_result.tree.root_node


def _header_text(node, source: bytes) -> str:
    return " ".join(jf.text(node, source).split())


def _condition_of(node):
    return jf.unwrap(node.child_by_field_name("condition"))


def _decl_value(method, name: str, before: int, source: bytes):
    """The value `name` was last declared with before byte `before`, if any."""
    found = None
    for declarator in jf.descendants(method, "variable_declarator"):
        if declarator.start_byte >= before:
            break
        if jf.text(declarator.child_by_field_name("name"), source) == name:
            found = declarator.child_by_field_name("value")
    return found


def _writes_between(method, name: str, start: int, end: int, source: bytes) -> int:
    return sum(1 for write in jf.writes_of(method, name, source) if start <= write.start_byte < end)


def _in_loop(node) -> float:
    return jf.flag(bool(jf.enclosing_loops(node)))


def _guard_texts(node, method, source: bytes) -> List[str]:
    """Conditions that must hold for `node` to run: enclosing if / ternary
    conditions it sits in the true branch of, and early-exit ifs before it."""
    texts: List[str] = []
    child = node
    for parent in jf.ancestors(node):
        if parent.type in ("if_statement", "ternary_expression", "while_statement"):
            condition = parent.child_by_field_name("condition")
            branch = parent.child_by_field_name("alternative") if parent.type != "while_statement" else None
            if condition is not None and not jf.is_inside(node, condition):
                negated = branch is not None and jf.is_inside(node, branch)
                texts.append(("!" if negated else "") + jf.text(condition, source))
        if parent.type in ("binary_expression",) and jf.operator(parent) in ("&&", "||"):
            left = parent.child_by_field_name("left")
            if left is not None and not jf.is_inside(node, left):
                texts.append(("!" if jf.operator(parent) == "||" else "") + jf.text(left, source))
        if parent == method:
            break
        child = parent
    del child
    if method is not None:
        for statement in jf.descendants(method, "if_statement"):
            if statement.end_byte > node.start_byte:
                continue
            consequence = statement.child_by_field_name("consequence")
            if consequence is not None and any(s.type in ("return_statement", "throw_statement") for s in jf.statements(consequence)):
                texts.append("!" + jf.text(statement.child_by_field_name("condition"), source))
    return texts


_FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<=", "==": "==", "!=": "!="}


def _excludes_zero(op: str, k: int) -> bool:
    """Does `n op k` being TRUE rule out n == 0?"""
    return {"==": k != 0, "!=": k == 0, ">": k >= 0, ">=": k >= 1, "<": k <= 0, "<=": k <= -1}[op]


def _requires_zero_or_less(op: str, k: int) -> bool:
    """Does `n op k` being FALSE rule out n == 0? (it is an early-exit test)"""
    negated = {"==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<"}[op]
    return _excludes_zero(negated, k)


def _mentions_nonzero(texts: List[str], names: List[str]) -> bool:
    """Do these guard conditions rule out a zero value of any of `names`?

    `!` in front of a text means the code runs when that condition is false
    (an else branch, or after `if (...) return`)."""
    for raw in texts:
        negated = raw.startswith("!")
        guard = raw.lstrip("!")
        for name in names:
            if not name:
                continue
            n = re.escape(name)
            if re.search(rf"!\s*{n}\.isEmpty\(\)", guard) and not negated:
                return True
            if re.search(rf"(?<!!){n}\.isEmpty\(\)", guard) and negated:
                return True
            comparisons = [(m.group(1), int(m.group(2))) for m in re.finditer(rf"(?<![\w.]){n}\s*(==|!=|<=|>=|<|>)\s*(-?\d+)\b", guard)]
            comparisons += [(_FLIP[m.group(2)], int(m.group(1))) for m in re.finditer(rf"(-?\d+)\s*(==|!=|<=|>=|<|>)\s*{n}(?![\w(])", guard)]
            for op, k in comparisons:
                if (not negated and _excludes_zero(op, k)) or (negated and _requires_zero_or_less(op, k)):
                    return True
    return False


# ════════════════════════════════ 1. OFF_BY_ONE_LOOP_BOUNDARY ═════════════════
# `i <= a.length` makes one pass too many. `i <= n` is exactly right when n is
# a count and the body uses i itself, `i <= a.length` is right when the body
# reads a[i - 1] or the array written was made one longer (prefix sums).

def propose_off_by_one_loop_boundary(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "for_statement"):
        var = jf.for_loop_var(loop, source)
        condition_node = loop.child_by_field_name("condition")
        condition = jf.unwrap(condition_node)
        updates = jf.for_updates(loop)
        if not var or condition is None or condition.type != "binary_expression" or not updates:
            continue
        left = jf.unwrap(condition.child_by_field_name("left"))
        right = jf.unwrap(condition.child_by_field_name("right"))
        if left is None or left.type != "identifier" or jf.text(left, source) != var:
            continue
        op = jf.operator(condition)
        direction = jf.update_direction(updates[0], var, source)
        init_text = jf.for_init_value(loop, source).replace(" ", "")
        target, k = jf.length_minus(right, source)
        bound_text = jf.text(right, source).strip()
        method = jf.method_of(loop)
        if direction == 1 and op == "<=" and not (target and k >= 1):
            ascending = True
        elif direction == 1 and op == "<" and target and k < 0:
            ascending = True
        elif direction == -1 and op == ">=" and jf.length_minus(_init_node(loop), source)[0] and jf.length_minus(_init_node(loop), source)[1] <= 0:
            ascending, target = False, jf.length_minus(_init_node(loop), source)[0]
        else:
            continue
        body = jf.loop_body(loop)
        accesses = [(coll, jf.index_offset(index, var, source)) for _, coll, index in jf.indexed_accesses(body, source)]
        alias = _decl_value(method, bound_text, loop.start_byte, source) if right is not None and right.type == "identifier" else None
        alias_target, alias_k = jf.length_minus(alias, source) if alias is not None else (None, 0)
        collection = target or alias_target
        features = {
            "ascending": jf.flag(ascending),
            "cond_leq": jf.flag(op in ("<=", ">=")),
            "bound_is_length": jf.flag(bool(target) and k == 0),
            "bound_beyond_length": jf.flag(bool(target) and k < 0),
            "bound_is_identifier": jf.flag(right is not None and right.type == "identifier"),
            "bound_is_literal": jf.flag(bound_text.isdigit()),
            "bound_alias_of_length": jf.flag(bool(alias_target) and alias_k == 0),
            "bound_alias_of_length_minus": jf.flag(bool(alias_target) and alias_k >= 1),
            "bound_name_count_like": jf.has_token(bound_text, _COUNT_WORDS) if right is not None and right.type == "identifier" else 0.0,
            "init_is_zero": jf.flag(init_text == "0"),
            "init_is_one": jf.flag(init_text == "1"),
            "body_indexes_collection_at_var": jf.flag(any(c == collection and off == 0 for c, off in accesses)),
            "body_indexes_collection_before_var": jf.flag(any(c == collection and off is not None and off < 0 for c, off in accesses)),
            "body_indexes_other_at_var": jf.flag(any(c != collection and off == 0 for c, off in accesses)),
            "body_indexes_anything_at_var": jf.flag(any(off is not None and off >= 0 for _, off in accesses)),
            "collection_made_longer": jf.flag(_made_longer(method, collection, source)),
            "var_uses_in_body": float(jf.uses(body, var, source)),
            "body_has_break": jf.flag(bool(jf.descendants(body, "break_statement", "return_statement"))),
            "nested_in_loop": _in_loop(loop),
            "target_is_string": jf.flag(".length()" in bound_text),
        }
        array_match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\.(length|size)", jf.text(condition_node, source))
        array_name = array_match.group(1) if array_match else (collection if collection and re.fullmatch(r"[A-Za-z_]\w*", collection) else "")
        finding = _result(
            "OFF_BY_ONE_LOOP_BOUNDARY", condition_node, source, 0.8,
            "This loop may run one step too far: on its last pass the counter reaches the bound itself.",
            context_node=loop,
            details={"condition": jf.text(condition_node, source).strip(), "array": array_name},
        )
        found.append(Candidate(finding, features, [jf.span(condition_node), jf.span(loop.child_by_field_name("init") or condition_node)]))
    return found


def _init_node(for_node):
    init = for_node.child_by_field_name("init")
    if init is None:
        return None
    if init.type == "local_variable_declaration":
        declarator = init.child_by_field_name("declarator")
        return declarator.child_by_field_name("value") if declarator is not None else None
    if init.type == "assignment_expression":
        return init.child_by_field_name("right")
    return None


def _made_longer(method, collection: Optional[str], source: bytes) -> bool:
    """Was `collection` created with room for one more (new int[n + 1])?"""
    if method is None or not collection:
        return False
    for creation in jf.descendants(method, "array_creation_expression"):
        parent = creation.parent
        name = None
        if parent is not None and parent.type == "variable_declarator":
            name = jf.text(parent.child_by_field_name("name"), source)
        elif parent is not None and parent.type == "assignment_expression":
            name = jf.text(parent.child_by_field_name("left"), source)
        if name == collection and re.search(r"\+\s*\d+\s*\]", jf.text(creation, source)):
            return True
    return False


# ═════════════════════════ 2. INCORRECT_CONDITIONAL_OPERATOR ═════════════════
# `if (done = true)` assigns instead of comparing, and the condition is always
# what was just assigned. `while ((pos = s.indexOf(c, pos)) != -1)` assigns
# inside a condition on purpose, and is idiomatic.

def propose_incorrect_conditional_operator(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    types = Types(parse_result)
    found: List[Candidate] = []
    for statement in jf.descendants(_root(parse_result), "if_statement", "while_statement", "do_statement", "for_statement", "ternary_expression"):
        condition_node = statement.child_by_field_name("condition")
        if condition_node is None:
            continue
        for assignment in jf.descendants(condition_node, "assignment_expression"):
            if jf.enclosing(assignment, {"lambda_expression", "method_invocation"}) not in (None,) and jf.is_inside(jf.enclosing(assignment, {"lambda_expression", "method_invocation"}), condition_node):
                continue
            left = assignment.child_by_field_name("left")
            right = jf.unwrap(assignment.child_by_field_name("right"))
            parent = assignment.parent
            while parent is not None and parent.type == "parenthesized_expression":
                parent = parent.parent
            whole = jf.unwrap(condition_node) == assignment
            variable = jf.text(left, source)
            body = statement.child_by_field_name("body") or statement.child_by_field_name("consequence")
            features = {
                "whole_condition": jf.flag(whole),
                "right_is_boolean_literal": jf.flag(right is not None and right.type in ("true", "false")),
                "left_is_boolean": jf.flag(types.kind(left) == "boolean"),
                "inside_comparison": jf.flag(parent is not None and parent.type == "binary_expression" and jf.operator(parent) in ("==", "!=", "<", ">", "<=", ">=")),
                "inside_logical": jf.flag(parent is not None and parent.type == "binary_expression" and jf.operator(parent) in ("&&", "||", "&", "|")),
                "negated": jf.flag(parent is not None and parent.type == "unary_expression"),
                "compound_operator": jf.flag(jf.operator(assignment) != "="),
                "right_has_call": jf.flag(bool(jf.descendants(right, "method_invocation"))),
                "right_is_identifier": jf.flag(right is not None and right.type == "identifier"),
                "in_loop_condition": jf.flag(statement.type in ("while_statement", "do_statement", "for_statement")),
                "left_used_in_body": jf.flag(body is not None and jf.uses(body, variable, source) > 0),
            }
            finding = _result(
                "INCORRECT_CONDITIONAL_OPERATOR", assignment, source, 0.8,
                "Possible assignment used inside a condition.",
                context_node=statement,
                details={"assignment": jf.text(assignment, source).strip(), "variable": variable.strip()},
            )
            found.append(Candidate(finding, features, [jf.span(assignment)]))
    return found


# ═══════════════════════════════ 3. ARRAY_LENGTH_INDEX_MISUSE ═════════════════
# `a[a.length]` is one past the end. `b[a.length]` is fine when b was made one
# longer, and `a[a.length - 1]` - the look-alike every correct "last element"
# has - is right.

def propose_array_length_index_misuse(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for access, collection, index in jf.indexed_accesses(_root(parse_result), source):
        index_node = jf.unwrap(index)
        target, k = jf.length_minus(index_node, source)
        method = jf.method_of(access)
        alias_k = None
        if target is None and index_node is not None and index_node.type == "identifier":
            value = _decl_value(method, jf.text(index_node, source), access.start_byte, source)
            alias_target, alias_k = jf.length_minus(value, source) if value is not None else (None, 0)
            if alias_target is None or _writes_between(method, jf.text(index_node, source), value.start_byte if value is not None else 0, access.start_byte, source):
                continue
            target, k = alias_target, alias_k
        if target is None or k > 2:
            continue
        parent = access.parent
        guards = _guard_texts(access, method, source)
        features = {
            "minus_k": float(k),
            "at_or_past_length": jf.flag(k <= 0),
            "same_collection": jf.flag(target == collection),
            "collection_made_longer": jf.flag(_made_longer(method, collection, source)),
            "is_write": jf.flag(parent is not None and parent.type == "assignment_expression" and parent.child_by_field_name("left") == access),
            "via_alias": jf.flag(alias_k is not None),
            "is_string": jf.flag(jf.text(access, source).find(".charAt(") >= 0),
            "is_list": jf.flag(".get(" in jf.text(access, source)),
            "in_loop": _in_loop(access),
            "guarded_by_length": jf.flag(any(re.search(r"\.length|\.size\(\)|isEmpty", g) for g in guards)),
            "in_return": jf.flag(jf.enclosing(access, {"return_statement"}) is not None),
        }
        reported = index if index is not None else access
        finding = _result(
            "ARRAY_LENGTH_INDEX_MISUSE", reported, source, 0.8,
            "Possible array index out-of-bounds issue detected.",
            context_node=access,
            details={"access": jf.text(access, source).strip(), "array": collection.strip()},
        )
        found.append(Candidate(finding, features, [jf.span(index if index is not None else access)]))
    return found


# ═══════════════════════════════ 4. MISSING_BREAK_IN_SWITCH ═══════════════════
# A case without break runs on into the next one. Harmless when the next case
# does the same thing or only breaks, intended when it says so or when the
# cases build on each other (a running total that falls through).

def propose_missing_break_in_switch(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for switch_block in jf.descendants(_root(parse_result), "switch_block"):
        groups = [child for child in switch_block.named_children if child.type == "switch_block_statement_group"]
        for position, group in enumerate(groups[:-1]):
            statements = [c for c in group.named_children if c.type not in ("switch_label",) and c.type not in jf.COMMENT_TYPES]
            if not statements or _ends_in_exit(statements[-1]):
                continue
            following = groups[position + 1]
            next_statements = [c for c in following.named_children if c.type != "switch_label" and c.type not in jf.COMMENT_TYPES]
            between = source[group.start_byte:following.start_byte].decode("utf-8", errors="replace")
            body = [s for s in next_statements if s.type != "break_statement"]
            mine = [" ".join(jf.text(s, source).split()) for s in statements]
            theirs = [" ".join(jf.text(s, source).split()) for s in body]
            written = jf.written_vars(group, source)
            label = next((c for c in group.named_children if c.type == "switch_label"), None)
            features = {
                "fallthrough_comment": jf.flag(bool(re.search(r"(?i)fall|falls|through|no break|continue", " ".join(c.group(0) for c in re.finditer(r"//[^\n]*|/\*.*?\*/", between, re.S))))),
                "next_identical": jf.flag(bool(mine) and mine == theirs),
                "next_only_breaks": jf.flag(not body),
                "next_is_default": jf.flag("default" in jf.text(following, source).split(":", 1)[0]),
                "next_writes_same_var": jf.flag(bool(written & jf.written_vars(following, source))),
                "next_prints": jf.flag("System.out" in " ".join(theirs)),
                "next_returns": jf.flag(any(s.type == "return_statement" for s in next_statements)),
                "cumulative": jf.flag(bool(written) and all(jf.is_compound_update(w, v, source) for v in written for w in jf.writes_of(group, v, source)) and bool(written & jf.written_vars(following, source))),
                "statement_count": float(len(statements)),
                "group_prints": jf.flag("System.out" in " ".join(mine)),
                "last_group_follows": jf.flag(position + 1 == len(groups) - 1),
                "in_loop": _in_loop(switch_block),
                # This case sets a variable and the next one plainly sets it
                # again: the value this case chose is lost on the way out.
                "overwritten_by_next": jf.flag(bool(_plain_writes(group, source) & _plain_writes(following, source))),
            }
            finding = _result(
                "MISSING_BREAK_IN_SWITCH", group, source, 0.8,
                "This case may fall through into the next case because it does not end with break.",
                details={"case": jf.text(label, source).strip() if label is not None else ""},
            )
            found.append(Candidate(finding, features, [(group.start_byte, following.start_byte)]))
    return found


def _ends_in_exit(statement) -> bool:
    """`break;` - or a `{ ... break; }` block around the case's code."""
    while statement is not None and statement.type == "block":
        inner = jf.statements(statement)
        statement = inner[-1] if inner else None
    return statement is not None and statement.type in _EXIT_TYPES


# Calls that only read: a condition variable they are called on does not change.
_READ_ONLY_CALLS = {"size", "length", "get", "charAt", "isEmpty", "contains", "containsKey", "equals", "equalsIgnoreCase",
                    "indexOf", "lastIndexOf", "substring", "toString", "startsWith", "endsWith", "hasNext", "hasNextInt",
                    "hasNextLine", "compareTo", "trim", "toUpperCase", "toLowerCase", "peek", "getOrDefault"}


def _plain_writes(node, source: bytes) -> set:
    """Variables given a new value outright (`x = ...`, not `x += ...`)."""
    names = set()
    for assignment in jf.descendants(node, "assignment_expression"):
        left = assignment.child_by_field_name("left")
        if jf.operator(assignment) == "=" and left is not None and left.type == "identifier":
            names.add(jf.text(left, source))
    return names


# ════════════════════════════ 5. WHILE_VARIABLE_NOT_UPDATED ═══════════════════
# A while loop whose condition never changes runs forever. One that changes it
# only on some passes, or reads something a call changes (hasNext, a field),
# or leaves through break, may be fine.

def propose_while_variable_not_updated(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "while_statement", "do_statement"):
        condition_node = loop.child_by_field_name("condition")
        body = loop.child_by_field_name("body")
        if condition_node is None or body is None:
            continue
        names = sorted({n for n in jf.identifiers(condition_node, source) if not re.fullmatch(r"[A-Z][A-Z0-9_]*", n)})
        call_names = {jf.text(c.child_by_field_name("name"), source) for c in jf.descendants(condition_node, "method_invocation")}
        names = [n for n in names if n not in call_names]
        if not names:
            continue
        # `queue.remove(0)`, `sc.next()`, `list.add(x)`: the condition's
        # variable changes through the call, which no assignment shows.
        if any(
            jf.text(call.child_by_field_name("object"), source).strip() in names
            and jf.text(call.child_by_field_name("name"), source) not in _READ_ONLY_CALLS
            for call in jf.descendants(body, "method_invocation") if call.child_by_field_name("object") is not None
        ):
            continue
        writes = [w for n in names for w in jf.writes_of(body, n, source)]
        top = jf.statements(body)
        unconditional = [w for w in writes if any(jf.is_inside(w, s) and s.type in ("expression_statement", "local_variable_declaration") for s in top)]
        in_branch = [w for w in writes if jf.enclosing(w, {"if_statement", "switch_block", "ternary_expression"}) is not None and jf.is_inside(jf.enclosing(w, {"if_statement", "switch_block", "ternary_expression"}), body)]
        in_nested = [w for w in writes if any(jf.is_inside(l, body) for l in jf.enclosing_loops(w))]
        index_vars = {n for _, _, ix in jf.indexed_accesses(condition_node, source) for n in jf.identifiers(ix, source)}
        features = {
            "cond_vars_written": jf.flag(bool(writes)),
            "written_unconditionally": jf.flag(bool(unconditional)),
            "written_only_in_branch": jf.flag(bool(writes) and len(in_branch) == len(writes)),
            "written_only_in_nested_loop": jf.flag(bool(writes) and len(in_nested) == len(writes)),
            "write_count": float(len(writes)),
            "cond_var_count": float(len(names)),
            "cond_vars_unwritten": float(sum(1 for n in names if not jf.writes_of(body, n, source))),
            "cond_has_call": jf.flag(bool(call_names)),
            "cond_has_index": jf.flag(bool(index_vars)),
            "index_var_written": jf.flag(any(jf.writes_of(body, n, source) for n in index_vars)),
            "cond_is_flag": jf.flag(jf.unwrap(condition_node) is not None and (jf.unwrap(condition_node).type == "identifier" or jf.text(condition_node, source).strip("() ").startswith("!"))),
            "body_has_break": jf.flag(bool([b for b in jf.descendants(body, "break_statement") if not any(jf.is_inside(l, body) for l in jf.enclosing_loops(b))])),
            "body_has_return": jf.flag(bool(jf.descendants(body, "return_statement", "throw_statement"))),
            "body_calls_methods": jf.flag(bool(jf.descendants(body, "method_invocation"))),
            "is_do_while": jf.flag(loop.type == "do_statement"),
        }
        finding = _result(
            "WHILE_VARIABLE_NOT_UPDATED", condition_node, source, 0.8,
            "No variable used in this while condition changes inside the loop, so the loop may never end.",
            context_node=loop,
            details={"condition": jf.text(jf.unwrap(condition_node), source).strip(), "variables": ", ".join(names)},
        )
        found.append(Candidate(finding, features, [jf.span(loop)]))
    return found


# ════════════════════════════ 6. STRING_EQUALITY_WITH_OPERATOR ════════════════
# `==` on Strings compares which object, not which text. The rule only knew
# plain String variables; this also reads method results, array elements and
# fields, and leaves null checks, chars and numbers to the model to dismiss.

def propose_string_equality_with_operator(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    types = Types(parse_result)
    found: List[Candidate] = []
    for node in jf.descendants(_root(parse_result), "binary_expression"):
        op = jf.operator(node)
        if op not in ("==", "!="):
            continue
        left, right = jf.unwrap(node.child_by_field_name("left")), jf.unwrap(node.child_by_field_name("right"))
        if left is None or right is None:
            continue
        kinds = (types.kind(left), types.kind(right))
        if "null" in kinds or not ({"string", "unknown", "object"} & set(kinds)):
            continue
        if set(kinds) & {"int", "char", "decimal", "boolean"}:
            primitive_other = True
        else:
            primitive_other = False
        features = {
            "both_string": jf.flag(kinds == ("string", "string")),
            "one_string": jf.flag("string" in kinds),
            "string_literal_side": jf.flag("string_literal" in (left.type, right.type)),
            "unknown_side": jf.flag("unknown" in kinds),
            "object_side": jf.flag("object" in kinds),
            "primitive_other_side": jf.flag(primitive_other),
            "constant_side": jf.flag("constant" in kinds),
            "call_side": jf.flag("method_invocation" in (left.type, right.type)),
            "element_side": jf.flag("array_access" in (left.type, right.type)),
            "operator_not_equal": jf.flag(op == "!="),
            "in_condition": jf.flag(jf.enclosing(node, {"if_statement", "while_statement", "for_statement", "ternary_expression"}) is not None),
            "same_text_both_sides": jf.flag(jf.text(left, source).strip() == jf.text(right, source).strip()),
        }
        finding = _result(
            "STRING_EQUALITY_WITH_OPERATOR", node, source, 0.8,
            "Possible string comparison using == or != instead of .equals().",
            details={"comparison": jf.text(node, source).strip()},
        )
        found.append(Candidate(finding, features, [jf.span(node)]))
    return found


# ═══════════════════════════ 7. LOOP_UPDATE_WRONG_DIRECTION ═══════════════════
# The counter moves away from the bound: `i < n; i--`. Every counted for loop
# is a candidate, so the model sees the countless right ones too.

def propose_loop_update_wrong_direction(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "for_statement"):
        var = jf.for_loop_var(loop, source)
        condition = _condition_of(loop)
        update_node = loop.child_by_field_name("update")
        if not var or condition is None or condition.type != "binary_expression" or update_node is None:
            continue
        op = jf.operator(condition)
        if op not in ("<", "<=", ">", ">="):
            continue
        left, right = jf.unwrap(condition.child_by_field_name("left")), jf.unwrap(condition.child_by_field_name("right"))
        if left is None or right is None:
            continue
        if jf.text(left, source).strip() == var:
            upward = op in ("<", "<=")
        elif jf.text(right, source).strip() == var:
            upward = op in (">", ">=")
        else:
            continue
        direction = jf.update_direction(update_node, var, source)
        if direction == 0:
            continue
        init_text = jf.for_init_value(loop, source).strip()
        bound = right if jf.text(left, source).strip() == var else left
        bound_text = jf.text(bound, source).strip()
        body = jf.loop_body(loop)
        features = {
            "direction_agrees": jf.flag((direction == 1) == upward),
            "update_up": jf.flag(direction == 1),
            "condition_upward": jf.flag(upward),
            "cond_inclusive": jf.flag(op in ("<=", ">=")),
            "init_literal": jf.flag(jf.literal_kind(init_text) == "int"),
            "bound_literal": jf.flag(jf.literal_kind(bound_text) == "int"),
            "init_below_bound": jf.flag(jf.literal_kind(init_text) == "int" and jf.literal_kind(bound_text) == "int" and int(init_text.rstrip("lL")) < int(bound_text.rstrip("lL"))),
            "init_is_length_minus": jf.flag(bool(jf.length_minus(_init_node(loop), source)[0])),
            "bound_is_zero": jf.flag(bound_text == "0"),
            "bound_is_length": jf.flag(bool(jf.length_minus(bound, source)[0])),
            "body_writes_var": jf.flag(bool(jf.writes_of(body, var, source))),
            "body_exits": jf.flag(bool(jf.descendants(body, "break_statement", "return_statement"))),
            "step_is_one": jf.flag(jf.text(update_node, source).replace(" ", "") in (f"{var}++", f"++{var}", f"{var}--", f"--{var}")),
        }
        finding = _result(
            "LOOP_UPDATE_WRONG_DIRECTION", condition, source, 0.8,
            "Loop update moves the counter away from the loop bound, so the loop may never finish.",
            context_node=loop,
            details={"condition": jf.text(condition, source).strip(), "update": jf.text(update_node, source).strip()},
        )
        found.append(Candidate(finding, features, [jf.span(update_node), jf.span(condition)]))
    return found


# ═══════════════════════════ 8. CONSTANT_FALSE_LOOP_CONDITION ═════════════════
# A loop whose condition is already false on entry never runs:
# `for (i = 10; i < 5; i++)`, or `for (i = 0; i > a.length; i++)` - false for
# every array, which the literal-only rule could not see.

def propose_constant_false_loop_condition(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for loop in jf.descendants(_root(parse_result), "for_statement"):
        var = jf.for_loop_var(loop, source)
        condition = _condition_of(loop)
        init_node = jf.unwrap(_init_node(loop))
        if not var or condition is None or condition.type != "binary_expression" or init_node is None:
            continue
        op = jf.operator(condition)
        left, right = jf.unwrap(condition.child_by_field_name("left")), jf.unwrap(condition.child_by_field_name("right"))
        if op not in ("<", "<=", ">", ">=", "==", "!=") or left is None or right is None or jf.text(left, source).strip() != var:
            continue
        init_text = jf.text(init_node, source).strip()
        bound_text = jf.text(right, source).strip()
        updates = jf.for_updates(loop)
        direction = jf.update_direction(updates[0], var, source) if updates else 0
        literal_check = None
        if jf.literal_kind(init_text) == "int" and jf.literal_kind(bound_text) == "int":
            a, b = int(init_text.rstrip("lL")), int(bound_text.rstrip("lL"))
            literal_check = {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b, "==": a == b, "!=": a != b}[op]
        bound_length = bool(jf.length_minus(right, source)[0]) and jf.length_minus(right, source)[1] <= 0
        init_small = init_text in ("0", "1")
        never_for_lengths = bound_length and init_small and op in (">", ">=", "==")
        same_text = init_text.replace(" ", "") == bound_text.replace(" ", "")
        # False on entry for every n that is not negative: counting up from
        # 0 or 1 while `i > n`, or starting from n while `i < 0`. (Counting
        # DOWN from 0 while `i < n` is true on entry - it runs forever, which
        # is the wrong-direction mistake, not this one.)
        points_away = direction == 1 and op in (">", ">=") and init_small
        below_zero = bound_text == "0" and op in ("<", "<=") and jf.literal_kind(init_text) != "int"
        # Two literals decide the first check outright - `10 >= 1` is true -
        # so a literal loop is a candidate only when that check fails. The
        # model judges what the text cannot settle: `i > values.length`, `i > n`.
        if literal_check is True:
            continue
        if literal_check is None and not (never_for_lengths or points_away or below_zero or (same_text and op in ("<", ">", "!="))):
            continue
        features = {
            "literal_decidable": jf.flag(literal_check is not None),
            "false_on_entry_literal": jf.flag(literal_check is False),
            "never_for_lengths": jf.flag(never_for_lengths),
            "init_equals_bound": jf.flag(same_text),
            "op_strict": jf.flag(op in ("<", ">")),
            "op_equality": jf.flag(op in ("==", "!=")),
            "update_up": jf.flag(direction == 1),
            "update_down": jf.flag(direction == -1),
            "direction_toward_bound": jf.flag((direction == 1 and op in ("<", "<=")) or (direction == -1 and op in (">", ">="))),
            "points_away": jf.flag(points_away),
            "bound_zero_counting_below": jf.flag(below_zero),
            "init_small": jf.flag(init_small),
            "bound_identifier": jf.flag(right.type == "identifier"),
            "body_statement_count": float(len(jf.statements(jf.loop_body(loop)))),
            "nested_in_loop": _in_loop(loop),
        }
        finding = _result(
            "CONSTANT_FALSE_LOOP_CONDITION", condition, source, 0.8,
            "The loop condition is already false at the first check, so the loop body never runs.",
            context_node=loop,
            details={"variable": var, "start": init_text, "condition": jf.text(condition, source).strip()},
        )
        found.append(Candidate(finding, features, [jf.span(condition), jf.span(loop.child_by_field_name("init") or condition)]))
    return found


# ═══════════════════════════ 9. IGNORED_STRING_METHOD_RESULT ═════════════════
# `name.trim();` changes nothing: Strings never change in place. The same
# call on a StringBuilder - `sb.reverse();` - is exactly right, and a rule
# going by the method name alone cannot tell them apart.

_STATEMENT_CALLS = _IMMUTABLE_STRING_METHODS | _BUILDER_METHODS | {"strip", "stripLeading", "stripTrailing", "toCharArray", "split", "intern"}


def propose_ignored_string_method_result(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    types = Types(parse_result)
    found: List[Candidate] = []
    for statement in jf.descendants(_root(parse_result), "expression_statement"):
        call = next((c for c in statement.named_children if c.type not in jf.COMMENT_TYPES), None)
        if call is None or call.type != "method_invocation":
            continue
        receiver = call.child_by_field_name("object")
        name = jf.text(call.child_by_field_name("name"), source)
        if receiver is None or name not in _STATEMENT_CALLS:
            continue
        kind = types.kind(receiver)
        method = jf.method_of(call)
        receiver_name = jf.text(receiver, source).strip()
        features = {
            "receiver_string": jf.flag(kind == "string"),
            "receiver_builder": jf.flag(kind == "builder"),
            "receiver_list": jf.flag(kind == "list"),
            "receiver_unknown": jf.flag(kind in ("unknown", "object")),
            "receiver_literal": jf.flag(receiver.type == "string_literal"),
            "receiver_chained_call": jf.flag(receiver.type == "method_invocation"),
            "method_transforms": jf.flag(name in _IMMUTABLE_STRING_METHODS),
            "method_builds": jf.flag(name in _BUILDER_METHODS),
            "receiver_read_after": jf.flag(receiver.type == "identifier" and jf.reads_after(method, call.end_byte, receiver_name, source) > 0),
            "receiver_is_parameter": jf.flag(method is not None and any(jf.text(p.child_by_field_name("name"), source) == receiver_name for p in jf.descendants(method, "formal_parameter"))),
            "in_loop": _in_loop(call),
        }
        finding = _result(
            "IGNORED_STRING_METHOD_RESULT", call, source, 0.8,
            "This String method returns a new value that is thrown away; strings are never changed in place.",
            details={"call": jf.text(call, source).strip(), "target": receiver_name},
        )
        found.append(Candidate(finding, features, [jf.span(statement)]))
    return found


# ═════════════════════════════ 10. DIVISION_BY_ZERO_LITERAL ═══════════════════
# `x / 0` always crashes. So does `total / count` when nothing was counted, or
# `sum / values.length` on an empty array - and a guard before it, or a count
# that is always at least one, makes the same line safe.

def propose_division_by_zero(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    types = Types(parse_result)
    found: List[Candidate] = []
    for node in jf.descendants(_root(parse_result), "binary_expression", "assignment_expression"):
        op = jf.operator(node)
        if op not in ("/", "%", "/=", "%="):
            continue
        divisor = jf.unwrap(node.child_by_field_name("right"))
        if divisor is None:
            continue
        divisor_text = jf.text(divisor, source).strip()
        literal = jf.literal_kind(divisor_text)
        zero_literal = literal in ("int", "decimal") and float(divisor_text.rstrip("lLdDfF") or 1) == 0.0
        if literal in ("int", "decimal") and not zero_literal:
            continue
        dividend = node.child_by_field_name("left")
        # A double divided by zero is Infinity or NaN, not a crash; this type
        # is the ArithmeticException.
        if not zero_literal and "decimal" in (types.kind(dividend), types.kind(divisor)):
            continue
        method = jf.method_of(node)
        length_of, length_k = jf.length_minus(divisor, source)
        names = [divisor_text] if divisor.type == "identifier" else ([f"{length_of}.length", f"{length_of}.size()", f"{length_of}.length()", length_of] if length_of else [])
        guards = _guard_texts(node, method, source)
        declared = _decl_value(method, divisor_text, node.start_byte, source) if divisor.type == "identifier" else None
        declared_zero = declared is not None and jf.text(declared, source).strip() in ("0", "0.0")
        written = jf.writes_of(method, divisor_text, source) if divisor.type == "identifier" else []
        written_before = [w for w in written if w.start_byte < node.start_byte]
        is_parameter = divisor.type == "identifier" and method is not None and any(
            jf.text(p.child_by_field_name("name"), source) == divisor_text for p in jf.descendants(method, "formal_parameter"))
        alias_of_length = declared is not None and jf.length_minus(declared, source)[0] is not None and jf.length_minus(declared, source)[1] == 0
        # Only divisors that can be zero in the ways beginners meet: an empty
        # array or list, a count that starts at 0 and stays there when nothing
        # matches, a value the caller chooses. `top / d` with d = gcd(...), or
        # a loop counter that starts at 2, is not one of them - and proposing
        # every divisor made the model guess about all of them.
        if not zero_literal and not (length_of and length_k == 0) and not (
            divisor.type == "identifier" and (is_parameter or declared_zero or alias_of_length)
        ):
            continue
        features = {
            "divisor_zero_literal": jf.flag(zero_literal),
            "divisor_identifier": jf.flag(divisor.type == "identifier"),
            "divisor_is_length": jf.flag(bool(length_of) and length_k == 0),
            "divisor_is_parameter": jf.flag(divisor.type == "identifier" and method is not None and any(jf.text(p.child_by_field_name("name"), source) == divisor_text for p in jf.descendants(method, "formal_parameter"))),
            "divisor_declared_zero": jf.flag(declared_zero),
            "divisor_declared_nonzero_literal": jf.flag(declared is not None and jf.literal_kind(jf.text(declared, source)) in ("int", "decimal") and not declared_zero),
            "divisor_written_before": jf.flag(bool(written_before)),
            "divisor_incremented_in_loop": jf.flag(any(jf.enclosing_loops(w) and jf.is_compound_update(w, divisor_text, source) for w in written_before)),
            "guarded_nonzero": jf.flag(_mentions_nonzero(guards, names)),
            "any_guard": jf.flag(bool(guards)),
            "decimal_division": jf.flag("decimal" in (types.kind(dividend), types.kind(divisor))),
            "is_modulo": jf.flag(op in ("%", "%=")),
            "in_loop": _in_loop(node),
            "divisor_is_expression": jf.flag(divisor.type in ("binary_expression", "method_invocation") and not length_of),
        }
        message = ("Dividing by the literal 0 will crash the program with an ArithmeticException." if zero_literal else
                   f"`{divisor_text}` can be zero when this line runs, and dividing a whole number by zero crashes the program.")
        details = {"expression": jf.text(node, source).strip()}
        if not zero_literal:
            details["divisor"] = divisor_text
        finding = _result("DIVISION_BY_ZERO_LITERAL", node, source, 0.8, message, details=details)
        found.append(Candidate(finding, features, [jf.span(node)]))
    return found


# ═════════════════════ 11. INTEGER_DIVISION_IN_DECIMAL_CONTEXT ════════════════
# Two whole numbers divided drop the remainder - wanted for a midpoint or a
# digit, a bug for an average stored in a double. Every int / int division is
# a candidate; where its value goes decides it.

def propose_integer_division_in_decimal_context(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    types = Types(parse_result)
    found: List[Candidate] = []
    for node in jf.descendants(_root(parse_result), "binary_expression"):
        if jf.operator(node) != "/":
            continue
        left, right = node.child_by_field_name("left"), node.child_by_field_name("right")
        if types.kind(left) not in ("int", "char") or types.kind(right) not in ("int", "char"):
            continue
        divisor_text = jf.text(jf.unwrap(right), source).strip()
        if divisor_text == "0":
            continue
        method = jf.method_of(node)
        target_name, target_kind = _value_destination(node, method, types, source)
        parent = node.parent
        while parent is not None and parent.type == "parenthesized_expression":
            parent = parent.parent
        call = jf.enclosing(node, {"method_invocation"})
        call_text = jf.text(call.child_by_field_name("object"), source) + "." + jf.text(call.child_by_field_name("name"), source) if call is not None and call.child_by_field_name("object") is not None else ""
        features = {
            "stored_in_decimal": jf.flag(target_kind == "decimal"),
            "stored_in_int": jf.flag(target_kind in ("int", "char")),
            "returned_from_decimal_method": jf.flag(target_kind == "decimal_return"),
            "cast_after_division": jf.flag(parent is not None and parent.type == "cast_expression" and _kind_of_type(jf.text(parent.child_by_field_name("type"), source)) == "decimal"),
            "combined_with_decimal": jf.flag(parent is not None and parent.type == "binary_expression" and "decimal" in (types.kind(parent.child_by_field_name("left")), types.kind(parent.child_by_field_name("right")))),
            "in_rounding_call": jf.flag(call_text in ("Math.ceil", "Math.floor", "Math.round", "Math.sqrt", "Math.pow")),
            "in_print": jf.flag("System.out" in call_text or (call is not None and jf.text(call.child_by_field_name("name"), source) in ("println", "print", "printf", "format"))),
            "used_as_index": jf.flag(jf.enclosing(node, {"array_access"}) is not None and jf.is_inside(node, jf.enclosing(node, {"array_access"}).child_by_field_name("index"))),
            "divisor_is_two": jf.flag(divisor_text == "2"),
            "divisor_is_ten_power": jf.flag(divisor_text in ("10", "100", "1000")),
            "modulo_nearby": jf.flag(_modulo_near(node, source)),
            "name_suggests_fraction": jf.has_token(target_name or "", _AVERAGE_WORDS),
            "divisor_is_length": jf.flag(bool(jf.length_minus(right, source)[0])),
            "dividend_is_sum": jf.flag(jf.unwrap(left) is not None and jf.unwrap(left).type == "binary_expression" and jf.operator(jf.unwrap(left)) == "+"),
        }
        finding = _result(
            "INTEGER_DIVISION_IN_DECIMAL_CONTEXT", node, source, 0.8,
            "Both sides of this division are whole numbers, so the remainder is dropped before the result is used as a decimal.",
            details={"expression": jf.text(node, source).strip(), "target": target_name if target_kind in ("decimal", "decimal_return") else ""},
        )
        found.append(Candidate(finding, features, [jf.span(node)]))
    return found


def _value_destination(node, method, types: Types, source: bytes):
    """Where this value ends up: (name, kind) - a variable it is stored in,
    or ("<method>", "decimal_return") when a double method returns it."""
    current = node.parent
    while current is not None:
        if current.type == "variable_declarator":
            declaration = current.parent
            type_text = jf.text(declaration.child_by_field_name("type"), source) if declaration is not None else ""
            return jf.text(current.child_by_field_name("name"), source), _kind_of_type(type_text)
        if current.type == "assignment_expression":
            left = current.child_by_field_name("left")
            return jf.text(left, source), types.kind(left)
        if current.type == "return_statement":
            kind = _kind_of_type(jf.method_return_type(method, source))
            return jf.text(method.child_by_field_name("name"), source) if method is not None else "", "decimal_return" if kind == "decimal" else kind
        if current.type in ("expression_statement", "block", "if_statement", "while_statement", "for_statement", "argument_list", "array_access"):
            return None, "unknown"
        current = current.parent
    return None, "unknown"


def _modulo_near(node, source: bytes) -> bool:
    left = jf.text(node.child_by_field_name("left"), source).strip()
    right = jf.text(node.child_by_field_name("right"), source).strip()
    scope = jf.enclosing(node, {"block"})
    return scope is not None and re.search(rf"{re.escape(left)}\s*%\s*{re.escape(right)}", jf.text(scope, source)) is not None


# ═════════════════════════════ 12. DECIMAL_EQUALITY_COMPARISON ════════════════
# `total == 0.3` fails by a rounding error. `value == 0.0` before dividing, or
# `x == Math.floor(x)` to ask "is it whole", are deliberate exact checks.

def propose_decimal_equality_comparison(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    types = Types(parse_result)
    found: List[Candidate] = []
    for node in jf.descendants(_root(parse_result), "binary_expression"):
        op = jf.operator(node)
        if op not in ("==", "!="):
            continue
        left, right = jf.unwrap(node.child_by_field_name("left")), jf.unwrap(node.child_by_field_name("right"))
        if left is None or right is None:
            continue
        kinds = (types.kind(left), types.kind(right))
        if "decimal" not in kinds:
            continue
        texts = (jf.text(left, source).strip(), jf.text(right, source).strip())
        literals = [t for t in texts if jf.literal_kind(t) in ("int", "decimal")]
        values = []
        for t in literals:
            try:
                values.append(float(t.rstrip("dDfFlL")))
            except ValueError:
                pass
        names = " ".join(texts)
        features = {
            "zero_literal": jf.flag(any(v == 0.0 for v in values)),
            "fractional_literal": jf.flag(any(v != int(v) for v in values)),
            "whole_literal": jf.flag(any(v == int(v) and v != 0.0 for v in values)),
            "negative_sentinel": jf.flag(any(v < 0 for v in values) or any(t.startswith("-") for t in texts)),
            "both_computed": jf.flag(not literals),
            "arithmetic_side": jf.flag(any(n.type == "binary_expression" for n in (left, right))),
            "rounding_side": jf.flag(bool(re.search(r"Math\.(floor|ceil|round|rint)|\(int\)|\(long\)", names))),
            "operator_not_equal": jf.flag(op == "!="),
            "money_name": jf.has_token(names, _MONEY_WORDS),
            "both_decimal": jf.flag(kinds == ("decimal", "decimal")),
            "in_condition": jf.flag(jf.enclosing(node, {"if_statement", "while_statement", "for_statement", "ternary_expression"}) is not None),
            "in_loop": _in_loop(node),
        }
        finding = _result(
            "DECIMAL_EQUALITY_COMPARISON", node, source, 0.8,
            "Decimal values are compared for an exact match, which calculated doubles often fail by a tiny amount.",
            details={"comparison": jf.text(node, source).strip()},
        )
        found.append(Candidate(finding, features, [jf.span(node)]))
    return found


# ═════════════════════════════ 13. EMPTY_CONDITIONAL_BODY ═════════════════════
# `if (x > 0);` controls nothing - the block after it always runs. A search
# loop whose header does all the work, `for (i = 0; i < n && a[i] != key; i++);`,
# has an empty body on purpose.

def propose_empty_conditional_body(parse_result: ParseResult) -> List[Candidate]:
    source = parse_result.source_bytes
    found: List[Candidate] = []
    for statement in jf.descendants(_root(parse_result), "if_statement", "while_statement", "for_statement"):
        body = statement.child_by_field_name("consequence" if statement.type == "if_statement" else "body")
        if body is None:
            continue
        empty_block = body.type == "block" and not [c for c in body.named_children]
        if body.type != ";" and not empty_block:
            continue
        condition = statement.child_by_field_name("condition")
        following = statement.next_named_sibling
        while following is not None and following.type in jf.COMMENT_TYPES:
            following = following.next_named_sibling
        header_row = statement.start_point[0]
        next_deeper = following is not None and jf.line_indent(source, following.start_point[0]) > jf.line_indent(source, header_row)
        condition_text = jf.text(condition, source)
        features = {
            "kind_if": jf.flag(statement.type == "if_statement"),
            "kind_while": jf.flag(statement.type == "while_statement"),
            "kind_for": jf.flag(statement.type == "for_statement"),
            "empty_block": jf.flag(empty_block),
            "semicolon_same_line": jf.flag(body.type == ";" and body.start_point[0] == (condition.end_point[0] if condition is not None else header_row)),
            "next_is_block": jf.flag(following is not None and following.type == "block"),
            "next_indented_deeper": jf.flag(next_deeper),
            "condition_has_side_effect": jf.flag(bool(jf.descendants(condition, "update_expression", "assignment_expression"))),
            "for_has_update": jf.flag(statement.type == "for_statement" and bool(jf.for_updates(statement))),
            "condition_has_call": jf.flag(bool(jf.descendants(condition, "method_invocation"))),
            "condition_has_logical_and": jf.flag("&&" in condition_text),
            "has_else": jf.flag(statement.type == "if_statement" and statement.child_by_field_name("alternative") is not None),
        }
        finding = _result(
            "EMPTY_CONDITIONAL_BODY", statement, source, 0.8,
            "A semicolon right after the condition makes the body empty, so the condition controls nothing.",
            details={"statement": " ".join(jf.text(statement, source).splitlines()[0].split()) if jf.text(statement, source) else ""},
        )
        found.append(Candidate(finding, features, [jf.span(statement)]))
    return found


PROMOTED_PROPOSERS: Dict[str, ProposerFn] = {
    "OFF_BY_ONE_LOOP_BOUNDARY": propose_off_by_one_loop_boundary,
    "INCORRECT_CONDITIONAL_OPERATOR": propose_incorrect_conditional_operator,
    "ARRAY_LENGTH_INDEX_MISUSE": propose_array_length_index_misuse,
    "MISSING_BREAK_IN_SWITCH": propose_missing_break_in_switch,
    "WHILE_VARIABLE_NOT_UPDATED": propose_while_variable_not_updated,
    "STRING_EQUALITY_WITH_OPERATOR": propose_string_equality_with_operator,
    "LOOP_UPDATE_WRONG_DIRECTION": propose_loop_update_wrong_direction,
    "CONSTANT_FALSE_LOOP_CONDITION": propose_constant_false_loop_condition,
    "IGNORED_STRING_METHOD_RESULT": propose_ignored_string_method_result,
    "DIVISION_BY_ZERO_LITERAL": propose_division_by_zero,
    "INTEGER_DIVISION_IN_DECIMAL_CONTEXT": propose_integer_division_in_decimal_context,
    "DECIMAL_EQUALITY_COMPARISON": propose_decimal_equality_comparison,
    "EMPTY_CONDITIONAL_BODY": propose_empty_conditional_body,
}
