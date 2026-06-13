import base64
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore Railway-injected vars that aren't declared here
    )

    # App
    APP_NAME: str = "E-Yantra EEP Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database — individual components (used for local dev / docker-compose)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "grading_user"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "grading_db"

    # Railway injects a single DATABASE_URL — takes precedence when set
    DATABASE_URL_OVERRIDE: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("DATABASE_URL", "DATABASE_URL_OVERRIDE")
    )
    # Railway injects a single REDIS_URL — takes precedence when set
    REDIS_URL_OVERRIDE: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("REDIS_URL", "REDIS_URL_OVERRIDE")
    )

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            if url.startswith("postgresql://") and "+" not in url.split("://")[0]:
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            for prefix in ["postgres://", "postgresql://", "postgresql+asyncpg://"]:
                if url.startswith(prefix):
                    base = "postgresql://" if prefix == "postgres://" else url[: url.index("://") + 3].replace("+asyncpg", "")
                    return url.replace(prefix, "postgresql+psycopg2://", 1)
            return url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_URL_OVERRIDE:
            return self.REDIS_URL_OVERRIDE
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE_THIS"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Proof signing — same key must be embedded in the grader binary
    PROOF_SIGNING_KEY: str = "CHANGE_THIS"

    # Evaluator bootstrap (used by start-evaluator endpoint)
    EVALUATOR_SHARED_KEY: str = ""

    # CORS — comma-separated list of allowed origins for production
    # e.g. "https://app.example.com,https://admin.example.com"
    ALLOWED_ORIGINS: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """Always includes localhost for dev; prepends configured prod origins.
        Empty ALLOWED_ORIGINS → localhost only (never an empty list).
        """
        local = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
        ]
        if self.ALLOWED_ORIGINS.strip():
            prod = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
            return list(dict.fromkeys(prod + local))  # prod first, no duplicates
        return local

    # Rate limiting
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10

    # Celery & Redis
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # MinIO / S3
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_SUBMISSIONS: str = "submissions"
    MINIO_BUCKET_ASSETS: str = "grader-assets"
    MINIO_USE_SSL: bool = False
    MINIO_REGION: str = "us-east-1"  # use "auto" for Cloudflare R2

    # EEP verifier (.eep1 / .eep2 / .eep3) RSA decryption
    RSA_PRIVATE_KEY_PATH: str = "keys/instructor_private.pem"
    RSA_PRIVATE_KEY_B64: str = ""
    EEP_MAX_UPLOAD_BYTES: int = 5_000_000

    # Instructor files directory (replace hardcoded paths)
    INSTRUCTOR_FILES_DIR: str = "/app/instructor_files"

    # AI Feedback — disabled by default
    ENABLE_AI_FEEDBACK: bool = False
    AI_FEEDBACK_MODEL: str = "claude-sonnet-4-20250514"
    AI_FEEDBACK_MAX_TOKENS: int = 500

    @model_validator(mode="after")
    def materialize_rsa_private_key(self) -> "Settings":
        """Decode RSA_PRIVATE_KEY_B64 into /tmp for production deployments."""
        if self.RSA_PRIVATE_KEY_B64 and self.RSA_PRIVATE_KEY_B64.strip():
            key_path = Path("/tmp/instructor_private.pem")
            key_path.write_bytes(base64.b64decode(self.RSA_PRIVATE_KEY_B64.strip()))
            self.RSA_PRIVATE_KEY_PATH = str(key_path)
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
