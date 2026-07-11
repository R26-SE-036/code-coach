# Session 3 — The AST and the Locators

> **Goal of this session:** understand how flat Java text becomes a TREE you
> can ask questions about, and how a locator walks that tree to pin a bug to
> an exact line and column.

## The problem locators solve

A locator receives Java code and must answer: *"is the buggy pattern here,
and exactly where?"* But code arrives as a flat string of characters. You
can't reliably ask a string "what is your loop condition?" — you need
structure. That structure is the **AST**.

## Tree-sitter: text → tree

**Tree-sitter** is a parsing library (with a Java grammar,
`tree_sitter_java`). Give it Java text; it returns an **Abstract Syntax
Tree (AST)**: every syntactic construct becomes a *node*, nested inside its
parent construct.

This is the REAL tree tree-sitter produced for
`for(int i=0; i<=a.length; i++){ print(a[i]); }` — run against your actual
parser (the `«...»` shows the source text each node covers):

```
for_statement                     «for(int i=0; i<=a.length; i++)...»
  init: local_variable_declaration    «int i=0;»
    type: integral_type                   «int»
    declarator: variable_declarator      «i=0»
      name: identifier                       «i»
      value: decimal_integer_literal         «0»
  condition: binary_expression        «i<=a.length»
    left: identifier                      «i»
    right: field_access                   «a.length»
      object: identifier                      «a»
      field: identifier                       «length»
  update: update_expression           «i++»
  body: block                         «{ print(a[i]); }»
    expression_statement
      method_invocation                 «print(a[i])»
        arguments: argument_list
          array_access                  «a[i]»
            array: identifier               «a»
            index: identifier               «i»
```

Three properties make this queryable:

1. **Every node has a `type`** — `for_statement`, `binary_expression`,
   `field_access`, `identifier`. These are the grammar's categories.
2. **Children sit in NAMED FIELDS** — a `for_statement` has slots called
   `init`, `condition`, `update`, `body`. You reach in directly:
   `for_node.child_by_field_name("condition")`. No searching, no guessing.
3. **It's recursive** — the condition is itself a tree (`binary_expression`
   with `left`/`right`); `a.length` is a `field_access` with
   `object`/`field`. Structure all the way down.

**Plain English:** tree-sitter turns "one long sentence" into "a labeled
family tree", so instead of string-searching you ask precise questions like
*"give me every for-loop"* and *"show me your condition slot"*.

## parser_utils.py — the toolbox every locator uses

| Function | What it does |
|----------|--------------|
| `parse_java_code_safe(code)` | Parses; returns `ParseResult` (tree + source bytes + health + crashed flag). THE door between text and tree. |
| `collect_nodes_by_type(root, "for_statement")` | Walks the whole tree, returns EVERY node of one type. The workhorse. |
| `find_first_descendant_by_type(node, t)` | Like above but stops at the first match — "is there an assignment anywhere inside this condition?" |
| `get_node_text(node, source_bytes)` | A node only stores byte offsets; this slices the original text back out. |
| `inspect_tree_health(root)` | Half-typed code still parses but with ERROR/missing nodes; this scores completeness 0–1. Analyzer bails below 0.35 and scales confidence by it. |

One subtlety: tree-sitter counts lines/columns from **0**; editors count from
**1**. The `+1` happens in `node_to_span` / `_node_line` — and the reverse
`-1` happens client-side in `createRangeFromDiagnostic`. The two halves meet
in the middle.

## Anatomy of a locator (they ALL follow this template)

From `issue_locators.py` — the real off-by-one locator:

```python
def locate_off_by_one_loop_boundaries(parse_result):
    root = parse_result.tree.root_node
    findings = []
    for for_node in collect_nodes_by_type(root, "for_statement"):   # 1. hunt a node type
        condition = for_node.child_by_field_name("condition")        # 2. reach into a field slot
        if condition is None:
            continue
        text = _node_text(condition, source_bytes)                   # 3. inspect it
        if "<=" in text and ".length" in text:                       # 4. check the pattern
            findings.append(_result("OFF_BY_ONE_LOOP_BOUNDARY",      # 5. report node's line/col
                                    condition, ...))
    return _deduplicate(findings)                                    # 6. drop repeats
```

**Template:** hunt node type → reach into field slots → check a pattern →
report the node's exact line/column → deduplicate. All 15 locators are this
shape; only steps 1 and 4 differ.

## The precision dial: crude vs precise checks

