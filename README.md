<div align="center">

# Engineering Exploration Program 2

An automated, cloud-native grading platform built for the **Engineering Exploration Program (EEP-2)**. Students submit weekly assignments via GitHub URL or ZIP upload, and the platform automatically evaluates them inside isolated Docker sandboxes — providing instant rubric-based feedback and scores.

[![Category](https://img.shields.io/badge/Category-Software%20%2F%20Web-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![e-Yantra](https://img.shields.io/badge/e--Yantra-IIT%20Bombay-orange)](https://www.e-yantra.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB)](https://react.dev)
[![Docker](https://img.shields.io/badge/Sandbox-Docker-2496ED)](https://www.docker.com)

</div>

---

## Table of Contents

- [About](#about)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Submission Lifecycle](#submission-lifecycle)
- [Assignments](#assignments)
- [Deployment](#deployment)
- [Security](#security)
- [Testing](#testing)
- [Team](#team)
- [License](#license)

---

## About

This project falls within the **EdTech domain** and is part of the Engineering Exploration Program (EEP-2), aimed at developing problem-solving skills in first-year students through a 12-week hands-on software exploration curriculum — covering Linux, Git, Python, web scraping, NLP, and search engine development.

**Project Type:** Software / Web  
**Mentors:** Sidharth Priyadarshi, Prem Kumar

### Key Features

- 🚀 **Instant Automated Grading** — Submit via GitHub URL or ZIP, get rubric-based feedback in seconds
- 🐳 **Secure Docker Sandboxes** — Student code runs in network-isolated, resource-capped containers
- 📊 **Rich Rubric Feedback** — Per-check pass/fail, scores, hints, and execution logs
- 🧑‍🏫 **Mentor Dashboard** — Manage assignments, review submissions, publish scores
- 🎓 **Student Portal** — Track progress, view detailed feedback, resubmit attempts
- 🔄 **Real-time Updates** — Server-Sent Events (SSE) for live grading status

### System Overview

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

> The Celery grading worker runs on EC2 because it must mount `/var/run/docker.sock` to spin up isolated sibling containers per submission — something PaaS platforms like Railway don't support.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Python 3.10+
- Node.js 18+ and npm
- Git

---

## Getting Started

```bash
git clone https://github.com/RohitWakade07/v1.git
cd v1
```

### Step 1: Backend & Infrastructure

The `docker-compose.yml` spins up **PostgreSQL, Redis, MinIO, the API server, and the Celery worker** all at once.

```bash
cd backend

# Copy and configure environment variables
cp .env.example .env

# Build images and start all services
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
| MinIO Console | http://localhost:9001 | `minioadmin` / `minioadmin` |
| PostgreSQL | `localhost:5433` | `grading_user` / `changeme` |
| Redis | `localhost:6379` | — |

### Step 2: Apply Database Migrations

```bash
cd backend
$env:PYTHONPATH="$(pwd)"    # Windows PowerShell
# export PYTHONPATH=.       # Linux/macOS
alembic upgrade head
```

### Step 3: Seed Admin User & Assignments

```bash
# Seed admin user
docker compose exec -T backend python seed_admin.py

# Seed all 12 weekly assignments
docker compose exec -T backend python seed_assignments.py
```

### Step 4: Frontend

In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**

---

## Architecture

### Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, Zustand, React Query |
| **Backend API** | FastAPI, SQLModel (Async SQLAlchemy) |
| **Database** | PostgreSQL 16 |
| **Task Queue** | Celery + Redis |
| **Object Storage** | MinIO (S3-compatible) |
| **Sandbox** | Docker (isolated per-submission sibling containers) |
| **Schema Migrations** | Alembic |

---

## Project Structure

```
v1/
├── frontend/........................ React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── api/..................... API client functions
│   │   ├── components/.............. UI components (student, mentor, shared)
│   │   ├── hooks/................... React Query hooks
│   │   ├── layouts/................. Layout wrappers
│   │   ├── lib/..................... Utility functions
│   │   ├── pages/................... Page-level components
│   │   ├── router/.................. React Router configuration
│   │   ├── store/................... Zustand global state
│   │   └── types/................... TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/........... FastAPI route handlers
│   │   ├── core/.................... Config, security, dependencies
│   │   ├── db/...................... Database session setup
│   │   ├── models/.................. SQLModel ORM models
│   │   ├── schemas/................. Pydantic request/response schemas
│   │   └── services/................ Business logic (grading, storage, workspace)
│   ├── alembic/..................... Database migration scripts
│   ├── graders/..................... Per-week grader scripts + test wrappers
│   │   ├── week1/ … week11/........ Assignment-specific graders
│   │   └── base_grader.py.......... Abstract base grader class
│   ├── workers/..................... Celery task definitions + Docker executor
│   ├── seed_assignments.py.......... Database seeder for all 12 assignments
│   ├── seed_admin.py................ Seeds initial admin/mentor user
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env.example
│
├── scripts/
│   └── test_data/................... ZIP generators for mock submissions
│
├── docs/............................ LaTeX & Markdown documentation
├── tests/........................... Integration and end-to-end tests
├── assets/.......................... Images and static resources
└── README.md
```

> See [`docs/`](docs/) for detailed deployment guides and architecture documentation.

---

## Submission Lifecycle

1. **Student submits** a GitHub repository URL (branch/subfolder) or a ZIP file via the React frontend.
2. **API validates** the submission (file size, format, assignment exists), creates a `Submission` row in PostgreSQL, and enqueues a `GradingJob` via Celery.
3. **Celery Worker** on EC2 picks up the job, downloads/clones the submission, and extracts it into a shared Docker volume (`/autograder_jobs/<job-id>/submission/`).
4. **Docker sandbox** is spawned: a network-disabled sibling container with CPU/memory limits runs the assignment's `test_wrapper.py` against the student's code.
5. **Grader scripts** parse the wrapper's JSON output and evaluate it against the per-assignment rubric (defined in `graders/weekN/grader.py`).
6. **Results** (score breakdown, pass/fail per rubric check, stdout/stderr logs, hints) are written back to PostgreSQL.
7. **Frontend** receives live updates via SSE and displays the results on the student dashboard.

---

## Assignments

| Week | Title | Category | Key Files |
|------|-------|----------|-----------|
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
| 12 | Final Capstone Demonstration | Manual Review | Full project repository |

---

## Deployment

We use a **split-hosting strategy**:

| Component | Platform | Reason |
|---|---|---|
| PostgreSQL + Redis | Railway | Managed, low-latency to API |
| FastAPI Backend API | Railway | Auto-scaling, zero-ops |
| React Frontend | Vercel | CDN, instant deploys from Git |
| Celery Grading Worker | AWS EC2 | Needs host Docker socket access |

### Frontend (Vercel)

1. Import the repository into [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Set **Build Command** to `npm run build` and **Output Directory** to `dist`.
4. Add environment variable: `VITE_API_BASE_URL=https://<your-railway-api-url>`

### Backend API (Railway)

1. Create a new Railway project with **PostgreSQL** and **Redis** plugins.
2. Create a service pointing to the `backend/` directory.
3. Set environment variables (see `.env.example`).
4. Startup command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Worker (AWS EC2)

1. Launch an Ubuntu EC2 instance (recommended: `m7i-flex.large`, 8GB RAM).
2. Install Docker and clone the repository.
3. Configure `.env` with Railway connection strings.
4. Start: `docker compose up -d`

> See [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) for the complete step-by-step deployment guide.

---

## Security

| Control | Detail |
|---|---|
| **Non-root sandbox** | Student code runs as UID `1000:1000`, never root |
| **Network isolation** | `--network=none` — no internet access inside the sandbox |
| **Resource caps** | CPU, memory (256MB default), and PID limits enforced |
| **Privilege escalation** | `no-new-privileges:true` + `cap_drop=["ALL"]` |
| **Path traversal protection** | ZIP extraction validates all paths before writing |
| **Atomic concurrency** | `SELECT ... FOR UPDATE` locks prevent duplicate attempts |

---

## Testing

```bash
cd backend

# Set up virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt

# Run tests (ensure Docker services are running)
PYTHONPATH=. pytest tests/
```

### Populating the `git-test` Branch

A helper script generates mock perfect-score submissions for all weeks (useful for end-to-end grading tests):

```bash
# From the repo root, on v1-backend branch:
python populate_all.py
```

---

## Team

| Name | Role |
|------|------|
| Rohit Wakade | Intern |
| Sidharth Priyadarshi, Prem Kumar | Mentor |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  Made with ❤️ at <a href="https://www.e-yantra.org">e-Yantra, IIT Bombay</a>
</div>
