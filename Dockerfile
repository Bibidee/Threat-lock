# Threat-Lock backend (FastAPI) container for Fly.io.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first for layer caching.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --upgrade pip && pip install -r backend/requirements.txt

# App code (config.py resolves REPO_ROOT as /app, so keep this structure).
COPY backend/ backend/
COPY monitoring/ monitoring/
COPY contracts/ contracts/

EXPOSE 8000

# run.py reads settings from environment (Fly secrets) and binds 0.0.0.0:8000.
CMD ["python", "backend/run.py"]
