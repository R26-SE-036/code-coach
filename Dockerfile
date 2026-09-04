# Code Coach backend - the platform's identity provider and diagnostics store.
#
# Build (from the repo root):
#   docker build -t code-coach-backend .
#
# Run:
#   docker run --rm -p 8000:8080 \
#     -e MONGODB_URI='mongodb+srv://...' \
#     -e MONGODB_DB_NAME=code-guru \
#     -e JWT_SECRET=<your secret> \
#     code-coach-backend
#
# This header used to describe Firestore and Cloud Run - a service-account key
# mounted at FIREBASE_CREDENTIALS_PATH, and ADC on Cloud Run. The store moved to
# MongoDB Atlas and the target is ECS, so both were wrong: anyone following them
# would have mounted a key the code no longer reads and set a project id nothing
# looks at. requirements-prod.txt already carries pymongo rather than
# google-cloud-firestore, so the image itself was correct; only the instructions
# for running it were not.
#
# There is no default for MONGODB_URI on purpose. build_storage() still prefers
# Firestore if either FIREBASE_* variable is set, so leaving them unset is what
# selects MongoDB.

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

# PORT is honoured wherever it is injected; 8080 is the default the task
# definition and the ALB target group both expect.
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
