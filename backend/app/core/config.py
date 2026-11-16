import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()


class Settings:
    """Application Settings loaded from environment variables."""

    # Application Metadata
    APP_NAME: str = os.getenv(
        "APP_NAME", "AI-Based Real-Time Student Performance Prediction System"
    )
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Server Settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

    # Security & CORS
    SECRET_KEY: str = os.getenv("SECRET_KEY", "temporary_dev_secret_key_change_me")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or os.getenv(
        "SECRET_KEY", "temporary_jwt_secret_key_change_me"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )  # 24 hours default

    # Parse allowed origins as a list
    _raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in _raw_origins.split(",") if origin.strip()
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # PostgreSQL Database Credentials
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "student_perf_db")

    # Database URL with psycopg (v3) driver
    _raw_db_url = os.getenv("DATABASE_URL")
    if _raw_db_url and _raw_db_url.strip():
        if _raw_db_url.startswith("postgresql://"):
            DATABASE_URL: str = _raw_db_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        else:
            DATABASE_URL: str = _raw_db_url
    else:
        DATABASE_URL: str = (
            f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
            f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )

    # Database connection pool settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))


settings = Settings()
