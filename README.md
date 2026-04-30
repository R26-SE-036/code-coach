# Code Coach

Code Coach is a beginner-focused programming support tool for Java learners. It runs as a VS Code extension backed by a local FastAPI service, detects selected beginner mistakes without executing the program, and turns diagnostics into scaffolded hints that help students self-correct.

The current research prototype intentionally focuses on three error types:

- `OFF_BY_ONE_LOOP_BOUNDARY`
- `INCORRECT_CONDITIONAL_OPERATOR`
- `ARRAY_LENGTH_INDEX_MISUSE`

## Detection Pipeline

Code Coach now uses an ML-led hybrid pipeline:

```text
Java code
  -> Tree-sitter AST parsing
  -> AST feature extraction
  -> scikit-learn classifiers predict the 3 target error types
  -> AST locators find line/column only for ML-positive predictions
  -> hint engine returns beginner-friendly feedback
```

The ML engine decides whether a target error type is likely present. The AST locator does not independently create diagnostics; it only finds the exact source location after the ML model crosses its confidence threshold.

Diagnostics include:

- `detection_engine`
- `ml_probability`
- `locator_confidence`
- `diagnostic_id`
- `severity`
- `confidence`
- `concept_tag`
- `explanation_key`
- tiered hints

## Features

- Real-time VS Code feedback for Java files using debounced editor-change analysis.
- Local FastAPI backend with Tree-sitter Java parsing.
- ML-gated detection for the three current research categories.
- AST-based line/column localization after ML detection.
- Beginner-friendly hint levels:
  - Concept hint
  - Guidance hint
  - Targeted hint
- Optional local anonymized evaluation logging for research use.

## Current Error Categories

| # | Error type | What it catches |
|---|---|---|
| 1 | `OFF_BY_ONE_LOOP_BOUNDARY` | Loop conditions that include `array.length` as a valid index boundary. |
| 2 | `INCORRECT_CONDITIONAL_OPERATOR` | Assignment used inside `if` or `while` conditions. |
| 3 | `ARRAY_LENGTH_INDEX_MISUSE` | Direct use of `array.length` as an array index. |

## Project Structure

- `extension/code-coach-vscode/` - VS Code extension written in TypeScript.
- `backend/` - Python FastAPI backend.
  - `app/main.py` - API entry point.
  - `app/analyzer.py` - ML-led analysis pipeline.
  - `app/ml_engine.py` - scikit-learn model loading and prediction.
  - `app/feature_extractor.py` - AST-based feature extraction.
  - `app/issue_locators.py` - AST line/column locators for the 3 target errors.
  - `app/hint_engine.py` - Diagnostic-to-hint mapping.
  - `app/evaluation_logger.py` - Optional anonymized local logging.
  - `app/dev_tools/` - ML dataset, split, and baseline training scripts.
  - `models/` - Trained baseline `.joblib` models and metrics.
- `knowledge_base/code_coach_errors.json` - Concept tags, explanation keys, and tiered hint templates for the 3 target errors.
- `data/ml/` - Curated Java snippets, extracted features, splits, and metadata.
- `docs/proposal_traceability.md` - Requirement-by-requirement comparison with the proposal.
- `logs/` - Runtime evaluation logs when explicitly enabled.

## Backend Setup

From the `backend` directory:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend starts at `http://127.0.0.1:8000`.

Useful endpoints:

- `GET /health`
- `POST /analyze`
- `POST /debug-ast`

## Extension Setup

From `extension/code-coach-vscode`:

```bash
npm install
npm run compile
```

Open `extension/code-coach-vscode` in VS Code and press `F5` to launch an Extension Development Host.

Commands:

- `Code Coach: Start`
- `Code Coach: Analyze Current File`
- `Code Coach: Previous Hint`
- `Code Coach: Next Hint`

Settings:

- `codeCoach.backendUrl` - local backend URL, default `http://127.0.0.1:8000`.
- `codeCoach.enableEvaluationLogging` - sends anonymized diagnostic events to the local backend when enabled.

## ML Pipeline

The ML pipeline trains baseline classifiers for the three current categories:

- `has_off_by_one`
- `has_incorrect_conditional`
- `has_array_length_index_misuse`

Run from the `backend` directory:

```bash
py -m app.dev_tools.build_dataset
py -m app.dev_tools.split_dataset
py -m app.dev_tools.train_baselines
```

Current outputs:

- `data/ml/extracted/features_v1.csv`
- `data/ml/splits/train_v1.csv`
- `data/ml/splits/val_v1.csv`
- `data/ml/splits/test_v1.csv`
- `backend/models/*.joblib`
- `backend/models/baseline_metrics_v1.csv`

## Verification

Backend regression tests:

```bash
cd backend
python -m unittest discover -s tests
```

Extension checks:

```bash
cd extension/code-coach-vscode
npm run compile
npm run lint
```

## Proposal Status

See `docs/proposal_traceability.md` for the detailed comparison between the proposal requirements and the current implementation. The main remaining academic work is improving and evaluating the dataset/model quality for these three categories, benchmarking response time and resource usage, expert hint review, novice user testing, and comparison against compiler/linter feedback.

## Proposal Status
Test Teams Worklow 2