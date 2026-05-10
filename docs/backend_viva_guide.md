# Code Coach Backend Viva Guide

This guide explains the backend from the beginning, excluding the ML data extraction, splitting, and training parts that you already know.

## 1. Big Picture

Code Coach has two main sides:

- VS Code extension: the user interface inside VS Code.
- FastAPI backend: the local/server API that receives code, analyzes it, stores results, and returns beginner-friendly feedback.

The backend is responsible for:

- user registration, login, refresh token, and logout
- learning session creation
- Java code analysis
- diagnostic generation
- diagnostic persistence
- learning event creation
- concept struggle calculation
- remediation trigger creation
- Study Guider recommendations
- gamification recommendations and result recording
- collaboration prompts and peer review recording
- dashboard overview and timeline data

The current analysis pipeline is:

```text
User writes Java code in VS Code
-> extension waits briefly using debounce
-> extension sends current Java file text to backend
-> backend validates the user token
-> backend checks the learning session
-> backend parses Java with Tree-sitter
-> backend extracts AST features
-> ML models predict likely target issue categories
-> AST locators find exact line/column only for ML-positive categories
-> hint engine attaches concept/guidance/targeted hints
-> backend stores diagnostics and learning events
-> backend returns JSON response to extension
-> extension displays warnings, hints, panel data, and status
```

## 2. Basic Terms You Must Know

### What is a backend?

The backend is the server-side part of the system. It receives requests, performs logic, talks to storage/database, and sends responses. In Code Coach, the backend is written in Python.

### What is FastAPI?

FastAPI is a Python web framework used to build APIs. An API is a set of endpoints that other programs can call. For example:

```text
POST /api/v1/code-coach/analyze
```

The VS Code extension calls this endpoint to analyze code.

FastAPI is useful because:

- it is fast and lightweight
- it automatically validates request bodies using Pydantic models
- it generates API documentation
- it supports dependency injection, such as injecting the current user or storage

### What is Uvicorn?

Uvicorn is the server that runs the FastAPI app. FastAPI defines the app; Uvicorn serves it over HTTP.

Typical command:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Meaning:

- `app.main` means `backend/app/main.py`
- `app` means the FastAPI app object inside that file
- `--reload` restarts the server automatically during development

### What is a virtual environment / `.venv`?

`.venv` is a private Python environment for this project. It keeps this project's packages separate from the global Python installation.

Why it matters:

- avoids package version conflicts
- makes the project reproducible
- lets the backend use exact versions from `requirements.txt`

### What is `requirements.txt`?

`requirements.txt` lists Python packages needed by the backend. Running this installs the dependencies:

```powershell
pip install -r requirements.txt
```

Important packages in this project:

- `fastapi`: API framework
- `uvicorn`: runs the FastAPI server
- `pydantic`: validates request and response data
- `pydantic-settings`: loads settings from environment variables
- `python-dotenv`: reads `.env` files
- `pymongo`: connects to MongoDB
- `argon2-cffi`: password hashing
- `tree-sitter` and `tree-sitter-java`: parses Java code into AST
- `scikit-learn`: ML model runtime
- `joblib`: loads saved ML models
- `pandas` and `numpy`: data/model support
- `requests` / `httpx`: HTTP client utilities
- `jupyter`, `matplotlib`: experiment and analysis support

### What is `.env`?

`.env` stores local configuration secrets. Example values come from `backend/.env.example`:

```text
MONGODB_URI=...
MONGODB_DB_NAME=code-guru
JWT_SECRET=...
ACCESS_TOKEN_TTL_SECONDS=3600
REFRESH_TOKEN_TTL_SECONDS=604800
```

You do not hard-code secrets in source code. The backend reads them through `core/config.py`.

### What is JWT?

JWT means JSON Web Token. After login, the backend gives the extension an access token. The extension sends it with later requests. The backend checks this token to know which user is making the request.

### What is Pydantic?

Pydantic defines request and response models. For example, `AnalyzeRequest` says an analyze request must contain fields such as `language`, `code`, and `learning_session_id`.

