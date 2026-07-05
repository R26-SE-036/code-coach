# Code Coach Complete Project Guide

This guide explains the complete Code Coach project from first principles. It is written for someone who needs to understand the implementation, explain it in a viva, and trace how data moves through the system.

## 1. Project in One Sentence

Code Coach is a VS Code extension and FastAPI backend that analyzes beginner Java code without executing it, predicts three selected error categories using trained machine-learning models, locates the exact source position using the AST, and returns progressive educational hints.

## 2. Main Parts of the System

```text
VS Code extension (TypeScript)
        |
        | HTTP/JSON requests
FastAPI backend (Python)
        |
        +--> Authentication and learning sessions
        +--> Tree-sitter Java parser
        +--> AST feature extraction
        +--> scikit-learn ML models
        +--> AST issue localization
        +--> Hint knowledge base
        +--> MongoDB or in-memory storage
        +--> Learning signals for other Code Guru components
```

The current supported Java error categories are:

1. `OFF_BY_ONE_LOOP_BOUNDARY`
2. `INCORRECT_CONDITIONAL_OPERATOR`
3. `ARRAY_LENGTH_INDEX_MISUSE`

The current system does not attempt to detect every Java syntax or logic error.

# Part I: Machine Learning

## 3. What Machine Learning Means Here

Machine learning is used to decide whether the current Java file probably contains each target error category.

The system does not send raw source code directly into a neural network. Instead:

```text
Java source code
-> Tree-sitter AST
-> numeric structural features
-> trained scikit-learn classifier
-> probability for each error category
```

This is supervised machine learning because the models were trained using examples with known labels.

Example:

```text
Java snippet: for (int i = 0; i <= values.length; i++)
Known label: has_off_by_one = 1
```

For a correct snippet:

```text
Java snippet: for (int i = 0; i < values.length; i++)
Known label: has_off_by_one = 0
```

## 4. Type of ML Problem

The project uses three independent binary classification tasks:

```text
Model 1: has_off_by_one                  -> 0 or 1
Model 2: has_incorrect_conditional       -> 0 or 1
Model 3: has_array_length_index_misuse   -> 0 or 1
```

This is effectively a multi-label design because one Java file could theoretically contain more than one error category at the same time.

It is not one three-class model. There are three separate yes/no models.

## 5. Dataset Structure

The raw Java snippets are under:

```text
data/ml/raw_snippets/
```

Important groups:

```text
clean/
off_by_one/buggy/
off_by_one/fixed/
incorrect_conditional_operator/buggy/
incorrect_conditional_operator/fixed/
array_length_index_misuse/buggy/
array_length_index_misuse/fixed/
```

Meaning:

- `buggy`: positive examples containing a target issue
- `fixed`: corrected versions used as negative examples for that issue
- `clean`: general negative examples without the target issues

Metadata is stored in:

```text
data/ml/metadata/snippet_index.csv
```

Extracted numeric data is stored in:

```text
data/ml/extracted/features_v1.csv
data/ml/extracted/off_by_one_binary_v1.csv
data/ml/extracted/incorrect_conditional_binary_v1.csv
data/ml/extracted/array_length_index_binary_v1.csv
```

Train, validation, and test data are stored in:

```text
data/ml/splits/train_v1.csv
data/ml/splits/val_v1.csv
data/ml/splits/test_v1.csv
```

## 6. Why an AST Is Used

AST means Abstract Syntax Tree. It is a structured representation of source code.

Example Java:

```java
if (x = 5) {
    System.out.println(x);
}
```

Tree-sitter represents this using nodes such as:

```text
if_statement
condition
assignment_expression
block
method_invocation
```

The AST is more useful than plain text because the system can understand that `=` occurs inside an `if` condition rather than somewhere unrelated.

## 7. Features Used by the Models

Feature extraction happens in:

```text
backend/app/analysis/feature_extractor.py
```

### Parse-health features

- `line_count`
- `char_count`
- `parse_crashed`
- `parse_completeness`
- `has_error_nodes`
- `error_node_count`
- `missing_node_count`
- `unstable_span_count`

### General AST features

- `class_declaration_count`
- `method_declaration_count`
- `local_variable_declaration_count`
- `return_statement_count`
- `while_statement_count`
- `assignment_expression_count`
- `binary_expression_count`
- `max_ast_depth`
- `ast_node_count`

### Loop features

- `for_statement_count`
- `loop_condition_contains_lt`
- `loop_condition_contains_leq`
- `loop_condition_contains_gt`
- `loop_condition_contains_geq`
- `loop_condition_contains_length`
- `loop_condition_off_by_one_pattern_count`
- `for_node_with_array_access_count`
- `max_for_loop_body_size`

### Conditional features

- `if_statement_count`
- `assignment_inside_if_condition_count`
- `equality_in_if_condition_count`
- `boolean_literal_in_if_condition_count`
- `logical_operator_in_if_condition_count`

### Array features

- `array_access_count`
- `array_index_uses_length_directly_count`
- `array_index_uses_length_expression_count`
- `unique_arrays_accessed_count`

These features create one numeric row for each Java snippet.

## 8. Models Compared During Training

Training is implemented in:

```text
backend/app/dev_tools/train_baselines.py
```

Three algorithms are trained for every target:

### Logistic Regression

Logistic Regression is a linear binary classifier.

It calculates a weighted score:

```text
z = w1*x1 + w2*x2 + ... + b
```

It then converts the score into a probability using the sigmoid function:

```text
sigmoid(z) = 1 / (1 + e^(-z))
```

