"""
Import all models and the Base class here so that Alembic and SQLAlchemy
have complete visibility into all table metadata.
"""

from app.db.base_class import Base, TimestampMixin
from app.models.academic_record import AcademicRecord
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Student",
    "Subject",
    "Attendance",
    "AcademicRecord",
    "Prediction",
    "Recommendation",
    "Notification",
]
