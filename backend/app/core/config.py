import base64
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    APP_NAME: str = "E-Yantra EEP Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "grading_user"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "grading_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
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
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE_THIS"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Proof signing — same key must be embedded in the grader binary
    PROOF_SIGNING_KEY: str = "CHANGE_THIS"

    # Rate limiting
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10

    # EEP verifier (.eep1 / .eep2 / .eep3) RSA decryption
    RSA_PRIVATE_KEY_PATH: str = "keys/instructor_private.pem"
    RSA_PRIVATE_KEY_B64: str = ""
    EEP_MAX_UPLOAD_BYTES: int = 50000

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