The project does not manually implement sigmoid. Scikit-learn performs it internally, and the runtime reads the result using:

```python
model.predict_proba(x)[0][1]
```

`[0]` means the first input row. `[1]` means the probability of the positive class.

Logistic Regression is not a Perceptron. They are both linear classifiers, but Logistic Regression produces a probability while a basic Perceptron produces a hard decision.

### Random Forest

Random Forest combines many decision trees.

Each tree makes a prediction based on feature decisions. The forest combines those predictions. It can model nonlinear relationships and usually does not require feature scaling.

Current training configuration:

```text
200 trees
class_weight = balanced
random_state = 42
```

### SVM

SVM means Support Vector Machine. It tries to find a decision boundary with the largest possible margin between positive and negative examples.

The project uses:

```text
RBF kernel
probability = True
class_weight = balanced
```

The RBF kernel allows nonlinear decision boundaries. `probability=True` enables probability estimates.

## 9. Why StandardScaler Is Used

Logistic Regression and SVM are placed inside a scikit-learn `Pipeline` with `StandardScaler`.

Standardization changes features approximately to:

```text
mean = 0
standard deviation = 1
```

This prevents large-scale features such as `ast_node_count` from dominating small binary features only because of numeric size.

Random Forest does not require scaling, so its pipeline contains only the model.

## 10. Why `class_weight="balanced"` Is Used

Some labels may contain fewer positive examples than negative examples.

`class_weight="balanced"` gives more importance to the smaller class so the model does not simply learn to predict the majority class every time.

## 11. Why `random_state=42` Is Used

Randomized algorithms can produce different results each run. A fixed random state improves reproducibility.

The number `42` has no mathematical advantage. It is simply a commonly used fixed seed.

## 12. Training Pipeline

The training flow is:

```text
load train/validation/test CSV files
-> identify numeric feature columns
-> convert features and labels to numeric values
-> build Logistic Regression, Random Forest, and SVM pipelines
-> for each of the three targets:
     train each model
     evaluate on validation data
     evaluate on test data
     save model as .joblib
-> save all metrics to baseline_metrics_v1.csv
```

Saved models are under:

```text
backend/models/
```

There are nine model files:

```text
3 targets x 3 algorithms = 9 models
```

## 13. Evaluation Metrics

Metrics are implemented in `_evaluate_model()`:

### Accuracy

```text
correct predictions / all predictions
```

Accuracy can be misleading when classes are imbalanced.

### Precision

```text
true positives / all predicted positives
```

High precision means that when Code Coach predicts an issue, it is often correct.

### Recall

```text
true positives / all actual positives
```

High recall means Code Coach finds many of the real issues.

### F1-score

F1 is the harmonic mean of precision and recall:

```text
F1 = 2 * precision * recall / (precision + recall)
```

### Average latency

The training script measures average prediction time per sample in milliseconds.

Important limitation:

> The current metrics come from a small curated dataset. They demonstrate prototype behavior but should not be presented as proof of general performance on all beginner Java programs.

## 14. Which Models Are Used at Runtime

Although nine models exist, runtime currently uses only the Logistic Regression model for each target.

This is configured in:

```text
backend/app/analysis/error_catalog.py
```

`ERROR_CATALOG` holds one `ErrorTypeSpec` per error type, which for ML-gated
entries includes:

- public error type
- Logistic Regression `.joblib` file
- probability threshold

All current thresholds are:

```text
0.65
```

Example:

```text
predicted probability = 0.81
threshold = 0.65
result = positive
```

```text
predicted probability = 0.42
threshold = 0.65
result = negative
```

## 15. Runtime ML Functions

### `MLPrediction`

A dataclass containing:

- `error_type`
- `target_column`
- `probability`
- `predicted_positive`

### `_get_model(target_column)`

- checks the in-memory model cache
- finds the configured `.joblib` file
- loads it with `joblib.load()`
- stores it in `_LOADED_MODELS`

Caching avoids loading the same model from disk for every analysis request.

### `_build_feature_frame(model, feature_dict)`

- reads the exact feature names expected by the trained model
- places current feature values in the correct order
- fills a missing feature with `0`
- returns a one-row Pandas DataFrame

Feature order must match training. Otherwise, the model could interpret the wrong value as the wrong feature.

### `predict_issue_types(feature_dict)`

- loads each of the three runtime models
- creates the model input row
- calls `predict_proba()`
- compares probability with `0.65`
- returns three `MLPrediction` objects

## 16. Detection Is Not Localization

This is one of the most important project concepts.

ML answers:

```text
"Does this file probably contain this error category?"
```

ML does not answer:

```text
"The issue is exactly at line 7, column 18."
```

After a positive ML prediction, `issue_locators.py` searches the AST to find the source location.

That is why the detection engine is named:

```text
ml_gated_ast_locator
```

The ML result gates or allows the locator to run.

## 17. Final Confidence Calculation

The final displayed diagnostic confidence is not just the ML probability.

In `analyzer.py`:

```text
weighted confidence =
    ML probability * 0.8
    + locator confidence * 0.2
```

Then:

```text
final confidence =
    weighted confidence * parse completeness
```

The result is capped at `0.99` and rounded to two decimals.

Example:

```text
ML probability = 0.80
locator confidence = 0.95
parse completeness = 1.00

weighted = 0.80*0.8 + 0.95*0.2
         = 0.64 + 0.19
         = 0.83

final confidence = 0.83
```

If the Java code is incomplete and parse completeness is `0.70`:

```text
final confidence = 0.83 * 0.70 = 0.581
```

## 18. Important ML Limitations