### What is MongoDB?

MongoDB is the database used for persistent storage. It stores users, sessions, diagnostics, events, mastery, remediation triggers, collaboration sessions, and similar documents.

The project also has `InMemoryStorage` for tests, so tests can run without a real MongoDB database.

## 3. Backend Folder Structure

```text
backend/
  app/
    main.py
    models.py
    core/
    db/
    analysis/
    api/routes/
    services/
    dev_tools/
  models/
  tests/
  requirements.txt
  .env.example
```

The clean way to explain it in viva:

> `api/routes` receives HTTP requests. `services` contains business logic. `analysis` contains code-analysis logic. `db` stores and retrieves data. `core` contains common infrastructure such as config, auth dependencies, and security. `models.py` defines the data contracts shared across the backend.

## 4. Full Request Flow: Analyze Code

This is the most important viva flow.

### Step 1: User action in VS Code

The user opens a Java file and runs analysis, or auto-analysis runs after typing stops briefly.

The extension sends:

```json
{
  "language": "java",
  "code": "public class Test { ... }",
  "learning_session_id": "ls_xxx",
  "enable_logging": false
}
```

to:

```text
POST /api/v1/code-coach/analyze
```

### Step 2: FastAPI receives the request

File:

```text
backend/app/api/routes/code_coach.py
```

Function:

```python
analyze_for_authenticated_user()
```

It does four main checks:

- Is the user authenticated?
- Did the request include `learning_session_id`?
- Does the session belong to the logged-in user?
- Is the session active?

If any check fails, FastAPI returns an error like `401`, `404`, or `409`.

### Step 3: Service runs the analyzer

File:

```text
backend/app/services/code_coach_service.py
```

Function:

```python
run_analysis()
```

It calls:

```python
analyze_code(payload.code)
```

and measures how long analysis took in milliseconds.

### Step 4: Analyzer pipeline

File:

```text
backend/app/analysis/analyzer.py
```

Function:

```python
analyze_code()
```

It performs:

1. Parse Java safely.
2. Reject crashed or very incomplete parse results.
3. Extract features.
4. Ask ML engine to predict target issue types.
5. For each positive ML prediction, use AST locator to find exact location.
6. Build final diagnostic with hints.
7. Sort diagnostics by confidence.

### Step 5: Parser

File:

```text
backend/app/analysis/parser_utils.py
```

Important function:

```python
parse_java_code_safe()
```

It parses Java using Tree-sitter and returns:

- syntax tree
- source bytes
- parse health
- whether parsing crashed

`inspect_tree_health()` checks if the parse contains error or missing nodes. This helps the backend avoid bad feedback when the student is still typing incomplete code.

### Step 6: Feature extraction

File:

```text
backend/app/analysis/feature_extractor.py
```

Important function:

```python
extract_features()
```

It creates numeric features such as:

- number of lines
- AST node count
- parse completeness
- number of `for` statements
- whether loop condition uses `.length`
- whether loop condition uses `<=`
- assignment inside `if` condition count
- array access count
- direct `array.length` index usage count

### Step 7: ML prediction

File:

```text
backend/app/analysis/ml_engine.py
```

Important function:

```python
predict_issue_types()
```

It loads trained `.joblib` models and predicts probabilities for:

- `OFF_BY_ONE_LOOP_BOUNDARY`
- `INCORRECT_CONDITIONAL_OPERATOR`
- `ARRAY_LENGTH_INDEX_MISUSE`

Important point:

> ML decides whether the issue type is likely present. It does not directly find the line number.

### Step 8: AST localization

File:

```text
backend/app/analysis/issue_locators.py
```

Important functions:

- `locate_off_by_one_loop_boundaries()`
- `locate_incorrect_conditional_operators()`
- `locate_array_length_index_misuses()`

These functions search the AST for the exact source location after ML says the category is positive.

This is why the implementation is called:

```text
ml_gated_ast_locator
```

### Step 9: Hint generation

File:

```text
backend/app/analysis/hint_engine.py
```

Important function:

```python
build_diagnostic()
```

