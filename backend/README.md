# Code Coach backend

FastAPI service behind the Code Coach extension, and the identity provider for
the whole of Code Guru. It stores everything in MongoDB Atlas.

## Setup

1. Create `backend/.env` (it is not committed).
2. Install the dependencies into `backend/.venv`:
   `python -m venv .venv` then `.venv/Scripts/python -m pip install -r requirements.txt`.
3. Start it from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API is then at `http://127.0.0.1:8000`, with interactive docs at `/docs`.

## Environment

Required:

| Variable | |
|---|---|
| `MONGODB_URI` | Atlas connection string. Without it the service runs on in-memory storage, which forgets everything on restart. |
| `JWT_SECRET` | Signs access and refresh tokens. |

Used when the feature is wanted:

| Variable | For |
|---|---|
| `MONGODB_DB_NAME` | Database name, default `code_coach`. |
| `CORS_ALLOWED_ORIGINS` | Browser origins allowed to call the API directly. |
| `PUBLIC_WEB_URL` | The web app, for links in emails. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` | Email confirmation and password reset. |
| `INTERNAL_SERVICE_KEY` | Shared with PairPath for the server-to-server `/api/v1/internal` routes. |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | "Explain this error" and other model-written explanations. `LLM_DAILY_LIMIT` caps them per student. |
| `PAYHERE_MERCHANT_ID`, `PAYHERE_MERCHANT_SECRET`, `PAYHERE_SANDBOX`, `BILLING_DEMO_MODE` | The Pro subscription. |
| `RESEARCH_COLLECTION_ENABLED`, `RESEARCH_ID_SALT` | Consented, pseudonymised research snapshots. |

Every setting and its default is in `app/core/config.py`.

## Structure

| Path | |
|---|---|
| `app/main.py` | Application entry point and router wiring. |
| `app/api/routes/` | One module per area: auth and account, analysis (`code_coach.py`), coach assist, learning sessions, events, students, remediation, gamification, collaboration, dashboard, billing, research, internal. |
| `app/analysis/` | The detection pipeline: parser, candidate extraction, feature extraction, models, locators, error catalogue, hint engine. |
| `app/services/` | Service layer: analysis responses, disputes, learning signals and mastery, remediation, billing, mail, LLM client, research collection. |
| `app/db/storage.py` | Storage: MongoDB, and an in-memory twin used by the tests. |
| `app/models.py` | Request and response models. |
| `app/dev_tools/` | Dataset, training, calibration and evaluation scripts. Some connect to the live database - read before running. |
| `models/` | Trained models, calibration files and metrics. |
| `tests/` | The test suite. |

## Endpoints

All routes are under `/api/v1`. The complete list, with request and response
shapes, is [`integration/API_CONTRACT.md`](../integration/API_CONTRACT.md),
generated from the code by `python -m app.dev_tools.export_api_contract`.
Regenerate it after changing a route.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The tests use in-memory storage and never touch Atlas.
