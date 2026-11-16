import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import setup_error_handlers
from app.core.logging import logger
from app.db.session import check_db_connection
from app.schemas.health import DatabaseHealth, HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for application startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} [Environment: {settings.APP_ENV}]")
    logger.info(f"Allowed CORS origins: {settings.CORS_ORIGINS}")
    
    # Check database connection on startup
    db_ok, latency, msg = check_db_connection()
    if db_ok:
        logger.info(f"PostgreSQL connection verified ({latency:.2f}ms) on {settings.POSTGRES_DB}")
    else:
        logger.warning(f"PostgreSQL initial check failed: {msg}")

    logger.info(f"Swagger docs available at http://{settings.HOST}:{settings.PORT}/docs")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


# OpenAPI metadata tags definition
tags_metadata = [
    {
        "name": "Authentication & Users",
        "description": "User registration, JWT authentication, current user profile, and RBAC provisioning.",
    },
    {
        "name": "Students & Records",
        "description": "Student management with strict role-based and object-level authorization.",
    },
    {
        "name": "Subjects & Modules",
        "description": "Subject and curriculum management, lecturer assignments, and student course enrollments.",
    },
    {
        "name": "Attendance Tracking",
        "description": "Session-based attendance tracking, bulk logging, excused absence policy calculations, and analytics.",
    },
    {
        "name": "Health",
        "description": "System health monitoring, diagnostics, and PostgreSQL connectivity checks.",
    },
    {
        "name": "Root",
        "description": "Root entry points and API service metadata.",
    },
]

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "REST API for the AI-Based Real-Time Student Performance Prediction System. "
        "Provides real-time academic risk prediction, telemetry, and analytics backed by PostgreSQL."
    ),
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# CORS Middleware Configuration
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Request Logging & Profiling Middleware
# ------------------------------------------------------------------------------
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Logs incoming HTTP requests, process times, and response status codes."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000.0

    client_host = request.client.host if request.client else "unknown"
    logger.info(
        f"{client_host} - \"{request.method} {request.url.path}\" "
        f"{response.status_code} ({process_time_ms:.2f}ms)"
    )
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
    return response


# ------------------------------------------------------------------------------
# Centralized Error Handlers Registration
# ------------------------------------------------------------------------------
setup_error_handlers(app)

# ------------------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)


# ------------------------------------------------------------------------------
# Root-Level Endpoints
# ------------------------------------------------------------------------------
@app.get(
    "/",
    tags=["Root"],
    status_code=status.HTTP_200_OK,
    summary="Root Service Info",
    description="Returns general metadata, health status, and links to documentation.",
)
def root():
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": f"{settings.API_V1_STR}/health",
        "db_health_check": f"{settings.API_V1_STR}/health/db",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    status_code=status.HTTP_200_OK,
    summary="Convenience Root Health Check",
    description="Root-level shortcut for operational and database health checks.",
)
def root_health(response: Response) -> HealthResponse:
    db_ok, latency, msg = check_db_connection()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc),
        database=DatabaseHealth(
            status="connected" if db_ok else "disconnected",
            latency_ms=latency if db_ok else None,
            database_name=settings.POSTGRES_DB,
            error=None if db_ok else msg,
        ),
    )


@app.get(
    "/health/db",
    response_model=DatabaseHealth,
    tags=["Health"],
    status_code=status.HTTP_200_OK,
    summary="Root Database Diagnostic Check",
    description="Root-level shortcut for PostgreSQL database connectivity.",
)
def root_db_health(response: Response) -> DatabaseHealth:
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
