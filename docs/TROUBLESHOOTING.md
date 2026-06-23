# Troubleshooting Guide

This document tracks common issues encountered during development and deployment, and the specific methods used to resolve them.

## 1. Gunicorn Boot Loop (`405 Method Not Allowed`)

**Symptoms**:
- The FastAPI backend constantly restarts.
- Frontend API calls return `405 Method Not Allowed` or `502 Bad Gateway`.
- Railway or EC2 logs show Gunicorn workers exiting repeatedly.

**Root Cause**:
A SyntaxError or `IndentationError` in the backend Python code (often during rapid feature development, such as when updating `assignments.py`). When the Python interpreter fails to parse the file, Gunicorn crashes on startup, leading to an infinite reboot loop.

**Troubleshooting & Resolution**:
1. **Identify the Syntax Error**: SSH into the backend instance or view Railway logs to spot the exact file and line number. Example log: `IndentationError: unexpected indent in backend/app/api/v1/routes/assignments.py`.
2. **Remote Hotfix (EC2)**: If deployed on an EC2 instance, you can use a python script to quickly fix the syntax error directly inside the running container to stabilize the server before pushing a git fix.
   ```bash
   # SSH into the instance
   ssh -i "your-key.pem" ubuntu@<ec2-public-ip>
   
   # Copy a hotfix script into the worker container and execute it
   docker cp remote_fix.py $(docker compose ps -q worker):/app/remote_fix.py
   docker compose exec worker python /app/remote_fix.py
   ```
3. **Prevention**: Always run a quick syntax check (`python -m py_compile filename.py`) before committing backend routing changes.

## 2. Frontend TypeScript Build Failures

**Symptoms**:
- The frontend deployment fails during the build step.
- Local `npm run build` fails with `error TS1002: Unterminated string literal` or `TS1005: ',' expected`.

**Root Cause**:
React components that parse multi-line text (like `AssignmentDetailPanel.tsx` processing the `expected_structure` field) can break the TypeScript compiler if newlines are not handled properly in template literals or string splits (e.g., using a literal newline inside a `.split('')` call instead of `\n`).

**Troubleshooting & Resolution**:
1. Check the build logs to locate the exact component failing.
2. Fix the string literal parsing. Instead of splitting by an actual multi-line string, use the escape character:
   ```typescript
   // Incorrect
   assignment.expected_structure.split('
   ').map(...)
   
   // Correct
   assignment.expected_structure.split('\n').map(...)
   ```

## 3. Worker Background Task Updates

**Symptoms**:
- You pushed new background logic (e.g., a grading normalization script update in `tasks.py`), but the system is still using the old logic.

**Root Cause**:
Celery worker containers do not automatically hot-reload code changes unless explicitly configured to do so (which is not recommended for production due to performance overhead).

**Troubleshooting & Resolution**:
After pulling new code to the EC2 instance, you must manually restart the worker container to pick up the changes:
```bash
docker compose restart worker
```
