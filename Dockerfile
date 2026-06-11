# This file exists solely so Railway's build detector picks up Dockerfile-based
# deployment automatically. The actual build is defined in railway.toml.
# See backend/Dockerfile.api for the real image definition.

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl openssl build-essential librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --group app

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN chown -R app:app /app
USER app

ENV PORT=8000

CMD alembic upgrade head && \
    gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
