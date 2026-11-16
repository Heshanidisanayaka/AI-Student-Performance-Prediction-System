from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"

    @classmethod
    def from_str(cls, value: str) -> "AttendanceStatus":
        clean = value.strip().lower()
        for member in cls:
            if member.value == clean:
                return member
        raise ValueError(f"Status must be one of: {[m.value for m in cls]}")


class AttendanceRecordItem(BaseModel):
    """Single student attendance marking inside a session."""

    student_id: int
    status: str = Field("present", example="present")
    remarks: Optional[str] = Field(None, example="Medical certificate provided")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("present", "absent", "excused"):
            raise ValueError("Status must be 'present', 'absent', or 'excused'.")
        return clean


class AttendanceSessionCreate(BaseModel):
    """Payload to record attendance for an entire subject session."""

    subject_id: int
    date: date
    session_name: str = Field("Session 1", example="Session 1", min_length=1, max_length=50)
    records: List[AttendanceRecordItem] = Field(..., min_length=1)


class AttendanceSingleCreate(BaseModel):
    """Payload to record or manually log attendance for an individual student."""

    student_id: int
    subject_id: int
    date: date
    session_name: str = Field("Session 1", example="Session 1")
    status: str = Field("present")
    remarks: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("present", "absent", "excused"):
            raise ValueError("Status must be 'present', 'absent', or 'excused'.")
        return clean


class AttendanceUpdate(BaseModel):
    """Payload to update an existing attendance record."""

    status: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            if clean not in ("present", "absent", "excused"):
                raise ValueError("Status must be 'present', 'absent', or 'excused'.")
            return clean
        return v


class AttendanceResponse(BaseModel):
    """Attendance record view with student, subject, and recorder details."""

    id: int
    student_id: int
    student_name: str
    student_id_number: str
    subject_id: int
    subject_code: str
    subject_name: str
    date: date
    session_name: str
    status: str
    remarks: Optional[str] = None
    recorded_by_user_id: Optional[int] = None
    recorded_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaginatedAttendanceResponse(BaseModel):
    """Paginated attendance history response."""

    items: List[AttendanceResponse]
    total: int
    page: int
    size: int
    pages: int


class AttendanceStats(BaseModel):
    """Attendance metrics calculated according to the institutional Excused Absence policy."""

    total_sessions: int
    present_count: int
    absent_count: int
    excused_count: int
    effective_sessions: int = Field(
        ..., description="Total countable sessions excluding excused absences: (total - excused)"
    )
    attendance_percentage: float = Field(
        ..., description="Present / (Total - Excused) * 100"
    )
    policy_note: str = (
        "Institutional Policy: Excused absences do not penalize the student and are excluded "
        "from the denominator [Percentage = Present / (Total - Excused) * 100]."
    )


class SubjectAttendanceSummary(BaseModel):
    """Subject-wise summary metrics for a student."""

    subject_id: int
    subject_code: str
    subject_name: str
    stats: AttendanceStats


class StudentAttendanceSummary(BaseModel):
    """Detailed summary of attendance for a student across all subjects."""

    student_id: int
    student_name: str
    student_id_number: str
    overall_stats: AttendanceStats
    subject_breakdown: List[SubjectAttendanceSummary]


class AttendanceAnalytics(BaseModel):
    """Aggregated analytics data for Recharts visualizations."""

    daily_trends: List[dict]  # [{date: '2026-11-10', present: 24, absent: 3, excused: 1, rate: 88.9}]
    subject_comparisons: List[dict]  # [{subject_code: 'CS101', subject_name: 'Intro', percentage: 92.4, sessions: 12}]
    status_distribution: List[dict]  # [{name: 'Present', value: 120}, {name: 'Absent', value: 14}, {name: 'Excused', value: 6}]
    overall_stats: AttendanceStats
