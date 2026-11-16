from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin


class StudentSubject(Base, TimestampMixin):
    """Enrollment entity mapping students to enrolled subjects with status and academic year."""

    __tablename__ = "student_subjects"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject_id", "academic_year", name="uq_student_subject_academic_year"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    academic_year: Mapped[str] = mapped_column(String(20), default="2025-2026", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="enrolled", nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<StudentSubject student_id={self.student_id} subject_id={self.subject_id} status={self.status}>"
