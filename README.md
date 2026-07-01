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
├── frontend/                   # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── api/                # API client functions
│   │   ├── components/         # Reusable UI components (student, mentor, shared)
│   │   ├── hooks/              # React Query hooks
│   │   ├── layouts/            # Layout wrappers (AuthLayout, DashboardLayout)
│   │   ├── lib/                # Utility functions
│   │   ├── pages/              # Page-level components
│   │   ├── router/             # React Router configuration
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
│   │   └── services/           # Business logic (submission, storage, workspace)
│   ├── alembic/                # Database migration scripts
│   ├── graders/                # Per-week grader scripts + test wrapper assets
│   │   ├── week1/              # Filesystem validation grader
│   │   ├── week2/ … week11/    # Execution-based graders
│   │   └── base_grader.py      # Abstract base grader class
│   ├── workers/                # Celery task definitions + Docker executor
│   ├── seed_assignments.py     # Database seeder for all 12 assignments
│   ├── seed_admin.py           # Seeds initial admin/mentor user
│   ├── Dockerfile.api          # Dockerfile for the FastAPI API server
│   ├── Dockerfile.worker       # Dockerfile for the Celery grading worker
│   ├── docker-compose.yml      # Full local/EC2 development stack
│   ├── requirements.txt
│   └── .env.example            # Template for all required env variables
│
├── scripts/
│   └── test_data/              # ZIP generators for mock submissions (week 1–12)
│
├── docs/                       # LaTeX & Markdown documentation
│
└── README.md
```

---

## 🔄 Submission Lifecycle

1. **Student submits** a GitHub repository URL (pointing to a specific branch/subfolder) or a ZIP file via the React Frontend.
2. **API validates** the submission (file size, format, assignment exists), creates a `Submission` row in PostgreSQL, and enqueues a `GradingJob` via Celery.
3. **Celery Worker** on EC2 picks up the job, downloads/clones the submission from MinIO or GitHub, and extracts it into a shared Docker volume (`/autograder_jobs/<job-id>/submission/`).
4. **Docker sandbox** is spawned: a network-disabled sibling container with CPU/memory limits runs the assignment's `test_wrapper.py` against the student's code.
5. **Grader scripts** parse the wrapper's JSON output and evaluate it against the per-assignment rubric (defined in `graders/weekN/grader.py`).
6. **Results** (score breakdown, pass/fail per rubric check, stdout/stderr logs, hints) are written back to PostgreSQL via a `SubmissionResult` row.
7. **Frontend** polls the submission status via SSE (Server-Sent Events) and updates the student dashboard in real-time.

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

### Step 4: Seed Assignments

```bash
# Populate all 12 weekly assignments into the database
docker compose exec -T backend python seed_assignments.py
```

### Step 5: Frontend

In a separate terminal:
```bash
cd frontend
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
2. Set the **Root Directory** to `frontend`.
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

| Week | Title | Category | Key Files |
|---|---|---|---|
| 1 | Workspace Setup | Filesystem Validation | `commands.txt` |
| 2 | Command-Line Log Analyzer | Deterministic Execution | `analyze.sh` |
| 3 | Automated File Organizer | Filesystem Validation | `organize.sh` |
| 4 | Local Repository Recovery | Git Validation | `.gitignore`, `RECOVERY.md` |
| 5 | GitHub Collaboration | Git Validation | `TEAMWORK.md` |
| 6 | Text Corpus Analyzer | Deterministic Execution | `analyze.py`, `requirements.txt` |
| 7 | Wikipedia Collector | Deterministic Execution | `collect_wiki.py`, `requirements.txt` |
| 8 | Metadata Organizer | Deterministic Execution | `main.py`, `metadata_organizer/` |
| 9 | Inverted Index | Deterministic Execution | `build_index.py`, `lookup.py` |
| 10 | Indexing & Search Architecture | Deterministic Execution | `query.py`, `build_index.py` |
| 11 | Final Capstone Development | Deterministic Execution | `query.py`, `corpus/`, `engine/` |
| 12 | Final Capstone Demonstration | Manual Review | Full project repo |

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

## 🧰 Populating the `git-test` Branch

A helper script populates the `git-test` branch with mock perfect-score submissions for all weeks (useful for end-to-end grading tests):

```bash
# From the repo root, on v1-backend branch:
python populate_all.py
```

This generates ZIP archives, switches to `git-test`, extracts them into `week1/` through `week12/`, commits, and pushes.

---

*Built to replace offline grading workflows with a fully centralized, cloud-native evaluation infrastructure.*