It loads hint templates from:

```text
knowledge_base/code_coach_errors.json
```

Then it creates the final diagnostic containing:

- diagnostic ID
- error type
- line and column
- confidence
- message
- code context
- concept tag
- explanation key
- detection engine
- ML probability
- locator confidence
- concept hint
- guidance hint
- targeted hint

### Step 10: Save diagnostics and events

Back in:

```text
backend/app/api/routes/code_coach.py
```

The backend converts diagnostics to database records using:

```python
build_diagnostic_records()
```

Then storage syncs diagnostics:

```python
storage.sync_code_diagnostics()
```

This marks old diagnostics as resolved and current diagnostics as active.

Then it creates learning events:

```python
build_code_coach_learning_events()
```

These events help the rest of Code Guru understand student progress.

### Step 11: Remediation trigger sync

The backend calls:

```python
sync_code_coach_remediation_triggers()
```

If the student repeatedly struggles with a concept, the system can create remediation triggers for Study Guider.

### Step 12: JSON response returned

The backend returns an `AnalyzeResponse`:

```json
{
  "status": "ok",
  "message": "Analysis completed.",
  "timestamp": "...",
  "analysis_duration_ms": 25.4,
  "learning_session_id": "ls_xxx",
  "diagnostics": [...]
}
```

The extension displays the result in VS Code.

## 5. File-by-File Explanation

## Root Backend Files

### `backend/requirements.txt`

Lists all Python packages required by the backend.

In viva:

> This file makes the backend reproducible. Any developer can install the same dependencies by running `pip install -r requirements.txt`.

### `backend/.env.example`

Shows required environment variables without exposing real secrets.

Fields:

- `MONGODB_URI`: MongoDB connection string
- `MONGODB_DB_NAME`: database name
- `JWT_SECRET`: secret used to sign access tokens
- `ACCESS_TOKEN_TTL_SECONDS`: access token lifetime
- `REFRESH_TOKEN_TTL_SECONDS`: refresh token lifetime

### `backend/app/__init__.py`

Marks `app` as a Python package.

It can be empty. Its job is to allow imports like:

```python
from app.main import app
```

## Main Application

### `backend/app/main.py`

Purpose:

- creates the FastAPI app
- initializes storage during app lifespan
- registers all routers
- provides simple root, health, public analyze, and debug AST endpoints

Important function:

```python
create_app(storage=None)
```

Why `storage=None`?

- In real running mode, it builds MongoDB or in-memory storage from settings.
- In tests, we can inject `InMemoryStorage`.

Registered routers:

- auth
- learning sessions
- code coach
- diagnostics
- events
- users
- remediation
- gamification
- collaboration
- dashboard

Important endpoints:

- `GET /`: confirms backend is running
- `GET /health`: health check
- `POST /analyze`: unauthenticated analysis route, useful for basic/local testing
- `POST /debug-ast`: returns Tree-sitter AST text for debugging

## Shared Data Models

### `backend/app/models.py`

Purpose:

- defines request and response structures
- defines database view models
- defines analysis models
- keeps API contracts consistent

Main model groups:

Analyze models:

- `AnalyzeRequest`: request body for code analysis
- `HintSet`: concept/guidance/targeted hints
- `DetectionResult`: internal raw detection before final diagnostic
- `Diagnostic`: final diagnostic returned to frontend
- `AnalyzeResponse`: full API response

Auth models:

- `RegisterRequest`
- `LoginRequest`
- `RefreshRequest`
- `AuthUser`
- `AuthSessionView`
- `TokenBundle`
- `AuthResponse`
- `MeResponse`
- `StatusResponse`

Learning session and diagnostics:

- `LearningSessionCreateRequest`
- `LearningSessionResponse`
- `PersistedDiagnosticView`
- `DiagnosticListResponse`

Learning events and summaries:

- `LearningEventCreateRequest`
- `LearningEventView`
- `DiagnosticSummaryResponse`
- `ConceptStruggleView`
- `ConceptMasteryView`

Remediation:

