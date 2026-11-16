import math
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload
from app.api.deps import (
    get_current_active_user,
    require_lecturer,
    verify_student_access,
)
from app.core.security import UserRole
from app.db.session import get_db
from app.models.attendance import Attendance
from app.models.enrollment import StudentSubject
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User
from app.schemas.attendance import (
    AttendanceAnalytics,
    AttendanceRecordItem,
    AttendanceResponse,
    AttendanceSessionCreate,
    AttendanceSingleCreate,
    AttendanceStats,
    AttendanceStatus,
    AttendanceUpdate,
    PaginatedAttendanceResponse,
    StudentAttendanceSummary,
    SubjectAttendanceSummary,
)
from app.schemas.user import MessageResponse

router = APIRouter()


def build_attendance_response(att: Attendance) -> AttendanceResponse:
    """Helper to convert ORM Attendance model to AttendanceResponse schema."""
    student_name = (
        f"{att.student.first_name} {att.student.last_name}" if att.student else "Unknown Student"
    )
    student_id_number = att.student.student_id_number if att.student else "N/A"
    subject_code = att.subject.code if att.subject else "N/A"
    subject_name = att.subject.name if att.subject else "N/A"
    recorded_by_name = att.recorded_by.full_name if att.recorded_by else None

    return AttendanceResponse(
        id=att.id,
        student_id=att.student_id,
        student_name=student_name,
        student_id_number=student_id_number,
        subject_id=att.subject_id,
        subject_code=subject_code,
        subject_name=subject_name,
        date=att.date,
        session_name=att.session_name,
        status=att.status,
        remarks=att.remarks,
        recorded_by_user_id=att.recorded_by_user_id,
        recorded_by_name=recorded_by_name,
        created_at=att.created_at,
        updated_at=att.updated_at,
    )


def compute_attendance_stats(records: List[Attendance]) -> AttendanceStats:
    """
    Computes attendance metrics using institutional Excused Absence policy:
    Attendance Percentage = Present / (Total Sessions - Excused) * 100
    Excused absences do not penalize students and are excluded from the denominator.
    """
    total = len(records)
    present = sum(1 for r in records if r.status.lower() == AttendanceStatus.PRESENT.value)
    absent = sum(1 for r in records if r.status.lower() == AttendanceStatus.ABSENT.value)
    excused = sum(1 for r in records if r.status.lower() == AttendanceStatus.EXCUSED.value)
    effective = total - excused

    if effective > 0:
        pct = round((present / effective) * 100.0, 2)
    elif total > 0:
        pct = 100.0
    else:
        pct = 0.0

    return AttendanceStats(
        total_sessions=total,
        present_count=present,
        absent_count=absent,
        excused_count=excused,
        effective_sessions=max(0, effective),
        attendance_percentage=pct,
    )


@router.post(
    "/session",
    response_model=List[AttendanceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record Attendance for a Subject Session",
    description="Bulk-records attendance for enrolled students in a subject session. Prevents duplicate session recording.",
)
def record_session_attendance(
    payload: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    """
    Lecturers & Admins: Record attendance for an entire classroom session.
    Enforces that the subject exists, students exist and are enrolled, and prevents duplicates.
    """
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {payload.subject_id} not found.",
        )

    # Check for existing duplicate records for this subject, date, and session
    existing_records = (
        db.query(Attendance)
        .filter(
            Attendance.subject_id == payload.subject_id,
            Attendance.date == payload.date,
            Attendance.session_name == payload.session_name,
        )
        .all()
    )
    existing_student_ids = {r.student_id for r in existing_records}

    conflicts = [r.student_id for r in payload.records if r.student_id in existing_student_ids]
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Attendance for subject '{subject.code}', date '{payload.date}', and session '{payload.session_name}' "
                f"has already been recorded for {len(conflicts)} student(s). Use the update endpoint to modify existing entries."
            ),
        )

    # Validate students exist
    submitted_student_ids = [r.student_id for r in payload.records]
    students = db.query(Student).filter(Student.id.in_(submitted_student_ids)).all()
    found_student_ids = {s.id for s in students}
    missing_students = [sid for sid in submitted_student_ids if sid not in found_student_ids]
    if missing_students:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Students not found with IDs: {missing_students}",
        )

    # Validate enrollment
    enrollments = (
        db.query(StudentSubject.student_id)
        .filter(
            StudentSubject.subject_id == payload.subject_id,
            StudentSubject.student_id.in_(submitted_student_ids),
        )
        .all()
    )
    enrolled_ids = {e[0] for e in enrollments}
    not_enrolled = [sid for sid in submitted_student_ids if sid not in enrolled_ids]
    if not_enrolled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student(s) with ID(s) {not_enrolled} are not enrolled in subject '{subject.code}'.",
        )

    # Create attendance records
    created_items = []
    for item in payload.records:
        att = Attendance(
            student_id=item.student_id,
            subject_id=payload.subject_id,
            date=payload.date,
            session_name=payload.session_name,
            status=item.status.lower(),
            remarks=item.remarks,
            recorded_by_user_id=current_user.id,
        )
        db.add(att)
        created_items.append(att)

    db.commit()

    # Eagerly reload to populate student and subject relationships for response
    for att in created_items:
        db.refresh(att)

    return [build_attendance_response(att) for att in created_items]


