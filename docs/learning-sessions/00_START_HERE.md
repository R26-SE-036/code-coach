# Code Coach — Learning Sessions Study Guide

> **⚠️ System changed on 2026-07-11 (after docs 01–07 were written).** Where
> the older docs disagree with this list, this list wins:
> - **5 ml_gated types** now (not 3): MISSING_BREAK_IN_SWITCH and
>   WHILE_VARIABLE_NOT_UPDATED were promoted; 10 types remain rule_only.
> - **52 features** now (not 35): switch/while families + one structural
>   off-by-one signal were added.
> - Training data is a **2,010-file synthetic corpus** (generate_snippets.py,
>   seed 42); the 210 manual snippets are a held-out test set.
> - New thresholds: 0.5295 / 0.5008 / 0.504 / 0.5202 / 0.5027 (all
>   margin-midpoint; margins 0.94–0.99).
> - The Session-4 OOD failure (0.9941→0.0328 in big files) is **fixed** by
>   size-diverse training data: the same experiment now scores 0.9989 in both.
> Full story: [08_promoting_rule_to_ml.md](08_promoting_rule_to_ml.md).

These documents capture everything from Sessions 1–5 of your learning plan.
They are written to be re-read months later and still make sense. Each one
mixes plain English (the intuition) with the technical detail (the exact
files, functions, and numbers), because in the viva you need both.

## How to use these docs

1. Read `01` → `05` in order the first time. Each session builds on the last.
2. Before the viva, re-read `00` (this file) and take the quiz in `07`.
3. When you forget what a file or function does, look it up in `06`.
4. Every experiment in these docs was actually run against your real code.
   The numbers (0.9941, 0.0328, 0.6321, 0.285...) are real measurements,
   not made-up examples. If you change the models or data, re-run and update.

## The documents

| Doc | Session | One-line summary |
|-----|---------|------------------|
| [01_big_picture.md](01_big_picture.md) | 1 | What Code Coach is: client-server, the two halves, the two detection modes |
| [02_request_journey.md](02_request_journey.md) | 2 | One keystroke traced end-to-end: editor → backend → yellow underline |
| [03_ast_and_locators.md](03_ast_and_locators.md) | 3 | How flat text becomes a tree, and how locators walk it to find the exact line |
| [04_ml_engine.md](04_ml_engine.md) | 4 | What the ML model actually sees (35 numbers), what it can and cannot do |
| [05_training_and_calibration.md](05_training_and_calibration.md) | 5 | Where the models come from and how each threshold line was chosen |
| [06_file_and_method_reference.md](06_file_and_method_reference.md) | all | Every important file and function, one line each |
| [07_glossary_and_quiz.md](07_glossary_and_quiz.md) | all | Plain-English definitions + viva-style self-test |
| [08_promoting_rule_to_ml.md](08_promoting_rule_to_ml.md) | runbook | Solo checklist: author data + train + calibrate to promote MISSING_BREAK and WHILE_NOT_UPDATED to ml_gated |
| [09_how_probability_is_computed.md](09_how_probability_is_computed.md) | 9 | Open the black box: sigmoid(w·x+b) verified by hand, the real learned weights, calibration + latency measurements |
| [10_candidate_level_features.md](10_candidate_level_features.md) | 10 | The known limitation: per-site false positives through an open gate (demonstrated), and the candidate-level fix — cite in the thesis limitations chapter |

## The one-picture summary of the whole system

If you remember nothing else, remember this spine. Every session is a zoom-in
on one part of it:

```
 YOU TYPE JAVA IN VS CODE
        │
        │  (Session 2: the journey)
        ▼
 extension: debounce 900ms → runAnalysisForEditor → POST /api/v1/code-coach/analyze
        │                     {language, code, learning_session_id}
        ▼
 backend: route (code_coach.py) → service → analyzer.analyze_code(code)
        │
        │  (Session 3)                    (Session 4)
        ▼                                      ▼
 tree-sitter parses text into an AST    feature_extractor turns the SAME code
 (a tree of typed nodes)                into whole-file numbers (35 at first;
                                        52 since the switch/while features — doc 08)
        │                                      │
        │                                      ▼
        │                              ml_engine scores the numbers with
        │                              3 trained models → probabilities
        │                                      │
        │                      (Session 5: where models & thresholds come from)
        │                                      │
        ▼                                      ▼
 FOR EACH of the 15 error types in ERROR_CATALOG:
   • rule_only (10 types):  AST locator runs directly on the tree
   • ml_gated  (5 types):   locator runs ONLY IF probability >= threshold
        │
        ▼
 locator finds the EXACT line/column → hint_engine attaches 3-level hints
        │
        ▼
 diagnostics JSON travels back → extension paints YELLOW UNDERLINES
```

## The five sentences to memorize

1. **Code Coach is a client-server system**: a TypeScript VS Code extension
   (the face) talks HTTP/JSON to a Python FastAPI backend (the brain).
2. **Tree-sitter turns Java text into a tree** of typed nodes with named
   fields, and locators walk that tree to find the exact buggy spot.
3. **The ML model never sees code — only 35 whole-file counts.** It answers
   "is this bug probably in this file?", never "where?".
4. **ml_gated = ML gate in front of the locator; rule_only = locator alone.**
   The gate filters the crude locators' false alarms, but can also suppress
   real bugs in files that don't look like its small training snippets.
5. **Each threshold was calibrated, not guessed**: middle of the gap when the
   classes separate cleanly (margin midpoint), best-F1 sweep when they overlap.
