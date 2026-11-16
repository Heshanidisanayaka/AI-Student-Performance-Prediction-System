from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, require_admin
from app.core.config import settings
from app.core.security import (
    UserRole,
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.user import (
    AdminUserCreate,
    MessageResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter()


def build_user_response(user: User) -> UserResponse:
    """Helper to convert ORM User and linked Student to UserResponse."""
    student_id = user.student.id if user.student else None
    student_id_number = user.student.student_id_number if user.student else None
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        student_id=student_id,
        student_id_number=student_id_number,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Student",
    description=(
        "Public user registration. Enforces Student role assignment to prevent "
        "privilege escalation. Automatically initializes student profile."
    ),
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
) -> TokenResponse:
    # 1. Check if email is already registered
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    # 2. Check if student_id_number already exists if supplied
    if payload.student_id_number:
        existing_student = (
            db.query(Student)
            .filter(Student.student_id_number == payload.student_id_number)
            .first()
        )
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student ID number '{payload.student_id_number}' is already registered.",
            )

    # 3. Create User record (strictly assigned Student role)
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole.STUDENT.value,  # Enforce unprivileged role
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()  # Populate user.id

    # 4. Create linked Student entity
    names = payload.full_name.strip().split(" ", 1)
    first_name = names[0]
    last_name = names[1] if len(names) > 1 else ""

    student_id_num = (
        payload.student_id_number
        if payload.student_id_number
        else f"STU{user.id:05d}"
    )

    student = Student(
        user_id=user.id,
        student_id_number=student_id_num,
        first_name=first_name,
        last_name=last_name,
        email=user.email,
        academic_year="2025-2026",
        class_name="Class A",
        department=payload.department or "Computer Science",
        enrollment_year=payload.enrollment_year or 2026,
        current_semester=payload.current_semester or 1,
        status="active",
    )
    db.add(student)
    db.commit()
    db.refresh(user)

    # 5. Generate initial access token
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=build_user_response(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with email and password to receive a JWT access token.",
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact administrator.",
        )

    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=build_user_response(user),
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 Form Login",
    description="OAuth2-compatible login endpoint for Swagger UI Authorize modal.",
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    email = form_data.username.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=build_user_response(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current Authenticated User",
    description="Returns profile information for the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return build_user_response(current_user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Logs out the current session and instructs client to purge JWT token.",
)
def logout(
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    return MessageResponse(
        success=True,
        message=f"User {current_user.email} successfully logged out.",
    )


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin User Provisioning",
    description="Administrative endpoint to create privileged users (Admin, Lecturer, or Student).",
)
def create_privileged_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role.value,
        is_active=payload.is_active,
        is_superuser=(payload.role == UserRole.ADMIN),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return build_user_response(user)
