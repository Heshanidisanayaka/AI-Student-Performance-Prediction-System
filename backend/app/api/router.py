from fastapi import APIRouter
from app.api.v1.endpoints import attendance, auth, health, students, subjects

api_router = APIRouter()

# Health checks
api_router.include_router(health.router, tags=["Health"])

# Authentication & User Management
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Users"])

# Students & Records (with Role & Object-level Authorization)
api_router.include_router(students.router, prefix="/students", tags=["Students & Records"])

# Subjects & Modules Management (Task 5)
api_router.include_router(subjects.router, prefix="/subjects", tags=["Subjects & Modules"])

# Attendance Tracking (Task 6)
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance Tracking"])
