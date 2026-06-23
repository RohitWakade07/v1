# Deployment Progress

## Phases

- [x] Phase 1: Repository audit — `REPOSITORY_AUDIT.md` created
- [x] Phase 2: Security fixes — `.env.example` real secrets replaced, `.gitignore` hardened
- [x] Phase 3: Backend deployment fixes — Railway URL overrides, `extra=ignore`, CORS, health endpoint
- [x] Phase 4: Dockerfile — `Dockerfile.api` updated (Alembic step, non-root user, `$PORT`)
- [x] Phase 4b: `.dockerignore` created
- [x] Phase 5: Railway config — `railway.toml` + `RAILWAY_DEPLOYMENT.md`
- [x] Phase 6: Docker Compose — existing `docker-compose.yml` adequate, no changes needed
- [x] Phase 7: Frontend verification — `app/.env.example` created; API client confirmed clean
- [x] Phase 8: Documentation — audit, progress, status, next steps files created
- [x] All commits pushed ✅

## Remaining (optional improvements)

- [ ] Split `requirements.txt` — move pytest/aiosqlite to `requirements-dev.txt`
- [ ] Add GitHub Actions CI workflow
- [ ] Add `LICENSE` file before making repo public

## Known Issues

| Severity | Issue | Status |
|---|---|---|
| P0 | Real secrets in `.env.example` | FIXED & COMMITTED |
| P1 | CORS empty array in production | FIXED & COMMITTED |
| P1 | Health endpoint didn't check Redis | FIXED & COMMITTED |
| P2 | Test deps in prod `requirements.txt` | Open — low risk |
| INFRA | Worker requires Docker-in-Docker (Railway can't run this) | By design — use VPS for worker |
