from typing import List

from app.models import DetectionCandidate
from app.parser_utils import collect_nodes_by_type, get_node_text, node_to_span


def detect_off_by_one_loop_boundary(tree, source_bytes: bytes) -> List[DetectionCandidate]:
    findings: List[DetectionCandidate] = []
    root = tree.root_node

    for_nodes = collect_nodes_by_type(root, "for_statement")

    for for_node in for_nodes:
        condition_node = for_node.child_by_field_name("condition")

        if condition_node is None:
            continue

        condition_text = get_node_text(condition_node, source_bytes).strip()

        if "<=" in condition_text and ".length" in condition_text:
            context_lines = get_node_text(for_node, source_bytes).splitlines()
            code_context = (
                context_lines[0].strip()
                if context_lines
                else get_node_text(for_node, source_bytes).strip()
            )

            findings.append(
                DetectionCandidate(
                    error_type="OFF_BY_ONE_LOOP_BOUNDARY",
                    line=condition_node.start_point[0] + 1,
                    column=condition_node.start_point[1] + 1,
                    base_confidence=0.95,
                    message="Possible off-by-one loop boundary issue detected.",
                    code_context=code_context,
                    source_span=node_to_span(condition_node),
                    requires_stable_region=True,
                )
            )

    return findings