# EYSIP Auto-Grading Platform v2.0

The EYSIP Auto-Grading Platform is a fully online, server-side project evaluation platform designed for the EEP Software Exploration Program (EEP-2). It allows students to submit their mini-project repositories (via GitHub URL or ZIP upload) for automated grading, providing instant feedback and final scores.

This system replaces the legacy offline grader architecture with a modern, scalable, and secure microservices approach.

## 🏗️ Architecture & Tech Stack

The platform is built around a robust asynchronous, event-driven architecture using the following technologies:

- **Backend API:** FastAPI, SQLModel (Async SQLAlchemy), PostgreSQL
- **Message Broker:** Confluent Kafka (for reliable grading job distribution)
- **Object Storage:** MinIO (S3-compatible storage for submission ZIP files)
- **Execution Engine:** Docker (Sandbox for securely running untrusted student code)
- **Caching & Locks:** Redis
- **Containerization:** Docker Compose

### System Workflow

1. **Submission API:** A student submits a GitHub URL or a ZIP file. The API uploads the source to MinIO, creates a database record, and publishes a grading job to Kafka.
2. **Grading Workers:** Kafka consumers (backend workers) pick up the job, download the ZIP from MinIO, and extract it safely.
3. **Docker Sandbox Execution:** The worker injects hidden assets and test files into the submission workspace, then spawns an ephemeral, network-disabled Docker container to execute the student's code (with memory and CPU limits).
4. **Grading Checks:** After the container exits, Python-based grader scripts validate the artifacts, output, and exit codes against strict rubrics.
5. **Persistence:** Results, score breakdowns, and stdout/stderr logs are stored in PostgreSQL.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)

### Running the Platform

1. **Start Infrastructure & Services:**
   Run the following command in the `backend/` directory to spin up Postgres, Redis, Kafka, MinIO, the API server, and multiple Grading Workers:

   ```bash
   cd backend
   docker compose up -d --build
   ```

2. **Verify Services:**
   Ensure all core containers are running and healthy:
   ```bash
   docker compose ps
   ```

3. **Accessing the Services:**
   - **FastAPI Docs (Swagger UI):** http://localhost:8000/docs
   - **MinIO Console:** http://localhost:9001 (Credentials: `minioadmin` / `minioadmin`)
   - **Kafka UI:** http://localhost:8080
   - **PostgreSQL:** `localhost:5433` (User: `grading_user`, Password: `changeme`, DB: `grading_db`)

## 📁 Repository Structure

- `backend/app/` - FastAPI backend application (Routes, Models, Services)
- `backend/workers/` - Kafka consumer logic and `DockerExecutor` for sandbox orchestration
- `backend/graders/` - Grader scripts and hidden test assets for each assignment (Weeks 1-9)
- `backend/docker-compose.yml` - Defines the full local infrastructure stack

## 🧪 Testing the Platform

An End-to-End integration test pipeline is available to validate the entire lifecycle.

To run the E2E tests:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python3 /path/to/test_e2e_pipeline.py
```

*Note: Ensure the backend services are up and running before executing the test pipeline.*

## 🔒 Security Posture

- **No Root Privileges in Sandbox:** Code executes as a restricted non-root user (`1000:1000`).
- **Network Isolation:** Internet access is explicitly disabled during evaluation to prevent external leaks.
- **Resource Limits:** Docker restricts CPU, memory (512MB default), and PIDs.
- **Privilege Escalation Blocked:** Containers run with `no-new-privileges:true` and drop all Linux capabilities (`cap_drop=["ALL"]`).
- **Path Traversal Protection:** ZIP extraction prevents overwriting host files outside the designated workspace.

## 📜 Assignments Supported

The platform currently evaluates the following program milestones:
- **Week 1:** Git & GitHub Validation
- **Week 2:** Bash Log Parsing
- **Week 3:** Bash File Organizer
- *(Weeks 4-9 pending implementation)*

---

*This platform was built to replace offline grading systems, bringing 100% of the evaluation infrastructure into a centralized, robust, cloud-native environment.*
