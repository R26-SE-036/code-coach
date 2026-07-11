# Glossary & Self-Quiz

> Plain-English definitions of every term from Sessions 1–5, then a
> viva-style quiz. Answer each question OUT LOUD before reading the answer —
> recalling is what makes it stick, re-reading alone does not.

## Glossary

| Term | Plain English | Technical |
|---|---|---|
| **Client-server** | The face and the brain, talking over the network. | VS Code extension (TS) ↔ FastAPI backend (Python) via HTTP/JSON. |
| **Logical error** | Code that runs but does the wrong thing. | Compiles fine; wrong behavior (infinite loop, off-by-one...). Compiler can't catch it. |
| **Debounce** | Wait until they stop typing, then act once. | 900ms timer per document, reset on each keystroke (`scheduleAutoAnalysis`). |
| **AST** | The family tree of the code. | Abstract Syntax Tree: typed nodes (`for_statement`) with named field slots (`condition`). |
| **Tree-sitter** | The machine that builds that tree. | Parser library + Java grammar; tolerant of broken code (ERROR nodes). |
| **Parse health / completeness** | How trustworthy the tree is for half-typed code. | 0–1 score; analyzer bails < 0.35 and multiplies confidence by it. |
| **Locator** | The bug-finder that walks the tree to the exact line. | `locate_*` in issue_locators.py; template: collect type → field slots → pattern → line/col. |
| **rule_only** | The locator is trusted alone. | 12 types; deterministic AST patterns; engine `ast_locator_rule`. |
| **ml_gated** | A model must say "probably here" before the locator runs. | 3 types; `probability >= ml_threshold` opens the gate; engine `ml_gated_ast_locator`. |
| **Feature vector** | The 35-box form describing a file to a model that can't see code. | Whole-file counts from `extract_features`; column names must match training. |
| **Supervised learning** | Learning from an answer key. | Rows = features + human label (`has_off_by_one = 1`); model learns the mapping. |
| **Label / target** | The answer column. | `has_off_by_one`, `has_incorrect_conditional`, `has_array_length_index_misuse`. |
| **Overfitting** | Memorizing the answers instead of learning the subject. | Perfect on training data, useless on new data. Why we never test on train. |
| **Train / val / test** | Learn on one pile, choose on the second, get the honest grade on the third. | 147 / 28 / 35; val gets "used up" by decisions; test touched once. |
| **Probability (predict_proba)** | The model's confidence, 0 to 1 — not a verdict. | `model.predict_proba(x)[0][1]` = P(bug present). |
| **Threshold** | The line: above → flag, below → ignore. | Per-target in ERROR_CATALOG (0.6321 / 0.285 / 0.5371). |
| **Precision** | When it cries wolf, how often is there a wolf? | flagged-and-real / all-flagged. |
| **Recall** | Of all the wolves, how many did it catch? | caught / all-real. |
| **F1** | One number balancing precision and recall. | Harmonic mean; used because classes are ~14% positive (accuracy misleads). |
| **Margin** | The empty gap between the worst-scored bug and the best-scored clean file. | `lowest_positive − highest_negative` on validation. |
| **Margin midpoint** | Put the line in the middle of the gap — farthest from both dangers. | `(lowest_positive + highest_negative)/2`; used when a gap exists. |
| **F1 sweep** | No gap? Try every line, keep the least-bad one. | Fallback when classes overlap (incorrect_conditional → 0.285). |
| **Out of distribution (OOD)** | The input doesn't look like anything the model studied. | Big files: context counts (ast_node_count 67→277) drift from small-snippet training; probability collapses 0.99→0.03. |
| **Candidate-level scoring** | Grade each loop separately instead of the whole file. | The planned fix for OOD + localization: per-candidate feature rows. |
| **Diagnostic** | One underline with its teaching material. | `Diagnostic` model: id, type, line/col, confidence, engine, ml_probability, hints. |
| **HintSet** | Three escalating nudges. | concept → guidance → targeted, from `code_coach_errors.json`. |
| **Learning session** | The container tying a student's analyses together. | `learning_session_id` from `/api/v1/learning-sessions`, sent with every analyze. |
| **Bearer token** | The "I'm signed in" pass attached to every request. | JWT access token in the Authorization header; refresh token trades for a new one on 401. |
| **ERROR_CATALOG** | The single registration desk for all 15 error types. | One `ErrorTypeSpec` each; `validate_catalog()` cross-checks models + hints at startup. |

## Self-Quiz (answers below each question — try first!)

**Q1. Trace the spine: what happens between a keystroke and a yellow underline? Name at least 6 hops.**

<details><summary>Answer</summary>

Keystroke → `onDidChangeTextDocument` (extension.ts) → `scheduleAutoAnalysis`
debounce 900ms → `runAnalysisForEditor` → `ensureAuthenticated` +
`ensureLearningSession` (auth.ts) → `requestAnalyze` →
`authorizedRequestJson` (api.ts, adds Bearer) → POST
`/api/v1/code-coach/analyze` → route (code_coach.py) → service →
`analyze_code` (analyzer.py) → diagnostics JSON back →
`applyEditorFeedback` → `diagnosticCollection.set` → underline.
</details>

**Q2. Why 900ms debounce instead of analyzing on every keystroke?**

<details><summary>Answer</summary>

Every keystroke would flood the backend with requests analyzing half-typed
code. The timer resets on each keystroke, so a burst of typing collapses
into ONE request when the student pauses.
</details>

**Q3. What are the two detection modes, and what exactly does the ML decide vs the locator?**

<details><summary>Answer</summary>

