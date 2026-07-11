# Runbook — Promoting a rule_only Type to ml_gated

> **What this is:** the complete solo-workflow for turning
> MISSING_BREAK_IN_SWITCH and WHILE_VARIABLE_NOT_UPDATED into ml_gated types.
> All the code plumbing is DONE — the pipeline already knows about both
> targets and skips them gracefully until data exists. Your job is the data;
> this document is the checklist.

## Why these two (and not the other ten)

The principle from Sessions 3–4: **gate a rule with ML only when the rule is
a guess.** When the rule is a proof (SELF_ASSIGNMENT, DIVISION_BY_ZERO...),
a gate can only do one thing to a correct finding — suppress it. These two
rules are guesses:

- **MISSING_BREAK_IN_SWITCH** — intentional fall-through is a legal, common
  Java idiom. The rule cannot read intent.
- **WHILE_VARIABLE_NOT_UPDATED** — loop state can change through method side
  effects the rule cannot track (it already carries skip-heuristics as an
  admission of this).

## What is already built (you don't touch these)

| Piece | Status |
|---|---|
| Feature extractor | 16 new features (8 switch + 8 while) — vector is now 51 numbers |
| Snippet index generator | knows both categories; folders exist under `data/ml/raw_snippets/` |
| snippet_index.csv | has `has_missing_break`, `has_while_not_updated` columns (all 0 for now) |
| build/split/train/calibrate | all 5 targets wired; empty targets warn-and-skip |
| Regression proof | with zero new data, calibration still outputs 0.6321 / 0.285 / 0.5371 |

The key new features (what the future models will see):

