from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.db.redis import get_redis, close_redis
from app.api.v1.endpoints import auth, assignments, sessions, proof, results


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[startup] {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    redis = await get_redis()
    await redis.ping()
    print("[startup] PostgreSQL and Redis connected")
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
    allow_origins=["http://localhost:3000"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth.router,        prefix=PREFIX)
app.include_router(assignments.router, prefix=PREFIX)
app.include_router(sessions.router,    prefix=PREFIX)
app.include_router(proof.router,       prefix=PREFIX)
app.include_router(results.router,     prefix=PREFIX)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