- Only three target categories are supported.
- The models use file-level engineered features, not token sequences.
- ML predicts category presence, not source span.
- The AST locator still uses deterministic patterns.
- The dataset is curated and relatively small.
- The current runtime always uses Logistic Regression models.
- Threshold `0.65` is configured manually, not dynamically calibrated per user.
- `_safe_predict_issue_types()` returns an empty list if model prediction fails, so a model-loading failure produces no diagnostics instead of crashing the API.
- True candidate-level ML scoring is not implemented.
- This is not CNN, RNN, GAN, Transformer, or generative AI.

# Part II: Technical Foundations

## 19. What Is the Backend?

The backend is the server-side application. It:

- receives HTTP requests
- validates request data
- authenticates users
- runs analysis
- reads and writes database data
- returns JSON responses

The backend is written in Python using FastAPI.

## 20. What Is FastAPI?

FastAPI is a Python framework for building web APIs.

It provides:

- route decorators such as `@router.post()`
- automatic request validation
- response serialization
- dependency injection
- HTTP error handling
- generated API documentation

Example:

```python
@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_for_authenticated_user(...):
    ...
```

## 21. What Is Uvicorn?

FastAPI defines the application. Uvicorn is the ASGI server that runs it and listens for HTTP requests.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Meaning:

- `app.main`: import `backend/app/main.py`
- `:app`: use the object named `app`
- `--reload`: restart after source changes during development

## 22. What Is `.venv`?

`.venv` is a Python virtual environment dedicated to this project.

It isolates project packages from system Python and other projects.

Benefits:

- avoids version conflicts
- supports reproducible setup
- prevents global Python pollution

## 23. What Is `requirements.txt`?

`backend/requirements.txt` records installed Python packages and versions.

Install them using:

```powershell
pip install -r requirements.txt
```

Core directly relevant packages include:

- `fastapi`: API framework
- `uvicorn`: application server
- `pydantic`: request/response validation
- `pydantic-settings`: environment settings
- `pymongo`: MongoDB driver
- `argon2-cffi`: password hashing
- `tree-sitter`: AST parser framework
- `tree-sitter-java`: Java grammar
- `scikit-learn`: ML algorithms
- `joblib`: model persistence
- `pandas`: tabular features
- `numpy`: numerical support

The file is a broad environment freeze, so it also contains transitive and development packages such as Jupyter, Matplotlib, HTTP libraries, and their dependencies. Not every listed package is imported directly by the application.

## 24. What Is `.env`?

`.env` contains local configuration and secrets, such as:

```text
MONGODB_URI
MONGODB_DB_NAME
JWT_SECRET
ACCESS_TOKEN_TTL_SECONDS
REFRESH_TOKEN_TTL_SECONDS
```

`config.py` loads these values with `pydantic-settings`.

Secrets should not be committed to Git.

## 25. What Is Pydantic?

Pydantic validates Python data using declared models.

For example, `RegisterRequest` requires valid fields such as a name, email, and password. FastAPI automatically rejects an invalid request before the route's main logic runs.

Pydantic models also define the exact response shape sent back to the extension.

## 26. What Is MongoDB?

MongoDB is a document database. It stores JSON-like documents.

Code Coach stores:

- users
- authentication sessions
- learning sessions
- diagnostics
- learning events
- remediation triggers
- mastery snapshots
- collaboration sessions
- gamification records

`InMemoryStorage` stores equivalent information in Python dictionaries for tests.

## 27. What Are JWT Access and Refresh Tokens?

After login:

- access token: short-lived proof used on normal API requests
- refresh token: longer-lived random token used to request a new access token

The access token contains:

- user ID
- authentication session ID
- role
- token type
- expiry time

It is signed using HMAC SHA-256 and the configured secret.

Passwords are hashed with Argon2. Refresh tokens are hashed with SHA-256 before storage.

# Part III: Folder and File Guide

## 28. Root Project Folders

### `backend/`

Python FastAPI API, analysis pipeline, storage, services, models, and tests.

### `extension/`

VS Code extension written in TypeScript.

### `data/`

Raw Java snippets, metadata, extracted ML features, and dataset splits.

### `knowledge_base/`

Structured JSON content for hints, remediation lessons, games, and collaboration prompts.

### `docs/`

Architecture, API contract, shared model, proposal traceability, and study documentation.

### `logs/`

Optional local anonymized evaluation logs.

### `shared/`

Reserved/shared project material used across the broader Code Guru system.

## 29. Backend Root Files

### `backend/README.md`

Backend setup, environment variables, structure, endpoints, and integration summary.

### `backend/requirements.txt`

Pinned Python dependencies.

### `backend/.env`

Local environment settings and secrets. Do not expose its values.

### `backend/models/`

Nine trained `.joblib` pipelines and `baseline_metrics_v1.csv`.

### `backend/tests/`

- `test_analyzer_requirements.py`: analysis behavior and diagnostic requirements
- `test_phase1_auth_and_persistence.py`: authentication, sessions, and persistence
- `test_phase2_learning_signals.py`: events, mastery, remediation, gamification, collaboration, and dashboard

## 30. `backend/app/main.py`

This is the FastAPI entry point.

### `create_app(storage=None)`

- defines application lifespan
- accepts optional injected storage for tests
- otherwise calls `build_storage()`
- creates FastAPI app
- registers routers
- closes storage when the app stops

Registered route groups:

- auth
- learning sessions
- collaboration
- code coach
- dashboard
- diagnostics
- events
- gamification
- remediation
- users

Direct endpoints:

- `GET /`: simple running message
- `GET /health`: health check
- `POST /analyze`: public/basic analysis route
- `POST /debug-ast`: returns AST text for Java debugging

