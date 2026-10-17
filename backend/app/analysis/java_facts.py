"""Small facts about Java code, read off the tree, shared by the candidate
proposers in logic_candidates.py.

Each helper answers one plain question - which variable does this for loop
count with, is this expression a length, which variables does this block
write, how deep is this line indented - so the proposers can describe a site
in a few lines each. Nothing here decides whether code is wrong.
"""

from __future__ import annotations

import re
from typing import Iterable, Iterator, List, Optional, Sequence, Set, Tuple

LOOP_TYPES = {"for_statement", "enhanced_for_statement", "while_statement", "do_statement"}
COMMENT_TYPES = {"line_comment", "block_comment"}


def text(node, source: bytes) -> str:
    if node is None:
        return ""
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def walk(node) -> Iterator:
    """Every node under `node`, including itself, in source order."""
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def descendants(node, *types: str) -> List:
    wanted = set(types)
    return [n for n in walk(node) if n.type in wanted] if node is not None else []


def ancestors(node) -> Iterator:
    current = node.parent
    while current is not None:
        yield current
        current = current.parent


def enclosing(node, types: Set[str]):
    for parent in ancestors(node):
        if parent.type in types:
            return parent
    return None


def enclosing_loops(node) -> List:
    """Loops around `node`, innermost first."""
    return [parent for parent in ancestors(node) if parent.type in LOOP_TYPES]


def method_of(node):
    return enclosing(node, {"method_declaration", "constructor_declaration"})


def unwrap(node):
    while node is not None and node.type == "parenthesized_expression":
        inner = [child for child in node.named_children if child.type not in COMMENT_TYPES]
        if not inner:
            break
        node = inner[0]
    return node


def statements(node) -> List:
    """The statements a body holds: a block's children, or the one statement."""
    if node is None:
        return []
    if node.type == "block":
        return [child for child in node.named_children if child.type not in COMMENT_TYPES]
    return [node]


def operator(node) -> str:
    op = node.child_by_field_name("operator")
    if op is not None:
        return op.type
    return node.children[1].type if len(node.children) >= 3 else ""


def is_inside(node, container) -> bool:
    return container is not None and container.start_byte <= node.start_byte and node.end_byte <= container.end_byte


def span(node) -> Tuple[int, int]:
    return (node.start_byte, node.end_byte)


# ── loops ──

def for_loop_var(for_node, source: bytes) -> Optional[str]:
    """The counter a for loop declares or assigns in its init part."""
    init = for_node.child_by_field_name("init")
    if init is None:
        return None
    if init.type == "local_variable_declaration":
        declarator = init.child_by_field_name("declarator")
        name = declarator.child_by_field_name("name") if declarator is not None else None
        return text(name, source) if name is not None else None
    if init.type == "assignment_expression":
        left = init.child_by_field_name("left")
        if left is not None and left.type == "identifier":
            return text(left, source)
    return None


def for_declared_vars(for_node, source: bytes) -> List[str]:
    init = for_node.child_by_field_name("init")
    if init is None or init.type != "local_variable_declaration":
        return []
    names = []
    for declarator in init.named_children:
        if declarator.type == "variable_declarator":
            name = declarator.child_by_field_name("name")
            if name is not None:
                names.append(text(name, source))
    return names


def for_init_value(for_node, source: bytes) -> str:
    init = for_node.child_by_field_name("init")
    if init is None:
        return ""
    if init.type == "local_variable_declaration":
        declarator = init.child_by_field_name("declarator")
        value = declarator.child_by_field_name("value") if declarator is not None else None
        return text(value, source).strip()
    if init.type == "assignment_expression":
        return text(init.child_by_field_name("right"), source).strip()
    return ""


def for_updates(for_node) -> List:
    return list(for_node.children_by_field_name("update"))


def loop_body(loop_node):
    return loop_node.child_by_field_name("body")


def loop_var_of(loop_node, source: bytes) -> Optional[str]:
    if loop_node.type == "for_statement":
        return for_loop_var(loop_node, source)
    if loop_node.type == "enhanced_for_statement":
        name = loop_node.child_by_field_name("name")
        return text(name, source) if name is not None else None
    return None


