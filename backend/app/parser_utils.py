from tree_sitter import Language, Parser
import tree_sitter_java as tsjava

from app.models import ParseHealth, ParseResult, Span

JAVA_LANGUAGE = Language(tsjava.language())
JAVA_PARSER = Parser(JAVA_LANGUAGE)


def parse_java_code(code: str):
    source_bytes = code.encode("utf8")
    tree = JAVA_PARSER.parse(source_bytes)
    return tree, source_bytes


def get_node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf8")


def collect_nodes_by_type(root_node, target_type: str):
    results = []

    def visit(node):
        if node.type == target_type:
            results.append(node)

        for child in node.children:
            visit(child)

    visit(root_node)
    return results


def find_first_descendant_by_type(node, target_type: str):
    if node.type == target_type:
        return node

    for child in node.children:
        result = find_first_descendant_by_type(child, target_type)
        if result is not None:
            return result

    return None


def node_to_span(node) -> Span:
    return Span(
        start_line=node.start_point[0] + 1,
        start_col=node.start_point[1] + 1,
        end_line=node.end_point[0] + 1,
        end_col=node.end_point[1] + 1,
    )


def inspect_tree_health(root_node) -> ParseHealth:
    error_count = 0
    missing_count = 0
    unstable_spans: list[Span] = []

    stack = [root_node]
    while stack:
        node = stack.pop()

        is_error = getattr(node, "is_error", False) or node.type == "ERROR"
        is_missing = getattr(node, "is_missing", False)

        if is_error:
            error_count += 1
            unstable_spans.append(node_to_span(node))

        if is_missing:
            missing_count += 1
            unstable_spans.append(node_to_span(node))

        stack.extend(reversed(node.children))

    penalty = min(0.8, (error_count * 0.15) + (missing_count * 0.10))
    completeness_score = max(0.0, 1.0 - penalty)

    return ParseHealth(
        has_error_nodes=(error_count + missing_count) > 0,
        error_node_count=error_count,
        missing_node_count=missing_count,
        unstable_spans=unstable_spans,
        completeness_score=completeness_score,
    )


def parse_java_code_safe(code: str) -> ParseResult:
    source_bytes = code.encode("utf-8")

    try:
        tree = JAVA_PARSER.parse(source_bytes)
        health = inspect_tree_health(tree.root_node)

        return ParseResult(
            tree=tree,
            source_bytes=source_bytes,
            health=health,
            crashed=False,
        )
    except Exception:
        return ParseResult(
            tree=None,
            source_bytes=source_bytes,
            health=ParseHealth(
                has_error_nodes=True,
                completeness_score=0.0,
            ),
            crashed=True,
        )