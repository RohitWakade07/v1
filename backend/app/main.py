from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.db.redis import get_redis, close_redis
from app.api.v1.endpoints import auth, session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[startup] {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    redis = await get_redis()
    await redis.ping()
    print("[startup] Redis connected")
    yield
    # Shutdown
    await close_redis()
    print("[shutdown] Redis connection closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,   # hide Swagger in production
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS — restrict to your on-premise frontend in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(session.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
