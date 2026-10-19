"""The kind of code each error type's proposer offers as a candidate site, shown after the title in the reports."""

CANDIDATE_SITES = {
    "NON_SHORT_CIRCUIT_OPERATOR": "& or | operator",
    "UNREACHABLE_ELSE_IF_ORDER": "if / else-if chain",
    "INCORRECT_CONDITIONAL_OPERATOR": "assignment in a condition",
    "DECIMAL_EQUALITY_COMPARISON": "== or != comparison",
    "DIVISION_BY_ZERO_LITERAL": "division or %",
    "MISLEADING_INDENTATION_NO_BRACES": "if or loop without braces",
    "ARRAY_LENGTH_INDEX_MISUSE": "array access",
    "INTEGER_DIVISION_IN_DECIMAL_CONTEXT": "int / int division",
    "CONSTANT_FALSE_LOOP_CONDITION": "for loop",
    "LOOP_COUNTER_CHANGED_IN_BODY": "for loop",
    "LOOP_UPDATE_WRONG_DIRECTION": "for loop",
    "NESTED_LOOP_WRONG_COUNTER": "for loop",
    "EARLY_RETURN_IN_LOOP": "loop",
    "OFF_BY_ONE_LOOP_BOUNDARY": "for loop",
    "LOOP_SKIPS_LAST_ELEMENT": "for loop",
    "WRONG_EXTREME_INITIAL_VALUE": "variable declaration",
    "MISSING_BREAK_IN_SWITCH": "switch case",
    "INDEX_PLUS_ONE_OUT_OF_BOUNDS": "array access in a for loop",
    "ACCUMULATOR_RESET_INSIDE_LOOP": "assignment inside a loop",
    "EMPTY_CONDITIONAL_BODY": "if or loop body",
    "IGNORED_STRING_METHOD_RESULT": "string method call",
    "STRING_EQUALITY_WITH_OPERATOR": "== or != comparison",
    "WHILE_VARIABLE_NOT_UPDATED": "while loop",
    "WRONG_LOOP_VARIABLE_IN_INDEX": "array access in a nested loop",
}


def with_site(error_type: str, title: str) -> str:
    site = CANDIDATE_SITES.get(error_type)
    return f"{title} ({site})" if site else title
