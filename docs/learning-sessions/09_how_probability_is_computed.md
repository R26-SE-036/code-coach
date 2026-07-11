# Session 9 — How the Probability Is Actually Computed

> **Goal:** open the black box. When Code Coach says *"probability 0.9989 that
> this file has an off-by-one"*, you should be able to derive that number by
> hand, say what it can and cannot mean, and defend every design choice
> around it. Every number in this doc was measured on the real system
> (July 2026, the 5-target models trained on the synthetic corpus).

## The journey of one number

```
Java code
   │  feature_extractor.py
   ▼
52 numbers  (the feature row — Session 4)
   │  ml_engine.predict_issue_types()          ← THIS DOC
   ▼
probability per ml_gated type  (e.g. 0.9989)
   │  compare to spec.ml_threshold (0.5295)    ← calibration, Session 5
   ▼
gate OPEN → locator runs → finding
   │  analyzer._combine_confidence()
   ▼
confidence = 0.8·probability + 0.2·locator_confidence, × parse completeness
   │
   ▼
the number VS Code shows next to the underline
```

One line of code produces the probability:

```python
probability = float(model.predict_proba(x)[0][_positive_class_index(model)])
```

`predict_proba` returns one probability **per class**, in `model.classes_`
order — we read the index of class `1` ("issue present") instead of
hard-coding `[1]`, so a differently-encoded model can never be misread.

## What predict_proba computes — it is ONE formula

For the logistic-regression pipelines (all 5 selected models are LR), the
"built-in method" is exactly this, nothing more:

```
z = w·x + b          take the 52 features (scaled), multiply each by its
                     learned weight, add them up, add the intercept
p = 1 / (1 + e^(-z)) squash the score into (0, 1) with the sigmoid
```

**We verified this by hand** — computed the formula manually with numpy and
compared to the library call, on the real off-by-one model:

```
manual  sigmoid(w·x + b) = 0.9988636115
model.predict_proba      = 0.9988636115     identical to 10 decimal places
```

So `predict_proba` is not a mysterious built-in to replace with something
"more professional" — it IS the professional method, and it's 52
multiplications, one addition, one exponential.

### The sigmoid, in plain English

`z` is an unbounded score: 0 means "no idea", large positive means "very
bug-like", large negative "very clean". The sigmoid maps that score onto
(0, 1) so it can be read as a probability:

```
z:      -6      -2       0       +2      +6
p:     0.002   0.12     0.5     0.88    0.998
```

## The learned weights — read your own model's mind

These are the REAL coefficients inside `has_off_by_one__logistic_regression
.joblib` (read from `lr.coef_`), the evidence that training *learned* rather
than being told:

| Feature | Weight | Meaning |
|---|---|---|
| `loop_condition_leq_bare_length_count` | **+2.74** | the structural signal (`<=` against a bare `arr.length`) — by far the strongest |
| `loop_condition_off_by_one_pattern_count` | +0.67 | the crude text pattern (`<=` and `.length` anywhere) |
| `loop_condition_contains_leq` | +0.67 | any `<=` in a loop condition |
| `unique_arrays_accessed_count` | +0.13 | mild context |
| ... 43 small-weight context features ... | ≈0 | file shape, mostly ignored |
| `binary_expression_count` | −0.13 | more general expressions → slightly less suspicious |
| **intercept `b`** | **−6.69** | the prior: "assume CLEAN unless evidence accumulates" |

Two things worth saying out loud in a viva:

1. **Nobody set these numbers.** Training minimized log-loss over 1,397
   labeled examples; the weights are where that optimization settled. The
   model discovered on its own that the structural feature deserves 4× the
   weight of the crude text features — the same conclusion we reached by
   experiment in doc 08.
2. **The intercept is the skepticism.** At −6.69, a file with no suspicious
   features scores p ≈ 0.001. The bug-signal features must overcome that
   baseline before the gate opens.

### Worked example (the demo snippet)

