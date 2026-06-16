# EYSIP Auto-Grading Platform v2.0

A fully online, server-side project evaluation platform built for the **EEP Software Exploration Program (EEP-2)**. Students submit their mini-project repositories via GitHub URL or a ZIP upload, and the platform automatically grades them, providing instant feedback and final scores.

---

## 📐 Architecture

The platform follows a **microservices architecture** split across three concerns: the API, the task queue, and the Docker-based execution engine.

```
┌─────────────┐     REST/SSE     ┌──────────────────┐
│  React      │ ─────────────── │  FastAPI Backend  │
│  Frontend   │                 │  (Railway)        │
│  (Vercel)   │                 └────────┬─────────┘
└─────────────┘                          │
                                 ┌───────▼──────────────┐
                         Celery  │  PostgreSQL + Redis   │
                         Jobs    │  (Railway)            │
                                 └───────┬──────────────┘
                                         │  picks up job
                                 ┌───────▼──────────────┐
                                 │   Celery Worker       │
                                 │   (AWS EC2)           │
                                 │  ┌─────────────────┐  │
                                 │  │  Docker Sandbox  │  │
                                 │  │  (student code)  │  │
                                 │  └─────────────────┘  │
                                 └──────────────────────┘
```

### Why EC2 for the Worker?
The Celery grading worker must **mount `/var/run/docker.sock`** to spin up isolated sibling containers per submission. PaaS platforms like Railway use container-in-container setups that don't support this. A plain EC2 VM has direct access to the host Docker daemon, making it the right home for the worker.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Zustand, React Query |
| **Backend API** | FastAPI, SQLModel (Async SQLAlchemy) |
| **Database** | PostgreSQL 16 |
| **Task Queue** | Celery + Redis |
| **Object Storage** | MinIO (S3-compatible, runs locally in Docker) |
| **Sandbox** | Docker (isolated per-submission container) |
| **Schema Migrations** | Alembic |

---

## 📁 Repository Structure

```
v1/
├── app/                        # React frontend (Vite)
│   ├── src/
│   │   ├── api/                # API client functions
│   │   ├── components/         # Reusable UI components
│   │   ├── hooks/              # React Query hooks
│   │   ├── pages/              # Page-level components
│   │   ├── store/              # Zustand global state
│   │   └── types/              # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/      # FastAPI route handlers
│   │   ├── core/               # Config, security, dependencies
│   │   ├── db/                 # Database session setup
│   │   ├── models/             # SQLModel ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic (submission, storage)
│   ├── alembic/                # Database migration scripts
│   ├── graders/                # Per-assignment grader scripts + test assets
│   ├── workers/                # Celery task definitions + Docker executor
│   ├── Dockerfile.api          # Dockerfile for the FastAPI API server
│   ├── Dockerfile.worker       # Dockerfile for the Celery grading worker
│   ├── docker-compose.yml      # Full local development stack
│   ├── docker-compose.worker.yml  # Production EC2 worker deployment
│   ├── requirements.txt
│   └── .env.example            # Template for all required env variables
│
└── README.md
```

---

## 🔄 Submission Lifecycle

1. **Student submits** a GitHub URL or ZIP file via the React Frontend.
2. **API validates** the submission (file size, format, assignment exists), creates a `Submission` row in PostgreSQL, and enqueues a `GradingJob` via Celery.
3. **Celery Worker** on EC2 picks up the job, downloads the ZIP from MinIO storage, and extracts it into a shared Docker volume (`/tmp/autograder_jobs/<job-id>/`).
4. **Docker sandbox** is spawned: a network-disabled container with CPU/memory limits runs the student's code. The container has access to the shared jobs volume.
5. **Grader scripts** evaluate the container's output against the assignment rubric.
6. **Results** (score, pass/fail, stdout/stderr logs) are written back to PostgreSQL via a `SubmissionResult` row.
7. **Frontend** polls the submission status via SSE (Server-Sent Events) and updates in real-time.

---

## 🖥️ Local Development Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Node.js 18+
- Python 3.10+

### Step 1: Backend & Infrastructure

The `docker-compose.yml` spins up **PostgreSQL, Redis, MinIO, the API server, and the Celery worker** all at once.

```bash
cd backend

# 1. Copy the env template and review it (no changes needed for local dev)
cp .env.example .env

# 2. Build images and start all services in the background
docker compose up -d --build
```

**Verify everything is up:**
```bash
docker compose ps
# All services should show "running" or "healthy"
```

**Local service endpoints:**
| Service | URL | Credentials |
|---|---|---|
| FastAPI Swagger Docs | http://localhost:8000/docs | — |
| MinIO Console (file browser) | http://localhost:9001 | `minioadmin` / `minioadmin` |
| PostgreSQL | `localhost:5433` | `grading_user` / `changeme` |
| Redis | `localhost:6379` | — |

### Step 2: Apply Database Migrations

```bash
# Run Alembic migrations to create all tables
cd backend
$env:PYTHONPATH="$(pwd)"    # Windows PowerShell
# source venv/bin/activate  # Linux/macOS (if using a local venv)
venv/Scripts/alembic upgrade head
```

### Step 3: Seed an Admin User

```bash
cd backend
# Windows
$env:PYTHONPATH="$(pwd)"; venv\Scripts\python seed_admin.py

# Linux/macOS
PYTHONPATH=. python seed_admin.py
```

### Step 4: Frontend

