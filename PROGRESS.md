# Deployment Progress

## Phases

- [x] Phase 1: Repository audit — `REPOSITORY_AUDIT.md` created
- [x] Phase 2: Security fixes — `.env.example` real secrets replaced, `.gitignore` hardened
- [x] Phase 3: Backend deployment fixes — Railway URL overrides, `extra="ignore"`, CORS, health endpoint
- [x] Phase 4: Dockerfile — `Dockerfile.api` updated (Alembic step, non-root user, `$PORT`)
- [x] Phase 4b: `.dockerignore` created
- [x] Phase 5: Railway config — `railway.toml` + `RAILWAY_DEPLOYMENT.md`
- [ ] Phase 6: Docker Compose — existing `docker-compose.yml` is adequate; no changes needed
- [x] Phase 7: Frontend verification — `app/.env.example` created; API client confirmed clean
- [x] Phase 8: Documentation — `REPOSITORY_AUDIT.md`, this file, `DEPLOYMENT_STATUS.md`, `NEXT_STEPS.md`
- [ ] Phase 9: CI/CD — GitHub Actions workflow not yet created

## Known Issues

| Severity | Issue |
|---|---|
| P0 FIXED | Real secrets were in `.env.example` — replaced with placeholders |
| P1 FIXED | CORS was empty array in production — now reads `ALLOWED_ORIGINS` env var |
| P1 FIXED | Health endpoint didn't check Redis |
| P2 | Test dependencies mixed into `requirements.txt` — split into `requirements-dev.txt` |
| INFRA | Worker (Docker-in-Docker) cannot run on Railway shared runtime — needs VPS or self-hosted runner |

## Commits Needed

These changes are ready to commit (not yet committed — user must do this):

```
fix: security — replace real secrets in .env.example with placeholders
chore: harden root .gitignore for frontend, scratch files, and keys
fix: config — Railway URL overrides, extra=ignore, ALLOWED_ORIGINS, cors_origins
fix: main — dynamic CORS from settings, Redis health check
feat: Dockerfile.api — Alembic migration step, non-root user, PORT env var
feat: add .dockerignore for backend
feat: add railway.toml and RAILWAY_DEPLOYMENT.md
docs: add frontend .env.example
docs: add REPOSITORY_AUDIT.md, PROGRESS.md, DEPLOYMENT_STATUS.md, NEXT_STEPS.md
```
