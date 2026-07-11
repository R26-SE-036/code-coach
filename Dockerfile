# Code Coach backend — container image for Cloud Run / Render / any host.
#
# Build (from the repo root):   docker build -t code-coach-backend .
# Run locally against Firestore with the dev service-account key:
#   docker run --rm -p 8000:8080 \
#     -v ./backend/secrets:/app/backend/secrets:ro \
#     -e FIREBASE_CREDENTIALS_PATH=secrets/firebase-service-account.json \
#     -e JWT_SECRET=<your secret> \
#     code-coach-backend
#
# On Cloud Run no key file is used: set FIREBASE_PROJECT_ID only and the
# service authenticates as its runtime service account (ADC).

FROM python:3.12-slim

# Install dependencies first so this layer caches across code changes.
COPY backend/requirements-prod.txt /tmp/requirements-prod.txt
RUN pip install --no-cache-dir -r /tmp/requirements-prod.txt

# Mirror the repo layout the code expects:
#   /app/backend/app        (source; PROJECT_ROOT resolves to /app)
#   /app/backend/models     (trained .joblib models, validated at startup)
#   /app/knowledge_base     (hint/lesson content, loaded at import time)
WORKDIR /app/backend
COPY backend/app /app/backend/app
COPY backend/models /app/backend/models
COPY knowledge_base /app/knowledge_base

# Cloud Run injects PORT (8080 by default); honor it everywhere else too.
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