In a separate terminal:
```bash
cd app
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**

---

## 🌍 Production Deployment

We use a **split-hosting strategy**:

| What | Where | Why |
|---|---|---|
| PostgreSQL + Redis | Railway | Managed, low-latency to API |
| FastAPI Backend API | Railway | Auto-scaling, zero-ops |
| React Frontend | Vercel | CDN, instant deploys from Git |
| Celery Grading Worker | AWS EC2 | Needs host Docker socket access |

---

### Phase 1: Database & API (Railway)

1. Create a new Railway project at https://railway.app
2. Add a **PostgreSQL** plugin and a **Redis** plugin.
3. Create a new **Service** pointing to the `backend/` directory.
4. Set the following environment variables in Railway:

```env
# Auto-provided by Railway plugins — copy from the plugin dashboard
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Celery
CELERY_BROKER_URL=redis://<redis-url>/0
CELERY_RESULT_BACKEND=redis://<redis-url>/1

# MinIO / Storage (see Phase 2)
MINIO_ENDPOINT=http://<your-ec2-ip>:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_SUBMISSIONS=submissions
MINIO_BUCKET_ASSETS=grader-assets
MINIO_USE_SSL=false

# Security (generate your own!)
JWT_SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(64))">
PROOF_SIGNING_KEY=<run: python -c "import secrets; print(secrets.token_hex(64))">

# Frontend CORS
ALLOWED_ORIGINS=https://your-app.vercel.app
```

5. Run migrations via Railway's shell, or set the startup command to:
   ```
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

---

### Phase 2: Grading Worker + MinIO (AWS EC2)

#### 2a. Launch the EC2 Instance
1. Go to **AWS Console → EC2 → Launch Instance**.
2. **AMI:** Ubuntu Server 24.04 LTS
3. **Instance Type:** `m7i-flex.large` (8GB RAM) — recommended. Avoid `t3.small` (2GB is too little for running Docker grading containers).
4. **Key Pair:** Create or select an existing `.pem` key so you can SSH in.
5. **Security Group:** Allow **port 22 (SSH)** and **port 9000 (MinIO)** from the internet.

#### 2b. Install Docker
```bash
ssh -i "your-key.pem" ubuntu@<your-ec2-public-ip>

# Install Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git

# Allow ubuntu user to run docker without sudo (log out and back in after this!)
sudo usermod -aG docker ubuntu
```
> ⚠️ **You must log out and log back in for the `usermod` change to take effect.**

#### 2c. Clone & Configure
```bash
git clone https://github.com/RohitWakade07/v1.git grading-platform
cd grading-platform/backend

# Create the .env file with your Railway connection strings
cp .env.example .env
nano .env   # Fill in DATABASE_URL_OVERRIDE, REDIS_URL_OVERRIDE, CELERY_BROKER_URL etc.
```

The `.env` on EC2 must contain at minimum:
```env
SERVICE_TYPE=worker

# From your Railway PostgreSQL plugin
DATABASE_URL_OVERRIDE=postgresql://postgres:...@...railway.app:5432/railway

# From your Railway Redis plugin
REDIS_URL_OVERRIDE=redis://default:...@...railway.app:6379
CELERY_BROKER_URL=redis://default:...@.../0
CELERY_RESULT_BACKEND=redis://default:...@.../1

# MinIO running locally on this same EC2 instance
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_SUBMISSIONS=submissions
MINIO_BUCKET_ASSETS=grader-assets
MINIO_USE_SSL=false

# Same secret keys as Railway
JWT_SECRET_KEY=<same value as Railway>
PROOF_SIGNING_KEY=<same value as Railway>
```

#### 2d. Start the Worker
```bash
cd grading-platform/backend

# Build and start the Celery worker container (runs MinIO too if you add it to the compose file)
docker compose -f docker-compose.worker.yml up -d --build
```

**View live worker logs:**
```bash
docker logs -f grading_worker
```

---

### Phase 3: Frontend (Vercel)

1. Import this repository into [Vercel](https://vercel.com).
2. Set the **Root Directory** to `app`.
3. Set **Build Command** to `npm run build` and **Output Directory** to `dist`.
4. Add environment variable:
   ```
   VITE_API_BASE_URL=https://<your-railway-api-url>
   ```
5. Deploy! Vercel will auto-deploy on every push to your branch.

---

## 🔒 Security Posture

| Control | Detail |
|---|---|
| **Non-root sandbox** | Student code runs as UID `1000:1000`, never root |
| **Network isolation** | `--network=none` — no internet access inside the sandbox |
| **Resource caps** | CPU, memory (256MB default), and PID limits enforced |
| **Privilege escalation** | `no-new-privileges:true` + `cap_drop=["ALL"]` |
| **Path traversal protection** | ZIP extraction validates all paths before writing |
| **Atomic concurrency** | `SELECT ... FOR UPDATE` locks prevent duplicate `attempt_number` on concurrent submissions |

---

## 📜 Assignments Supported

| Assignment | Topic |
|---|---|
| Week 1 | Git & GitHub Validation |
| Week 2 | Bash Log Parsing |
| Week 3 | Bash File Organizer |
| Week 4 | Python Scripting |
| Week 5–9 | *(In progress)* |

---

## 🧪 Running Tests

```bash
cd backend

# Activate virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt

# Run the backend tests (ensure services are running first)
PYTHONPATH=. pytest tests/
```

---

*Built to replace offline grading workflows with a fully centralized, cloud-native evaluation infrastructure.*
