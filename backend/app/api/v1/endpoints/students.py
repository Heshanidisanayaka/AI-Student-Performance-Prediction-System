import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.api.deps import (
    get_current_active_user,
    require_admin,
    require_lecturer,
    verify_student_access,
)
from app.core.security import UserRole, get_password_hash
from app.db.session import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.student import (
    PaginatedStudentResponse,
    StudentCreate,
    StudentPrivateDetail,
    StudentResponse,
    StudentUpdate,
)
from app.schemas.user import MessageResponse

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedStudentResponse,
    status_code=status.HTTP_200_OK,
    summary="List, Search, and Filter Students",
    description=(
        "Retrieves a paginated directory of students with multi-field search, "
        "department/class/status filters, and dynamic sorting. Restricted to Lecturers and Admins."
    ),
)
def list_students(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, student ID, or email"),
    department: Optional[str] = Query(None, description="Filter by department"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    class_name: Optional[str] = Query(None, description="Filter by class/section"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    semester: Optional[int] = Query(None, ge=1, le=12, description="Filter by current semester"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort direction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
) -> PaginatedStudentResponse:
    query = db.query(Student)

    # 1. Search across name, student ID number, and email
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Student.first_name.ilike(term),
                Student.last_name.ilike(term),
                Student.student_id_number.ilike(term),
                Student.email.ilike(term),
            )
        )

    # 2. Field Filters
    if department and department.strip():
        query = query.filter(Student.department == department.strip())

    if academic_year and academic_year.strip():
        query = query.filter(Student.academic_year == academic_year.strip())

    if class_name and class_name.strip():
        query = query.filter(Student.class_name == class_name.strip())

    if status_filter and status_filter.strip():
        query = query.filter(Student.status == status_filter.strip().lower())

    if semester is not None:
        query = query.filter(Student.current_semester == semester)

    # 3. Dynamic Sorting
    allowed_sort_fields = {
        "id": Student.id,
        "student_id_number": Student.student_id_number,
        "first_name": Student.first_name,
        "last_name": Student.last_name,
        "email": Student.email,
        "department": Student.department,
        "class_name": Student.class_name,
        "academic_year": Student.academic_year,
        "current_semester": Student.current_semester,
        "status": Student.status,
        "created_at": Student.created_at,
    }
    sort_column = allowed_sort_fields.get(sort_by, Student.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 4. Pagination
    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return PaginatedStudentResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Student Profile",
    description=(
        "Creates a new student profile and prevents duplicate student IDs and emails. "
        "Automatically provisions an associated student user account if requested. "
        "Restricted to Lecturers and Administrators."
    ),
)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
) -> StudentResponse:
    # 1. Prevent duplicate Student ID
    existing_by_id = (
        db.query(Student)
        .filter(Student.student_id_number == payload.student_id_number.strip())
        .first()
    )
    if existing_by_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student ID '{payload.student_id_number}' is already registered.",
        )

    # 2. Prevent duplicate Email
    existing_by_email = (
        db.query(Student).filter(Student.email == payload.email.strip().lower()).first()
    )
    if existing_by_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with email '{payload.email}' already exists.",
        )

    # 3. Connect to user account
    user_id = payload.user_id
    if user_id:
        existing_user = db.query(User).filter(User.id == user_id).first()
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User account with ID {user_id} does not exist.",
            )
    elif payload.create_user_account:
        # Check if user with this email already exists
        user_match = db.query(User).filter(User.email == payload.email.strip().lower()).first()
        if user_match:
            user_id = user_match.id
        else:
            # Auto-provision student user login account
            default_pass = payload.default_password or "StudentPass2026!"
            new_user = User(
                email=payload.email.strip().lower(),
                hashed_password=get_password_hash(default_pass),
                full_name=f"{payload.first_name.strip()} {payload.last_name.strip()}",
                role=UserRole.STUDENT.value,
                is_active=True,
                is_superuser=False,
            )
            db.add(new_user)
            db.flush()
            user_id = new_user.id

    # 4. Create Student entity
    student = Student(
        user_id=user_id,
        student_id_number=payload.student_id_number.strip(),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.strip().lower(),
        department=payload.department.strip(),
        academic_year=payload.academic_year.strip(),
        class_name=payload.class_name.strip(),
        current_semester=payload.current_semester,
        enrollment_year=payload.enrollment_year,
        gender=payload.gender,
        date_of_birth=payload.date_of_birth,
        status=payload.status.lower(),
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return student


@router.get(
    "/{student_id}",
    response_model=StudentPrivateDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Single Student Record",
    description=(
        "Retrieves detailed student profile metrics. "
        "Strictly enforces object-level authorization: Students can only view their own profile. "
        "Lecturers and Admins may view any student."
    ),
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StudentPrivateDetail:
    # Enforce object-level privacy
    verify_student_access(target_student_id=student_id, current_user=current_user)

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    return StudentPrivateDetail(
        id=student.id,
        user_id=student.user_id,
        student_id_number=student.student_id_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email or (student.user.email if student.user else None),
        department=student.department,
        academic_year=student.academic_year,
        class_name=student.class_name,
        current_semester=student.current_semester,
        enrollment_year=student.enrollment_year,
        gender=student.gender,
        date_of_birth=student.date_of_birth,
        status=student.status,
        created_at=student.created_at,
        updated_at=student.updated_at,
        attendance_count=len(student.attendance_records),
        records_count=len(student.academic_records),
        predictions_count=len(student.predictions),
    )


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Student Profile",
    description=(
        "Updates an existing student profile. Prevents conflicting duplicate "
        "student IDs and emails. Restricted to Lecturers and Administrators."
    ),
)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
) -> StudentResponse:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    # 1. Check duplicate Student ID if changing
    if payload.student_id_number and payload.student_id_number != student.student_id_number:
        conflict = (
            db.query(Student)
            .filter(
                Student.student_id_number == payload.student_id_number.strip(),
                Student.id != student_id,
            )
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student ID '{payload.student_id_number}' is already taken by another student.",
            )
        student.student_id_number = payload.student_id_number.strip()

    # 2. Check duplicate Email if changing
    if payload.email and payload.email.lower() != (student.email or "").lower():
        clean_email = payload.email.strip().lower()
        conflict = (
            db.query(Student)
            .filter(Student.email == clean_email, Student.id != student_id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{clean_email}' is already registered to another student.",
            )
        student.email = clean_email
        # Sync linked user account email if exists
        if student.user:
            student.user.email = clean_email

    # 3. Update remaining fields
    if payload.first_name is not None:
        student.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        student.last_name = payload.last_name.strip()
    if payload.first_name is not None or payload.last_name is not None:
        if student.user:
            student.user.full_name = f"{student.first_name} {student.last_name}"

    if payload.department is not None:
        student.department = payload.department.strip()
    if payload.academic_year is not None:
        student.academic_year = payload.academic_year.strip()
    if payload.class_name is not None:
        student.class_name = payload.class_name.strip()
    if payload.current_semester is not None:
        student.current_semester = payload.current_semester
    if payload.enrollment_year is not None:
        student.enrollment_year = payload.enrollment_year
    if payload.gender is not None:
        student.gender = payload.gender
    if payload.date_of_birth is not None:
        student.date_of_birth = payload.date_of_birth
    if payload.status is not None:
        student.status = payload.status.lower()

    db.commit()
    db.refresh(student)
    return student


@router.delete(
    "/{student_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Student Record",
    description=(
        "Permanently removes a student record and cascades deletion to academic records, "
        "attendance, and predictions. Restricted to Administrators."
    ),
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> MessageResponse:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    roll_num = student.student_id_number
    # Also delete associated student user account if it is a pure student role
    if student.user and student.user.role == UserRole.STUDENT.value and not student.user.is_superuser:
        db.delete(student.user)
    else:
        db.delete(student)

    db.commit()
    return MessageResponse(
        success=True,
        message=f"Student '{roll_num}' and associated academic records successfully deleted.",
    )
