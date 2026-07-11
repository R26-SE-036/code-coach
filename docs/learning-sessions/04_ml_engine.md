# Session 4 — What the ML Model Actually Sees

> **Goal of this session:** know exactly what the model receives (35 numbers),
> what it fundamentally cannot answer, and why the same bug scores 0.99 in a
> small file but 0.03 in a big one. This is the honest heart of the ML story.

## The model never sees code

Not the text. Not the tree. Not a line number. A scikit-learn model only eats
a fixed-length **row of numbers** — the *feature vector*. The job of
[feature_extractor.py](../../backend/app/analysis/feature_extractor.py) is to
squash an entire Java file into that row.

**Plain English:** imagine describing a house to someone who can never see
it, using only a form with 35 numeric boxes: rooms, windows, floors... They
must guess "does this house have a leaky roof?" from the form alone. That's
the model's life.

> **Update (July 2026):** the extractor now emits **51** numbers — 16 switch/
> while features were added for the MISSING_BREAK / WHILE_NOT_UPDATED
> promotion (see [doc 08](08_promoting_rule_to_ml.md)). The 3 original models
> still see only their 35 training columns: `_build_feature_frame` aligns each
> model to `feature_names_in_` and ignores columns it never trained on.
> Everything below remains true for those models.

## The 35 numbers (measured from your real extractor)

For `class A{ void m(int[] a){ for(int i=0; i<=a.length; i++){ ... } } }`
the extractor produced (abridged):

```
line_count = 1            char_count = 89          parse_completeness = 1.0
class_declaration_count = 1   method_declaration_count = 1
for_statement_count = 1       if_statement_count = 0     while_statement_count = 0
ast_node_count = 67           max_ast_depth = 11         binary_expression_count = 1
array_access_count = 1        unique_arrays_accessed_count = 1
loop_condition_contains_lt = 1
loop_condition_contains_leq = 1          ← bug signal
loop_condition_contains_length = 1
loop_condition_off_by_one_pattern_count = 1   ← bug signal (<= AND .length together)
assignment_inside_if_condition_count = 0
array_index_uses_length_directly_count = 0
... (error_node counts, etc.)
```

Four families, built by four helpers in feature_extractor.py:
- `_extract_general_ast_features` — the shape of the file (counts, depth).
- `_extract_for_loop_features` — signals for OFF_BY_ONE (`<=`, `.length`...).
- `_extract_if_features` — signals for INCORRECT_CONDITIONAL (assignment
  inside an if-condition...).
- `_extract_array_access_features` — signals for ARRAY_LENGTH
  (`a[a.length]` counted directly).

## Experiment 1: the signal is tiny and specific

We extracted features for the buggy loop (`i<=a.length`) and the corrected
one (`i<a.length`) and diffed the rows. Out of 35 numbers, exactly **two**
changed:

```
loop_condition_contains_leq              buggy=1   correct=0
loop_condition_off_by_one_pattern_count  buggy=1   correct=0
```

That's the needle the model watches. Important nuance: the model does NOT
contain a hand-written rule "if leq==1 then bug". During **training** it
*learned by itself* that these features correlate with off-by-one files and
gave them weight. Learned weighting, not coded rule.

## The one question the model can never answer

Every one of the 35 numbers is a **count over the whole file**. None of them
says "line 5". Therefore the model can answer *"is this kind of bug probably
somewhere in this file?"* but is structurally incapable of answering
*"WHERE?"* — that is why the AST locator must exist. ML = IF, locator = WHERE.

## Experiment 2: the same bug drowns in a big file

We put the IDENTICAL buggy loop into (a) a tiny class and (b) a bigger class
with 4 extra ordinary methods, then scored both:

```
                              small file    big file
bug-signal features:
  loop_condition_contains_leq        1            1     ← identical!
  off_by_one_pattern_count           1            1     ← identical!
context features:
  ast_node_count                    67          277
  method_declaration_count           1            5
  if_statement_count                 0            3
  for_statement_count                1            3

MODEL PROBABILITY               0.9941       0.0328
GATE (threshold 0.6321)          OPEN       CLOSED  ← real bug SUPPRESSED
```

The bug did not change. The model saw the row both times — it wasn't blind,
it was **wrong**. Why: it was trained on small single-bug snippets, where
context counts are near zero. It effectively learned *"an off-by-one file is
a SMALL file with one loop and a `<=`"*. A big multi-method file no longer
matches that learned shape, so the model loses confidence — even though the
tell-tale features are still lit. This is called being
**out of distribution** (OOD): the input's overall shape drifts away from
anything seen in training.

## Why this matters twice (the central tension)

| The gate HELPS | The gate HURTS |
|---|---|
| Filters the crude locator's false positives (Session 3: `i <= a.length - 1`) | Suppresses REAL bugs in files that don't look like training data (Experiment 2) |

Both problems share ONE root cause: **the features are whole-file
aggregates.** That single design choice explains:
- why the model can't localize (no line info in the row) → locators exist;
- why big files break it (context counts go OOD) → the viva demo needed
  small single-bug files for the 3 ML types (measured: bugs combined in one
  file scored 0.003/0.23/0.0 — all suppressed; alone they scored
  0.97/0.63/0.67 — all detected);
- why the standard fix is **candidate-level features**: describe each
  individual loop/if/access with its own small feature row and score
  candidates one at a time. Then a buggy loop looks the same whether it's
  alone or inside 500 lines.

## ml_engine.py — the mechanics

| Piece | What it does |
|---|---|
| `MLPrediction` | dataclass returned per ml_gated type: error_type, probability, `predicted_positive` (the gate flag) |
| `_LOADED_MODELS` | cache — each `.joblib` model is loaded from disk once, reused across requests |
| `_get_model(spec)` | lazy-loads the model file named in the catalog spec (`spec.model_file`) from `backend/models/` |
| `_build_feature_frame(model, feature_dict)` | CRITICAL alignment: reorders the feature dict into the exact columns the model was trained on (`model.feature_names_in_`), filling gaps with 0. Get this wrong → model reads garbage. |
| `predict_issue_types(feature_dict)` | loops over `ml_gated_specs()` from the catalog; `model.predict_proba(x)[0][1]` → probability; `probability >= spec.ml_threshold` → gate open/closed |

And in `analyzer.py`: `_safe_predict_issue_types` wraps it in try/except —
a broken model file means "no ml_gated diagnostics", never a crashed request.

## What you should be able to say out loud

- "The model only ever sees 35 whole-file counts — never code, never a tree,
  never a line number. So it can say IF, never WHERE."
- "Fixing the off-by-one changed exactly 2 of the 35 numbers; the model
  learned to weight those during training."
- "The same bug scored 0.99 alone and 0.03 inside a big file, because the
  context features drifted out of the training distribution — the model
  learned 'off-by-one files are small files'."
- "Both the gate's benefit (filtering crude locators) and its failure
  (suppressing real bugs in unfamiliar files) come from the same root cause:
  file-level features. The fix is candidate-level scoring."

**Next:** [Session 5](05_training_and_calibration.md) — where the models come
from, and how each threshold line was chosen.
