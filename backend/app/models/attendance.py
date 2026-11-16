from datetime import date
from typing import Optional
from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin


class Attendance(Base, TimestampMixin):
    """Daily and session-based student attendance tracking."""

    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject_id", "date", "session_name", name="uq_student_subject_date_session"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    session_name: Mapped[str] = mapped_column(String(50), default="Session 1", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="present", nullable=False)  # 'present', 'absent', 'excused'
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Faculty/user who recorded this entry
    recorded_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="attendance_records")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="attendance_records")
    recorded_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[recorded_by_user_id])

    def __repr__(self) -> str:
        return f"<Attendance student_id={self.student_id} subject_id={self.subject_id} date={self.date} session={self.session_name} status={self.status}>"
