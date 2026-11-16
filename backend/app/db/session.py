import time
from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

# Initialize SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Automatically verify connections before using from pool
    echo=False,
)

# Factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session for a single request,
    ensuring proper commit/rollback and cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, float, str]:
    """
    Checks database connectivity by executing a lightweight query.
    Returns:
        (is_connected: bool, latency_ms: float, message: str)
    """
    start_time = time.perf_counter()
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            if result == 1:
                return True, round(latency_ms, 2), "Database connection healthy"
            return False, round(latency_ms, 2), "Unexpected query result"
    except SQLAlchemyError as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(f"Database health check failed: {exc}")
        return False, round(latency_ms, 2), str(exc)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(f"Unexpected database connection error: {exc}")
        return False, round(latency_ms, 2), str(exc)