@router.post(
    "/",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log Single Student Attendance",
    description="Manually records or logs attendance for a single student in a specific session.",
)
def record_single_attendance(
    payload: AttendanceSingleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    """Lecturers & Admins: Record individual student attendance."""
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {payload.subject_id} not found.",
        )

    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {payload.student_id} not found.",
        )

    # Validate enrollment
    enrollment = (
        db.query(StudentSubject)
        .filter(
            StudentSubject.subject_id == payload.subject_id,
            StudentSubject.student_id == payload.student_id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student {student.student_id_number} is not enrolled in subject '{subject.code}'.",
        )

    # Check for duplicate
    duplicate = (
        db.query(Attendance)
        .filter(
            Attendance.student_id == payload.student_id,
            Attendance.subject_id == payload.subject_id,
            Attendance.date == payload.date,
            Attendance.session_name == payload.session_name,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Attendance for student {student.student_id_number} in subject '{subject.code}' "
                f"on {payload.date} ({payload.session_name}) has already been recorded."
            ),
        )

    att = Attendance(
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        date=payload.date,
        session_name=payload.session_name,
        status=payload.status.lower(),
        remarks=payload.remarks,
        recorded_by_user_id=current_user.id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)

    return build_attendance_response(att)


@router.get(
    "/",
    response_model=PaginatedAttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Attendance History",
    description="Retrieve attendance history with filtering by subject, student, date range, session, and status.",
)
def list_attendance(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    start_date: Optional[date] = Query(None, description="Filter from this date"),
    end_date: Optional[date] = Query(None, description="Filter up to this date"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: present, absent, excused"),
    session_name: Optional[str] = Query(None, description="Filter by session name (e.g., Session 1)"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Enforces privacy:
    Students can strictly only retrieve their own attendance records.
    Lecturers and Admins can query institutional attendance history.
    """
    query = (
        db.query(Attendance)
        .options(
            joinedload(Attendance.student),
            joinedload(Attendance.subject),
            joinedload(Attendance.recorded_by),
        )
    )

    # Role privacy enforcement
    if current_user.role.lower() == UserRole.STUDENT.value:
        if not current_user.student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account does not have an associated student profile.",
            )
        # Enforce student only views their own records
        query = query.filter(Attendance.student_id == current_user.student.id)
    else:
        if student_id is not None:
            query = query.filter(Attendance.student_id == student_id)

    if subject_id is not None:
        query = query.filter(Attendance.subject_id == subject_id)

    if start_date is not None:
        query = query.filter(Attendance.date >= start_date)

    if end_date is not None:
        query = query.filter(Attendance.date <= end_date)

    if status_filter:
        query = query.filter(func.lower(Attendance.status) == status_filter.strip().lower())

    if session_name:
        query = query.filter(Attendance.session_name.ilike(f"%{session_name.strip()}%"))

    total = query.count()
    pages = math.ceil(total / size) if size > 0 else 1

    records = (
        query.order_by(desc(Attendance.date), Attendance.session_name.asc(), desc(Attendance.id))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return PaginatedAttendanceResponse(
        items=[build_attendance_response(r) for r in records],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/analytics",
    response_model=AttendanceAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Get Attendance Analytics for Visualizations",
    description="Aggregated data for Recharts: daily trends, subject comparisons, and status distribution.",
)
def get_attendance_analytics(
    subject_id: Optional[int] = Query(None, description="Filter analytics by specific subject"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    """Provides structured time-series and comparative metrics for Recharts."""
    query = (
        db.query(Attendance)
        .options(
            joinedload(Attendance.subject),
            joinedload(Attendance.student),
        )
    )
    if subject_id is not None:
        query = query.filter(Attendance.subject_id == subject_id)

    all_records = query.order_by(Attendance.date.asc()).all()

    overall_stats = compute_attendance_stats(all_records)

    # 1. Daily trends
    daily_groups = {}
    for r in all_records:
        date_str = r.date.isoformat()
        if date_str not in daily_groups:
            daily_groups[date_str] = {"present": 0, "absent": 0, "excused": 0, "total": 0}
        stat = r.status.lower()
        if stat in daily_groups[date_str]:
            daily_groups[date_str][stat] += 1
        daily_groups[date_str]["total"] += 1

    daily_trends = []
    for d_str, counts in sorted(daily_groups.items()):
        eff = counts["total"] - counts["excused"]
        rate = round((counts["present"] / eff) * 100.0, 1) if eff > 0 else 100.0
        daily_trends.append({
            "date": d_str,
            "present": counts["present"],
            "absent": counts["absent"],
            "excused": counts["excused"],
            "percentage": rate,
        })

    # 2. Subject comparisons
    subject_groups = {}
    for r in all_records:
        sid = r.subject_id
        if sid not in subject_groups:
            subject_groups[sid] = {
                "subject_code": r.subject.code if r.subject else f"Sub-{sid}",
                "subject_name": r.subject.name if r.subject else "Unknown",
                "records": [],
            }
        subject_groups[sid]["records"].append(r)

    subject_comparisons = []
    for sid, info in subject_groups.items():
        sub_stats = compute_attendance_stats(info["records"])
        subject_comparisons.append({
            "subject_id": sid,
            "subject_code": info["subject_code"],
            "subject_name": info["subject_name"],
            "percentage": sub_stats.attendance_percentage,
            "total_sessions": sub_stats.total_sessions,
            "present": sub_stats.present_count,
            "absent": sub_stats.absent_count,
            "excused": sub_stats.excused_count,
        })

    # 3. Status distribution
    status_distribution = [
        {"name": "Present", "value": overall_stats.present_count, "color": "#10b981"},
        {"name": "Absent", "value": overall_stats.absent_count, "color": "#ef4444"},
        {"name": "Excused", "value": overall_stats.excused_count, "color": "#f59e0b"},
    ]

    return AttendanceAnalytics(
        daily_trends=daily_trends,
        subject_comparisons=subject_comparisons,
        status_distribution=status_distribution,
        overall_stats=overall_stats,
    )


@router.get(
    "/stats/student/{student_id}",
    response_model=StudentAttendanceSummary,
    status_code=status.HTTP_200_OK,
    summary="Get Student Attendance Summary and Subject Breakdown",
    description="Calculates student attendance percentages and subject breakdown with excused absence policy.",
)
def get_student_attendance_stats(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Object-level access check:
    Students may only view their own stats.
    Lecturers & Admins can view any student's metrics.
    """
    verify_student_access(student_id, current_user)

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    records = (
        db.query(Attendance)
        .options(joinedload(Attendance.subject))
        .filter(Attendance.student_id == student_id)
        .all()
    )

    overall_stats = compute_attendance_stats(records)

    # Group records by subject
    subject_map = {}
    for r in records:
        sid = r.subject_id
        if sid not in subject_map:
            subject_map[sid] = {
                "code": r.subject.code if r.subject else "N/A",
                "name": r.subject.name if r.subject else "N/A",
                "records": [],
            }
        subject_map[sid]["records"].append(r)

    subject_breakdown = []
    for sid, data in subject_map.items():
        sub_stats = compute_attendance_stats(data["records"])
        subject_breakdown.append(
            SubjectAttendanceSummary(
                subject_id=sid,
                subject_code=data["code"],
                subject_name=data["name"],
                stats=sub_stats,
            )
        )

    return StudentAttendanceSummary(
        student_id=student.id,
        student_name=f"{student.first_name} {student.last_name}",
        student_id_number=student.student_id_number,
        overall_stats=overall_stats,
        subject_breakdown=subject_breakdown,
    )


@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Attendance Record Details",
)
def get_attendance_record(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieves single attendance record with student privacy enforcement."""
    att = (
        db.query(Attendance)
        .options(
            joinedload(Attendance.student),
            joinedload(Attendance.subject),
            joinedload(Attendance.recorded_by),
        )
        .filter(Attendance.id == attendance_id)
        .first()
    )
    if not att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found.",
        )

    if current_user.role.lower() == UserRole.STUDENT.value:
        verify_student_access(att.student_id, current_user)

    return build_attendance_response(att)


@router.put(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Attendance Record",
    description="Allows lecturers and administrators to modify attendance status or remarks.",
)
def update_attendance_record(
    attendance_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    """Lecturers & Admins: Update student attendance status or add excuse remarks."""
    att = (
        db.query(Attendance)
        .options(
            joinedload(Attendance.student),
            joinedload(Attendance.subject),
            joinedload(Attendance.recorded_by),
        )
        .filter(Attendance.id == attendance_id)
        .first()
    )
    if not att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found.",
        )

    if payload.status is not None:
        att.status = payload.status.lower()

    if payload.remarks is not None:
        att.remarks = payload.remarks

    db.commit()
    db.refresh(att)

    return build_attendance_response(att)


@router.delete(
    "/{attendance_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Attendance Record",
    description="Removes an erroneous attendance entry. Available to Admins and Lecturers.",
)
def delete_attendance_record(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lecturer),
):
    """Lecturers & Admins: Delete attendance record."""
    att = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found.",
        )

    db.delete(att)
    db.commit()

    return MessageResponse(
        message=f"Attendance record {attendance_id} deleted successfully.",
        success=True,
    )