- `RemediationTriggerView`
- `StudyGuiderRecommendationView`
- `LessonOpenedRequest`
- `QuizCompletedRequest`

Gamification:

- `GamificationRecommendationView`
- `GamificationAdaptationDecisionRequest`
- `GamificationSessionCompletedRequest`

Collaboration:

- `CollaborationPromptView`
- `CollaborationSessionCreateRequest`
- `CollaborationPromptShownRequest`
- `PeerReviewSubmittedRequest`

Dashboard:

- `DashboardOverviewResponse`
- `DashboardTimelineResponse`

Parser/analysis dataclasses:

- `Span`
- `ParseHealth`
- `ParseResult`
- `DiagnosticSyncResult`
- `DetectionCandidate`

Viva answer:

> `models.py` is the contract layer. It defines what data enters and leaves the backend.

## Core Package

### `backend/app/core/config.py`

Purpose:

- loads environment variables
- gives app-wide settings

Important class:

```python
Settings
```

Important function:

```python
get_settings()
```

It reads values such as:

- MongoDB URI
- database name
- JWT secret
- token expiry durations

### `backend/app/core/security.py`

Purpose:

- password hashing
- password checking
- access token creation
- access token decoding
- refresh token creation
- refresh token hashing

Important functions:

- `hash_password()`: stores password securely using Argon2
- `verify_password()`: checks login password
- `create_access_token()`: creates JWT-like signed access token
- `decode_access_token()`: verifies and reads token
- `create_refresh_token()`: creates random refresh token
- `hash_refresh_token()`: stores refresh token safely as hash
- `refresh_token_expiry()`: calculates expiry time

Important classes:

- `TokenPayload`: decoded token data
- `TokenError`: error when token is invalid

Viva answer:

> Passwords and refresh tokens are not stored in plain text. Passwords are hashed with Argon2 and refresh tokens are stored as hashes.

### `backend/app/core/dependencies.py`

Purpose:

- provides reusable FastAPI dependencies

Important class:

```python
AuthContext
```

It stores:

- user ID
- auth session ID
- user document
- auth session document

Important functions:

- `get_storage()`: returns storage object from app state
- `get_current_auth()`: reads `Authorization: Bearer <token>`, validates it, finds user/session, and returns `AuthContext`

Viva answer:

> This file protects endpoints. Routes that require login use `Depends(get_current_auth)`.

### `backend/app/core/common.py`

Purpose:

- small reusable helpers

Functions:

- `utcnow()`: current UTC time
- `generate_prefixed_id(prefix)`: creates IDs like `user_xxx`, `ls_xxx`, `diag_xxx`

## Database Layer

### `backend/app/db/storage.py`

Purpose:

- abstracts database operations
- provides both in-memory and MongoDB implementations

Classes:

```python
InMemoryStorage
MongoStorage
```

`InMemoryStorage`:

- stores data in Python dictionaries
- used mainly for tests
- no external database required

`MongoStorage`:

- stores data in MongoDB collections
- used in real/backend running mode when MongoDB URI exists

Important operations:

- create/find users
- create/revoke auth sessions
- create/find learning sessions
- sync diagnostics
- list diagnostics
- create learning events
- list events
- upsert remediation triggers
- update mastery
- create collaboration sessions
- store gamification records

Important function:

```python
build_storage()
```

It decides whether to use MongoDB or in-memory storage based on configuration.

Viva answer:

> Routes and services do not directly talk to MongoDB. They call storage methods. This keeps the system testable and modular.

## Analysis Package

### `backend/app/analysis/parser_utils.py`

Purpose:

- parse Java code using Tree-sitter
- inspect parse health
- provide AST helper functions

Functions:

- `parse_java_code()`: parses Java and returns tree/source bytes
- `get_node_text()`: extracts original source text for an AST node
- `collect_nodes_by_type()`: finds all AST nodes of a given type
- `find_first_descendant_by_type()`: finds first child node of a type
- `node_to_span()`: converts AST node position to line/column span
- `inspect_tree_health()`: counts parser error/missing nodes
- `parse_java_code_safe()`: safe wrapper that never crashes the analyzer

