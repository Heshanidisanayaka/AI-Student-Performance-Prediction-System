from datetime import date
from typing import Optional
from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin


class AcademicRecord(Base, TimestampMixin):
    """Academic evaluation, assignment, exam scores, and performance history."""

    __tablename__ = "academic_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    weightage_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    recorded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="academic_records")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="academic_records")

    def __repr__(self) -> str:
        return f"<AcademicRecord student_id={self.student_id} subject_id={self.subject_id} assessment={self.assessment_type} score={self.score}/{self.max_score}>"
