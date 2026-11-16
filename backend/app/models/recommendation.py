from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin


class Recommendation(Base, TimestampMixin):
    """Actionable recommendations generated to mitigate predicted academic risks."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("predictions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="recommendations")
    student: Mapped["Student"] = relationship("Student", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} student_id={self.student_id} category={self.category} priority={self.priority}>"