def update_direction(update_node, var: str, source: bytes) -> int:
    """+1 for i++ / i += k, -1 for i-- / i -= k, 0 when unclear."""
    body = text(update_node, source).replace(" ", "")
    if body in (f"{var}++", f"++{var}") or body.startswith(f"{var}+="):
        return 1
    if body in (f"{var}--", f"--{var}") or body.startswith(f"{var}-="):
        return -1
    match = re.fullmatch(rf"{re.escape(var)}={re.escape(var)}([+-])\d+", body)
    if match:
        return 1 if match.group(1) == "+" else -1
    return 0


# ── what a piece of code reads and writes ──

def identifiers(node, source: bytes) -> List[str]:
    return [text(n, source) for n in descendants(node, "identifier")]


def written_vars(node, source: bytes) -> Set[str]:
    names: Set[str] = set()
    for assignment in descendants(node, "assignment_expression"):
        left = assignment.child_by_field_name("left")
        if left is not None and left.type == "identifier":
            names.add(text(left, source))
    for update in descendants(node, "update_expression"):
        for identifier in update.named_children:
            if identifier.type == "identifier":
                names.add(text(identifier, source))
    return names


def writes_of(node, var: str, source: bytes) -> List:
    """Assignments and ++/-- to `var` under `node`."""
    found = []
    for assignment in descendants(node, "assignment_expression"):
        left = assignment.child_by_field_name("left")
        if left is not None and left.type == "identifier" and text(left, source) == var:
            found.append(assignment)
    for update in descendants(node, "update_expression"):
        if any(child.type == "identifier" and text(child, source) == var for child in update.named_children):
            found.append(update)
    return found


def uses(node, var: str, source: bytes) -> int:
    return sum(1 for name in identifiers(node, source) if name == var)


def is_compound_update(write, var: str, source: bytes) -> bool:
    """`x += ...`, `x++`, or `x = x op ...`: a write that builds on the old value."""
    if write.type == "update_expression":
        return True
    op = operator(write)
    if op in ("+=", "-=", "*=", "/=", "%=", "|=", "&="):
        return True
    right = write.child_by_field_name("right")
    return op == "=" and right is not None and var in identifiers(right, source)


def reads_after(method, position: int, var: str, source: bytes) -> int:
    """How often `var` is read in `method` after byte `position`."""
    if method is None:
        return 0
    count = 0
    for identifier in descendants(method, "identifier"):
        if identifier.start_byte >= position and text(identifier, source) == var:
            parent = identifier.parent
            if parent is not None and parent.type == "assignment_expression" and parent.child_by_field_name("left") == identifier:
                continue
            count += 1
    return count


def declared_before(method, var: str, position: int, source: bytes) -> bool:
    if method is None:
        return False
    for declarator in descendants(method, "variable_declarator"):
        name = declarator.child_by_field_name("name")
        if name is not None and text(name, source) == var and declarator.start_byte < position:
            return True
    for parameter in descendants(method, "formal_parameter"):
        name = parameter.child_by_field_name("name")
        if name is not None and text(name, source) == var:
            return True
    return False


def declared_type(method, var: str, source: bytes) -> str:
    if method is None:
        return ""
    for declaration in descendants(method, "local_variable_declaration", "formal_parameter"):
        type_node = declaration.child_by_field_name("type")
        if declaration.type == "formal_parameter":
            name = declaration.child_by_field_name("name")
            if name is not None and text(name, source) == var:
                return text(type_node, source)
            continue
        for declarator in declaration.named_children:
            if declarator.type == "variable_declarator":
                name = declarator.child_by_field_name("name")
                if name is not None and text(name, source) == var:
                    return text(type_node, source)
    return ""


def method_return_type(method, source: bytes) -> str:
    if method is None:
        return ""
    type_node = method.child_by_field_name("type")
    return text(type_node, source) if type_node is not None else ""


# ── lengths and indexes ──

