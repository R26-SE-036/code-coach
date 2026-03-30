from typing import List

from app.models import DetectionCandidate
from app.parser_utils import collect_nodes_by_type, get_node_text, node_to_span


def detect_array_length_index_misuse(tree, source_bytes: bytes) -> List[DetectionCandidate]:
    findings: List[DetectionCandidate] = []
    root = tree.root_node

    array_access_nodes = collect_nodes_by_type(root, "array_access")

    for array_access_node in array_access_nodes:
        array_node = array_access_node.child_by_field_name("array")
        index_node = array_access_node.child_by_field_name("index")

        if array_node is None or index_node is None:
            continue

        array_text = get_node_text(array_node, source_bytes).strip()
        index_text = get_node_text(index_node, source_bytes).strip()
        expected_bad_index = f"{array_text}.length"

        if index_text == expected_bad_index:
            code_context = get_node_text(array_access_node, source_bytes).strip()

            findings.append(
                DetectionCandidate(
                    error_type="ARRAY_LENGTH_INDEX_MISUSE",
                    line=index_node.start_point[0] + 1,
                    column=index_node.start_point[1] + 1,
                    base_confidence=0.94,
                    message="Possible array index out-of-bounds issue detected.",
                    code_context=code_context,
                    source_span=node_to_span(index_node),
                    requires_stable_region=True,
                )
            )

    return findings