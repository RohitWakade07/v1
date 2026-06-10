from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.redis import get_redis, close_redis
from app.api.v1.endpoints import (
    auth,
    assignments,
    sessions,
    proof,
    proof_eep,
    results,
    admin,
    mentor,
    students,
    classrooms,
    submissions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[startup] {settings.APP_NAME} v{settings.APP_VERSION}")
    # NOTE: Database schema creation/migrations are handled via Alembic.
    # Do NOT call SQLModel.metadata.create_all() in production startup.
    redis = await get_redis()
    await redis.ping()
    print("[startup] Redis connected")
    yield
    await close_redis()
    print("[shutdown] connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth.router,        prefix=PREFIX)
app.include_router(assignments.router, prefix=PREFIX)
app.include_router(sessions.router,    prefix=PREFIX)
app.include_router(submissions.router, prefix=PREFIX)
app.include_router(proof.router,       prefix=PREFIX)
app.include_router(proof_eep.router,   prefix=PREFIX)
app.include_router(results.router,     prefix=PREFIX)
app.include_router(admin.router,       prefix=PREFIX)
app.include_router(mentor.router,      prefix=PREFIX)
app.include_router(students.router,    prefix=PREFIX)
app.include_router(classrooms.router,  prefix=PREFIX)


@app.get("/health", tags=["Health"])
async def health():
    db_status = "ok"
    try:
        from sqlalchemy import text
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return {"status": "ok", "database": db_status, "version": settings.APP_VERSION}

# Trivial comment to force uvicorn reload
 
