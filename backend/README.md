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

## Phase 1 Endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/learning-sessions`
- `GET /api/v1/learning-sessions/{learning_session_id}`
- `POST /api/v1/code-coach/analyze`
