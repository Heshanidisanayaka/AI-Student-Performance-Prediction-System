from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import DatabaseHealth, HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Comprehensive Health Check",
    description="Returns the operational status of the backend API and connected PostgreSQL database.",
    response_description="System and database operational status",
)
def get_health(response: Response) -> HealthResponse:
    """Performs an operational health check including database ping."""
    db_ok, latency, msg = check_db_connection()

    db_health = DatabaseHealth(
        status="connected" if db_ok else "disconnected",
        latency_ms=latency if db_ok else None,
        database_name=settings.POSTGRES_DB,
        error=None if db_ok else msg,
    )

    overall_status = "healthy" if db_ok else "degraded"
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc),
        database=db_health,
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealth,
    status_code=status.HTTP_200_OK,
    summary="Database Diagnostic Health Check",
    description="Tests direct PostgreSQL database connectivity and measures query response latency.",
    response_description="Database connectivity metrics",
)
def get_db_health(response: Response) -> DatabaseHealth:
    """Verifies PostgreSQL connectivity by executing a SELECT 1 query."""
    db_ok, latency, msg = check_db_connection()

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealth(
            status="disconnected",
            latency_ms=latency,
            database_name=settings.POSTGRES_DB,
            error=msg,
        )

    return DatabaseHealth(
        status="connected",
        latency_ms=latency,
        database_name=settings.POSTGRES_DB,
        error=None,
    )
