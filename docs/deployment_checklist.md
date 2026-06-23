# Celery Worker Deployment Checklist (Oracle Cloud / Docker Socket)

This document tracks what you need to configure before the Celery grading worker can execute real code.

---

## 1. Environment Variables

### Required on the Worker host (Oracle VM or Railway worker service)

| Variable | Example | Notes |
|---|---|---|
| `CELERY_BROKER_URL` | `redis://default:pass@host:6379/0` | Your Railway Redis URL |
| `CELERY_RESULT_BACKEND` | `redis://default:pass@host:6379/1` | Same Redis URL, DB index 1 |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:port/db` | Your Railway Postgres URL |
| `MINIO_ENDPOINT` | `s3.us-east-005.backblazeb2.com` | Backblaze B2 endpoint |
| `MINIO_ACCESS_KEY` | `0050ecb9...` | B2 key ID |
| `MINIO_SECRET_KEY` | `...` | B2 application key |
| `MINIO_BUCKET_NAME` | `eysip-eep-grading-2026` | Your B2 bucket |
| `MINIO_SECURE` | `True` | Must be True for B2 |

### Variables REMOVED (no longer needed)

- `DOCKER_HOST` — not used; socket is always `unix://var/run/docker.sock`
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_SASL_USERNAME`
- `KAFKA_SASL_PASSWORD`
- `KAFKA_SECURITY_PROTOCOL`
- `KAFKA_SASL_MECHANISM`

---

## 2. Docker Socket Mount

The worker container **must** have the Docker socket mounted as a volume so it can spin up sibling grading containers on the host.

**In docker-compose.yml (local / Oracle VM):**
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
  - grader_jobs:/tmp/autograder_jobs
```

**On Railway (worker service config):**

Add a volume mount pointing `/var/run/docker.sock` to the host socket. In Railway's service settings → Volumes, or via the `railway.toml`:
```toml
[[services]]
name = "worker"

[[services.volumes]]
source = "/var/run/docker.sock"
target = "/var/run/docker.sock"
```

> **Note:** Railway standard containers do NOT expose a Docker socket. You must either:
> - Deploy the worker on **Oracle Cloud Free Tier** (recommended), or
> - Use a Railway custom environment with Docker-in-Docker support.

---

## 3. Architecture: How Grading Works

```
Student submits code
        │
        ▼
FastAPI (Railway) ──► Postgres outbox
        │
        ▼ (poller picks up)
Celery task dispatched via Redis
        │
        ▼
Worker: run_fresh_container(language, image)
  ┌─────────────────────────────────────────┐
  │  docker run python:3.10-slim            │
  │  - user=nobody                          │
  │  - network_disabled=True                │
  │  - mem_limit=256m / memswap=256m        │
  │  - cpu_quota=50000 / cpu_period=100000  │
  │  - pids_limit=64                        │
  │  - read_only=True                       │
  │  - tmpfs=/tmp:size=128m,noexec          │
  │  - cap_drop=ALL                         │
  │  - no-new-privileges                    │
  └─────────────────────────────────────────┘
        │
        ▼
  exec_run(grading command)
        │
        ▼
  cleanup_container(container)   ← always runs, even on failure
        │
        ▼
  Write result to PostgreSQL
```

---

## 4. Files Changed in This Refactor

| File | Change |
|---|---|
| `workers/docker_executor.py` | Rewritten — socket client, `run_fresh_container()`, `cleanup_container()` |
| `app/services/pool_service.py` | **Deleted** — pool system fully removed |
| `app/celeryconfig.py` | Removed stale `replace_container` route |
| `docker-compose.yml` | Removed Kafka service and all `KAFKA_*` env vars; added socket + grader_jobs volume |

---

## 5. Database Migrations

No new migrations needed for this refactor.
The `alembic upgrade head` in `Dockerfile.api` runs automatically on deploy.
