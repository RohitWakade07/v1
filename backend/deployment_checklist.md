# Celery Architecture: Railway Deployment Checklist

Before your new Celery-based grading architecture can run successfully on Railway, you must complete the following configuration steps in your Railway Dashboard.

---

## 1. Environment Variables
Update the environment variables for both the **API Service** and the **Worker Service**.

### Add These Variables:
* `CELERY_BROKER_URL`: Set this to your Redis connection string (e.g., `redis://default:password@containers.railway.app:6379/0`).
* `CELERY_RESULT_BACKEND`: Set this to your Redis connection string (e.g., `redis://default:password@containers.railway.app:6379/1`).

*(Note: You can use the exact same Redis URL you are currently using for rate limiting and SSE).*

### Remove These Variables (Optional but recommended):
* `KAFKA_BOOTSTRAP_SERVERS`
* `KAFKA_SASL_USERNAME`
* `KAFKA_SASL_PASSWORD`
* `KAFKA_SECURITY_PROTOCOL`
* `KAFKA_SASL_MECHANISM`

---

## 2. Remote Docker Engine (`DOCKER_HOST`)
Because the new architecture uses **Pre-Warmed Docker Pools**, the Python worker must maintain a fleet of running Docker containers. 

Railway's default service containers **do not** have a Docker daemon running inside them due to security restrictions (no native Docker-in-Docker).

To allow the `DockerExecutor` to spawn containers, you must:
1. Provide a remote Docker engine (such as a dedicated VM or a secure TCP Docker socket).
2. Set the `DOCKER_HOST` environment variable in your **Worker Service** to point to this engine.
   * *Example*: `DOCKER_HOST=tcp://your-remote-docker-engine.com:2376`

> **Warning**: If `DOCKER_HOST` is not set, `docker.from_env()` will crash when the worker starts, because it will be unable to find a local `/var/run/docker.sock`.

---

## 3. Database Migrations
**No manual action required.** 
The `Dockerfile.api` is already configured to run `alembic upgrade head` before starting `gunicorn`. The moment Railway deploys the new API container, the new `SubmissionOutbox`, `GradingJob`, `ExecutionMetrics`, and `ExecutionLogs` tables will be automatically created in your PostgreSQL database.
