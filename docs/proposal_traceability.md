# Code Coach Proposal Traceability

This document compares the March 2026 Code Coach proposal requirements against the current improving prototype. The current implementation deliberately focuses on the three research error types that already have datasets, features, ML models, and trained baseline metrics.

## Current Scope

| Active error type | Detection role |
|---|---|
| `OFF_BY_ONE_LOOP_BOUNDARY` | ML predicts whether an off-by-one loop boundary pattern is likely present; AST locator finds the loop condition location. |
| `INCORRECT_CONDITIONAL_OPERATOR` | ML predicts whether assignment-in-condition is likely present; AST locator finds the assignment expression location. |
| `ARRAY_LENGTH_INDEX_MISUSE` | ML predicts whether direct `array.length` indexing is likely present; AST locator finds the index expression location. |

## Current Detection Pipeline

```text
Java code
  -> Tree-sitter AST parsing
  -> AST feature extraction
  -> scikit-learn classifiers predict the 3 target error types
  -> only ML-positive predictions are passed to AST locators
  -> AST locators return line/column and context
  -> hint engine returns beginner-friendly feedback
```

The current system should be described as **ML-led hybrid analysis**. ML performs the target error decision. AST rules perform deterministic localization for the ML-positive category. This is stronger and clearer than claiming pure ML localization, because the trained models currently classify file-level error presence rather than predicting source spans directly.

Each diagnostic exposes this relationship through:

- `detection_engine`: currently `ml_gated_ast_locator`
- `ml_probability`: classifier probability for the target error
- `locator_confidence`: confidence of the AST location match
- `confidence`: weighted final confidence, mostly based on ML probability

## Proposal Objective Coverage

| Proposal objective | Current status | Evidence |
|---|---|---|
| Real-time educational support inside the coding environment | Implemented for prototype | VS Code extension runs debounced analysis on Java file edits and displays diagnostics/decorations inline. |
| Detect beginner-level syntax, structural, and early logic errors | Partially implemented by scoped prototype | Current scope is the three target Java error categories listed above. |
| Identify and classify at least 15 common errors | Future expansion | The project is intentionally scoped to 3 ML-backed categories for now. Additional categories should be added after data collection and validation. |
| Beginner-friendly hints | Implemented for current scope | `knowledge_base/code_coach_errors.json` maps each active error type to concept, guidance, and targeted hints. |
| Average response under 2 seconds | Supported by instrumentation; needs benchmark report | `/analyze` returns `analysis_duration_ms`; formal benchmark results should be recorded during evaluation. |
| At least 80% detection accuracy | Partially implemented | Existing metrics cover the 3 target categories. A cleaner held-out evaluation should be maintained as the dataset grows. |
| 75% positive user rating and 20% self-correction improvement | Not yet validated | These require the proposed novice-user study and comparison against compiler/linter feedback. |

## Functional Requirements

| Requirement | Status | Notes |
|---|---|---|
| FR1 Real-time code capture | Implemented | Extension listens to `onDidChangeTextDocument` and schedules analysis. |
| FR2 Incremental code analysis | Partial | Tree-sitter parsing is used and analysis is debounced, but true edit-delta incremental parsing is not yet implemented. |
| FR3 Beginner-level issue detection | Implemented for current scope | The 3 active beginner Java categories are detected through ML-gated analysis. |
| FR4 Lightweight classification of likely errors | Implemented for current scope | scikit-learn classifiers decide whether each of the 3 target categories is present. |
| FR5 Diagnostic generation | Implemented | Diagnostics include error type, confidence, ML probability, locator confidence, location, code context, concept tag, severity, status, and diagnostic ID. |
| FR6 Standardized JSON communication | Implemented | FastAPI response model returns structured JSON; extension consumes the standardized payload. |
| FR7 Pedagogical interpretation | Implemented for current scope | `knowledge_base/code_coach_errors.json` provides concept tags, explanation keys, and hints. |
| FR8 Tiered feedback generation | Implemented | Each category has concept, guidance, and targeted hint levels. |
| FR9 Language simplification | Implemented | Hints are short and beginner-oriented. |
| FR10 IDE feedback display | Implemented | VS Code diagnostics, decorations, hover details, and hint navigation commands are available. |
| FR11 Feedback update and removal | Implemented | Diagnostics/decorations are replaced or cleared after new analysis. |
| FR12 Safe support without direct answer leakage | Implemented | Hints guide learners without returning corrected full code. |
| FR13 Incomplete or partial code handling | Implemented | `parse_java_code_safe` avoids crashes and analyzer suppresses very incomplete files. |
| FR14 Logging for evaluation | Implemented with consent gate | Optional local anonymized JSONL logging is controlled by `codeCoach.enableEvaluationLogging`. |

## Non-Functional Requirements

| Requirement | Status | Notes |
|---|---|---|
| NFR1 Performance | Supported | Analysis duration is measured in the API response; formal benchmark still needed. |
| NFR2 Accuracy and reliability | Partial | Baseline metrics and regression tests exist; final academic claims need held-out evaluation. |
| NFR3 Consistency | Implemented | Deterministic localization, stable diagnostic IDs, and static hint mappings support consistent output. |
| NFR4 Usability | Implemented for prototype | Beginner wording and IDE decorations are available; learner usability study still needed. |
| NFR5 Security and privacy | Implemented for prototype | Processing is local; evaluation logging is optional and hashes identifiers/context. |
| NFR6 Resource efficiency | Supported | Lightweight scikit-learn models and AST locators are used; CPU/RAM benchmark still needed. |
| NFR7 Interoperability | Implemented | JSON/REST API is used between backend and extension. |
| NFR8 Scalability | Supported | New categories can be added through new labels, trained models, target locator entries, and knowledge-base entries. |
| NFR9 Maintainability | Improved | Feature extraction, ML prediction, localization, and hint mappings are separated. |
| NFR10 Ethical use | Implemented for prototype | Hints are scaffolded and avoid full corrected-code generation. |

## Recommended Next Improvements

1. Expand the dataset for the 3 active categories with more negative examples and near-miss examples.
2. Add per-category confusion matrices and false positive reports to the model training output.
3. Move toward candidate-level ML validation, where AST locators generate candidate spans and the ML model scores each candidate rather than the whole file.
4. Run latency/resource benchmarks and record the average response time against the proposal's 2-second target.
5. Conduct expert review of hint quality and novice user testing.
6. Compare Code Coach feedback against compiler/linter feedback for self-correction improvement.
7. Implement true edit-delta incremental parsing only if the final marking criteria require strict incremental analysis beyond debounced snapshot analysis.
