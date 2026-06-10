# E-Yantra EEP Autograder Platform

This platform is a scalable, secure, and asynchronous autograding system designed to execute student Bash scripts and Python code in heavily locked-down environments.

## Architecture Overview

The platform uses a decoupled microservices architecture to ensure high throughput and security:
- **Frontend (Vite/React)**: A modern, responsive dashboard where students select their weekly assignment and upload their `.sh` or `.txt` script.
- **Backend API (FastAPI)**: Receives the student's file, creates a record in MySQL, and publishes an asynchronous grading task.
- **Task Queue (Celery + Redis)**: Background workers pick up tasks from Redis and prepare the grading workspace.
- **Secure Sandbox (Docker)**: The worker mounts the student's code alongside the instructor's private test cases inside a hardened Alpine Docker container.

## How the Autograder Sandbox Works (Security)

To prevent students from cheating, accessing the host machine, or reading instructor files, the sandbox applies the following military-grade constraints:

1. **No Network Access**: The container uses `network_mode="none"`. Scripts cannot download cheat files from the internet or contact external servers.
2. **Read-Only Root Filesystem**: The entire OS is read-only.
3. **RAM Disk Emulation**: The student's workspace (`/home/grader`) is mounted as a `tmpfs` (temporary file system in RAM). The student's script can create folders and files, but the moment the container dies, everything is instantly purged from memory.
4. **Dropped Capabilities**: `cap_drop=["ALL"]` and `security_opt=["no-new-privileges:true"]` prevent privilege escalation.
5. **Strict Limits**: Memory is capped at 128MB, and process limits are capped at 64 to prevent Fork Bombs (`:(){ :|:& };:`).

## How to Start the System

To start the local development environment:

1. **Start the Databases & Worker:**
   From the `/autograder-system` directory:
   ```bash
   docker-compose up -d
   ```
   *This starts MySQL, Redis, and the Celery Autograder Worker.*

2. **Start the FastAPI Backend:**
   From the `/autograder-system` directory:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start the Frontend:**
   From the `/autograder-system/v1-backend/frontend` directory:
   ```bash
   npm run dev -- --host 0.0.0.0
   ```

## Weekly Assignments

The platform now dynamically supports multiple weekly assignments. 

When a student selects an assignment week from the UI dropdown:
1. The backend locates the matching `instructor_files/week-XX/` folder.
2. It injects the instructor's hidden `test.sh` evaluation script securely into the grading workspace alongside the student's file.
3. The student's script is executed, and then the instructor's script evaluates the output to generate a final `score` and `feedback`.
