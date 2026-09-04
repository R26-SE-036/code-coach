# The prerequisite graph, explained from scratch

This explains what Code Guru's "concept prerequisite graph" is, why it exists,
how the tool in `backend/app/dev_tools/derive_concept_prerequisites.py` builds
one, and why that tool currently refuses to run. No prior knowledge assumed.

---

## 1. The problem it solves

A student keeps writing this:

```java
for (int i = 0; i <= arr.length; i++) { sum += arr[i]; }
```

That's an off-by-one error. The obvious response is to explain off-by-one
errors. But quite often that isn't where the student is actually stuck. They may
not really understand what a loop's *condition* is doing, or what `arr.length`
means, or how the counter changes each pass. Explaining the symptom over and
over won't help, because the gap is one level down.

So the platform wants to answer a different question:

> **This student keeps failing at X. What should they understand *before* X that
> they haven't got yet?**

To answer that, something has to know that some concepts come before others.
That "comes before" relationship, written out across all the concepts, is the
**prerequisite graph**.

---

## 2. What a "concept" is here

Code Guru has a fixed vocabulary of 14 concepts. They're just labels:

```
assignment_logic        arithmetic_operations    boolean_logic
conditional_logic       control_flow             statement_structure
switch_statements       loop_initialization      loop_control
loop_termination        loop_boundaries          array_indexing
string_comparison       immutable_strings
```

Every mistake the VS Code extension detects is tagged with one of these. An
off-by-one in a loop is tagged `loop_boundaries`; using `=` instead of `==` in
an `if` is tagged `conditional_logic`.

---

## 3. What a "graph" means here

Nothing complicated. A graph is dots joined by arrows. The dots are concepts,
and an arrow means *"you need this one first"*:

```
assignment_logic  ──►  boolean_logic  ──►  conditional_logic  ──►  loop_initialization
                                                                          │
                                                                          ▼
                                                                    loop_control
                                                                          │
                                                                          ▼
                                                                  loop_boundaries
                                                                          │
                                                                          ▼
                                                                  array_indexing
```

Read an arrow as "comes before". So if a student is failing at `array_indexing`,
you can walk *backwards* up the arrows and check each concept on the way:
have they got `loop_boundaries`? `loop_control`? `loop_initialization`? The
first one they haven't got is where teaching should actually start.

That backwards walk is why Study Guider uses **Neo4j**, a graph database. The
query is "follow the arrows backwards, however many steps it takes, and at each
step check this student's own history". Neo4j does that in about five lines.
In a normal SQL database it's a recursive query that re-joins the history table
at every level — possible, but genuinely awkward.

---

## 4. Two ways to get the arrows

### Way A — a teacher writes them down

Someone who knows Java sits down and asserts the ordering: *assignment before
arithmetic, boolean logic before conditions, loops before array indexing*, and
so on.

**This is what the platform uses today.** It's 17 hand-written pairs in
`Study-Guider/backend/app/core/concepts.py`:

```python
PREREQUISITE_EDGES = [
    ("assignment_logic", "arithmetic_operations"),
    ("assignment_logic", "boolean_logic"),
    ("boolean_logic", "conditional_logic"),
    ...
]
```

It works, and it's honest as long as it's described as what it is: **a
pedagogical opinion**, not a finding. Nobody measured it. The comment in that
file says exactly that.

### Way B — infer them from what students actually did

Instead of asserting the order, watch real students and see which concepts they
tend to get right *first*. If nearly everyone masters `loop_control` before
`array_indexing`, that's evidence of a real ordering.

**This is what `derive_concept_prerequisites.py` does.** It's the more
interesting claim for a research project, because it's a result rather than an
opinion — *if* the data supports it.

---

## 5. How the inference works, step by step

### Step 1 — find when each student first "got" each concept

Every time the extension analyses a file, it records the mistakes it finds in a
MongoDB collection called `codeDiagnostics`. When the student fixes a mistake,
the next analysis no longer sees it, and Code Coach marks that record
`resolved` with a timestamp (`resolvedAt`).

So for each student, the tool builds a little timeline:

```
Alice:  conditional_logic  resolved Mon 09:14
        loop_control       resolved Tue 11:02
        array_indexing     resolved Thu 15:40
```

It uses the **first** time a concept was resolved, not the last. A later
recurrence is a relapse, not a second first time.

### Step 2 — compare every pair of concepts

Take two concepts, say `loop_control` and `array_indexing`. Look at every
student who has resolved **both**. For each one, ask: which came first?

```
students who resolved both:         40
loop_control came first:            34
array_indexing came first:           6
                                    ──
agreement that loop_control first:  34/40 = 85%
```

### Step 3 — keep the pairs where students agree

An arrow is drawn only if **both** of these hold:

| Bar | Value | Why |
|---|---|---|
| `MIN_PAIR_OBSERVATIONS` | 5 students did both | Two students agreeing is a coincidence |
| `MIN_PRECEDENCE_RATIO` | 70% agree on the direction | Below that it's a coin flip, not an ordering |

85% of 40 students clears both, so:
`loop_control ──► array_indexing` becomes an arrow.

### Step 4 — throw away the shortcuts

This is the one non-obvious step. Suppose the counting produces all three of:

```
A ──► B        B ──► C        A ──► C
```

The third one is true but useless. If A comes before B and B comes before C,
then obviously A comes before C — it adds nothing, and it's not a *direct*
prerequisite. Keep every one of these and the graph becomes almost fully
connected, so "what should I study first?" answers *"everything you have ever
seen"*, which is no help at all.

