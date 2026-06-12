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

## 2. Docker Engine Bypass (Testing Mode)
Currently, Railway's default service containers **do not** have a Docker daemon running inside them. 

Because you requested to skip the `DOCKER_HOST` setup for now so that you can start testing your backend, the grading worker has been configured with a **Mock Execution Bypass**. 

**How it works:**
* If the Celery worker cannot connect to a Docker daemon, it will not crash.
* Instead, it will instantly return a "MOCKED EXECUTION SUCCESS" with a perfect score (5.0/5.0).
* This allows you to test the entire data pipeline (API Submission -> Postgres Outbox -> Poller -> Celery Task -> Database Write) end-to-end on Railway without needing a running Docker engine.

When you are ready to execute real code, you will need to provide a remote Docker host and set the `DOCKER_HOST` environment variable.

---

## 3. Database Migrations
**No manual action required.** 
The `Dockerfile.api` is already configured to run `alembic upgrade head` before starting `gunicorn`. The moment Railway deploys the new API container, the new `SubmissionOutbox`, `GradingJob`, `ExecutionMetrics`, and `ExecutionLogs` tables will be automatically created in your PostgreSQL database.
