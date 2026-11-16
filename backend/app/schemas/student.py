import re
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class StudentBase(BaseModel):
    """Base student properties."""

    student_id_number: str = Field(..., min_length=2, max_length=50, example="STU2026001")
    first_name: str = Field(..., min_length=2, max_length=100, example="Emily")
    last_name: str = Field(..., min_length=1, max_length=100, example="Watson")
    email: str = Field(..., example="emily.watson@university.edu")
    department: str = Field(..., min_length=2, max_length=100, example="Computer Science")
    academic_year: str = Field("2025-2026", example="2025-2026")
    class_name: str = Field("Class A", example="CS-3A")
    current_semester: int = Field(1, ge=1, le=12, example=3)
    enrollment_year: int = Field(2026, ge=2000, le=2100, example=2026)
    gender: Optional[str] = Field(None, example="Female")
    date_of_birth: Optional[date] = Field(None, example="2005-04-12")
    status: str = Field("active", example="active")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("Invalid email address format.")
        return clean_email

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"active", "at_risk", "graduated", "suspended", "inactive"}
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v.lower()


class StudentCreate(StudentBase):
    """Schema for creating a new student record (Lecturer / Admin)."""

    create_user_account: bool = Field(
        True,
        description="Whether to automatically generate a student user login account if one doesn't exist",
    )
    user_id: Optional[int] = Field(
        None, description="Existing user ID to associate this student profile with"
    )
    default_password: Optional[str] = Field(
        None, min_length=8, description="Custom initial password if user account is created"
    )


class StudentUpdate(BaseModel):
    """Schema for updating an existing student profile."""

    student_id_number: Optional[str] = Field(None, min_length=2, max_length=50)
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    academic_year: Optional[str] = None
    class_name: Optional[str] = None
    current_semester: Optional[int] = Field(None, ge=1, le=12)
    enrollment_year: Optional[int] = Field(None, ge=2000, le=2100)
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    status: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean_email = v.strip().lower()
            if not EMAIL_REGEX.match(clean_email):
                raise ValueError("Invalid email address format.")
            return clean_email
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"active", "at_risk", "graduated", "suspended", "inactive"}
            if v.lower() not in allowed:
                raise ValueError(f"Status must be one of: {allowed}")
            return v.lower()
        return v


class StudentResponse(StudentBase):
    """Schema for public/administrative student view."""

    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentPrivateDetail(StudentResponse):
    """Detailed student record with operational counters."""

    attendance_count: int = 0
    records_count: int = 0
    predictions_count: int = 0


class PaginatedStudentResponse(BaseModel):
    """Paginated list of students with pagination metadata."""

    items: List[StudentResponse]
    total: int
    page: int
    size: int
    pages: int
