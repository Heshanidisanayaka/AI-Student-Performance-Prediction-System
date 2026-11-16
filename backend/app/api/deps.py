from typing import List, Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import UserRole, decode_access_token
from app.db.session import get_db
from app.models.student import Student
from app.models.user import User

# OAuth2 scheme configured for OpenAPI Swagger UI Bearer authorization
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates JWT token from Authorization header and retrieves the user.
    Handles expired and invalid tokens with appropriate 401 status codes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise expired_exception
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifies that the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Please contact administrator.",
        )
    return current_user


class RoleChecker:
    """Reusable dependency to enforce role-based access control (RBAC)."""

    def __init__(self, allowed_roles: List[Union[UserRole, str]]):
        self.allowed_roles = [
            r.value if isinstance(r, UserRole) else str(r).lower()
            for r in allowed_roles
        ]

    def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # Superusers bypass role checks
        if current_user.is_superuser:
            return current_user

        if current_user.role.lower() not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Forbidden: Insufficient privileges. Required roles: {self.allowed_roles}. "
                    f"Current role: '{current_user.role}'."
                ),
            )
        return current_user


# Predefined RBAC dependencies
require_admin = RoleChecker([UserRole.ADMIN])
require_lecturer = RoleChecker([UserRole.ADMIN, UserRole.LECTURER])
require_student = RoleChecker([UserRole.STUDENT])


def verify_student_access(target_student_id: int, current_user: User) -> None:
    """
    Object-level authorization check:
    Students may strictly only view/modify their own student records.
    Admin and Lecturer roles possess institutional oversight.
    """
    if current_user.is_superuser:
        return

    user_role = current_user.role.lower()
    if user_role in [UserRole.ADMIN.value, UserRole.LECTURER.value]:
        return

    # Check student ownership
    if not current_user.student or current_user.student.id != target_student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students are strictly restricted to accessing their own private records.",
        )