`rule_only` (12 types): the AST locator runs directly. `ml_gated` (3 types):
the model first answers IF — "is this bug probably in this file?" (a
probability vs a threshold) — and only if the gate opens does the locator
answer WHERE (exact line/column). ML never localizes; the locator never
decides for ml_gated types alone.
</details>

**Q4. What is an AST, and what three properties make it queryable?**

<details><summary>Answer</summary>

The code parsed into a tree of constructs. (1) Every node has a type
(`for_statement`, `binary_expression`); (2) children sit in NAMED fields
(`condition`, `body` → `child_by_field_name`); (3) it's recursive — every
condition/expression is itself a subtree.
</details>

**Q5. Give the false positive of the crude off-by-one check, and how a structural check would avoid it.**

<details><summary>Answer</summary>

`for (int i = 0; i <= a.length - 1; i++)` is CORRECT Java, but its condition
text contains both `"<="` and `".length"`, so the text-contains check flags
it. A structural check would inspect the comparison's `right` field and only
flag a BARE `a.length` field_access (like the array-length locator's exact
`index_text == f"{array_text}.length"`).
</details>

**Q6. What does the ML model actually receive as input, and what question can it therefore never answer?**

<details><summary>Answer</summary>

A row of 35 whole-file numeric counts (loops, ifs, node counts, pattern
flags). No code, no tree, no positions — so it can never answer WHERE the
bug is. That's why the AST locator must exist.
</details>

**Q7. The same buggy loop scored 0.9941 alone and 0.0328 inside a big file. The bug-signal features were identical. Explain.**

<details><summary>Answer</summary>

The context features ballooned (ast_node_count 67→277, methods 1→5...). The
model trained only on small single-bug snippets, so it effectively learned
"off-by-one files are small files with one loop". The big file is OUT OF
DISTRIBUTION — its overall shape doesn't match training — so the model loses
confidence despite the lit signal features. Root cause: file-level
aggregate features. Fix: candidate-level scoring.
</details>

**Q8. Why is the data split into THREE piles instead of two?**

<details><summary>Answer</summary>

Train fits the weights. But every CHOICE (which model, which threshold) made
by looking at a pile slowly overfits that pile — so validation absorbs the
decision-making, and test stays untouched until one final honest
measurement. Testing on train would only measure memorization.
</details>

**Q9. The metrics CSV says logistic regression beat random forest for incorrect_conditional, yet the catalog runs random forest. Why is that not a mistake?**

<details><summary>Answer</summary>

The CSV compared all models at the DEFAULT threshold 0.5 (RF: F1 0.667, LR:
0.75). Calibration gives each model its BEST line; RF at 0.285 reaches F1
0.889, beating LR. Model file and threshold are chosen together — a model is
only as good as the line paired with it.
</details>

**Q10. State the threshold-placement rule, both branches, with the real numbers.**

<details><summary>Answer</summary>

Score the validation pile. If the lowest-scoring real bug is ABOVE the
highest-scoring clean file (a gap), put the line at the midpoint —
off_by_one: (0.271+0.993)/2 = 0.6321; array_length: 0.5371. The midpoint is
farthest from BOTH dangers (new bug scoring lower / new clean scoring
higher). If they OVERLAP (incorrect_conditional: bug 0.285 < clean 0.290),
no perfect line exists → sweep all candidate thresholds, keep best F1 →
0.285 (F1 0.889).
</details>

**Q11. The 0.285 threshold accepts a false alarm to catch every bug. Argue why that's right — and what the limit is — for this tool.**

<details><summary>Answer</summary>

A missed bug is a total failure for a LEARNING tool: the student believes
wrong code is correct. A false alarm costs a moment of thought about your
own code — which is nearly the point of the tool. But cry wolf too often and
students stop trusting ALL underlines, so the line can't go arbitrarily low.
The threshold is a decision about which mistake you'd rather make.
</details>

**Q12. Which file computes the threshold, which stores it, which applies it — and when does each run?**

<details><summary>Answer</summary>

`calibrate_thresholds.py` (dev_tools) COMPUTES it — offline, run by hand
after retraining; a human copies the numbers. `error_catalog.py` STORES it
(`ml_threshold=` in ErrorTypeSpec) — the single source of truth.
`ml_engine.py` APPLIES it on every request:
`predicted_positive = probability >= spec.ml_threshold`.
</details>

**Q13. What is `validate_catalog()` and why does it exist?**

<details><summary>Answer</summary>

A startup check (called from main.py) that every ERROR_CATALOG entry is
FULLY registered: ml_gated entries have an existing model file, and every
type has a hints entry in code_coach_errors.json. Without it, a
half-registered type would silently drop diagnostics or serve generic hints;
with it, the app fails loudly at boot.
</details>

**Q14. Why did the viva demo need three SMALL single-bug files for the ML-gated types?**

<details><summary>Answer</summary>

Measured: the three ML bugs combined in one big file scored 0.003/0.23/0.0 —
all below threshold, all suppressed (training data has one bug per small
snippet, so another bug's features look like a NEGATIVE example). Alone in
small files they scored 0.97/0.63/0.67 — all detected. Same OOD root cause
as Q7.
</details>

**Q15. How does confidence shown in VS Code get computed for the two modes?**

<details><summary>Answer</summary>

ml_gated: 0.8 × ml_probability + 0.2 × locator_confidence. rule_only: the
locator's hand-set confidence alone. Both then multiplied by the parse
completeness score (messy half-typed files → lower confidence), capped at
0.99. (`_combine_confidence` in analyzer.py.)
</details>

---

**Scoring yourself:** 13+ solid → you're viva-ready on this material.
Under 10 → re-read the session doc for the questions you missed, then retake
in two days. Spaced recall beats cramming.
