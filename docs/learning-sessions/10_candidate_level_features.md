# Session 10 — Candidate-Level Features (the known limitation, and its fix)

> **Goal:** understand the one failure class that file-level ML gating cannot
> fix, be able to demonstrate it live, explain the architecture that would
> eliminate it, and defend the decision NOT to build it (yet). This doc is
> written to be cited directly in the thesis limitations chapter.

## The demonstrated failure (run on the real system, July 2026)

One Java file, two loops:

```java
class ReportTool {
    static int total(int[] marks) {
        int sum = 0;
        for (int i = 0; i <= marks.length; i++) {      // line 4: REAL BUG
            sum += marks[i];
        }
        return sum;
    }
    static void printAll(int[] marks) {
        for (int i = 0; i <= marks.length - 1; i++) {  // line 10: CORRECT JAVA
            System.out.println(marks[i]);
        }
    }
}
```

What the deployed pipeline does with it — measured, not hypothesized:

```
file-level gate: prob=1.0 -> OPEN
underline at line 4    confidence 0.99     ← real bug        ✓
underline at line 10   confidence 0.99     ← correct code    ✗ FALSE POSITIVE
```

**Why it happens.** The gate decides per FILE. There *is* an off-by-one in
this file, so opening is the correct file-level answer. But an open gate
protects nothing *inside* the file: the crude locator (text-contains `<=`
and `.length`, Session 3) then flags every matching loop — including the
perfectly legal `<= marks.length - 1`. The student sees a top-confidence
underline on correct code.

**The cruel detail:** the information needed to avoid this EXISTS in the
feature row. For this file:

```
loop_condition_leq_bare_length_count   = 1     ← "exactly ONE loop is truly bad"
loop_condition_off_by_one_pattern_count = 2    ← "two loops look suspicious"
```

The model effectively knows one loop is guilty and one is innocent — but the
features are whole-file **aggregates**, so the *which* is destroyed before
the model ever sees it. Aggregation is the root cause; no amount of training
data can restore information the representation threw away.

## The fix: change the unit of analysis

**File-level (current):** one feature row per file → "is this bug type
probably SOMEWHERE in this file?" → separate locator answers WHERE.

**Candidate-level:** one feature row per *candidate site* — every
`for_statement`, every switch case group, every `while` — describing only
itself. Score each row independently.

The demo file's two loops as candidate rows:

| Feature (per loop)                    | loop @ line 4 | loop @ line 10 |
|---|---|---|
| condition uses `<=`                   | 1 | 1 |
| right side is a *bare* `.length`      | **1** | **0** |
| right side is `.length - 1`           | 0 | **1** |
| body indexes the array with loop var  | 1 | 1 |
| loop starts at 0                      | 1 | 1 |

Model output: line 4 → ~0.99 (flag), line 10 → ~0.02 (silent). One
underline, the right one.

## What changes architecturally

| Aspect | File-level (current) | Candidate-level |
|---|---|---|
| Question answered | "bug somewhere in file?" | "is THIS site buggy?" |
| Localization | separate AST locator | the flagged candidate IS the location — gate and locator merge |
| Per-site false positives | possible through an open gate (demonstrated above) | eliminated **by construction** |
| Out-of-distribution risk | file shape is part of the input; mitigated by size-diverse training (Session 4: 0.0328 → 0.9989) | file size is not a feature at all; immune by construction |
| Training labels | one label per file | one label per candidate site |
| Examples from the same corpus | 2,220 rows | ~10,000+ rows (every distractor loop/switch/while is a free negative) |
| Threshold calibration | per target, unchanged in principle | per target, same margin-midpoint machinery |

Two facts make the migration cheap *for this specific project*:

1. **The generator already knows the per-candidate labels.** It plants the
   bug in a known payload method (doc 08) — emitting "this loop = 1, those
   loops = 0" is bookkeeping, not new labeling work.
2. **The pipeline seams survive.** ERROR_CATALOG, threshold calibration,
   train/split tooling, and the confidence blend all carry over; what
   changes is the extractor (per-candidate rows) and the gate wiring
   (score candidates instead of the file).

Estimated effort: 2–4 focused days, mostly in the extractor and the
retraining/verification loop.

## Do we need it? The decision, with evidence

**No — for the current scope.** Every measurement says file-level is at its
ceiling on this corpus:

- test F1 **0.973–1.0** on the human-written holdout (all 5 targets)
- Brier score **0.0000** on validation (probabilities already honest)
- all 15 demo detections correct; intentional fall-through correctly
  suppressed (0.0244) vs real missing break flagged (0.9955)
- the historical OOD failure empirically fixed by the size-diverse corpus

Re-architecting a system at ceiling risks a working product to chase metrics
with almost no room to move. The demonstrated failure above is real but
narrow: it needs a genuinely-buggy file that ALSO contains a
rule-matching-but-correct site of the same error type.

**When the answer flips to yes:**
- the false-positive class starts appearing in real student code (the
  learning-events data would show it), or
- the thesis needs a stronger ML contribution — *"file-level vs
  candidate-level, compared empirically on the same corpus"* is a
  publishable-shaped chapter and the infrastructure is ready for it.

That is a scope decision for the team and supervisor, not a technical
necessity.

## How to present this in the viva (the honest-limitation move)

> "My gate works at the file level, and I can demonstrate its structural
> limit: a file containing both a real off-by-one and a correct
> `<= length - 1` loop gets two 0.99-confidence underlines — the gate opens
> correctly for the file, but cannot protect individual sites inside it. The
> root cause is aggregation: my features count patterns per file, so the
> model knows ONE loop is bad but not WHICH. The principled fix is
> candidate-level scoring — one feature row per loop — which merges detection
> and localization and eliminates this failure class by construction. I chose
> not to implement it because every metric shows file-level at ceiling on my
> data; I documented the migration path instead."

Naming your own edge, demonstrating it live, explaining its root cause, and
justifying the engineering decision — that sequence displays more mastery
than a system presented as flawless.

## What you should be able to say out loud

- "File-level features aggregate per file, so the model can know a bug
  exists without knowing which site — and an open gate then lets the crude
  locator's false positives through. I can demo this: two loops, two 0.99
  underlines, one wrong."
- "Candidate-level features change the unit of analysis to one row per
  loop/switch/while; the flagged candidate IS the location, so gate and
  locator merge and per-site false positives disappear by construction."
- "It also removes out-of-distribution risk by construction — file size
  stops being an input — where my current fix (size-diverse training data)
  only mitigates it."
- "I don't need it yet: F1 0.973–1.0 on the human holdout, Brier 0.0.
  I need it if real usage surfaces the false-positive class, or if the
  thesis wants an architecture-comparison chapter — the generator already
  knows per-candidate labels, so the path is ~2–4 days."
