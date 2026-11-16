from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin


class Subject(Base, TimestampMixin):
    """Course and curriculum subject entity."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credits: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), default="2025-2026", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Assigned Lecturer
    lecturer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    lecturer: Mapped[Optional["User"]] = relationship(
        "User", back_populates="subjects_taught", foreign_keys=[lecturer_id]
    )

    # Student Enrollments
    enrollments: Mapped[List["StudentSubject"]] = relationship(
        "StudentSubject", back_populates="subject", cascade="all, delete-orphan"
    )
    enrolled_students: Mapped[List["Student"]] = relationship(
        "Student", secondary="student_subjects", back_populates="enrolled_subjects", viewonly=True
    )

    # Academic & Attendance Records
    attendance_records: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="subject", cascade="all, delete-orphan"
    )
    academic_records: Mapped[List["AcademicRecord"]] = relationship(
        "AcademicRecord", back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subject id={self.id} code={self.code} name={self.name} active={self.is_active}>"
