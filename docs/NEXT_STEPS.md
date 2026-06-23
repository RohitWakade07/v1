# Next Steps

## Current State
All code fixes are committed and pushed. The repo is clean and deployment-ready.
Next action is purely infrastructure configuration — no more code changes needed
before the first deploy.

---

## Step 1 — Deploy the API on Railway (do this first)

1. Go to https://railway.app → New Project → Deploy from GitHub → select this repo
2. Railway will detect `railway.toml` automatically

3. Add **PostgreSQL** plugin: New → Database → Add PostgreSQL

4. Add **Redis** plugin: New → Database → Add Redis

5. In your API service → **Variables** tab, add these (copy exact names):

   ```
   DATABASE_URL_OVERRIDE    = <paste Railway Postgres URL>
   REDIS_URL_OVERRIDE       = <paste Railway Redis URL>
   JWT_SECRET_KEY           = <generate: python -c "import secrets; print(secrets.token_hex(64))">
   PROOF_SIGNING_KEY        = <generate: python -c "import secrets; print(secrets.token_hex(64))">
   ALLOWED_ORIGINS          = https://your-frontend.vercel.app
   KAFKA_BOOTSTRAP_SERVERS  = <from Upstash or Confluent — see Step 2>
   MINIO_ENDPOINT           = <from your storage provider — see Step 3>
   MINIO_ACCESS_KEY         = <your key>
   MINIO_SECRET_KEY         = <your secret>
   ENVIRONMENT              = production
   DEBUG                    = false
   ```

6. Push any commit to trigger deploy, or click **Deploy** in Railway UI

7. Verify:
   ```bash
   curl https://your-api.railway.app/health
   # {"status":"ok","database":"ok","redis":"ok","version":"1.0.0"}
   ```

---

## Step 2 — Set up Kafka (free tier options)

**Option A — Upstash Kafka** (easiest, no credit card for free tier):
- https://upstash.com → Create Kafka cluster → copy bootstrap server URL
- Set `KAFKA_BOOTSTRAP_SERVERS` in Railway

**Option B — Confluent Cloud** (more generous free tier):
- https://confluent.io → free cluster → copy bootstrap servers

---

## Step 3 — Set up Object Storage for MinIO

**Option A — Keep MinIO, deploy it on Railway**:
- In your Railway project → New → Docker Image → `minio/minio:latest`
- Set env vars: `MINIO_ROOT_USER=minioadmin`, `MINIO_ROOT_PASSWORD=<strong-password>`
- Set start command: `server /data --console-address :9001`
- Copy the internal Railway URL → use as `MINIO_ENDPOINT`

**Option B — Cloudflare R2** (S3-compatible, generous free tier):
- https://cloudflare.com → R2 → Create bucket
- Get endpoint URL, access key, secret key
- Set `MINIO_USE_SSL=true` in Railway

---

## Step 4 — Deploy the Frontend on Vercel

1. https://vercel.com → New Project → Import from GitHub → select this repo
2. Framework: **Vite**
3. Root directory: `app`
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add env var: `VITE_API_BASE_URL=https://your-api.railway.app/api/v1`
7. Deploy → copy the Vercel URL

8. Go back to Railway → update `ALLOWED_ORIGINS` to the Vercel URL

---

## Step 5 — Deploy the Worker (requires Docker-in-Docker)

Railway's shared runtime cannot run Docker containers inside containers.
The grading worker **must** run on a machine with Docker access.

**Recommended: DigitalOcean Droplet ($6/mo) or Hetzner CX11 (~€4/mo)**

```bash
# On the VPS
git clone https://github.com/your-org/your-repo.git
cd your-repo/backend
cp .env.example .env
# Edit .env with the same secrets you used in Railway
docker build -f Dockerfile.worker -t grading-worker .
docker run -d \
  --env-file .env \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --restart unless-stopped \
  grading-worker
```

---

## Step 6 — Seed the database (first deploy only)

In Railway → your API service → Settings → one-off command:
```bash
python create_mentor.py
```

Or via Railway CLI:
```bash
npm install -g @railway/cli
railway login
railway run python create_mentor.py
```

---

## Optional Improvements (do after first deploy is working)

- [ ] Split `requirements.txt` — move `pytest`, `pytest-asyncio`, `aiosqlite` to `requirements-dev.txt`
- [ ] Add GitHub Actions CI (lint + docker build check)
- [ ] Add `LICENSE` file before making repo public
- [ ] Add `CONTRIBUTING.md`
