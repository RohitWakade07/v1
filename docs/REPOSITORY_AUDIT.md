# Repository Audit — E-Yantra EEP Platform

_Generated during deployment preparation. Update this file as issues are resolved._

---

## Section 1 — Project Structure

```
A:\eysip\v1\
├── app/                        Frontend — Vite + React 18 + TypeScript + TailwindCSS
│   ├── src/
│   │   ├── api/                Axios client + endpoint modules
│   │   ├── components/         Shared UI components (shadcn/ui + custom)
│   │   ├── pages/              Student / Mentor / Admin portal pages
│   │   ├── store/              Zustand stores (auth, notifications)
│   │   └── router/             React Router routes with RoleGuard
│   ├── vite.config.ts
│   └── package.json
├── backend/                    Python backend
│   ├── app/                    FastAPI application
│   │   ├── api/v1/             Routes and dependencies
│   │   ├── core/               Config and security
│   │   ├── db/                 Session, Redis, sync session
│   │   ├── models/             SQLModel models
│   │   ├── repositories/       DB query layer
│   │   ├── schemas/            Pydantic request/response schemas
│   │   └── services/           Business logic
│   ├── workers/                Kafka consumer + Docker executor
│   ├── graders/                Per-week grading scripts and test assets
│   ├── alembic/                Database migration scripts
│   ├── tests/                  Pytest test suite
│   ├── Dockerfile.api          Production API image
│   ├── Dockerfile.worker       Grading worker image
│   ├── docker-compose.yml      Full local dev stack
│   ├── requirements.txt        Python dependencies
│   ├── .env.example            Safe template — no real secrets [VERIFIED]
│   ├── .env                    [SHOULD NOT BE COMMITTED — in .gitignore]
│   ├── backend_log*.txt        [SHOULD NOT BE COMMITTED — in .gitignore]
│   ├── sync_test.txt           [SHOULD NOT BE COMMITTED — in .gitignore]
│   ├── challenge.json          [SHOULD NOT BE COMMITTED — in .gitignore]
│   ├── check_db.py             [SHOULD NOT BE COMMITTED — in .gitignore]
│   ├── alter_db.py             [SHOULD NOT BE COMMITTED — in .gitignore]
│   ├── *.zip                   [SHOULD NOT BE COMMITTED — in .gitignore]
│   └── venv/                   [SHOULD NOT BE COMMITTED — in .gitignore]
├── railway.toml                Railway deployment config
├── RAILWAY_DEPLOYMENT.md       Step-by-step Railway deployment guide
├── REPOSITORY_AUDIT.md         This file
├── PROGRESS.md                 Deployment phase tracking
├── DEPLOYMENT_STATUS.md        Current deployment readiness
├── NEXT_STEPS.md               Instructions for next session
└── README.md                   Project overview
```

---

## Section 2 — Backend Audit

### `app/main.py` ✅
- Lifespan: no `init_db()` call — clean. Alembic handles schema.
- CORS: now reads `settings.cors_origins` in production (fixed).
- Docs: guarded by `settings.DEBUG` — correct.
- Health: now checks both DB and Redis, returns `degraded` instead of `500` (fixed).

### `app/core/config.py` ✅ (fixed)
- Added `DATABASE_URL_OVERRIDE` and `REDIS_URL_OVERRIDE` for Railway.
- Added `extra="ignore"` so Railway-injected env vars don't crash Pydantic.
- Added `ALLOWED_ORIGINS` + `cors_origins` property.
- `PROOF_SIGNING_KEY` and `JWT_SECRET_KEY` default to `"CHANGE_THIS"` — correct for template.

### `app/db/session.py` ✅
- `init_db()` defined but NOT called in production startup — correct.
- `AsyncSessionLocal` used correctly.

### `app/db/redis.py` ✅
- Uses `settings.REDIS_URL` — works with Railway Redis URL override.

### `alembic/env.py` ✅
- Uses `settings.DATABASE_URL_SYNC` for offline/sync migrations.
- Uses `settings.DATABASE_URL` for async online migrations.

### `requirements.txt` ⚠️
- Test dependencies (`pytest`, `pytest-asyncio`, `aiosqlite`) are mixed into production requirements.
- Recommend splitting into `requirements.txt` (prod) and `requirements-dev.txt` (test/dev).
- All versions are pinned — good.
- `asyncpg`, `psycopg2-binary`, `gunicorn` all present — good.