### `backend/app/analysis/feature_extractor.py`

Purpose:

- convert Java code into numeric features for ML prediction

Main function:

```python
extract_features()
```

Helper functions:

- `_count_lines()`
- `_safe_text()`
- `_max_tree_depth()`
- `_count_descendants()`
- `_has_assignment_inside_condition()`
- `_count_logical_operators()`
- `_extract_for_loop_features()`
- `_extract_if_features()`
- `_extract_array_access_features()`
- `_extract_general_ast_features()`

Viva answer:

> Feature extraction turns code structure into numbers the ML model can understand.

### `backend/app/analysis/ml_engine.py`

Purpose:

- load trained ML models
- run predictions for target issue types

Important class:

```python
MLPrediction
```

Important functions:

- `_get_model()`: loads and caches `.joblib` model
- `_build_feature_frame()`: creates a Pandas row with expected model columns
- `predict_issue_types()`: returns predictions for the three target categories

Current target categories:

- `OFF_BY_ONE_LOOP_BOUNDARY`
- `INCORRECT_CONDITIONAL_OPERATOR`
- `ARRAY_LENGTH_INDEX_MISUSE`

### `backend/app/analysis/issue_locators.py`

Purpose:

- find exact line and column after ML says an issue category is likely

Important functions:

- `locate_off_by_one_loop_boundaries()`
- `locate_incorrect_conditional_operators()`
- `locate_array_length_index_misuses()`
- `_deduplicate()`
- `_result()`

Important dictionary:

```python
TARGET_LOCATORS
```

It maps error type to locator function.

Viva answer:

> ML detects likely category. AST locator finds where in the code it appears.

### `backend/app/analysis/hint_engine.py`

Purpose:

- convert a raw finding into a final diagnostic with educational hints

Important class:

```python
ErrorKnowledge
```

Important functions:

- `_load_error_knowledge_base()`: loads JSON hint data
- `get_error_knowledge()`: gets knowledge for an error type
- `_diagnostic_id_for()`: creates stable diagnostic ID from issue data
- `build_diagnostic()`: creates final `Diagnostic`

### `backend/app/analysis/analyzer.py`

Purpose:

- orchestrates the whole analysis pipeline

Important function:

```python
analyze_code()
```

Helper functions:

- `_safe_predict_issue_types()`
- `_combine_confidence()`
- `_prediction_to_localized_result()`
- `_localize_ml_positive_prediction()`

Viva answer:

> `analyzer.py` is the central controller for parsing, feature extraction, ML prediction, localization, and hint generation.

### `backend/app/analysis/detectors/*.py`

These are older/direct AST detector modules:

- `off_by_one.py`
- `incorrect_conditional_operator.py`
- `array_length_index_misuse.py`

They detect patterns directly and return `DetectionCandidate`.

Current main pipeline uses:

```text
ml_engine.py + issue_locators.py
```

So in viva:

> The detector files represent deterministic pattern-detection logic, but the current production analyzer is ML-gated and uses `issue_locators.py` for localization.

## Services Package

Services contain business logic. Routes should stay thin; services do the work.

### `backend/app/services/code_coach_service.py`

Purpose:

- run code analysis
- build API response
- convert diagnostics into database records

Functions:

- `run_analysis()`: calls analyzer and measures duration
- `build_analyze_response()`: wraps diagnostics into response JSON
- `_code_context_hash()`: hashes source context for safer storage
- `build_diagnostic_records()`: converts diagnostics to persistence format

### `backend/app/services/evaluation_logger.py`

Purpose:

- optional anonymized research logging

Functions:

- `_hash_identifier()`: hashes user/session identifiers
- `_context_hash()`: hashes code context
- `log_analysis_event()`: writes anonymized analysis event if enabled

Viva answer:

> Evaluation logging is optional and privacy-aware. It hashes identifiers and context rather than storing raw sensitive data.

### `backend/app/services/learning_signal_service.py`

Purpose:

- turn diagnostics and events into learning signals

