from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, TimestampMixin


class Prediction(Base, TimestampMixin):
    """AI Machine Learning prediction log and student academic risk evaluation."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    model_version: Mapped[str] = mapped_column(
        String(50), default="random_forest_v1.0", nullable=False
    )
    predicted_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    risk_probability: Mapped[float] = mapped_column(Float, nullable=False)
    feature_importance: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    prediction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="predictions")
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="prediction", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} student_id={self.student_id} risk={self.risk_level} prob={self.risk_probability}>"
