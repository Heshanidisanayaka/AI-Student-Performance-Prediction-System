from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Schema representing the PostgreSQL database connectivity status."""

    status: str = Field(..., example="connected", description="Database connection status")
    latency_ms: Optional[float] = Field(None, example=2.45, description="Ping query response latency in ms")
    database_name: Optional[str] = Field(None, example="student_perf_db", description="Target database name")
    error: Optional[str] = Field(None, description="Diagnostic error details if connection failed")


class HealthResponse(BaseModel):
    """Schema representing the comprehensive API health check response."""

    status: str = Field(..., example="healthy", description="Overall service health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Current deployment environment")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Current server timestamp in UTC",
    )
    database: Optional[DatabaseHealth] = Field(
        None, description="PostgreSQL database operational status"
    )
