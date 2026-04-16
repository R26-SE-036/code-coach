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

- `GET /api/v1/events/me`
- `GET /api/v1/users/me/diagnostic-summary`
- `GET /api/v1/users/me/concept-struggles`

These Phase 2 foundation endpoints turn stored Code Coach diagnostics into reusable learning signals for:

- Study Guider
- Adaptive Gamification
- Collaborative web application flows
