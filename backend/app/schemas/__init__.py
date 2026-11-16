"""Pydantic schemas for data validation and API request/response serialization."""

from app.schemas.health import DatabaseHealth, HealthResponse
from app.schemas.student import (
    PaginatedStudentResponse,
    StudentCreate,
    StudentPrivateDetail,
    StudentResponse,
    StudentUpdate,
)
from app.schemas.user import (
    AdminUserCreate,
    MessageResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

__all__ = [
    "HealthResponse",
    "DatabaseHealth",
    "UserRegister",
    "AdminUserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentPrivateDetail",
    "PaginatedStudentResponse",
]