---

## Section 3 — Frontend Audit

### `vite.config.ts` ✅
- Dev proxy `/api → localhost:8000` is dev-only and does not affect production build.
- No hardcoded localhost in production code paths.

### `src/api/client.ts` ✅
- `baseURL` reads from `import.meta.env.VITE_API_BASE_URL` with fallback to `/api/v1`.
- The `/api/v1` fallback works correctly when the frontend is served from the same origin as the API (reverse proxy), or when using Vite's dev proxy.
- No hardcoded `http://localhost` in API files.

### `package.json` ✅
- `build` script: `tsc -b && vite build` — correct.
- `preview` script: present.
- All dependencies declared.

### Missing
- `app/.env.example` — **created** this session.

---

## Section 4 — Security Risks

| Severity | File | Issue | Status |
|---|---|---|---|
| **P0** | `backend/.env.example` | Real generated JWT and PROOF keys committed | **FIXED** — replaced with placeholders |
| **P0** | `backend/app/core/config.py` | No Railway URL override — would crash on first deploy | **FIXED** |
| **P1** | `backend/app/main.py` | CORS in production was `[]` (allowed nothing) | **FIXED** — now reads `settings.cors_origins` |
| **P1** | `backend/app/main.py` | Health endpoint didn't check Redis | **FIXED** |
| **P2** | `backend/requirements.txt` | Test deps in production requirements | Document only — low risk |
| **P2** | `backend/app/core/config.py` | No `extra="ignore"` — Railway vars could crash Pydantic startup | **FIXED** |
| **INFO** | `backend/.env` | Real `.env` exists locally | Correctly excluded by `.gitignore` |
| **INFO** | `backend/app/main.py` | `docs_url=None` when `DEBUG=False` | Already correct ✅ |

---

## Section 5 — Deployment Blockers (Railway)

| # | File | Problem | Fix Applied |
|---|---|---|---|
| 1 | `backend/app/core/config.py` | Railway injects `DATABASE_URL` as a single var; config used individual components only | ✅ Added `DATABASE_URL_OVERRIDE` property |
| 2 | `backend/app/core/config.py` | Railway injects extra env vars; Pydantic would raise `ValidationError` | ✅ Added `extra="ignore"` |
| 3 | `backend/Dockerfile.api` | No Alembic run before server start; DB would be empty | ✅ CMD now runs `alembic upgrade head` first |
| 4 | `backend/Dockerfile.api` | Hardcoded port `8000`; Railway overrides with `$PORT` | ✅ Added `ENV PORT=8000`, shell-form CMD |
| 5 | `backend/.env.example` | Real secrets committed — would be exposed in public repo | ✅ Replaced with placeholders |
| 6 | `backend/app/main.py` | CORS `[]` in production blocks all frontend requests | ✅ Now reads `settings.cors_origins` |

### Remaining blocker (not fixable in code)
- **Docker-in-Docker**: The grading worker spawns Docker containers. Railway's shared runtime does not support this. The API can deploy on Railway; the worker needs a VPS or self-hosted runner with Docker access.

---

## Section 6 — Missing Files

| File | Status |
|---|---|
| `railway.toml` | ✅ Created |
| `backend/Dockerfile.api` | ✅ Exists (updated) |
| `backend/Dockerfile.worker` | ✅ Exists |
| `backend/.dockerignore` | ✅ Created |
| `backend/alembic.ini` | ✅ Exists |
| `app/.env.example` | ✅ Created |
| `README.md` | ✅ Exists (adequate) |
| `LICENSE` | ❌ Not present — add before making repo public |
| `CONTRIBUTING.md` | ❌ Not present — optional |

---

## Section 7 — Dependency Issues

| Check | Status |
|---|---|
| Versions pinned in `requirements.txt` | ✅ All pinned |
| `asyncpg` present | ✅ |
| `psycopg2-binary` present | ✅ |
| `gunicorn` present | ✅ |
| `alembic` present | ✅ |
| Test deps mixed into prod requirements | ⚠️ `pytest`, `pytest-asyncio`, `aiosqlite` should move to `requirements-dev.txt` |
| `package.json` has `build` script | ✅ |
| `package.json` has `preview` script | ✅ |