This is the deepest idea of Session 3. Step 4 (the pattern check) can be:

**CRUDE — text contains:** the off-by-one check above just asks whether the
condition's *text* contains `"<="` and `".length"`. Cheap to write — but we
PROVED it over-fires:

```
for (int i = 0; i <= a.length; i++)       → FLAGGED  (real bug ✓)
for (int i = 0; i <= a.length - 1; i++)   → FLAGGED  (FALSE POSITIVE ✗ — this is correct Java!)
for (int i = 0; i <  a.length; i++)       → clean    (✓)
```

`i <= a.length - 1` is perfectly valid, but its text contains both magic
substrings, so the crude check flags it.

**PRECISE — structural match:** compare with the array-length locator:

```python
if index_text == f"{array_text}.length":   # EXACT equality, not "contains"
```

It reaches into the `array_access` node's `array` and `index` fields and
requires the index to be *exactly* `a.length`. `a[a.length - 1]` does NOT
match. Zero false positives from that pattern.

**Why keep any crude checks?** They're cheaper to write and the trigger-happy
ones (off-by-one) got an ML gate stacked in front as a second filter — two
weak filters making one stronger decision. That's exactly WHY those types are
`ml_gated`: the crude locator alone over-fires, so the model pre-screens the
file. (Session 4 shows the flip side: the gate can also suppress real bugs.)

## What each locator does NOT do

A locator reports a raw `DetectionResult`: error type, line, column, a
hand-set `locator_confidence` (e.g. 0.95), a message. It does **not** attach
hints, IDs, or final confidence — `analyzer.py` blends confidence
(80% ML probability + 20% locator confidence for ml_gated; locator alone for
rule_only; then scaled by parse completeness) and `hint_engine.py` attaches
the hints afterwards. Division of labor.

## All 15 locators at a glance

| Error type | Node type hunted | Check (crude/precise) |
|---|---|---|
| OFF_BY_ONE_LOOP_BOUNDARY | `for_statement` | condition text contains `<=` and `.length` (crude) |
| INCORRECT_CONDITIONAL_OPERATOR | `if/while_statement` | any `assignment_expression` inside condition (structural) |
| ARRAY_LENGTH_INDEX_MISUSE | `array_access` | index text == `array.length` exactly (precise) |
| STRING_EQUALITY_WITH_OPERATOR | `binary_expression` | `==`/`!=` with a string literal or two known String vars; skips `null` |
| LOOP_UPDATE_WRONG_DIRECTION | `for_statement` | condition `<`/`<=` but update `--` (or `>` with `++`) |
| UNREACHABLE_CODE_AFTER_RETURN | `block` | any statement after a `return_statement` |
| MISSING_BREAK_IN_SWITCH | `switch_block` | non-last case group not ending in break/return/throw/continue/yield; skips empty stacked labels |
| EMPTY_CONDITIONAL_BODY | `if/while/for` | body slot is a bare `;` |
| SELF_ASSIGNMENT | `assignment_expression` | left text == right text with `=` |
| ALWAYS_TRUE_OR_CONDITION | `binary_expression` | `x != A \|\| x != B`, same var, different literals |
| IGNORED_STRING_METHOD_RESULT | `expression_statement` | bare call to toUpperCase/trim/substring/... (immutable String methods) |
| DIVISION_BY_ZERO_LITERAL | `binary_expression` | `/` or `%` with literal `0` on the right |
| CONSTANT_FALSE_LOOP_CONDITION | `for_statement` | init literal fails the condition on the FIRST check (actually evaluated) |
| DUPLICATE_IF_ELSE_CONDITION | `if_statement` chain | a repeated (whitespace-normalized) condition in the same chain |
| WHILE_VARIABLE_NOT_UPDATED | `while_statement` | no condition variable assigned/updated in body; skips method-call/field conditions and loops with break/return/throw |

## What you should be able to say out loud

- "Tree-sitter parses Java into an AST: typed nodes with named field slots,
  so I can ask a for-loop directly for its condition."
- "Every locator is the same template: collect nodes of one type, reach into
  field slots, check a pattern, report the node's line/column, deduplicate."
- "Checks range from crude text-contains to precise structural matches — the
  crude off-by-one check false-positives on `i <= a.length - 1`, which is
  exactly why that type has an ML gate in front of it."

**Next:** [Session 4](04_ml_engine.md) — the other transformation of the same
code: 35 numbers, and what the model can and cannot know.