Important functions:

- `build_learning_event_document()`: creates an event document
- `build_code_coach_learning_events()`: creates events for newly detected/resolved diagnostics
- `build_diagnostic_summary()`: summarizes user diagnostics
- `build_concept_struggles()`: calculates repeated concept struggles
- `_calculate_hint_dependency_score()`: measures hint dependence
- `_calculate_struggle_score()`: measures struggle severity

Viva answer:

> This service transforms raw activity into educational meaning.

### `backend/app/services/mastery_service.py`

Purpose:

- calculate and present concept mastery

Functions:

- `_mastery_level_for_score()`
- `build_concept_mastery_document()`
- `build_concept_mastery_view()`
- `build_concept_mastery_response()`

Mastery levels help other components understand whether a student is weak, developing, or improving in a concept.

### `backend/app/services/remediation_service.py`

Purpose:

- create and update remediation triggers
- connect Code Coach struggles with Study Guider actions

Functions:

- `build_remediation_trigger_document()`
- `record_micro_lesson_opened()`
- `record_quiz_completed()`
- `sync_code_coach_remediation_triggers()`

When repeated struggle is detected, this service can create a remediation trigger.

### `backend/app/services/study_guider_service.py`

Purpose:

- convert remediation triggers into Study Guider recommendations

Important functions:

- `_load_study_guider_content()`
- `_content_for_concept()`
- `_priority_for_trigger()`
- `_recommendation_id()`
- `_rationale_for_trigger()`
- `build_study_guider_recommendations()`

It reads:

```text
knowledge_base/study_guider_lessons.json
```

### `backend/app/services/gamification_service.py`

Purpose:

- create adaptive game recommendations
- record gamification decisions and results
- update mastery after game sessions

Important functions:

- `build_gamification_recommendations()`
- `record_gamification_adaptation_decision()`
- `record_gamification_session_completed()`

It reads:

```text
knowledge_base/gamification_catalog.json
```

### `backend/app/services/collaboration_service.py`

Purpose:

- create collaboration prompts
- create pair sessions
- record prompt shown events
- record peer reviews

Important functions:

- `build_collaboration_prompts()`
- `create_collaboration_session_document()`
- `record_pair_session_started()`
- `record_collaboration_prompt_shown()`
- `record_peer_review_submitted()`

It reads:

```text
knowledge_base/collaboration_prompts.json
```

### `backend/app/services/dashboard_service.py`

Purpose:

- build dashboard overview
- build timeline

Important functions:

- `build_dashboard_overview()`
- `build_dashboard_timeline()`

Dashboard combines data from:

- diagnostics
- events
- struggles
- mastery
- remediation
- gamification
- collaboration

## API Routes Package

Routes define HTTP endpoints.

### `backend/app/api/routes/auth.py`

Purpose:

- account creation
- login
- current user
- token refresh
- logout

Endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

Important functions:

- `register()`
- `login()`
- `me()`
- `refresh()`
- `logout()`

### `backend/app/api/routes/learning_sessions.py`

Purpose:

- create/reuse a learning session
- get session info
- list diagnostics for a session

Endpoints:

- `POST /api/v1/learning-sessions`
- `GET /api/v1/learning-sessions/{learning_session_id}`
- `GET /api/v1/learning-sessions/{learning_session_id}/diagnostics`

### `backend/app/api/routes/code_coach.py`

Purpose:

- authenticated Code Coach analysis

Endpoint:

- `POST /api/v1/code-coach/analyze`

Most important route for the project.

### `backend/app/api/routes/diagnostics.py`

Purpose:

- list current user's diagnostics

Endpoint:

- `GET /api/v1/diagnostics/me`

### `backend/app/api/routes/events.py`

Purpose:

- create and list learning events

Endpoints:

- `POST /api/v1/events`
- `GET /api/v1/events/me`

Examples of events:

- diagnostic detected
- diagnostic resolved
- hint shown
- hint navigation used
- lesson opened
- quiz completed
- game session completed
- peer review submitted

### `backend/app/api/routes/users.py`