The authenticated extension normally uses:

```text
POST /api/v1/code-coach/analyze
```

not the basic `/analyze` route.

## 31. `backend/app/models.py`

This is the shared data-contract file.

### Analysis models

- `AnalyzeRequest`: language, code, session ID, logging option
- `HintSet`: concept, guidance, targeted
- `DetectionResult`: internal localized finding
- `Diagnostic`: final issue sent to frontend
- `AnalyzeResponse`: complete analysis response

### Authentication models

- `RegisterRequest`
- `LoginRequest`
- `RefreshRequest`
- `AuthUser`
- `AuthSessionView`
- `TokenBundle`
- `AuthResponse`
- `MeResponse`
- `StatusResponse`

### Learning-session and diagnostic models

- `LearningSessionCreateRequest`
- `LearningSessionResponse`
- `PersistedDiagnosticView`
- `DiagnosticListResponse`

### Event and summary models

- `LearningEventView`
- `LearningEventCreateRequest`
- `LearningEventCreateResponse`
- `DiagnosticSummaryResponse`
- `ConceptStruggleView`
- `ConceptStruggleResponse`
- `ConceptMasteryView`
- `ConceptMasteryListResponse`

### Remediation and Study Guider models

- `RemediationTriggerView`
- `RemediationTriggerListResponse`
- `QuizRecommendationView`
- `MicroLessonRecommendationView`
- `StudyGuiderRecommendationView`
- `LessonOpenedRequest`
- `QuizCompletedRequest`

### Gamification models

- `GamificationRecommendationView`
- `GamificationAdaptationDecisionRequest`
- `GamificationSessionCompletedRequest`
- `GamificationActionResponse`

### Collaboration models

- `CollaborationPromptView`
- `CollaborationSessionView`
- `CollaborationSessionCreateRequest`
- `CollaborationPromptShownRequest`
- `PeerReviewSubmittedRequest`

### Dashboard models

- `DashboardCountsView`
- `DashboardMasterySummaryView`
- `DashboardConceptTrendView`
- `DashboardTimelineItemView`
- `DashboardOverviewResponse`
- `DashboardTimelineResponse`

### Internal dataclasses

- `Span`: source range
- `ParseHealth`: parse quality information
- `ParseResult`: tree, bytes, health, crash flag
- `DiagnosticSyncResult`: active/new/resolved persistence result
- `DetectionCandidate`: detector candidate

## 32. `backend/app/core/`

### `config.py`

`Settings` defines:

- MongoDB URI and database
- JWT secret and algorithm
- access-token lifetime
- refresh-token lifetime

`get_settings()` is cached with `lru_cache`, so settings are not repeatedly loaded.

### `common.py`

- `utcnow()`: returns current UTC datetime
- `generate_prefixed_id(prefix)`: creates IDs such as `user_...`, `auth_...`, and `diagrec_...`

### `security.py`

- `hash_password()`: Argon2 password hash
- `verify_password()`: validates password against hash
- `_base64url_encode()` / `_base64url_decode()`: JWT-safe encoding helpers
- `_json_bytes()`: deterministic JSON bytes
- `_sign()`: HMAC SHA-256 signature
- `_timestamp_after()`: expiry timestamp
- `create_access_token()`: manually builds signed JWT-format access token
- `TokenPayload`: decoded token values
- `TokenError`: invalid-token exception
- `decode_access_token()`: validates format, signature, expiry, and token type
- `create_refresh_token()`: secure random refresh token
- `hash_refresh_token()`: SHA-256 storage hash
- `refresh_token_expiry()`: refresh expiry datetime

### `dependencies.py`

- `AuthContext`: authenticated user/session bundle
- `get_storage()`: retrieves storage from FastAPI app state
- `get_current_auth()`: validates Bearer token, session, and user

Routes use:

```python
auth: AuthContext = Depends(get_current_auth)
```

This is FastAPI dependency injection.

## 33. `backend/app/db/storage.py`

This file abstracts persistence.

### Helper functions

- `_utcnow()`
- `_copy_document()`: deep copy and remove Mongo `_id`
- `_sort_by_created_desc()`
- `_sort_by_last_updated_desc()`

### `InMemoryStorage`

Uses Python dictionaries. It supports tests without MongoDB.

Main responsibilities:

- users
- auth sessions
- learning sessions
- code diagnostics
- learning events
- collaboration sessions
- remediation triggers
- concept mastery

### `MongoStorage`

Implements equivalent operations using MongoDB collections and indexes.

### Important storage behavior

`sync_code_diagnostics()` compares current diagnostics with previous active diagnostics:

- still present -> remain active
- newly present -> newly detected
- no longer present -> resolved

This lets the system know when a learner corrected an issue.

### `build_storage()`

Builds the configured storage implementation. Routes and services call storage methods rather than directly depending on MongoDB, which improves modularity and testability.

## 34. `backend/app/analysis/parser_utils.py`

- `parse_java_code()`: normal Java parse
- `get_node_text()`: source text represented by an AST node
- `collect_nodes_by_type()`: recursively finds all nodes with a type
- `find_first_descendant_by_type()`: recursively finds first matching descendant
- `node_to_span()`: converts zero-based Tree-sitter coordinates to one-based user coordinates
- `inspect_tree_health()`: counts error and missing nodes and calculates completeness
- `parse_java_code_safe()`: catches parser exceptions and always returns `ParseResult`

Completeness formula applies penalties:

```text
0.15 per error node
0.10 per missing node
maximum total penalty = 0.80
```