`for (int i = 0; i <= a.length; i++)` lights the three big features. Their
scaled contributions push z from −6.69 up past +6.8 → sigmoid → **0.9989**.
Fix the loop to `i < a.length`: those features go to 0, z stays far
negative → p ≈ 0.002 → gate closed. The probability moves for exactly the
reasons the weights say it should.

## The other two model families (trained but not selected)

`predict_proba` exists for every scikit-learn classifier; what differs is
the computation behind it:

| Family | predict_proba is... | Character |
|---|---|---|
| Logistic regression | sigmoid of a weighted sum | smooth, honest probabilities, fully inspectable |
| Random forest | fraction of the 200 trees voting "bug" | steppy (0.415, 0.42, ...), rarely reaches 0 or 1 |
| SVM | Platt scaling: a sigmoid fitted over the margin distance | a probability bolted onto a distance |

Calibration picked LR for all 5 targets (best validation F1, ties broken by
latency) — a nice bonus since LR is also the most explainable.

## Is the probability HONEST? (calibration, measured)

A probability is *calibrated* if "p = 0.8" is right about 80% of the time.
The standard measurement is the **Brier score** — mean squared gap between
predicted probability and truth (0 = perfect, 0.25 = coin flip). Measured on
the validation split for all five targets:

```
brier = 0.0000 for all 5 targets; 100% of scores < 0.05 or > 0.95
```

The classes separate so cleanly that every prediction is already near-certain
and near-correct. This is also the honest answer to "should we add
CalibratedClassifierCV?" (the textbook 'professional' upgrade): **it would
have nothing to fix** — we measured before adding machinery, and declined.

## Is it FAST? (measured, and one real optimization)

Median per-stage latency of a real analyze request (50 runs, warm caches):

| Stage | Time |
|---|---|
| tree-sitter parse | 0.04 ms |
| feature extraction (52 numbers) | 0.16 ms |
| build the 1-row feature frame | 0.27 ms |
| one model's predict_proba | 0.55 ms |
| all 5 gates | 5.2 ms → **3.2 ms** after the fix |
| entire analyze_code | 6.1 ms → **3.9 ms** |

The fix: all 5 models were trained on the same 52 columns, yet the feature
frame was being rebuilt 5 times per request. `predict_issue_types` now
builds it once and reuses it (keyed by column set, so differently-trained
future models still get correct frames). And the sense of proportion: the
whole pipeline is ~4 ms behind a **900 ms** debounce — the ML was never the
user-visible bottleneck, so we stopped optimizing there.

## What happens to the probability afterwards

The probability alone never underlines anything:

1. **The gate** — `probability >= ml_threshold` (0.5295 for off-by-one, a
   margin-midpoint from calibration, Session 5). Below: the locator never
   runs. Above: the locator finds WHERE.
2. **The blend** — the confidence VS Code displays is
   `0.8 × probability + 0.2 × locator_confidence`, then multiplied by parse
   completeness (messy half-typed files get lower confidence), capped at
   0.99 (`analyzer._combine_confidence`).
3. **Failure is loud now** — if prediction ever throws (corrupt model file),
   `_safe_predict_issue_types` returns no ML diagnostics *and logs the
   exception*. Fail safe, never fail silent.

## What you should be able to say out loud

- "The probability is `predict_proba` — for my logistic models that's
  literally sigmoid(w·x + b) over 52 features; I reproduced it manually and
  matched the library to 10 decimal places."
- "The weights were learned, not written: training gave my structural
  off-by-one feature +2.74, four times the crude text features, and a −6.69
  intercept that presumes files are clean."
- "I measured calibration instead of assuming: Brier 0.0000 on validation,
  so CalibratedClassifierCV had nothing to improve."
- "I measured latency instead of guessing: scoring is ~3 ms behind a 900 ms
  debounce; the one real inefficiency was rebuilding an identical feature
  frame 5 times, which I fixed."
- "The probability then faces a calibrated threshold, blends 80/20 with the
  locator's confidence, and is scaled by parse health before a student ever
  sees it."
