# Deployment Guide

This guide consolidates the steps required to deploy the full grading platform infrastructure, including the API, database, frontend, and the dedicated EC2 worker.

## Architecture Overview
- **Frontend**: Vercel or Netlify (React/Vite). Build command: `npm run build`
- **Backend API**: Railway (FastAPI). Uses `backend/Dockerfile.api`.
- **Database**: Railway PostgreSQL.
- **Redis**: Railway Redis (for Celery broker and results).
- **Backend Worker**: AWS EC2 Instance (Celery worker). Requires Docker to run grading sandboxes. Uses `backend/Dockerfile.worker`.
- **Storage**: Backblaze B2 (MinIO compatible) for submissions and assets.

---

## 1. Deploying the API and Databases (Railway)

1. Provision a **PostgreSQL** database and a **Redis** instance on Railway.
2. Link your GitHub repository to Railway and deploy the `backend/` directory.
3. Railway will use `backend/Dockerfile.api` to build the API.
4. Set the following environment variables in your Railway API service:
   - `DATABASE_URL` (Postgres connection string)
   - `REDIS_URL` (Redis connection string)
   - `MINIO_ENDPOINT` (e.g., `s3.us-east-005.backblazeb2.com`)
   - `MINIO_ACCESS_KEY`
   - `MINIO_SECRET_KEY`
   - `MINIO_BUCKET_NAME`
   - `MINIO_SECURE` (Set to `True`)
5. The API will automatically run `alembic upgrade head` on startup to apply database migrations.

---

## 2. Deploying the Grading Worker (AWS EC2)

Because the grading worker spins up sibling Docker containers to evaluate untrusted code, it must run on a machine where it has access to the Docker socket.

### Step 2.1: Provision an EC2 Instance
1. **AMI**: Ubuntu Server 24.04 LTS.
2. **Instance Type**: `m7i-flex.large` (8GB RAM) or `c7i.large` (4GB RAM) recommended. Avoid `t3.small` due to memory constraints when running multiple concurrent grading jobs.
3. Allow SSH traffic from Anywhere (Port 22).

### Step 2.2: Install Docker
SSH into the instance:
```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git
sudo usermod -aG docker ubuntu
```
*(Log out and log back in for the group change to take effect).*

### Step 2.3: Clone and Configure
```bash
git clone https://github.com/RohitWakade07/v1.git grading-platform
cd grading-platform/backend
```

Create a `.env` file with your connection strings from Railway and Backblaze:
```env
SERVICE_TYPE=worker
DATABASE_URL_OVERRIDE=postgresql://postgres:...
REDIS_URL_OVERRIDE=redis://default:...
CELERY_BROKER_URL=redis://default:.../0
CELERY_RESULT_BACKEND=redis://default:.../1
MINIO_ENDPOINT=...
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET_NAME=...
MINIO_SECURE=True
```

### Step 2.4: Launch the Worker
```bash
docker compose -f docker-compose.worker.yml up -d --build
```
You can view logs via: `docker logs -f grading_worker`

---

## 3. Worker Architecture Details

The worker handles submissions via a Celery task queue:
1. Student submits code via FastAPI.
2. Celery task dispatched via Redis.
3. EC2 Worker picks up task and calls `run_fresh_container(language, image)`.
4. A fresh, heavily sandboxed Docker container is spawned:
   - Network disabled, `mem_limit=256m`, `cpu_quota=50000`, read-only FS, etc.
5. Grading script runs.
6. Container is aggressively cleaned up (even on failure).
7. Results are written back to PostgreSQL.