def length_target(node, source: bytes) -> Optional[str]:
    """`a.length`, `s.length()`, `list.size()` -> the name; anything else None."""
    node = unwrap(node)
    if node is None:
        return None
    if node.type == "field_access":
        field = node.child_by_field_name("field")
        obj = node.child_by_field_name("object")
        if field is not None and text(field, source) == "length" and obj is not None:
            return text(obj, source)
    if node.type == "method_invocation":
        name = node.child_by_field_name("name")
        obj = node.child_by_field_name("object")
        args = node.child_by_field_name("arguments")
        if name is not None and obj is not None and text(name, source) in ("length", "size") and args is not None and not args.named_children:
            return text(obj, source)
    return None


def length_minus(node, source: bytes) -> Tuple[Optional[str], int]:
    """`a.length - k` -> ("a", k); `a.length` -> ("a", 0); else (None, 0)."""
    node = unwrap(node)
    target = length_target(node, source)
    if target is not None:
        return target, 0
    if node is not None and node.type == "binary_expression" and operator(node) in ("-", "+"):
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")
        target = length_target(left, source)
        literal = text(right, source).strip()
        if target is not None and literal.isdigit():
            k = int(literal)
            return target, k if operator(node) == "-" else -k
    return None, 0


def index_offset(index_node, var: str, source: bytes) -> Optional[int]:
    """`i` -> 0, `i + 1` -> 1, `i - 1` -> -1, anything else None."""
    index_node = unwrap(index_node)
    if index_node is None:
        return None
    if index_node.type == "identifier":
        return 0 if text(index_node, source) == var else None
    if index_node.type == "binary_expression" and operator(index_node) in ("+", "-"):
        left = unwrap(index_node.child_by_field_name("left"))
        right = unwrap(index_node.child_by_field_name("right"))
        if left is not None and left.type == "identifier" and text(left, source) == var and text(right, source).strip().isdigit():
            k = int(text(right, source))
            return k if operator(index_node) == "+" else -k
        if operator(index_node) == "+" and right is not None and right.type == "identifier" and text(right, source) == var and text(left, source).strip().isdigit():
            return int(text(left, source))
    return None


def indexed_accesses(node, source: bytes) -> List[Tuple[object, str, object]]:
    """(access node, collection name, index node) for a[i], s.charAt(i), list.get(i)."""
    found = []
    for access in descendants(node, "array_access"):
        array = access.child_by_field_name("array")
        index = access.child_by_field_name("index")
        if array is not None and index is not None:
            found.append((access, text(array, source), index))
    for call in descendants(node, "method_invocation"):
        name = call.child_by_field_name("name")
        obj = call.child_by_field_name("object")
        args = call.child_by_field_name("arguments")
        if name is None or obj is None or args is None:
            continue
        if text(name, source) in ("charAt", "get") and len(args.named_children) == 1:
            found.append((call, text(obj, source), args.named_children[0]))
    return found


# ── layout ──

def line_indent(source: bytes, row: int) -> int:
    lines = source.decode("utf-8", errors="replace").splitlines()
    if row >= len(lines):
        return 0
    line = lines[row].replace("\t", "    ")
    return len(line) - len(line.lstrip(" "))


# ── names ──

_CAMEL = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")


def name_tokens(name: str) -> Set[str]:
    return {token.lower() for token in _CAMEL.findall(name or "")}


def has_token(name: str, words: Sequence[str]) -> float:
    tokens = name_tokens(name)
    return 1.0 if any(word in tokens for word in words) else 0.0


def literal_kind(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"-?\d+[lL]?", value):
        return "int"
    if re.fullmatch(r"-?\d*\.\d+[dDfF]?|-?\d+\.\d*[dDfF]?", value):
        return "decimal"
    if value in ("true", "false"):
        return "boolean"
    if value.startswith('"'):
        return "string"
    if value.startswith("'"):
        return "char"
    return "other"


def flag(condition: bool) -> float:
    return 1.0 if condition else 0.0


def any_flag(values: Iterable[bool]) -> float:
    return 1.0 if any(values) else 0.0
