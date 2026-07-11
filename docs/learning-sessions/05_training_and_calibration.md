# Session 5 — Training and Calibration

> **Goal of this session:** know where the `.joblib` models come from, why the
> data is split into three piles, how three model types competed, what a
> threshold really is, and the exact rule that placed each threshold line.

## 1. The training data is an answer key

The models were not written — they were **trained** on labeled examples in
`data/ml/splits/`. Each row = one Java snippet, already run through the SAME
`extract_features` from Session 4, plus the correct answers a human attached:

```
snippet_id                = off_by_one_bug_023
has_off_by_one            = 1     ← the LABEL (the answer)
has_incorrect_conditional = 0
has_array_length_...      = 0
loop_condition_contains_leq = 1   ← the features (the clues)
ast_node_count            = 121
... (all 35 features)
```

That is **supervised learning**: every training row carries both the clues
and the answer; the model's job is to learn the mapping well enough to work
on snippets it has never seen. Note `ast_node_count = 121` — the training
positives are all SMALL snippets. That is the origin of Session 4's
out-of-distribution failure.

Measured sizes and balance:

```
train = 147 rows    val = 28 rows    test = 35 rows
positives per target: train 21/147 (~14%)   val 4/28   test 5/35
```

The classes are lopsided (~14% positive). A lazy model could score 86%
accuracy by always answering "no bug" — which is why training passes
`class_weight="balanced"` (rare positives count more) and why we judge with
F1, not accuracy.

## 2. Why THREE piles (train / val / test)?

**Why not test on the training data?** Because a big-enough model can just
MEMORIZE all 147 answers and score 100% while being useless on new code.
That's **overfitting**. Testing on training data measures memory, not
learning.

**Why not just two piles?** Because the moment you start making CHOICES based
on a pile — which model type is best? what threshold? — you begin indirectly
overfitting to THAT pile too. So:

- **train (147)** — the model fits its weights here.
- **validation (28)** — used repeatedly to make choices (model selection,
  threshold placement). Gets "used up" by decision-making.
- **test (35)** — touched ONCE at the end for the honest final number. Never
  optimized against, so it's the number you quote.

## 3. Three model types competed

`train_baselines.py` trains, per target, three scikit-learn pipelines:
- **logistic_regression** (with StandardScaler) — draws a weighted straight
  boundary through feature space; fast, interpretable.
- **random_forest** — a committee of decision trees voting; handles
  non-linear patterns.
- **svm** (RBF kernel, with scaler) — finds a maximum-margin boundary.

All get `class_weight="balanced"`, `random_state=42` (reproducibility). Each
trained model is saved as `backend/models/<target>__<model_name>.joblib`, and
the val/test scores go to `backend/models/baseline_metrics_v1.csv`.

## 4. A model outputs a PROBABILITY, and you draw a LINE

The single most important idea of Session 5. A model doesn't say yes/no — it
scores each file between 0 and 1. Real measured output of the
incorrect-conditional Random Forest on the 28 validation snippets:

```
true label | probability
     1     |   0.965   ← real bug
     1     |   0.905   ← real bug
     1     |   0.450   ← real bug
     0     |   0.290   ← clean, but suspicious-looking
     1     |   0.285   ← real bug
     0     |   0.265
     0     |   0.100
     ...   |   ≈0.000  (22 clean snippets near zero)
```

To act, you place a **threshold line**: above → flag, below → ignore. Moving
ONLY the line (same model, nothing retrained):

```
line at 0.5   → catches 2/4 bugs, 0 false alarms   → precision 1.00, recall 0.50, F1 0.667
line at 0.285 → catches 4/4 bugs, 1 false alarm    → precision 0.80, recall 1.00, F1 0.889
```

**The dial:** lower line = catch more real bugs but more false alarms;
higher line = fewer false alarms but more missed bugs. Choosing where to put
the line IS calibration.