Purpose:

- user-level learning summaries

Endpoints:

- `GET /api/v1/users/me/diagnostic-summary`
- `GET /api/v1/users/me/concept-struggles`
- `GET /api/v1/users/me/mastery`

### `backend/app/api/routes/remediation.py`

Purpose:

- expose remediation triggers
- provide Study Guider recommendations
- record lesson/quiz actions

Endpoints:

- `GET /api/v1/remediation/me/triggers`
- `GET /api/v1/remediation/me/recommendations`
- `POST /api/v1/remediation/me/triggers/{trigger_id}/lesson-opened`
- `POST /api/v1/remediation/me/triggers/{trigger_id}/quiz-completed`

### `backend/app/api/routes/gamification.py`

Purpose:

- provide game recommendations
- record adaptive decisions and completed game sessions

Endpoints:

- `GET /api/v1/gamification/me/recommendations`
- `POST /api/v1/gamification/me/adaptation-decisions`
- `POST /api/v1/gamification/me/session-results`

### `backend/app/api/routes/collaboration.py`

Purpose:

- provide collaboration prompts
- record pair programming sessions
- record prompt shown actions
- record peer reviews

Endpoints:

- `GET /api/v1/collaboration/me/prompts`
- `POST /api/v1/collaboration/me/pair-sessions`
- `POST /api/v1/collaboration/me/prompts/shown`
- `POST /api/v1/collaboration/me/peer-reviews`

### `backend/app/api/routes/dashboard.py`

Purpose:

- provide cross-component overview and timeline

Endpoints:

- `GET /api/v1/dashboard/me/overview`
- `GET /api/v1/dashboard/me/timeline`

## Tests

### `backend/tests/test_analyzer_requirements.py`

Tests the analyzer behavior:

- detects supported issues
- handles incomplete code safely
- returns expected diagnostic structure

### `backend/tests/test_phase1_auth_and_persistence.py`

Tests Phase 1:

- registration
- login
- auth/session handling
- learning sessions
- diagnostics persistence

### `backend/tests/test_phase2_learning_signals.py`

Tests Phase 2:

- learning events
- concept struggles
- hint dependency
- remediation triggers
- Study Guider handoff
- mastery updates
- gamification recommendations/results
- collaboration prompts/sessions/reviews
- dashboard overview/timeline

Run tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## 6. How Authentication Flow Works

### Register

Endpoint:

```text
POST /api/v1/auth/register
```

Flow:

```text
validate request
-> normalize email
-> check duplicate user
-> hash password
-> create user
-> create auth session
-> create access token and refresh token
-> return user and tokens
```

### Login

Endpoint:

```text
POST /api/v1/auth/login
```

Flow:

```text
find user by email
-> verify password hash
-> create auth session
-> return access token and refresh token
```

### Authenticated request

The extension sends:

```text
Authorization: Bearer <access_token>
```

Backend:

```text
get_current_auth()
-> decode token
-> find user
-> find auth session
-> check active status
-> allow route
```

### Refresh

When access token expires:

```text
POST /api/v1/auth/refresh
```

Backend:

```text
hash refresh token
-> find matching auth session
-> check expiry
-> rotate refresh token
-> create new access token
-> return new token bundle
```

## 7. How Learning Sessions Work

A learning session groups Code Coach diagnostics/events for a user's coding activity.

The extension creates or reuses a session before analysis:

```text
POST /api/v1/learning-sessions
```

Then analysis uses that session ID:

```text
POST /api/v1/code-coach/analyze
```

Why this matters:

- diagnostics are tied to a session
- events are tied to a session
- dashboards can show activity
- remediation can know repeated struggles

## 8. What Happens When Code Is Fixed?

During each analysis, backend compares current diagnostics with previously active diagnostics.

If an old diagnostic no longer appears:

```text
status = resolved
```

If a new diagnostic appears:

```text
status = active
```

This is handled by:

```python
storage.sync_code_diagnostics()
```

That is important because the system can measure whether the learner corrected the issue.

## 9. How Code Coach Connects To Other Components

