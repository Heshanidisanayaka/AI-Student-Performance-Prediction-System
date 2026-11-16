import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.api.deps import (
    get_current_active_user,
    require_admin,
    require_lecturer,
)
from app.core.security import UserRole
from app.db.session import get_db
from app.models.enrollment import StudentSubject
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import (
    AssignLecturerRequest,
    EnrollStudentRequest,
    LecturerInfo,
    PaginatedSubjectResponse,
    StudentEnrollmentItem,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from app.schemas.user import MessageResponse

router = APIRouter()


def build_subject_response(subject: Subject) -> SubjectResponse:
    """Helper to convert ORM Subject to SubjectResponse schema with computed stats."""
    lecturer_info = None
    if subject.lecturer:
        lecturer_info = LecturerInfo(
            id=subject.lecturer.id,
            full_name=subject.lecturer.full_name,
            email=subject.lecturer.email,
        )

    return SubjectResponse(
        id=subject.id,
        code=subject.code,
        name=subject.name,
        description=subject.description,
        credits=subject.credits,
        department=subject.department,
        semester=subject.semester,
        academic_year=subject.academic_year,
        is_active=subject.is_active,
        lecturer_id=subject.lecturer_id,
        lecturer=lecturer_info,
        enrolled_count=len(subject.enrollments),
        created_at=subject.created_at,
        updated_at=subject.updated_at,
    )


@router.get(
    "/",
    response_model=PaginatedSubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="List, Search, and Filter Subjects",
    description="Retrieves a paginated list of curriculum subjects with search, status filters, and sorting.",
)
def list_subjects(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by code or title"),
    department: Optional[str] = Query(None, description="Filter by department"),
    semester: Optional[int] = Query(None, ge=1, le=12),
    academic_year: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive subjects"),
    lecturer_id: Optional[int] = Query(None),
    my_subjects_only: bool = Query(False, description="Filter subjects taught by or enrolled in by current user"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedSubjectResponse:
    query = db.query(Subject)

    # Search by code or title
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(Subject.code.ilike(term), Subject.name.ilike(term)))

    # Filters
    if department and department.strip():
        query = query.filter(Subject.department == department.strip())

    if semester is not None:
        query = query.filter(Subject.semester == semester)

    if academic_year and academic_year.strip():
        query = query.filter(Subject.academic_year == academic_year.strip())

    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)

    if lecturer_id is not None:
        query = query.filter(Subject.lecturer_id == lecturer_id)

    # Filter to current user's subjects
    if my_subjects_only:
        if current_user.role == UserRole.LECTURER.value:
            query = query.filter(Subject.lecturer_id == current_user.id)
        elif current_user.role == UserRole.STUDENT.value and current_user.student:
            query = query.join(StudentSubject).filter(
                StudentSubject.student_id == current_user.student.id
            )

    # Sorting
    allowed_sort_fields = {
        "id": Subject.id,
        "code": Subject.code,
        "name": Subject.name,
        "credits": Subject.credits,
        "department": Subject.department,
        "semester": Subject.semester,
        "academic_year": Subject.academic_year,
        "is_active": Subject.is_active,
        "created_at": Subject.created_at,
    }
    sort_col = allowed_sort_fields.get(sort_by, Subject.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size
    subjects = query.offset(offset).limit(size).all()

    return PaginatedSubjectResponse(
        items=[build_subject_response(s) for s in subjects],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.post(
    "/",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Subject (Admin Only)",
    description="Registers a new subject in the curriculum. Prevents duplicate subject codes.",
)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SubjectResponse:
    # 1. Prevent duplicate subject code
    clean_code = payload.code.strip().upper()
    existing = db.query(Subject).filter(Subject.code == clean_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subject code '{clean_code}' is already registered.",
        )

    # 2. Verify assigned lecturer if provided
    if payload.lecturer_id:
        lecturer = db.query(User).filter(User.id == payload.lecturer_id).first()
        if not lecturer or lecturer.role not in [UserRole.LECTURER.value, UserRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User ID {payload.lecturer_id} is not an authorized faculty lecturer.",
            )

    subject = Subject(
        code=clean_code,
        name=payload.name.strip(),
        description=payload.description,
        credits=payload.credits,
        department=payload.department.strip(),
        semester=payload.semester,
        academic_year=payload.academic_year.strip(),
        is_active=payload.is_active,
        lecturer_id=payload.lecturer_id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)

    return build_subject_response(subject)


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Subject Details",
    description="Returns detailed information for a specific subject, including assigned lecturer and student counts.",
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SubjectResponse:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )
    return build_subject_response(subject)


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Subject (Admin Only)",
    description="Updates existing subject details and validates code uniqueness.",
)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SubjectResponse:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )

    # Check duplicate code if updating
    if payload.code and payload.code.upper() != subject.code:
        clean_code = payload.code.strip().upper()
        conflict = (
            db.query(Subject)
            .filter(Subject.code == clean_code, Subject.id != subject_id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subject code '{clean_code}' is already assigned to another course.",
            )
        subject.code = clean_code

    if payload.name is not None:
        subject.name = payload.name.strip()
    if payload.description is not None:
        subject.description = payload.description
    if payload.credits is not None:
        subject.credits = payload.credits
    if payload.department is not None:
        subject.department = payload.department.strip()
    if payload.semester is not None:
        subject.semester = payload.semester
    if payload.academic_year is not None:
        subject.academic_year = payload.academic_year.strip()
    if payload.is_active is not None:
        subject.is_active = payload.is_active

    if payload.lecturer_id is not None:
        if payload.lecturer_id == 0:
            subject.lecturer_id = None
        else:
            lecturer = db.query(User).filter(User.id == payload.lecturer_id).first()
            if not lecturer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lecturer with ID {payload.lecturer_id} does not exist.",
                )
            subject.lecturer_id = payload.lecturer_id

    db.commit()
    db.refresh(subject)
    return build_subject_response(subject)


