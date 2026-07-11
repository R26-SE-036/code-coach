# Viva Demo Guide

Six runnable Java programs with all 15 Code Coach error types planted, plus
deliberate syntax errors for the red-vs-yellow underline story. Every
diagnostic below was verified against the real backend analyzer, and every
program was compiled and run to confirm its visible symptom.

## Why six files instead of one big file (IMPORTANT — viva talking point)

The 12 **rule-only** error types are detected deterministically, so they work
inside big realistic programs. The 3 **ML-gated** types do not: the models were
trained on small, single-issue snippets with file-level features, so combining
several bugs in one large file pushes every model's probability below its
threshold (measured: 0.003 / 0.23 / 0.0 in a combined file vs 0.97 / 0.63 /
0.67 in single-bug files). That is why each ML-gated type has its own small
program — and it is an honest, measured limitation you can present if asked
("file-level features assume one dominant issue per file; candidate-level
scoring is the planned fix").

**Do not** add syntax errors to the three small ML files or merge them — either
change shifts the feature vector and can silence the ML gate.

---

## File 1: TotalMarksPrinter.java  (ML-gated)

| Line | Error type | Runtime symptom | Fix |
|------|-----------|-----------------|-----|
| 5 | OFF_BY_ONE_LOOP_BOUNDARY (`i <= marks.length`) | Crash: `ArrayIndexOutOfBoundsException: Index 4 out of bounds for length 4` | `i < marks.length` |

## File 2: AttendanceChecker.java  (ML-gated)

| Line | Error type | Runtime symptom | Fix |
|------|-----------|-----------------|-----|
| 6 | INCORRECT_CONDITIONAL_OPERATOR (`eligible = true`) | Prints "Allowed to sit the exam" with only 40/100 attendance | `eligible == true` (or just `if (eligible)`) |

## File 3: LastItemPrinter.java  (ML-gated)

| Line | Error type | Runtime symptom | Fix |
|------|-----------|-----------------|-----|
| 5 | ARRAY_LENGTH_INDEX_MISUSE (`queue[queue.length]`) | Crash: `ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3` | `queue[queue.length - 1]` |

## File 4: StudentGradeManager.java  (rule-only ×2, + 1 syntax error)

| Line | Kind | Detail | Symptom / Fix |
|------|------|--------|---------------|
| 11 | SYNTAX (red) | missing `;` after `+ grade)` | add `;` |
| 23 | DUPLICATE_IF_ELSE_CONDITION | second `mark >= 65` repeats the first | No student can ever receive grade C (silent logic hole). Fix: e.g. `mark >= 55` |
| 31 | STRING_EQUALITY_WITH_OPERATOR | `name == "Chathura"` | Prints "WARNING: could not verify record for Chathura" even though the name matches. Fix: `name.equals("Chathura")` |

Runs without crashing — shows *silent* wrong behavior.

## File 5: BankAccountSimulator.java  (rule-only ×5, + 1 syntax error)

| Line | Kind | Detail | Symptom / Fix |
|------|------|--------|---------------|
| 7 | IGNORED_STRING_METHOD_RESULT | `owner.toUpperCase();` result thrown away | Welcome message prints lowercase. Fix: `owner = owner.toUpperCase();` |
| 13, 15 | MISSING_BREAK_IN_SWITCH | cases 1 and 2 fall through | User picks "view balance" but a Rs. 250 deposit ALSO happens. Fix: add `break;` |
| 23 | SYNTAX (red) | missing `;` after `+ fee)` | add `;` |
| 26 | WHILE_VARIABLE_NOT_UPDATED | `emailsSent` never changes | **INFINITE LOOP** — "Sending monthly statement email..." forever (the star of the demo; stop with Ctrl+C / stop button). Fix: `emailsSent++;` inside the loop |
| 34 | SELF_ASSIGNMENT | `newBalance = newBalance;` | Does nothing (silent). Fix: delete the line |
| 41 | UNREACHABLE_CODE_AFTER_RETURN | println after `return` | **Also a red compile error** — javac refuses to compile until removed. Good for the story: "some logical errors the compiler catches, most it does not." |

Note: this file only compiles after line 41 is removed (and line 23 fixed).

## File 6: InventoryReportTool.java  (rule-only ×5, + 1 syntax error)

| Line | Kind | Detail | Symptom / Fix |
|------|------|--------|---------------|
| 11 | SYNTAX (red) | missing `;` after `printStockReport(items, stock)` | add `;` |
| 21 | ALWAYS_TRUE_OR_CONDITION | `categoryCode != 1 \|\| categoryCode != 2` | Prints "Invalid category code: 2" for a VALID category. Fix: `&&` |
| 31 | EMPTY_CONDITIONAL_BODY | `if (stock[i] < lowStockLimit);` | LOW STOCK WARNING printed for every item, even 25 in stock. Fix: delete the stray `;` |
| 39 | CONSTANT_FALSE_LOOP_CONDITION | `for (int row = 10; row < 4; ...)` | Stock report header/footer print with NO rows in between. Fix: `row = 0` |
| 50 | DIVISION_BY_ZERO_LITERAL | `total / 0` | Crash: `ArithmeticException: / by zero`. Fix: `total / stock.length` |
| 54 | LOOP_UPDATE_WRONG_DIRECTION | `for (... i < items.length; i--)` | (Reached only after fixing line 50) Crash: index -1. Fix: `i++` |

This file tells an iterative story: fix the division crash, rerun, hit the
next crash — exactly how students actually debug.

---

## Suggested viva flow

1. **Act 1 — red vs yellow.** Open `BankAccountSimulator.java` (NOT logged in
   to Code Coach). Point at the red underlines: "the compiler catches syntax
   errors — a missing semicolon, unreachable code. I'll fix those… but is the
   program correct now? No red lines left, yet it is full of logical errors
   the compiler cannot see."
2. **Act 2 — show the damage.** Run it: the fall-through deposit happens on
   "view balance", the name prints lowercase, and it hangs in the infinite
   email loop. Stop it.
3. **Act 3 — Code Coach.** Start the backend, sign in via the coach panel.
   The yellow underlines appear on all five logical errors. Hover one to show
   the three hint levels (concept → guidance → targeted).
4. **Act 4 — fix and prove.** Fix `emailsSent++` (and the break statements),
   rerun: loop terminates, exactly 3 emails, no accidental deposit.
5. **Optional depth.** `InventoryReportTool.java` for the iterative
   fix-crash-fix cycle; the three small files to show the ML-gated detectors
   (mention the diagnostics carry an `ml_probability`, visible in the Output
   channel, unlike the rule-only ones).

## Re-verify after any edit

Any edit to these files can change detection (especially the small ML ones).
Re-check by pasting the file content into the analyzer:

```
cd backend
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); from app.analysis.analyzer import analyze_code; from pathlib import Path; [print(d.line, d.error_type, d.confidence) for d in analyze_code(Path('../extension/code-coach-vscode/src/sample-java/BankAccountSimulator.java').read_text(encoding='utf-8'))]"
```