So the tool removes any arrow that you could already get to by following other
arrows. This is called a **transitive reduction**. What survives is the direct
prerequisites only.

### Step 5 — write it out

The result is a JSON file listing each arrow with the evidence behind it:

```json
{
  "edges": [
    { "prerequisite": "loop_control",
      "dependent":    "array_indexing",
      "observations": 40,
      "agreement":    0.85 }
  ]
}
```

Study Guider loads that instead of the hand-written list. The evidence travels
with the claim, which is the whole point: anyone can see that this arrow rests
on 40 students agreeing 85% of the time.

---

## 6. Why it lives in Code Coach and not Study Guider

Study Guider can't do this, by design. Every call it makes to Code Coach
forwards the individual student's own login token, so it can only ever see that
one student's data. That's a deliberate security property — it means no
authorization logic has to be written or maintained on that side.

But this calculation needs to look across *all* students at once. So it runs in
Code Coach, which owns `codeDiagnostics`, and hands over a finished JSON file.

---

## 7. Why it currently refuses to run

Run it today and it prints this:

```
REFUSING to derive an ordering from this data:

  - only 3 user(s) have resolved 2+ concepts; 20 needed for a pairwise
    proportion to mean anything
  - median history spans 0:03:12, under the 1:00:00 floor — a whole concept
    history inside an hour indicates generated data, not learning
  - 3/3 users resolved an identical set of concepts (100%) — a real cohort
    does not converge like that; this is one fixture dealt repeatedly

The ordering would be an artefact of how the data was produced.
```

At a glance the database looks fine — there are 98 diagnostic records. But
look closer:

| What's there | Why it isn't usable |
|---|---|
| 3 users with a real history | Not enough for any percentage to mean anything |
| All 3 resolved the **same 13 concepts** | Real students don't converge like that |
| Each history spans **32 seconds to 3.5 minutes** | Nobody learns 13 concepts in three minutes |

That's `backend/app/dev_tools/seed_student.py` — a script writing rows in a
loop — not people learning. If the tool ran anyway, it would produce a
confident, plausible-looking graph that had simply **recovered the seed
script's `for` loop order**.

### Why refusing matters more than it sounds

This is the failure mode worth understanding, because it's the one that's hard
to catch later:

> A number with a method behind it is much harder to disbelieve than an
> opinion.

The hand-written list in `concepts.py` is obviously someone's opinion, and any
reader treats it that way. A graph "derived from 98 real diagnostic records
across 3 users" *sounds* like evidence. It would sit in a dissertation looking
like a finding while actually describing a seed script. So the method itself
has to be the thing that says no — which is what the four thresholds at the top
of the file are for:

```python
MIN_USERS                       = 20        # enough people
MIN_MEDIAN_HISTORY_SPAN         = 1 hour    # learning takes time
MIN_PAIR_OBSERVATIONS           = 5         # enough evidence per arrow
MIN_PRECEDENCE_RATIO            = 0.70      # enough agreement per arrow
MAX_IDENTICAL_CONCEPT_SET_RATIO = 0.90      # a real cohort varies
```

It reports **every** reason at once rather than the first one it hits. Fixing
the user count on data that's also synthetic would just move the refusal one
step along, and someone would reasonably read a single complaint as the only
complaint.

---

## 8. What would make it work

Nothing in the code needs to change. It needs real usage:

- **20+ people** using the extension,
- over **days, not minutes**,
- working on **different things**, so their concept sets differ,
- with at least **5 people** having hit any two concepts you want an arrow
  between.

A first-year lab class of 25 students over two weeks would comfortably clear
all of it. So would the four of you plus classmates using it properly for a
fortnight.

Until then, the honest position is the one the platform already takes: ship the
hand-written ordering, describe it in the write-up as a pedagogical assumption
rather than a result, and note that the derivation exists and is gated.

---

## 9. Where everything is

| Thing | Path |
|---|---|
| The derivation tool | `code-coach/backend/app/dev_tools/derive_concept_prerequisites.py` |
| Its tests (9) | `code-coach/backend/tests/test_concept_prerequisite_derivation.py` |
| The raw data it reads | MongoDB `code-guru` → `codeDiagnostics` |
| The hand-written ordering in use today | `Study-Guider/backend/app/core/concepts.py` |
| The backwards-walk query | `Study-Guider/backend/app/services/learning_path_service.py` |

### Commands

Check the data and see the refusal reasons:

```bash
python -m app.dev_tools.derive_concept_prerequisites
```

Show every user's history before the verdict:

```bash
python -m app.dev_tools.derive_concept_prerequisites --explain
```

Write the graph out once the data supports it:

```bash
python -m app.dev_tools.derive_concept_prerequisites --out prerequisites.json
```

Run from `code-coach/backend/`. It exits with code `2` when it refuses, so it
can't silently succeed in a script.

---

## 10. One bug found while writing this

The tool read the database through the Firestore API
(`storage.client.collection(...).stream()`). When Code Coach moved to MongoDB,
that call stopped working entirely:

```
TypeError: 'Database' object is not callable
```

So the tool had been broken since the migration — it crashed before it reached
the sufficiency check. It now reads through a small helper that works with
either backend, and produces the refusal shown in section 7. The tests pass and
the `--explain` output above is real, not illustrative.