Code Coach does not only show hints. It creates data for the wider Code Guru platform.

### Study Guider

Uses:

- repeated struggles
- remediation triggers
- mastery data

Purpose:

- recommend micro-lessons
- recommend quizzes
- record lesson opened and quiz completed

### Adaptive Gamification

Uses:

- concept struggles
- hint dependency
- mastery score

Purpose:

- recommend game type
- adapt difficulty
- record game results
- update mastery

### Collaborative Studio

Uses:

- active diagnostics
- struggling concepts
- mastery

Purpose:

- create pair programming prompts
- guide peer review
- record collaboration events

### Dashboard

Uses everything:

- diagnostics
- learning events
- mastery
- remediation
- games
- collaboration

Purpose:

- show overview
- show timeline
- recommend focus

## 10. Best Viva Explanation In 60 Seconds

Use this if the panel asks, "Explain your backend."

> The Code Coach backend is a FastAPI-based Python service. The VS Code extension sends Java code to the backend through an authenticated API request. The backend first validates the user's JWT token and checks the active learning session. Then the analysis service parses the Java code using Tree-sitter, extracts AST-based features, and sends those features to scikit-learn models. The ML models predict whether one of the three target beginner error categories is present. If a prediction passes the threshold, AST locator functions find the exact line and column. Then the hint engine maps the diagnostic to concept, guidance, and targeted hints from the knowledge base. The backend stores active and resolved diagnostics, creates learning events, updates learning signals, creates remediation triggers if needed, and returns a structured JSON response to the extension. This design separates API routing, business logic, analysis logic, storage, and shared models, which makes the system modular and testable.

## 11. Common Panel Questions And Good Answers

### Why FastAPI?

FastAPI is lightweight, fast, and supports automatic request validation using Pydantic. It is suitable for JSON APIs between the VS Code extension and backend.

### Why Tree-sitter?

Tree-sitter gives an AST for Java code and can handle partially incomplete code better than a normal compiler. This is useful because students type incomplete code while learning.

### Why ML plus AST locator?

ML is used to decide whether an issue category is likely present. AST locators are used to find the exact location. This combines flexible prediction with deterministic line/column localization.

### Why not generate corrected code?

The system is educational. It gives scaffolded hints so students learn to self-correct instead of copying the answer.

### Why MongoDB?

The backend stores many document-like records: users, sessions, diagnostics, events, mastery, remediation triggers, and collaboration sessions. MongoDB fits this flexible document structure.

### Why InMemoryStorage?

It makes tests fast and independent from MongoDB. Tests can inject in-memory storage into `create_app()`.

### What is the most important endpoint?

```text
POST /api/v1/code-coach/analyze
```

It runs authenticated code analysis and connects Code Coach to learning signals.

### What are the three current error categories?

- Off-by-one loop boundary
- Incorrect conditional operator
- Array length index misuse

### What is `detection_engine = ml_gated_ast_locator`?

It means ML gates the decision first, then AST locators find the location.

### How does the system avoid outdated diagnostics?

Every new analysis syncs diagnostics. Missing old diagnostics are marked as resolved.

### How does it support other components?

It converts diagnostics into events and concept-level signals. Study Guider, Gamification, Collaboration, and Dashboard use those signals.

## 12. What You Should Memorize

Memorize this flow:

```text
Extension request
-> FastAPI route
-> auth dependency
-> learning session check
-> code_coach_service.run_analysis
-> analyzer.analyze_code
-> parser_utils.parse_java_code_safe
-> feature_extractor.extract_features
-> ml_engine.predict_issue_types
-> issue_locators locate line/column
-> hint_engine.build_diagnostic
-> storage sync diagnostics
-> learning_signal_service creates events
-> remediation triggers sync
-> AnalyzeResponse JSON returned
```

Memorize these layers:

```text
routes = receive HTTP requests
services = business logic
analysis = parsing, ML prediction, localization, hints
db/storage = persistence
core = config, auth, security, helpers
models.py = request/response/data contracts
```

That understanding is enough to answer most backend viva questions.