Vocabulary (plain English):
- **precision** — of everything I flagged, how much was really a bug? (don't cry wolf)
- **recall** — of all real bugs, how many did I catch? (don't miss any)
- **F1** — one number balancing both.

## 5. The puzzle this solves (why RF despite LR "winning")

`baseline_metrics_v1.csv` says LR beat RF for incorrect_conditional (val F1
0.75 vs 0.667) — yet the catalog runs **RF**. Resolution: that CSV measured
everyone at the DEFAULT line of 0.5. Calibration gives each model its BEST
line — and RF at its best line (0.285) hits **0.889**, beating LR. The model
file and the threshold are chosen **together**, because a model is only as
good as the line you pair it with.

## 6. The rule that places the line (calibrate_thresholds.py)

Score all validation snippets, then find two numbers:
- `lowest_positive` — the LOWEST score any real bug got.
- `highest_negative` — the HIGHEST score any clean snippet got.

### Case A: clean gap → MARGIN MIDPOINT
For off_by_one: every real bug scored ≥ 0.993, every clean ≤ 0.271:

```
clean ●●●●●                    gap                    ●●●● bugs
0 ────0.271━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━0.993──── 1
                       ▲
              line at (0.271+0.993)/2 = 0.6321
```

Any line inside the gap is perfect on validation — but the MIDDLE is safest
for unseen data, because it sits farthest from BOTH dangers at once: a new
bug scoring a bit lower than 0.993 still gets caught, and a new clean file
scoring a bit higher than 0.271 still gets rejected. Maximum buffer both
ways. The gap's width is the **margin**; hence "margin midpoint".

Results: off_by_one → **0.6321**; array_length → **0.5371** (same rule).

### Case B: overlap → F1 SWEEP
For incorrect_conditional the classes TANGLE at the boundary:

```
lowest real bug  = 0.285
highest clean    = 0.290   ← a clean file out-scored a real bug!
```

No line can be perfect: at ≤0.285 you catch all bugs but flag that clean
file; just above 0.285 you miss a real bug. The overlap forces you to choose
which mistake to make. So the code falls back: try EVERY candidate
threshold, measure F1 at each, keep the best → **0.285** (F1 0.889).

The actual code (both branches):

```python
if lowest_positive > highest_negative:          # gap exists
    midpoint = (lowest_positive + highest_negative) / 2
    return midpoint, margin
# overlap → sweep
for candidate in sorted(set(probabilities)):
    f1 = _metrics_at_threshold(y_true, probabilities, candidate)["f1"]
    if f1 > best_f1: best_threshold, best_f1 = candidate, f1
```

## 7. Missed bug vs false alarm — the values question

The 0.285 line means: *"rather occasionally underline good code than ever
let a real bug slip past silently."* For a learning tool that's defensible:
- a **missed bug** = total failure — the student believes wrong code is fine
  and learns nothing;
- a **false alarm** = minor cost — the student looks, thinks, moves on (and
  thinking about your own code is the point of the tool).
- the limit: cry wolf too often and students stop trusting ALL underlines.

The threshold number is really a decision about which mistake you'd rather
make.

## 8. The three files, and who does what when

```
calibrate_thresholds.py   OFFLINE, run by hand after retraining.
  (backend/app/dev_tools)  Computes the line per target (midpoint or sweep),
        │                  compares LR/RF/SVM (best val F1, ties → latency),
        │                  writes backend/models/calibration_v1.json,
        │                  PRINTS recommendations.
        ▼  human copies the numbers
error_catalog.py           STORES the chosen model_file + ml_threshold.
  (backend/app/analysis)   The single source of truth the runtime reads.
        ▼  read at runtime
ml_engine.py               APPLIES the line on every request:
  (backend/app/analysis)   predicted_positive = probability >= spec.ml_threshold
```

The runtime never recalculates the line; it reads the stored one and
compares. Retrain models → rerun the calibration tool → copy the new numbers
into the catalog.

## What you should be able to say out loud

- "The models are trained on 147 labeled snippets; val (28) makes the
  choices, test (35) is touched once for the honest number — three piles
  because testing on training data measures memorization, and choosing on
  val slowly overfits val."
- "A model outputs a probability; the threshold is a line, and moving it
  trades missed bugs against false alarms — same model, F1 went 0.667→0.889
  just by moving the line."
- "If validation separates cleanly, the line goes at the margin midpoint —
  farthest from both dangers (0.6321, 0.5371). If the classes overlap, no
  perfect line exists, so we sweep for best F1 (0.285)."
- "calibrate_thresholds.py computes, error_catalog.py stores, ml_engine.py
  applies."

**Next:** [Session 6+] the service layer & learning signals (how struggle is
detected and sent to the Study Guider) — not yet covered by these docs.