## 35. `backend/app/analysis/feature_extractor.py`

- `_count_lines()`: source line count
- `_safe_text()`: safe AST node text
- `_max_tree_depth()`: deepest AST level
- `_count_descendants()`: subtree size
- `_has_assignment_inside_condition()`: finds assignment expression
- `_count_logical_operators()`: counts `&&` and `||`
- `_extract_for_loop_features()`: loop-related features
- `_extract_if_features()`: `if`-condition features
- `_extract_array_access_features()`: array-index features
- `_extract_general_ast_features()`: general structure counts
- `extract_features()`: returns complete feature dictionary

## 36. `backend/app/analysis/error_catalog.py` and `ml_engine.py`

### `error_catalog.py`

The single registry for every detectable error type:

- `ErrorTypeSpec`: one error type's full definition (detection mode, locator,
  model file, threshold)
- `ERROR_CATALOG`: dict of all registered error types
- `detection_mode`: `"ml_gated"` (ML model gates the locator) or
  `"rule_only"` (AST locator runs on its own, no model needed)
- `validate_catalog()`: called at app startup; fails loudly if an entry is
  missing its model file or knowledge-base hints

### `ml_engine.py`

- `MLPrediction`: one model's runtime result
- `_LOADED_MODELS`: in-memory cache
- `_get_model()`: load/cache model
- `_build_feature_frame()`: align runtime features with trained columns
- `predict_issue_types()`: produce a probability and decision for every
  ml_gated catalog entry

## 37. `backend/app/analysis/issue_locators.py`

Helpers:

- `_node_line()`
- `_node_column()`
- `_first_line()`
- `_node_text()`
- `_node_context()`
- `_result()`
- `_deduplicate()`

Locators:

- `locate_off_by_one_loop_boundaries()`: finds `for` conditions using `<=` and `.length`
- `locate_incorrect_conditional_operators()`: finds assignment expressions inside `if` or `while`
- `locate_array_length_index_misuses()`: finds direct `array[array.length]`

Each locator is registered against its error type in
`error_catalog.ERROR_CATALOG`.

## 38. `backend/app/analysis/hint_engine.py`

### `ErrorKnowledge`

Contains:

- concept tag
- explanation key
- three hints

### Knowledge source

`knowledge_base/code_coach_errors.json` is the single source of truth for
hints. `validate_catalog()` checks at startup that every registered error
type has an entry; if a lookup still misses, `DEFAULT_ERROR_KNOWLEDGE`
supplies generic hints.

### Functions

- `_load_error_knowledge_base()`: read and validate JSON
- `get_error_knowledge()`: find matching content or default
- `_diagnostic_id_for()`: stable SHA-1-derived diagnostic ID
- `build_diagnostic()`: combine technical finding with pedagogical content

## 39. `backend/app/analysis/analyzer.py`

This orchestrates the analysis pipeline.

- `_safe_predict_issue_types()`: prevents model errors from crashing request
- `_combine_confidence()`: combines ML, locator, and parse quality
- `_finalize_finding()`: enriches finding with detection metadata
- `_detect_for_spec()`: runs one catalog entry (ML-gated or rule-only)
- `analyze_code()`: full parse -> features -> ML -> locator -> hints flow

Files with completeness below `0.35` are suppressed.

## 40. `backend/app/analysis/detectors/`

Files:

- `off_by_one.py`
- `incorrect_conditional_operator.py`
- `array_length_index_misuse.py`

These contain direct deterministic detector functions that return `DetectionCandidate`.

The current main pipeline uses `ml_engine.py` for category decisions and `issue_locators.py` for location. The detector files are supporting/legacy deterministic implementations rather than the central runtime decision path.

## 41. `backend/app/dev_tools/`

### `build_dataset.py`

- reads metadata
- loads Java files
- normalizes metadata
- extracts features
- writes master and binary CSV datasets

### `split_dataset.py`

- reads feature rows
- groups related pairs
- performs stratified train/validation/test allocation
- checks target coverage
- writes split CSVs

### `train_baselines.py`

- builds model pipelines
- trains all target/model combinations
- calculates metrics
- saves `.joblib` models and metrics CSV

### `debug_features.py`

Developer utility for inspecting extracted features from Java examples.

These tools run offline. They are not called for every user request.

## 42. `backend/app/services/`

### `code_coach_service.py`

- `run_analysis()`: language check, analyzer call, duration measurement
- `build_analyze_response()`: constructs API response
- `_code_context_hash()`: hashes code context
- `build_diagnostic_records()`: creates persistence documents

### `evaluation_logger.py`

- hashes identifiers and context
- writes optional anonymized analysis logs
- only logs when enabled

### `learning_signal_service.py`

- builds learning event documents
- creates detected/resolved diagnostic events
- calculates diagnostic summaries
- calculates hint dependency
- calculates concept struggle scores and levels

### `mastery_service.py`

- converts scores to mastery levels
- builds/upserts mastery documents
- serializes mastery responses

### `remediation_service.py`

- creates remediation triggers from high struggle
- records lesson opened
- records quiz completion
- updates events and mastery
- synchronizes Code Coach struggles with remediation

### `study_guider_service.py`

- loads lesson/quiz content
- maps triggers to recommendations
- assigns priority and rationale

### `gamification_service.py`

- loads game content
- chooses difficulty, support, priority, and goals
- builds recommendations from struggle/mastery
- records adaptation decisions
- records completed game sessions
- updates mastery

### `collaboration_service.py`

- loads collaboration prompt content
- combines diagnostics, struggle, and mastery
- creates pair-programming prompts
- records pair sessions, prompt views, and peer reviews