- Switch: `switch_fallthrough_case_count` (the rule's own signal),
  `switch_comment_count` (intentional fall-through is conventionally
  commented), `switch_empty_stacked_label_count` (`case 1: case 2:` idiom),
  terminator/default counts, case body size.
- While: `while_condition_var_not_updated_count` (the rule's own signal),
  `while_body_method_call_count` (side-effect updates the rule can't see),
  method-call / field-access condition counts, `while(true)` count, exit
  counts, body size.

## THE data-design rule (read this twice)

For the gate to be smarter than the rule, the dataset needs **three** kinds
of snippets, not two:

| Kind | Rule fires? | Truly a bug? | Label | What it teaches |
|---|---|---|---|---|
| buggy | yes | yes | `has_* = 1` | the bug shape |
| fixed | no | no | clean | the corrected shape |
| **intentional** | **yes** | **no** | **clean** | **the judgment — this is what the rule can't do** |

Without the third kind, the model just re-learns the rule and the gate adds
nothing (it would open every time the rule fires). We proved the features can
carry the distinction — measured on real snippets:

```
                                  buggy fall-through   intentional fall-through
switch_fallthrough_case_count            1                      1     ← rule signal IDENTICAL
switch_comment_count                     0                      1     ← context differs
switch_empty_stacked_label_count         0                      1     ← context differs
```

The rule sees the same thing in both files. The model can see the difference.
That gap is the entire value of the promotion — and your intentional
examples are what teach it.

### Suggested quantities (mirrors the existing 30-pair pattern)

Per type:
- **30 buggy** — `data/ml/raw_snippets/missing_break_in_switch/buggy/MissingBreakBug001.java` … `030`
- **30 fixed** — `…/fixed/MissingBreakFix001.java` … `030` (same number = same pair;
  the generator links them into a pair_group so buggy+fixed never straddle a split)
- **10–15 intentional** — put these in `data/ml/raw_snippets/clean/` continuing the
  numbering (`Clean031.java`, `Clean032.java`, …), then edit their `notes` in the
  regenerated CSV to say what they are (e.g. "intentional fall-through, commented").
  They are clean files whose features light up — exactly the negatives that matter.

Same scheme for while: `WhileNoUpdateBug001.java` / `WhileNoUpdateFix001.java`
(any name works — the generator only needs trailing digits — but keep it consistent).

### What the snippets should look like

**Keep them SMALL — one class, one or two methods.** Session 4's lesson: the
models learn the *shape* of training files. Big training files would help,
but mixing sizes with only ~75 examples per class mostly adds noise. Match
the existing corpus style (one small class per file, `public class X { … }`).

Buggy missing-break (behavior actually wrong — e.g. deposit falls into withdraw):

```java
public class OrderStatusPrinter {
    static String describe(int status) {
        String message = "";
        switch (status) {
            case 1:
                message = "Pending";      // BUG: falls through, becomes "Shipped"
            case 2:
                message = "Shipped";
                break;
            default:
                message = "Unknown";
        }
        return message;
    }
}
```

Intentional fall-through (clean — cumulative behavior, commented):

```java
public class AccessLevelPrinter {
    static void printPermissions(int level) {
        switch (level) {
            case 3:
                System.out.println("can delete");
                // fall through: admins also get editor rights
            case 2:
                System.out.println("can edit");
                // fall through: editors also get viewer rights
            case 1:
                System.out.println("can view");
                break;
            default:
                System.out.println("no access");
        }
    }
}
```

Buggy while (condition variable never changes):

```java
public class RetryCounter {
    static void countDown(int attempts) {
        while (attempts > 0) {
            System.out.println("attempts left: " + attempts);   // BUG: attempts never changes
        }
    }
}
```

Intentional-looking clean while (state advances through a method the rule
would have to guess about — vary these: Scanner loops, iterator loops,
`while(true)` + `break`, flag set inside a called helper, etc.):

```java
public class LineReader {
    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {           // rule skips method-call conditions,
            System.out.println(scanner.nextLine()); // but the MODEL should learn this shape too
        }
    }
}
```

**Vary everything that doesn't matter** (names, case counts, statement kinds,
whether there's a default) and **keep constant only what does** (the presence/
absence of the bug). Otherwise the model latches onto accidents — remember,
it learned "off-by-one files are small" by accident once already.

## The command sequence (run from `backend/`)

```bash
# 0. you have authored the .java files in data/ml/raw_snippets/...

# 1. regenerate the index (picks up every new file; preserves your notes)
python -m app.dev_tools.build_snippet_index

#    -> open snippet_index.csv, edit `notes` for the intentional cleans

# 2. extract features for every snippet -> features_v1.csv + 5 binary CSVs
python -m app.dev_tools.build_dataset

# 3. re-split train/val/test (stratified by error type, pairs kept together)
python -m app.dev_tools.split_dataset
#    -> check the printed summary: every target should now have positives
#       in train AND val AND test. If a split has zero, add a few more pairs.

# 4. train LR / RF / SVM for all 5 targets -> backend/models/*.joblib
python -m app.dev_tools.train_baselines

# 5. pick best model + threshold per target
python -m app.dev_tools.calibrate_thresholds
#    -> copy the printed "Values for ERROR_CATALOG" block
```

Use `./.venv/Scripts/python.exe -m …` if plain `python` lacks the packages.

## ⚠️ Re-splitting re-deals ALL the cards

Step 3 reshuffles units across train/val/test **for the original 3 targets
too** (new units change the stratified buckets). That means the old
thresholds 0.6321 / 0.285 / 0.5371 are **stale the moment you re-split** —
they were midpoints of the OLD validation margins. This is not a problem,
just a rule:

> **After any re-split, retrain and recalibrate ALL targets, and update ALL
> five catalog entries with the freshly printed values — never keep old
> thresholds with new splits.**

## Flipping the catalog (the only runtime change)

In [error_catalog.py](../../backend/app/analysis/error_catalog.py), each entry
goes from:

```python
"MISSING_BREAK_IN_SWITCH": ErrorTypeSpec(
    error_type="MISSING_BREAK_IN_SWITCH",
    detection_mode="rule_only",
    locator=locate_missing_breaks_in_switch,
),
```

to (values from the calibration printout — these are placeholders):

```python
"MISSING_BREAK_IN_SWITCH": ErrorTypeSpec(
    error_type="MISSING_BREAK_IN_SWITCH",
    detection_mode="ml_gated",
    locator=locate_missing_breaks_in_switch,          # unchanged — still finds WHERE
    target_column="has_missing_break",
    model_file="has_missing_break__<selected>.joblib",  # from calibration output
    ml_threshold=<selected>,                            # from calibration output
),
```

Same for WHILE_VARIABLE_NOT_UPDATED with `has_while_not_updated`. Also update
the 3 existing ml_gated entries if calibration printed new numbers for them
(it will have — see the warning above). `validate_catalog()` checks the model
files exist at startup, so a typo fails loudly at boot, not silently.

## Verifying it worked

1. **Threshold sanity** — in the calibration output, did the new targets get a
   healthy margin (midpoint rule) or an overlap (F1 sweep)? Overlap with a
   very low threshold means your intentional examples confuse the model —
   good sign for honesty, check which snippets score wrong.
2. **The gate must be smarter than the rule** — the whole point. Feed the
   backend an intentional fall-through file (like the one above): rule_only
   would underline it; the gate should stay CLOSED. Then a buggy one: gate
   OPEN, underline at the right line. Use the VS Code Output channel to see
   `ml_probability` per diagnostic.
3. **The demo files still work** — `BankAccountSimulator.java` contains
   MISSING_BREAK (×2) and WHILE_VARIABLE_NOT_UPDATED. It's a BIG multi-method
   file — the Session 4 OOD lesson predicts the small-snippet-trained gate may
   suppress these! Check it. If suppressed, that's not a mystery, it's the
   known file-level-features limitation — either add some bigger training
   files, or present it in the viva as the measured limitation it is (you
   already have the 0.9941→0.0328 evidence for the same phenomenon).
4. **Run the analyzer smoke checks** on the six sample-java demo programs and
   confirm the other 13 error types are unaffected.

## Failure modes to expect (so they don't surprise you)

| Symptom | Cause | Fix |
|---|---|---|
| split_dataset raises "zero positives in Validation" | too few pairs for a target | add ~3–5 more pairs; ratios are 70/15/15 |
| sklearn "y contains only one class" | you bypassed the skip logic with a tiny split | more data |
| calibration threshold ≈ 0.0x with margin 0.0 | intentional examples overlap bugs in feature space | inspect which snippets score wrong; strengthen the context differences (comments, stacked labels) |
| new type stops firing in big demo files | out-of-distribution (Session 4) | expected with file-level features; document it or diversify data |
| old types' F1 dropped after re-split | new val/test deal is harder — the old numbers weren't wrong, the deck changed | report the new numbers; never mix old thresholds with new splits |

## The viva story this gives you

*"I measured that my rule for missing breaks cannot distinguish intentional
fall-through from a forgotten break — the rule's signal is literally identical
for both. So I promoted the type to ml_gated: I authored buggy, fixed, and
intentional examples, added switch-context features (comment density, stacked
labels, terminator counts), trained and calibrated per-target models, and the
gate now encodes the judgment the rule can't make."* — that's a complete,
honest research arc: limitation → measurement → data design → evaluation.
