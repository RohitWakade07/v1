# Railway Deployment Guide

## Architecture Note

This platform has **two services** that need to run on Railway:
1. **API** (`Dockerfile.api`) — FastAPI backend
2. **Worker** (`Dockerfile.worker`) — Kafka consumer / grading worker

Both share the same Postgres and Redis. Kafka and MinIO are external dependencies
you need to provision separately (see options below).

---

## One-Time Setup

### 1. Create Railway project
Railway → New Project → Deploy from GitHub → select this repo

### 2. Add PostgreSQL plugin
New → Database → Add PostgreSQL
From the plugin's Variables tab, copy `DATABASE_URL`

### 3. Add Redis plugin
New → Database → Add Redis
From the plugin's Variables tab, copy `REDIS_URL`

### 4. Kafka — choose one option
- **Upstash Kafka** (recommended free tier): https://upstash.com/kafka
- **Confluent Cloud** free tier: https://confluent.io
- Copy the bootstrap servers string

### 5. MinIO — choose one option
- **Railway MinIO service**: deploy `minio/minio` as a Docker image in the same project
- **Backblaze B2** or **Cloudflare R2** (S3-compatible)
- For the API + worker, set `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

### 6. API Service — set environment variables

In your API service → Variables tab:

| Variable | Value |
|---|---|
| `DATABASE_URL_OVERRIDE` | Paste the Railway Postgres URL from step 2 |
| `REDIS_URL_OVERRIDE` | Paste the Railway Redis URL from step 3 |
| `JWT_SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(64))"` |
| `PROOF_SIGNING_KEY` | `python -c "import secrets; print(secrets.token_hex(64))"` |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` (comma-separated if multiple) |
| `KAFKA_BOOTSTRAP_SERVERS` | From step 4 |
| `MINIO_ENDPOINT` | From step 5 |
| `MINIO_ACCESS_KEY` | From step 5 |
| `MINIO_SECRET_KEY` | From step 5 |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

### 7. Worker Service — set same variables
The worker needs the same database, redis, kafka, and minio vars.
It does NOT need `JWT_SECRET_KEY`, `ALLOWED_ORIGINS`, or `PORT`.

Also add:
| Variable | Value |
|---|---|
| `DOCKER_HOST` | Only if running Docker-in-Docker; Railway may not support this — see note below |

> **Docker-in-Docker Note:** The grading worker spawns Docker containers to sandbox
> student code. Railway's default runtime does NOT support Docker-in-Docker.
> For production, use a VPS (e.g. Railway's $5/mo instance with Docker installed)
> or a dedicated self-hosted runner. The API can still deploy on Railway without the worker.

### 8. Configure Railway to use the right Dockerfile

The `railway.toml` at the repo root points to `backend/Dockerfile.api`.
For the worker service, override the Dockerfile in Railway UI:
Settings → Build → Dockerfile Path → `backend/Dockerfile.worker`
Build Context → `backend`

---

## Deploy

```bash
git push origin main
```

Railway auto-deploys on every push to main.

---

## Verify Deployment

```bash
curl https://your-api.railway.app/health
# Expected:
# {"status":"ok","database":"ok","redis":"ok","version":"1.0.0"}
```

---

## Database Seed (first deploy only)

In Railway → API service → Settings → Deploy → one-off command:
```bash
python create_mentor.py
```
Or use the Railway CLI:
```bash
railway run python create_mentor.py
```

---

## Alembic Migrations

Migrations run automatically on startup via `alembic upgrade head` in the Dockerfile CMD.
To run manually:
```bash
railway run alembic upgrade head
```

To create a new migration after model changes:
```bash
railway run alembic revision --autogenerate -m "describe your change"
```

---

## Rollback

Railway → Deployments → click any previous deployment → Rollback

---

## Useful Commands

```bash
# View live logs
railway logs

# Open a shell in the running container
railway shell

# Run a one-off command without deploying
railway run python -c "from app.core.config import settings; print(settings.DATABASE_URL[:30])"
```