### `dashboard_service.py`

- converts events into timeline items
- summarizes counts and mastery
- builds concept trends
- chooses recommended focus
- builds overview and timeline responses

## 43. `backend/app/api/routes/`

Routes are the HTTP/controller layer. They validate ownership and call services/storage.

### `auth.py`

Endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

Main methods:

- `_normalize_email()`
- `_serialize_user()`
- `_serialize_auth_session()`
- `_create_session_and_tokens()`
- `_auth_response()`
- `register()`
- `login()`
- `me()`
- `refresh()`
- `logout()`

### `learning_sessions.py`

Endpoints:

- `POST /api/v1/learning-sessions`
- `GET /api/v1/learning-sessions/{id}`
- `GET /api/v1/learning-sessions/{id}/diagnostics`

It creates or reuses an active learning session and enforces ownership.

### `code_coach.py`

Endpoint:

```text
POST /api/v1/code-coach/analyze
```

`analyze_for_authenticated_user()`:

1. requires a learning-session ID
2. checks ownership and active status
3. runs analysis
4. builds database records
5. syncs active/resolved diagnostics
6. creates learning events
7. syncs remediation triggers
8. touches session timestamp
9. optionally logs evaluation data
10. returns response

### `diagnostics.py`

Lists authenticated user's persisted diagnostics.

### `events.py`

Creates and lists learning events.

### `users.py`

Returns:

- diagnostic summary
- concept struggles
- mastery

### `remediation.py`

Returns triggers/recommendations and records lessons/quizzes.

### `gamification.py`

Returns recommendations and records decisions/session results.

### `collaboration.py`

Returns prompts and records pair sessions, prompt displays, and peer reviews.

### `dashboard.py`

Returns cross-component overview and learning timeline.

## 44. Knowledge-Base Files

### `knowledge_base/code_coach_errors.json`

Maps each target error to:

- concept tag
- explanation key
- concept hint
- guidance hint
- targeted hint

### `knowledge_base/study_guider_lessons.json`

Micro-lesson and quiz recommendation content.

### `knowledge_base/gamification_catalog.json`

Game types and concept-specific recommendation content.

### `knowledge_base/collaboration_prompts.json`

Pair-programming and peer-review prompts.

# Part IV: VS Code Extension

## 45. Extension Root Files

### `package.json`

Extension manifest. It defines:

- extension name/version
- VS Code version
- activation events
- activity-bar view
- commands
- settings
- walkthrough
- compile/lint/test scripts

### `package-lock.json`

Locks exact Node dependency versions.

### `tsconfig.json`

TypeScript compiler settings.

### `eslint.config.mjs`

Code-quality/lint rules.

### `media/`

Extension icons and walkthrough images.

### `out/`

Compiled JavaScript generated from TypeScript.

### `node_modules/`

Installed Node/extension development packages.

## 46. `src/constants.ts`

Defines:

- secret-storage keys
- global/workspace-state keys
- client name
- `DEBOUNCE_DELAY_MS = 900`

## 47. `src/types.ts`

TypeScript versions of backend response/request types:

- hints
- diagnostics
- analysis response
- auth user/session/token
- learning session
- events
- panel state
- extension shared state

`ApiError` stores HTTP status code.

`ExtensionState` is shared mutable state passed to extension modules.

## 48. `src/api.ts`

- `getBackendUrl()`: setting or default localhost URL
- `isEvaluationLoggingEnabled()`: reads extension setting
- `headersToRecord()`: normalizes headers
- `extractErrorMessage()`: reads FastAPI error body
- `requestJson()`: basic fetch + JSON
- `refreshAuthSession()`: refresh-token flow
- `authorizedRequestJson()`: adds Bearer token; retries once after 401 refresh
- `clearLearningSession()`: clears workspace session
- `clearStoredAuthState()`: deletes tokens/user/diagnostics
- `storeAuthResponse()`: securely saves tokens and user

Access and refresh tokens are stored in VS Code SecretStorage, not normal settings.

## 49. `src/auth.ts`

- `promptValue()`: reusable VS Code input box
- `createAccount()`: gather fields and register
- `signIn()`: gather credentials and login
- `signOut()`: backend logout plus local cleanup
- `restoreAuthSession()`: validate stored token using `/auth/me`
- `ensureAuthenticated()`: guarantee login before analysis
- `ensureLearningSession()`: create/reuse backend learning session
- `createLearningEvent()`: send event API request
- `trackLearningEvent()`: fire-and-forget event helper

## 50. `src/extension.ts`

Main extension entry point.

### `activate(context)`

Creates shared state:

- current user/session
- diagnostic maps
- timers
- output channel
- diagnostic collection
- warning decoration
- status bars

Registers:

- sidebar webview
- CodeLens provider
- code-action provider
- commands
- document/editor listeners

Commands:

- Start
- Sign In
- Create Account
- Sign Out
- Analyze Current File
- Open Coach Panel
- Previous Hint
- Next Hint
- Show CodeLens Hint
- Welcome Guide

Event listeners:

- `onDidChangeTextDocument`: schedule analysis after keystroke
- `onDidChangeActiveTextEditor`: analyze newly active editor
- `onDidCloseTextDocument`: clear feedback

### `deactivate()`

Empty because registered disposables are managed through `context.subscriptions`.

## 51. `src/analysis.ts`

### Range and feedback

- `createRangeFromDiagnostic()`: backend line/column to VS Code range
- `severityFromDiagnostic()`: backend severity to VS Code severity
- `clearTimerForUri()`: cancel old debounce
- `clearEditorFeedback()`
- `clearFeedbackForDocument()`
- `applyEditorFeedback()`: diagnostics and decorations

