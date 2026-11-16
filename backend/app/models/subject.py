from typing import List, Optional
from sqlalchemy import Integer, String, Text
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

    # Relationships
    attendance_records: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="subject", cascade="all, delete-orphan"
    )
    academic_records: Mapped[List["AcademicRecord"]] = relationship(
        "AcademicRecord", back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subject id={self.id} code={self.code} name={self.name}>"
