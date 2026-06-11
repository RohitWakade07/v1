# Next Steps

## If Resuming a Session
1. Read `PROGRESS.md` — see what was completed
2. Read `DEPLOYMENT_STATUS.md` — current deployment readiness
3. Run `git log --oneline -10` to see recent commits

## Immediate: Commit All Changes

These files were modified/created and need to be committed:

```bash
cd A:\eysip\v1

git add backend/.env.example
git commit -m "fix: security — replace real secrets in .env.example with placeholders"

git add .gitignore
git commit -m "chore: harden root .gitignore for frontend artifacts, scratch files, and keys"

git add backend/app/core/config.py
git commit -m "fix: config — Railway URL overrides, extra=ignore, ALLOWED_ORIGINS + cors_origins"

git add backend/app/main.py
git commit -m "fix: main — dynamic CORS from settings, Redis health check in /health"

git add backend/Dockerfile.api
git commit -m "feat: Dockerfile.api — Alembic migration step, non-root user, PORT env var"

git add backend/.dockerignore
git commit -m "feat: add backend .dockerignore"

git add railway.toml RAILWAY_DEPLOYMENT.md
git commit -m "feat: add railway.toml and deployment guide"

git add app/.env.example
git commit -m "docs: add frontend .env.example"

git add REPOSITORY_AUDIT.md PROGRESS.md DEPLOYMENT_STATUS.md NEXT_STEPS.md
git commit -m "docs: add audit, progress tracking, and deployment status files"
```

## Before First Railway Deploy

- [ ] Provision PostgreSQL plugin in Railway → copy `DATABASE_URL`
- [ ] Provision Redis plugin in Railway → copy `REDIS_URL`
- [ ] Set `DATABASE_URL_OVERRIDE` in Railway API service variables
- [ ] Set `REDIS_URL_OVERRIDE` in Railway API service variables
- [ ] Generate and set `JWT_SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(64))"`
- [ ] Generate and set `PROOF_SIGNING_KEY`: `python -c "import secrets; print(secrets.token_hex(64))"`
- [ ] Set `ALLOWED_ORIGINS` to your frontend URL (e.g. `https://your-app.vercel.app`)
- [ ] Set up Kafka (Upstash or Confluent Cloud) and set `KAFKA_BOOTSTRAP_SERVERS`
- [ ] Set up MinIO or S3-compatible storage and set `MINIO_*` vars
- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
- [ ] Verify `/health` returns `{"status":"ok",...}` after deploy

## Before Deploying the Frontend

- [ ] Create `app/.env.production` with `VITE_API_BASE_URL=https://your-api.railway.app/api/v1`
  (do NOT commit this file — it contains the real API URL)
- [ ] Run `cd app && npm run build` locally to verify the build succeeds
- [ ] Deploy to Vercel: connect repo, set build command `cd app && npm run build`, output `app/dist`

## For the Worker (Docker-in-Docker)

- [ ] Provision a VPS (DigitalOcean / Hetzner) with Docker installed
- [ ] Copy `.env` to the VPS
- [ ] Run: `cd backend && docker build -f Dockerfile.worker -t grading-worker . && docker run --env-file .env -v /var/run/docker.sock:/var/run/docker.sock grading-worker`

## Optional Improvements

- [ ] Split `requirements.txt` → move pytest/aiosqlite to `requirements-dev.txt`
- [ ] Add GitHub Actions CI (lint + docker build check) — see original plan Phase 9
- [ ] Add `LICENSE` file before making repo public
