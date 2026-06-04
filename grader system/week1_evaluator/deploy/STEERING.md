# Grader — Steering & Integration Guide

Purpose
- Quick reference for operators and integrators who will host or embed the EEP grader service.

When to use
- Host the grader as a standalone microservice and link or POST from your website.
- Or embed the grader endpoints into an existing Flask site (advanced).

Contents (what you should send to a friend)
- `app.py` — grader API and server logic
- `static/` — UI (index.html, dashboard.html, app.js, style.css)
- verifier binaries/scripts — `eep1_verifier`, `eep1_verifier.sh`, `eep2_*`, `eep3_*`
- `requirements.txt`, `Procfile`, `railway.toml`, `DEPLOY.md`, `.env.example`

Security & private key handling
- Do NOT commit `keys/instructor_private.pem` to any public repo.
- Preferred: provide the private key via `PRIVATE_KEY_B64` (base64-encoded PEM) set as an environment secret in the host/CI platform.
  - Example (operator machine):
    ```bash
    export PRIVATE_KEY_B64="$(openssl base64 -A -in /path/to/instructor_private.pem)"
    ```
- Alternative: set `PRIVATE_KEY_CONTENT` (raw text with proper newlines) or mount the key file and set `PRIVATE_KEY_PATH`.
- Store secrets in the host provider's secrets manager (Railway/Heroku/Github Actions secrets) — do not paste keys in chat or git.

Required environment variables
- `PRIVATE_KEY_B64` OR `PRIVATE_KEY_CONTENT` OR `PRIVATE_KEY_PATH`
- `PORT` (optional, default 8080)
- `UPLOADS_DIR` (optional, default `uploads`)
- `MAX_UPLOAD_BYTES` (optional)
- `DATABASE_URL` (optional, for Postgres persistence)

Run locally (quick test)
```bash
tar -xzf grader_week1_sanitized.tar.gz -C grader_pkg
cd grader_pkg
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PRIVATE_KEY_B64="$(openssl base64 -A -in /path/to/instructor_private.pem)"
export PORT=8080
python app.py
# Open http://localhost:8080
```

Docker (optional)
- A simple `Dockerfile` can be:
```
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENV FLASK_ENV=production
CMD ["python", "app.py"]
```
- Provide `PRIVATE_KEY_B64` as an environment secret to the container runtime.

Integration approaches
- Option A (recommended): Host grader as separate service and call `/api/grade` from your website.
  - Upload: multipart `file` POST to `/api/grade`.
  - Example curl:
    ```bash
    curl -F "file=@/path/to/STUDENT_EEP1_Week1.eep1" https://your-grader.example.com/api/grade
    ```
- Option B: Integrate code into an existing Flask app.
  - Move `decrypt_eep1()` and `grade_checks()` into a blueprint, merge `static/` assets, ensure deps installed and env vars set.

Testing & verification
- Use the provided `eep1_verifier.sh` locally to generate a `.eep1` file and upload to the running grader.
- Confirm responses at `/api/grade` and check `uploads/` or your DB for saved plaintext report when DB is not configured.

Security checklist (quick)
- Never store the private key in git.
- Limit access to the grader host (firewall, allowed origins if embedding in site).
- Use HTTPS for public endpoints.
- Enforce private key file permissions (`chmod 600`) if mounting a file.

Support notes
- If you want, I can produce:
  - a ready `Dockerfile` + `docker-compose.yml` and test run commands, or
  - a small Flask blueprint version to drop into an existing site.

Contact handoff
- When sending the package to your friend, include the sanitized archive (no private key) plus a separate secure transfer of the `instructor_private.pem` (or its base64). Also provide this `STEERING.md`.

-- End
