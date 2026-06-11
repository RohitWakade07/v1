# Deployment Status

## Backend API — Railway
**Status:** READY TO DEPLOY (pending env var configuration)
**Blockers resolved:** DATABASE_URL_OVERRIDE, REDIS_URL_OVERRIDE, PORT, Alembic, CORS, secrets
**Remaining:** Set env vars in Railway dashboard (see RAILWAY_DEPLOYMENT.md)
**Last deploy attempt:** Never
**Health check path:** `/health`
**Expected response:** `{"status":"ok","database":"ok","redis":"ok","version":"1.0.0"}`

## Backend Worker — Railway / VPS
**Status:** NOT DEPLOYABLE ON RAILWAY (Docker-in-Docker required)
**Recommended:** Deploy on a VPS with Docker installed (e.g. DigitalOcean $6/mo Droplet)
**Dockerfile:** `backend/Dockerfile.worker`

## Frontend — Vercel / Netlify
**Status:** READY TO DEPLOY
**Build command:** `cd app && npm run build`
**Output dir:** `app/dist`
**Env var needed:** `VITE_API_BASE_URL=https://your-api.railway.app/api/v1`
**Build verified:** Not run (TypeScript and deps appear clean from audit)

## Database — Railway PostgreSQL
**Status:** NOT CONFIGURED (provision via Railway dashboard)
**Migrations:** Alembic — auto-run on API startup

## Redis — Railway Redis
**Status:** NOT CONFIGURED (provision via Railway dashboard)

## Kafka
**Status:** NOT CONFIGURED (use Upstash Kafka or Confluent Cloud free tier)

## MinIO / Object Storage
**Status:** NOT CONFIGURED (use Railway Docker service or Cloudflare R2)
