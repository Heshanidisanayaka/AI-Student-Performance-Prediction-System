"""SQLAlchemy models for the Student Performance Prediction System."""

from app.models.academic_record import AcademicRecord
from app.models.attendance import Attendance
from app.models.enrollment import StudentSubject
from app.models.notification import Notification
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User

__all__ = [
    "User",
    "Student",
    "Subject",
    "StudentSubject",
    "Attendance",
    "AcademicRecord",
    "Prediction",
    "Recommendation",
    "Notification",
]
