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
# MONGODB_URI has no default on purpose. Without it the service falls back to
# in-memory storage and starts perfectly happily, which in a container means
# every account and diagnostic disappears on the next restart - a failure that
# looks like the database being empty rather than never having been configured.

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