@router.patch(
    "/{subject_id}/deactivate",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle Subject Active/Deactivated State (Admin Only)",
    description="Deactivates or reactivates a subject without deleting historical records.",
)
def toggle_subject_active(
    subject_id: int,
    is_active: bool = Query(False, description="Target active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SubjectResponse:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )

    subject.is_active = is_active
    db.commit()
    db.refresh(subject)
    return build_subject_response(subject)


@router.delete(
    "/{subject_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Subject (Admin Only)",
    description="Permanently deletes a subject and all associated enrollments.",
)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> MessageResponse:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )

    code = subject.code
    db.delete(subject)
    db.commit()
    return MessageResponse(
        success=True,
        message=f"Subject '{code}' successfully deleted.",
    )


@router.post(
    "/{subject_id}/lecturer",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign Lecturer to Subject (Admin Only)",
    description="Assigns or reassigns an academic staff member to lead the subject.",
)
def assign_lecturer(
    subject_id: int,
    payload: AssignLecturerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SubjectResponse:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )

    if payload.lecturer_id:
        lecturer = db.query(User).filter(User.id == payload.lecturer_id).first()
        if not lecturer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {payload.lecturer_id} not found.",
            )
        if lecturer.role not in [UserRole.LECTURER.value, UserRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{lecturer.full_name}' is not an authorized lecturer or admin.",
            )
        subject.lecturer_id = payload.lecturer_id
    else:
        subject.lecturer_id = None

    db.commit()
    db.refresh(subject)
    return build_subject_response(subject)


@router.get(
    "/{subject_id}/students",
    response_model=List[StudentEnrollmentItem],
    status_code=status.HTTP_200_OK,
    summary="Get Enrolled Students for Subject",
    description="Retrieves a list of all students enrolled in the specified subject.",
)
def get_enrolled_students(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[StudentEnrollmentItem]:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )

    # If student, verify they are enrolled or authorized
    if current_user.role == UserRole.STUDENT.value:
        if not current_user.student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no linked student profile.",
            )
        is_enrolled = (
            db.query(StudentSubject)
            .filter(
                StudentSubject.subject_id == subject_id,
                StudentSubject.student_id == current_user.student.id,
            )
            .first()
        )
        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students may only view rosters of subjects they are actively enrolled in.",
            )

    enrollments = (
        db.query(StudentSubject)
        .filter(StudentSubject.subject_id == subject_id)
        .all()
    )

    results = []
    for enr in enrollments:
        stu = enr.student
        results.append(
            StudentEnrollmentItem(
                enrollment_id=enr.id,
                student_id=stu.id,
                student_id_number=stu.student_id_number,
                first_name=stu.first_name,
                last_name=stu.last_name,
                email=stu.email or (stu.user.email if stu.user else None),
                department=stu.department,
                class_name=stu.class_name,
                academic_year=enr.academic_year,
                status=enr.status,
                enrolled_at=enr.enrolled_at,
            )
        )
    return results


@router.post(
    "/{subject_id}/enroll",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Enroll Students in Subject (Lecturer / Admin)",
    description="Enrolls one or more students into a subject for an academic year.",
)
def enroll_students(
    subject_id: int,
    payload: EnrollStudentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
) -> MessageResponse:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found.",
        )

    academic_year = payload.academic_year or subject.academic_year
    enrolled_count = 0

    for sid in payload.student_ids:
        student = db.query(Student).filter(Student.id == sid).first()
        if not student:
            continue

        existing_enr = (
            db.query(StudentSubject)
            .filter(
                StudentSubject.subject_id == subject_id,
                StudentSubject.student_id == sid,
                StudentSubject.academic_year == academic_year,
            )
            .first()
        )
        if not existing_enr:
            new_enr = StudentSubject(
                student_id=sid,
                subject_id=subject_id,
                academic_year=academic_year,
                status="enrolled",
            )
            db.add(new_enr)
            enrolled_count += 1

    db.commit()
    return MessageResponse(
        success=True,
        message=f"Successfully enrolled {enrolled_count} student(s) into '{subject.code}'.",
    )


@router.delete(
    "/{subject_id}/enroll/{student_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Unenroll Student from Subject (Lecturer / Admin)",
    description="Removes student enrollment from a subject.",
)
def unenroll_student(
    subject_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
) -> MessageResponse:
    enrollment = (
        db.query(StudentSubject)
        .filter(
            StudentSubject.subject_id == subject_id,
            StudentSubject.student_id == student_id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student ID {student_id} is not enrolled in subject {subject_id}.",
        )

    db.delete(enrollment)
    db.commit()
    return MessageResponse(
        success=True,
        message=f"Student successfully unenrolled from subject.",
    )