### Hint behavior

- `focusDiagnostic()`: move cursor/reveal issue
- `hintTextForLevel()`: choose concept/guidance/targeted text
- `showHintAtIndex()`: display hint and track event
- `showHintForActiveEditor()`: previous/next navigation
- `navigatePanelHint()`: silent panel navigation

### API and output

- `writeAnalysisOutput()`: output-channel details
- `requestAnalyze()`: authenticated `/api/v1/code-coach/analyze`
- `runAnalysisForEditor()`: complete frontend analysis operation
- `openCoachPanelFromState()`: delegates panel command

### Automatic analysis

`scheduleAutoAnalysis()`:

1. verifies Java document
2. cancels previous timer
3. starts a new 900 ms timer
4. analyzes only after no newer keystroke resets the timer

This is debounce.

The implementation sends the full current document snapshot after the pause. It is not true edit-delta incremental parsing.

## 52. `src/ui/statusBar.ts`

- `formatDuration()`
- `isSupportedDocument()`: returns true when VS Code identifies the document language as Java
- `updateAuthStatusBar()`
- `updateAnalysisStatusBar()`

## 53. `src/ui/decorations.ts`

- `createWarningDecorationType()`: visual warning style
- `buildHoverMarkdown()`: rich hover with diagnostics/hints
- `buildDecorationOptions()`: decoration ranges and hover content

## 54. `src/ui/panelHtml.ts`

- `escapeHtml()`: prevents unsafe HTML injection
- `formatProbability()`
- `getCoachPanelState()`: derives current panel data
- `buildCoachPanelHtml()`: generates panel UI
- `updateCoachPanel()`: refreshes panel and sidebar

Panel states:

- not signed in
- no Java file
- ready to analyze
- no issues
- active issue with hints

## 55. `src/ui/sidebarProvider.ts`

`CoachSidebarProvider` implements VS Code's `WebviewViewProvider`.

It:

- creates activity-bar sidebar HTML
- enables scripts
- handles sign-in, analyze, navigation, and output messages
- refreshes when state changes

## 56. `src/ui/codeLensProvider.ts`

`CoachCodeLensProvider` adds clickable hint actions above diagnostic lines.

It:

- reads current diagnostics
- creates concept/guidance/targeted hint links
- refreshes when diagnostics change

## 57. `src/ui/codeActionProvider.ts`

`CoachCodeActionProvider` adds actions to the VS Code lightbulb/quick-fix interface.

It exposes hint and panel commands for Code Coach diagnostics.

## 58. `src/test/extension.test.ts`

Extension-side automated test entry.

## 59. `src/sample-java/`

Manual test programs representing the three supported issue categories.

# Part V: Full User Keystroke-to-Feedback Flow

## 60. Step-by-Step Flow

### Step 1: User presses a key

VS Code emits:

```text
onDidChangeTextDocument
```

`extension.ts` verifies that:

- there is an active editor
- changes are not empty
- changed document is the active document

Then it calls:

```text
scheduleAutoAnalysis(state, editor)
```

### Step 2: Debounce

`analysis.ts` cancels the old timer for that file and starts a new 900 ms timer.

If the user presses another key before 900 ms, the timer resets.

After the user pauses:

```text
runAnalysisForEditor(..., showPopup=false, showOutput=false)
```

### Step 3: Frontend validation

The extension checks:

- is this a supported Java document?
- is the user authenticated?
- is the file non-empty?

If not authenticated, silent auto-analysis stops. Manual analysis can prompt sign-in.

### Step 4: Ensure learning session

`ensureLearningSession()` sends:

```text
POST /api/v1/learning-sessions
```

The backend creates or reuses an active Java learning session and returns its ID.

### Step 5: Build request

The extension reads:

```typescript
document.getText()
```

It sends:

```json
{
  "language": "java",
  "code": "full current Java document",
  "learning_session_id": "ls_...",
  "enable_logging": false
}
```

to:

```text
POST /api/v1/code-coach/analyze
```

with:

```text
Authorization: Bearer <access token>
Content-Type: application/json
```

### Step 6: Token handling

`authorizedRequestJson()` adds the access token.

If backend returns `401`:

1. extension sends refresh token to `/api/v1/auth/refresh`
2. stores new access/refresh tokens
3. retries original request once

### Step 7: FastAPI routing and validation

FastAPI:

- parses JSON into `AnalyzeRequest`
- validates field types
- runs `get_current_auth()`

`get_current_auth()`:

- validates Bearer scheme
- verifies token signature and expiry
- checks auth session is active
- checks session matches user
- checks user is active

### Step 8: Learning-session authorization

`code_coach.py` checks:

- learning-session ID exists
- session belongs to authenticated user
- session is active

### Step 9: Run analysis service

`run_analysis()` starts a timer and calls:

```text
analyze_code(payload.code)
```

### Step 10: Parse Java

`parse_java_code_safe()`:

- encodes source as UTF-8 bytes
- parses with Tree-sitter Java
- inspects error/missing nodes
- returns `ParseResult`

If parser crashes or completeness is below `0.35`, analyzer returns no diagnostics.

### Step 11: Extract features

`extract_features()` parses and converts code structure into numeric values.

### Step 12: Predict categories

`predict_issue_types()`:

- loads three Logistic Regression pipelines
- aligns features
- calls `predict_proba()`
- compares each result with `0.65`

### Step 13: Locate positive issues

For each positive category:

```text
ERROR_CATALOG[error_type].locator(parse_result)
```

