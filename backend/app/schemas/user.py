import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.core.security import UserRole


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegister(BaseModel):
    """Schema for public user registration. Enforces Student role assignment."""

    email: str = Field(..., example="student@university.edu", description="Valid university email address")
    full_name: str = Field(..., min_length=2, max_length=100, example="Jane Doe")
    password: str = Field(..., min_length=8, max_length=128, example="SecretPassword123")
    student_id_number: Optional[str] = Field(None, example="STU2026001", description="Student enrollment ID")
    department: Optional[str] = Field("Computer Science", example="Computer Science")
    enrollment_year: Optional[int] = Field(2026, example=2026)
    current_semester: Optional[int] = Field(1, ge=1, le=12, example=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("Invalid email address format.")
        return clean_email

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one alphabet character.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class AdminUserCreate(BaseModel):
    """Schema for administrative user creation (Admin or Lecturer accounts)."""

    email: str = Field(..., example="professor@university.edu")
    full_name: str = Field(..., min_length=2, max_length=100, example="Dr. Alan Turing")
    password: str = Field(..., min_length=8, max_length=128, example="AdminPass2026!")
    role: UserRole = Field(..., example=UserRole.LECTURER, description="Privileged role to assign")
    is_active: bool = Field(True)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("Invalid email address format.")
        return clean_email

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    """Schema for user login credentials."""

    email: str = Field(..., example="student@university.edu")
    password: str = Field(..., example="SecretPassword123")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    """Schema for returning user information."""

    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    student_id: Optional[int] = None
    student_id_number: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for returning JWT tokens."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifespan in seconds")
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response schema."""

    success: bool = True
    message: str
