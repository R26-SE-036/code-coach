# Code Coach Backend

## Local Setup

1. Create a local `backend/.env` file from `backend/.env.example`.
2. Set `MONGODB_URI` to your MongoDB Atlas connection string.
3. Set a strong `JWT_SECRET` for local development.
4. Install backend dependencies in `backend/.venv`.
5. Start the API from `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Required Environment Variables

- `MONGODB_URI`
- `JWT_SECRET`

Optional:

- `MONGODB_DB_NAME` defaults to `code-guru`
- `ACCESS_TOKEN_TTL_SECONDS` defaults to `3600`
- `REFRESH_TOKEN_TTL_SECONDS` defaults to `604800`

## Backend Structure

The backend is now grouped into a few focused packages:

- `app/api/routes`
  - FastAPI route modules such as auth, learning sessions, diagnostics, events, and user summaries
- `app/core`
  - cross-cutting backend concerns such as config, security, shared utilities, and request dependencies
- `app/analysis`
  - Code Coach analysis pipeline, parser helpers, ML engine, locators, hints, and detectors
- `app/services`
  - service-layer logic for analysis responses, learning signals, and evaluation logging
- `app/db`
  - persistence and storage access
- `app/models.py`
  - shared Pydantic and dataclass models used across the backend
- `app/main.py`
  - application entry point and router wiring

## Phase 1 Endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/learning-sessions`
- `GET /api/v1/learning-sessions/{learning_session_id}`
- `GET /api/v1/learning-sessions/{learning_session_id}/diagnostics`
- `POST /api/v1/code-coach/analyze`
- `GET /api/v1/diagnostics/me`

## Phase 2 Foundation Endpoints

- `POST /api/v1/events`
- `GET /api/v1/events/me`
- `GET /api/v1/collaboration/me/prompts`
- `POST /api/v1/collaboration/me/pair-sessions`
- `POST /api/v1/collaboration/me/prompts/shown`
- `POST /api/v1/collaboration/me/peer-reviews`
- `GET /api/v1/gamification/me/recommendations`
- `POST /api/v1/gamification/me/adaptation-decisions`
- `POST /api/v1/gamification/me/session-results`
- `GET /api/v1/remediation/me/triggers`
- `GET /api/v1/remediation/me/recommendations`
- `POST /api/v1/remediation/me/triggers/{trigger_id}/lesson-opened`
- `POST /api/v1/remediation/me/triggers/{trigger_id}/quiz-completed`
- `GET /api/v1/users/me/diagnostic-summary`
- `GET /api/v1/users/me/concept-struggles`
- `GET /api/v1/users/me/mastery`

These Phase 2 foundation endpoints turn stored Code Coach diagnostics into reusable learning signals for:

- Study Guider
- Adaptive Gamification
- Collaborative web application flows

Current Code Coach hint interaction events sent from the VS Code extension:

- `hint_shown`
- `hint_navigation_used`
- `hint_level_requested`

The user summary endpoints now also include hint-dependence signals such as:

- `total_hint_events`
- `concepts_with_hint_usage`
- per-concept `hint_event_count`
- per-concept `hint_dependency_score`
- per-concept `hint_dependency_level`

Code Coach now also creates automatic remediation triggers when a concept reaches a high struggle state. Those triggers are stored for the authenticated user and exposed through:

- `GET /api/v1/remediation/me/triggers`

Study Guider can now consume a direct handoff payload that maps active remediation triggers into micro-lesson and quiz recommendations:

- `GET /api/v1/remediation/me/recommendations`

Study Guider can also send the intervention feedback loop back into Code Guru:

- `POST /api/v1/remediation/me/triggers/{trigger_id}/lesson-opened`
- `POST /api/v1/remediation/me/triggers/{trigger_id}/quiz-completed`

These actions update the trigger lifecycle and emit follow-up learning events such as:

- `micro_lesson_viewed`
- `quiz_completed`
- `mastery_updated`

The backend now also persists a `conceptMastery` snapshot per user and concept. This gives the rest of Code Guru one stable mastery view to read, instead of recalculating mastery from raw event history on every request. The authenticated read endpoint is:

- `GET /api/v1/users/me/mastery`

Adaptive Gamification can now consume both current concept struggles and mastery snapshots through:

- `GET /api/v1/gamification/me/recommendations`

That endpoint returns game recommendations such as game type, difficulty level, support level, priority, and the concept behind the recommendation.

Adaptive Gamification can now also write its feedback loop back into Code Guru through:

- `POST /api/v1/gamification/me/adaptation-decisions`
- `POST /api/v1/gamification/me/session-results`

The session result endpoint records the completed game event and updates the student's `conceptMastery` snapshot for that concept.

Gamification-related learning events now include:

- `game_adaptation_decision_created`
- `game_session_completed`

Collaborative Studio can now consume Code Coach-backed collaboration prompts through:

- `GET /api/v1/collaboration/me/prompts`

It can also write its session and review flow back into Code Guru through:

- `POST /api/v1/collaboration/me/pair-sessions`
- `POST /api/v1/collaboration/me/prompts/shown`
- `POST /api/v1/collaboration/me/peer-reviews`

Those endpoints validate session ownership, can link back to Code Coach diagnostics, and emit learning events such as:

- `pair_session_started`
- `collaboration_prompt_shown`
- `peer_review_submitted`