The locator finds exact AST node, line, column, and code context.

If ML predicts positive but locator cannot find the pattern, no diagnostic is returned for that prediction.

### Step 14: Calculate confidence

Analyzer combines:

- 80% ML probability
- 20% locator confidence
- parse completeness multiplier

### Step 15: Attach hints

`build_diagnostic()`:

- generates stable diagnostic ID
- loads concept information
- attaches three hint levels
- returns final `Diagnostic`

### Step 16: Persist and synchronize

The authenticated route:

- converts diagnostics to storage records
- syncs active/resolved state
- creates detected/resolved learning events
- recalculates/synchronizes remediation triggers
- updates session last-analysis time
- optionally writes anonymized evaluation log

### Step 17: Build response

`build_analyze_response()` returns:

```json
{
  "status": "ok",
  "message": "Analysis completed.",
  "timestamp": "...",
  "analysis_duration_ms": 12.34,
  "learning_session_id": "ls_...",
  "diagnostics": [
    {
      "diagnostic_id": "cc_...",
      "error_type": "OFF_BY_ONE_LOOP_BOUNDARY",
      "line": 5,
      "column": 21,
      "confidence": 0.86,
      "detection_engine": "ml_gated_ast_locator",
      "ml_probability": 0.84,
      "locator_confidence": 0.95,
      "hints": {
        "concept": "...",
        "guidance": "...",
        "targeted": "..."
      }
    }
  ]
}
```

### Step 18: Extension receives response

`runAnalysisForEditor()` stores an analysis snapshot.

If there are no diagnostics:

- clear old diagnostics/decorations
- preserve snapshot
- update panel and status

If diagnostics exist:

- convert each to VS Code range
- create VS Code diagnostics
- add warning decorations and hover
- refresh CodeLens
- refresh Coach Panel
- update status bar

Manual analysis also displays progress and popups. Auto-analysis runs silently.

## 61. Complete Flow to Memorize

```text
Keystroke
-> onDidChangeTextDocument
-> 900 ms debounce
-> runAnalysisForEditor
-> ensureAuthenticated
-> ensureLearningSession
-> authorizedRequestJson
-> POST /api/v1/code-coach/analyze
-> FastAPI AnalyzeRequest validation
-> get_current_auth
-> learning-session ownership check
-> code_coach_service.run_analysis
-> analyzer.analyze_code
-> parser_utils.parse_java_code_safe
-> feature_extractor.extract_features
-> ml_engine.predict_issue_types
-> issue_locators find line/column
-> analyzer combines confidence
-> hint_engine.build_diagnostic
-> storage.sync_code_diagnostics
-> learning events and remediation sync
-> AnalyzeResponse JSON
-> extension applyEditorFeedback
-> warning, hover, CodeLens, panel, status bar
```

# Part VI: Viva Answers

## 62. Explain the Architecture in One Minute

> Code Coach has a TypeScript VS Code extension and a Python FastAPI backend. The extension observes Java document changes and uses a 900 millisecond debounce before sending the full current file to an authenticated analysis endpoint. The backend validates the JWT and learning session, parses Java using Tree-sitter, extracts AST-based numeric features, and uses three scikit-learn Logistic Regression models to estimate the probability of the three target error categories. Predictions above 0.65 are passed to deterministic AST locators that identify the exact line and column. The analyzer combines ML probability, locator confidence, and parse completeness. The hint engine attaches concept, guidance, and targeted hints from a JSON knowledge base. The backend then synchronizes active and resolved diagnostics, creates learning signals for the wider Code Guru platform, and returns JSON. The extension displays the results as VS Code diagnostics, decorations, hovers, CodeLens actions, and Coach Panel content.

## 63. Why Use ML and AST Together?

> ML decides whether the overall feature pattern resembles a target error. AST logic provides reliable structural localization. This gives probabilistic classification together with deterministic source positions.

## 64. Does the Project Use Sigmoid?

> Yes, indirectly. The runtime uses scikit-learn Logistic Regression. Logistic Regression uses sigmoid internally, and the application reads the positive-class probability using `predict_proba(x)[0][1]`.

## 65. Does Scikit-learn Use a Perceptron Here?

> No. Scikit-learn provides many algorithms, but this runtime loads Logistic Regression models. A Perceptron is a different linear classifier and does not normally provide the calibrated probability used here.

## 66. Is This Deep Learning?

> No. It is traditional supervised machine learning using engineered AST features and scikit-learn Logistic Regression at runtime. CNN, RNN, GAN, and Transformer models are not used.

## 67. Is Parsing Incremental?

> Tree-sitter supports incremental parsing as a technology, but this implementation currently sends and parses the full document snapshot after a 900 millisecond debounce. True edit-delta incremental parsing is not implemented.

## 68. Why Three Hint Levels?

> The system is designed for learning rather than answer generation. Concept hints explain the idea, guidance narrows the area, and targeted hints become more specific without returning a complete corrected program.

## 69. Why Store Diagnostics?

> Persistence allows the system to detect newly introduced and resolved issues, calculate repeated struggles, measure hint use, trigger remediation, update mastery, and share learning signals with other Code Guru components.

## 70. What You Should Study First

Recommended order:

1. Section 60: full keystroke flow
2. Sections 14-17: runtime ML and confidence
3. Sections 30-43: backend files
4. Sections 46-57: extension files
5. Sections 62-69: viva answers

The central idea to remember is:

```text
ML classifies the issue category.
AST locates it.
The hint engine teaches it.
The backend records learning progress.
The extension presents it inside VS Code.
```
