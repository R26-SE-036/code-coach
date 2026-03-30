from typing import List

from app.models import DetectionCandidate
from app.parser_utils import (
    collect_nodes_by_type,
    find_first_descendant_by_type,
    get_node_text,
    node_to_span,
)


def detect_incorrect_conditional_operator(tree, source_bytes: bytes) -> List[DetectionCandidate]:
    findings: List[DetectionCandidate] = []
    root = tree.root_node

    if_nodes = collect_nodes_by_type(root, "if_statement")

    for if_node in if_nodes:
        condition_node = if_node.child_by_field_name("condition")

        if condition_node is None:
            continue

        assignment_node = find_first_descendant_by_type(
            condition_node,
            "assignment_expression",
        )

        if assignment_node is None:
            continue

        context_lines = get_node_text(if_node, source_bytes).splitlines()
        code_context = (
            context_lines[0].strip()
            if context_lines
            else get_node_text(if_node, source_bytes).strip()
        )

        findings.append(
            DetectionCandidate(
                error_type="INCORRECT_CONDITIONAL_OPERATOR",
                line=assignment_node.start_point[0] + 1,
                column=assignment_node.start_point[1] + 1,
                base_confidence=0.92,
                message="Possible assignment used inside an if condition.",
                code_context=code_context,
                source_span=node_to_span(assignment_node),
                requires_stable_region=True,
            )
        )

    return findings