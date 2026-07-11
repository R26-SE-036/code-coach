"""Foundation layer: turn raw Java text into a Tree-sitter syntax tree.

Pipeline position: this is the bottom of the analysis stack. Nothing here
knows about ML, error types, or hints — it only knows how to parse Java and
walk the resulting tree.

Who calls into this file:
- analyzer.analyze_code()           -> parse_java_code_safe()  (step 1: parse)
- feature_extractor.extract_features() -> parse_java_code_safe() (parses again
                                          to count AST features)
- every locator in issue_locators.py -> collect_nodes_by_type / get_node_text /
                                        find_first_descendant_by_type

What it produces: a ParseResult (defined in app/models.py) holding the tree,
the original bytes, and a ParseHealth score. Callers key everything off that
one object, so this file is the single door between "text" and "tree".
"""

from tree_sitter import Language, Parser
import tree_sitter_java as tsjava

from app.models import ParseHealth, ParseResult, Span

JAVA_LANGUAGE = Language(tsjava.language())
JAVA_PARSER = Parser(JAVA_LANGUAGE)


def parse_java_code(code: str):
    source_bytes = code.encode("utf8")
    tree = JAVA_PARSER.parse(source_bytes)
    return tree, source_bytes


# Tree-sitter stores the tree separately from the text: a node only knows its
# byte offsets, not the characters. This slices the original bytes back out so
# a locator can read the actual source of a node (e.g. the text "i <= a.length").
# Used constantly by issue_locators.py and feature_extractor.py.
def get_node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf8")


# Walk the whole tree top-to-bottom and return EVERY node of one kind
# (e.g. all "for_statement" nodes, all "array_access" nodes). This is the
# workhorse the feature extractor and locators use to find the constructs
# they care about.
def collect_nodes_by_type(root_node, target_type: str):
    results = []

    def visit(node):
        if node.type == target_type:
            results.append(node)

        for child in node.children:
            visit(child)

    visit(root_node)
    return results


# Like collect_nodes_by_type but stops at the FIRST match (depth-first).
# Used when a locator only needs to know "is there an assignment anywhere
# inside this condition?" rather than a full list.
def find_first_descendant_by_type(node, target_type: str):
    if node.type == target_type:
        return node

    for child in node.children:
        result = find_first_descendant_by_type(child, target_type)
        if result is not None:
            return result

    return None


# Convert Tree-sitter's 0-based (row, col) points into a 1-based Span
# (editor line/column numbers start at 1). Locators use the same +1 idea
# when they report a finding's line/column back to VS Code.
def node_to_span(node) -> Span:
    return Span(
        start_line=node.start_point[0] + 1,
        start_col=node.start_point[1] + 1,
        end_line=node.end_point[0] + 1,
        end_col=node.end_point[1] + 1,
    )


# Half-typed code still parses, but with "ERROR"/"missing" nodes scattered in.
# This scores how complete/trustworthy the tree is (completeness_score 0..1).
# That score is used twice downstream:
#   - analyzer bails out entirely if it is below MIN_FILE_COMPLETENESS,
#   - analyzer also multiplies each finding's confidence by it, so diagnostics
#     from messy half-typed files come back less confident.
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

# THE public entry point of this file. Parses Java and returns a ParseResult:
#   - tree:         the parse tree (None if parsing threw)
#   - source_bytes: the source as bytes (needed by get_node_text)
#   - health:       ParseHealth from inspect_tree_health() above
#   - crashed:      True only if the parser itself raised
#
# analyzer.analyze_code() calls this first and immediately bails out if the
# result is crashed or completeness_score is too low — that guard is why the
# rest of the pipeline can assume it is working with a usable tree.
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
