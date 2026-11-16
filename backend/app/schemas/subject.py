from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class LecturerInfo(BaseModel):
    """Basic lecturer profile information."""

    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    """Core attributes for curriculum subjects."""

    code: str = Field(..., min_length=2, max_length=50, example="CS101", description="Unique subject code")
    name: str = Field(..., min_length=2, max_length=255, example="Introduction to Computer Science")
    description: Optional[str] = Field(None, example="Foundations of programming, algorithms, and logic.")
    credits: int = Field(3, ge=1, le=12, example=3)
    department: str = Field(..., min_length=2, max_length=100, example="Computer Science")
    semester: int = Field(1, ge=1, le=12, example=1)
    academic_year: str = Field("2025-2026", example="2025-2026")
    is_active: bool = Field(True, description="Whether the subject is currently offered")

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()


class SubjectCreate(SubjectBase):
    """Schema for creating a new subject (Admin only)."""

    lecturer_id: Optional[int] = Field(None, description="Optional ID of assigned lecturer")


class SubjectUpdate(BaseModel):
    """Schema for updating an existing subject profile (Admin only)."""

    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=12)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    semester: Optional[int] = Field(None, ge=1, le=12)
    academic_year: Optional[str] = None
    is_active: Optional[bool] = None
    lecturer_id: Optional[int] = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v


class SubjectResponse(SubjectBase):
    """Public and administrative response model for subjects."""

    id: int
    lecturer_id: Optional[int] = None
    lecturer: Optional[LecturerInfo] = None
    enrolled_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedSubjectResponse(BaseModel):
    """Paginated list of subjects with pagination metadata."""

    items: List[SubjectResponse]
    total: int
    page: int
    size: int
    pages: int


class StudentEnrollmentItem(BaseModel):
    """Detailed view of an enrolled student in a subject."""

    enrollment_id: int
    student_id: int
    student_id_number: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    department: str
    class_name: str
    academic_year: str
    status: str
    enrolled_at: datetime


class EnrollStudentRequest(BaseModel):
    """Payload to enroll students into a subject."""

    student_ids: List[int] = Field(..., min_length=1, description="List of student IDs to enroll")
    academic_year: Optional[str] = Field("2025-2026", description="Academic session for enrollment")


class AssignLecturerRequest(BaseModel):
    """Payload to assign or remove a lecturer from a subject."""

    lecturer_id: Optional[int] = Field(None, description="Lecturer user ID, or null to unassign")
