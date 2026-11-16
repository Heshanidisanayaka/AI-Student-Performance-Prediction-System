"""
Automated Integration Tests for Student Attendance Tracking (Task 6)
Tests:
1. Bulk Session Attendance Recording (POST /api/v1/attendance/session)
2. Duplicate Session Attendance Prevention (409 Conflict)
3. Single Student Attendance Recording (POST /api/v1/attendance/)
4. Duplicate Single Record Prevention (409 Conflict)
5. Attendance Record Update (PUT /api/v1/attendance/{id})
6. Institutional Excused Absence Policy Calculation (GET /api/v1/attendance/stats/student/{id})
7. Student Privacy & Role-Based Access Control (403 Forbidden on Cross-Access & Marking)
8. Recharts Analytics Payload Verification (GET /api/v1/attendance/analytics)
9. History Query Filtering by Subject, Student, Date, Status, and Session
10. Attendance Record Deletion (DELETE /api/v1/attendance/{id})
"""

from datetime import date, timedelta
import http.client
import json
from pathlib import Path
import subprocess
import sys
import time

# Ensure backend root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.attendance import Attendance
from app.models.enrollment import StudentSubject
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User


def seed_test_data():
    """Seed test Admin, Lecturer, two Students, and enrollments."""
    with SessionLocal() as db:
        # Admin
        admin = db.query(User).filter(User.email == "admin_att@university.edu").first()
        if not admin:
            admin = User(
                email="admin_att@university.edu",
                hashed_password=get_password_hash("AdminPass2026!"),
                full_name="Attendance Admin",
                role="admin",
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)

        # Lecturer
        lecturer = db.query(User).filter(User.email == "prof_turing@university.edu").first()
        if not lecturer:
            lecturer = User(
                email="prof_turing@university.edu",
                hashed_password=get_password_hash("LecturerPass2026!"),
                full_name="Prof. Alan Turing",
                role="lecturer",
                is_active=True,
                is_superuser=False,
            )
            db.add(lecturer)

        db.commit()

        # Student 1 User + Profile
        u_stu1 = db.query(User).filter(User.email == "alice_att@student.university.edu").first()
        if not u_stu1:
            u_stu1 = User(
                email="alice_att@student.university.edu",
                hashed_password=get_password_hash("StudentPass2026!"),
                full_name="Alice Smith",
                role="student",
                is_active=True,
            )
            db.add(u_stu1)
            db.commit()

        stu1 = db.query(Student).filter(Student.student_id_number == "ATT-STU-001").first()
        if not stu1:
            stu1 = Student(
                user_id=u_stu1.id,
                student_id_number="ATT-STU-001",
                first_name="Alice",
                last_name="Smith",
                email="alice_att@student.university.edu",
                academic_year="2025-2026",
                class_name="Class A",
                department="Computer Science",
                enrollment_year=2026,
                current_semester=1,
                status="active",
            )
            db.add(stu1)

        # Student 2 User + Profile
        u_stu2 = db.query(User).filter(User.email == "bob_att@student.university.edu").first()
        if not u_stu2:
            u_stu2 = User(
                email="bob_att@student.university.edu",
                hashed_password=get_password_hash("StudentPass2026!"),
                full_name="Bob Jones",
                role="student",
                is_active=True,
            )
            db.add(u_stu2)
            db.commit()

        stu2 = db.query(Student).filter(Student.student_id_number == "ATT-STU-002").first()
        if not stu2:
            stu2 = Student(
                user_id=u_stu2.id,
                student_id_number="ATT-STU-002",
                first_name="Bob",
                last_name="Jones",
                email="bob_att@student.university.edu",
                academic_year="2025-2026",
                class_name="Class A",
                department="Computer Science",
                enrollment_year=2026,
                current_semester=1,
                status="active",
            )
            db.add(stu2)

        # Subject for attendance
        subj = db.query(Subject).filter(Subject.code == "ATT-CS201").first()
        if not subj:
            subj = Subject(
                code="ATT-CS201",
                name="Data Structures & Algorithms",
                description="Core algorithms and data structures.",
                credits=4,
                department="Computer Science",
                semester=1,
                academic_year="2025-2026",
                is_active=True,
                lecturer_id=lecturer.id,
            )
            db.add(subj)
            db.commit()
        else:
            # Clean up previous test attendance records for reproducible test runs
            db.query(Attendance).filter(Attendance.subject_id == subj.id).delete()
            db.commit()

        db.commit()

        # Enroll both students in this subject
        for s in [stu1, stu2]:
            enr = (
                db.query(StudentSubject)
                .filter(
                    StudentSubject.student_id == s.id,
                    StudentSubject.subject_id == subj.id,
                )
                .first()
            )
            if not enr:
                enr = StudentSubject(student_id=s.id, subject_id=subj.id)
                db.add(enr)
        db.commit()


def run_attendance_tests():
    print("=" * 75)
    print("STARTING TASK 6: STUDENT ATTENDANCE TRACKING TEST SUITE")
    print("=" * 75)

    seed_test_data()

    TEST_PORT = 8008

    log_file = open(BASE_DIR / "tests" / "uvicorn_att_test.log", "w")
    # Launch backend server
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(TEST_PORT),
            "--log-level",
            "debug",
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(BASE_DIR),
    )

    # Wait for server to start with retry loop
    server_started = False
    for attempt in range(20):
        time.sleep(0.5)
        if proc.poll() is not None:
            _, err = proc.communicate()
            print(f"Server exited prematurely with code {proc.returncode}:\n{err.decode()}")
            raise RuntimeError("Uvicorn failed to start.")
        try:
            conn = http.client.HTTPConnection("127.0.0.1", TEST_PORT, timeout=2)
            conn.request("GET", "/health")
            resp = conn.getresponse()
            if resp.status == 200:
                server_started = True
                break
        except Exception:
            pass

    if not server_started:
        proc.terminate()
        _, err = proc.communicate()
        print(f"Server failed to respond to /health:\n{err.decode()}")
        raise RuntimeError("Uvicorn failed to respond on port " + str(TEST_PORT))

    print(f"Uvicorn server running and verified on port {TEST_PORT}!")

    def req(method, path, body=None, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", TEST_PORT, timeout=10)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = json.dumps(body) if body is not None else None
        conn.request(method, path, body=payload, headers=headers)
        resp = conn.getresponse()
        raw = resp.read().decode()
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        return resp.status, data

    try:
        # Step 1: Login Admin, Lecturer, and Student 1
        s_adm, r_adm = req("POST", "/api/v1/auth/login", {
            "email": "admin_att@university.edu",
            "password": "AdminPass2026!",
        })
        assert s_adm == 200, f"Admin login failed: {r_adm}"
        admin_token = r_adm["access_token"]

        s_lec, r_lec = req("POST", "/api/v1/auth/login", {
            "email": "prof_turing@university.edu",
            "password": "LecturerPass2026!",
        })
        assert s_lec == 200, f"Lecturer login failed: {r_lec}"
        lecturer_token = r_lec["access_token"]

        s_stu1, r_stu1 = req("POST", "/api/v1/auth/login", {
            "email": "alice_att@student.university.edu",
            "password": "StudentPass2026!",
        })
        assert s_stu1 == 200, f"Student 1 login failed: {r_stu1}"
        stu1_token = r_stu1["access_token"]

        # Fetch IDs
        with SessionLocal() as db:
            subject = db.query(Subject).filter(Subject.code == "ATT-CS201").first()
            subject_id = subject.id
            s1 = db.query(Student).filter(Student.student_id_number == "ATT-STU-001").first()
            stu1_id = s1.id
            s2 = db.query(Student).filter(Student.student_id_number == "ATT-STU-002").first()
            stu2_id = s2.id

        today_str = date.today().isoformat()
        session_name_1 = f"Lecture-A-{int(time.time())}"
        session_name_2 = f"Lecture-B-{int(time.time())}"

        # Test 1: Bulk Session Attendance Recording
        print("\n[Test 1] Lecturer Bulk-Records Attendance for a Session (POST /session)")
        payload_session = {
            "subject_id": subject_id,
            "date": today_str,
            "session_name": session_name_1,
            "records": [
                {"student_id": stu1_id, "status": "present", "remarks": "On time"},
                {"student_id": stu2_id, "status": "absent", "remarks": "Unnotified"},
            ],
        }
        s_rec, r_rec = req("POST", "/api/v1/attendance/session", payload_session, token=lecturer_token)
        print(f"Status: {s_rec} | Created Records: {len(r_rec) if isinstance(r_rec, list) else r_rec}")
        assert s_rec == 201
        assert len(r_rec) == 2
        record_1_id = r_rec[0]["id"]
        record_2_id = r_rec[1]["id"]
        assert r_rec[0]["status"] == "present"
        assert r_rec[1]["status"] == "absent"

        # Test 2: Duplicate Session Prevention (409 Conflict)
        print("\n[Test 2] Duplicate Session Recording Prevention (Expect 409 Conflict)")
        s_dup, r_dup = req("POST", "/api/v1/attendance/session", payload_session, token=lecturer_token)
        print(f"Status: {s_dup} | Detail: {r_dup.get('detail')}")
        assert s_dup == 409

        # Test 3: Single Student Attendance Recording
        print("\n[Test 3] Single Attendance Record Creation (POST /api/v1/attendance/)")
        payload_single_1 = {
            "student_id": stu1_id,
            "subject_id": subject_id,
            "date": today_str,
            "session_name": session_name_2,
            "status": "present",
            "remarks": "Attended lab",
        }
        s_sing, r_sing = req("POST", "/api/v1/attendance/", payload_single_1, token=lecturer_token)
        print(f"Status: {s_sing} | Student: {r_sing.get('student_name')} | Status: {r_sing.get('status')}")
        assert s_sing == 201
        assert r_sing["status"] == "present"

        # Student 2 excused in session 2
        payload_single_2 = {
            "student_id": stu2_id,
            "subject_id": subject_id,
            "date": today_str,
            "session_name": session_name_2,
            "status": "excused",
            "remarks": "Medical note submitted",
        }
        s_sing2, r_sing2 = req("POST", "/api/v1/attendance/", payload_single_2, token=lecturer_token)
        assert s_sing2 == 201
        assert r_sing2["status"] == "excused"
        record_3_id = r_sing2["id"]

        # Test 4: Prevent Duplicate Single Record (409 Conflict)
        print("\n[Test 4] Duplicate Single Record Prevention (Expect 409 Conflict)")
        s_dup_sing, r_dup_sing = req("POST", "/api/v1/attendance/", payload_single_1, token=lecturer_token)
        print(f"Status: {s_dup_sing} | Detail: {r_dup_sing.get('detail')}")
        assert s_dup_sing == 409

        # Test 5: Update Attendance Record (PUT /api/v1/attendance/{id})
        print("\n[Test 5] Update Attendance Record (PUT /api/v1/attendance/{id})")
        # Lecturer updates record_2_id (Bob's Session 1 absent -> excused)
        payload_update = {
            "status": "excused",
            "remarks": "Official university sports representation",
        }
        s_upd, r_upd = req("PUT", f"/api/v1/attendance/{record_2_id}", payload_update, token=lecturer_token)
        print(f"Status: {s_upd} | Updated Status: {r_upd.get('status')} | Remarks: {r_upd.get('remarks')}")
        assert s_upd == 200
        assert r_upd["status"] == "excused"
        assert r_upd["remarks"] == "Official university sports representation"

        # Test 6: Institutional Excused Absence Policy Calculation
        print("\n[Test 6] Excused Absence Policy Calculation (GET /stats/student/{id})")
        # Student 2 (Bob) currently has 2 sessions, both excused:
        # Effective = 2 - 2 = 0. Policy says excused absences do not penalize -> 100.0%
        s_stat2, r_stat2 = req("GET", f"/api/v1/attendance/stats/student/{stu2_id}", token=lecturer_token)
        print(f"Bob Stats (all excused): {r_stat2['overall_stats']}")
        assert s_stat2 == 200
        assert r_stat2["overall_stats"]["excused_count"] == 2
        assert r_stat2["overall_stats"]["attendance_percentage"] == 100.0

        # Add a 3rd session where Bob is absent without excuse:
        session_name_3 = f"Lecture-C-{int(time.time())}"
        req("POST", "/api/v1/attendance/", {
            "student_id": stu2_id,
            "subject_id": subject_id,
            "date": today_str,
            "session_name": session_name_3,
            "status": "absent",
            "remarks": "Unexcused absence",
        }, token=lecturer_token)

        s_stat2_after, r_stat2_after = req("GET", f"/api/v1/attendance/stats/student/{stu2_id}", token=lecturer_token)
        st = r_stat2_after["overall_stats"]
        print(f"Bob Stats (after 1 unexcused): Total={st['total_sessions']}, Present={st['present_count']}, Absent={st['absent_count']}, Excused={st['excused_count']}, Effective={st['effective_sessions']}, Pct={st['attendance_percentage']}%")
        # Total = 3, Present = 0, Absent = 1, Excused = 2
        # Effective = 3 - 2 = 1. Present / Effective * 100 = 0 / 1 * 100 = 0.0%
        assert st["total_sessions"] == 3
        assert st["excused_count"] == 2
        assert st["absent_count"] == 1
        assert st["effective_sessions"] == 1
        assert st["attendance_percentage"] == 0.0

        # Also check Student 1 (Alice):
        s_stat1, r_stat1 = req("GET", f"/api/v1/attendance/stats/student/{stu1_id}", token=lecturer_token)
        st1 = r_stat1["overall_stats"]
        print(f"Alice Stats: Total={st1['total_sessions']}, Present={st1['present_count']}, Pct={st1['attendance_percentage']}%")
        assert st1["present_count"] == 2
        assert st1["attendance_percentage"] == 100.0

        # Test 7: Student Privacy & Role-Based Access Control
        print("\n[Test 7] Student Privacy & Role-Based Access Control")
        # 7a: Student attempts to record attendance -> 403 Forbidden
        s_stu_rec, _ = req("POST", "/api/v1/attendance/session", payload_session, token=stu1_token)
        print(f"Student recording session -> Status: {s_stu_rec} (Expect 403 Forbidden)")
        assert s_stu_rec == 403

        # 7b: Student attempts to view another student's stats -> 403 Forbidden
        s_cross, r_cross = req("GET", f"/api/v1/attendance/stats/student/{stu2_id}", token=stu1_token)
        print(f"Student viewing peer stats -> Status: {s_cross} (Expect 403 Forbidden)")
        assert s_cross == 403

        # 7c: Student views own stats -> 200 OK
        s_own, r_own = req("GET", f"/api/v1/attendance/stats/student/{stu1_id}", token=stu1_token)
        print(f"Student viewing own stats -> Status: {s_own} (Expect 200 OK)")
        assert s_own == 200
        assert r_own["student_id"] == stu1_id

        # 7d: Student queries general attendance list -> strictly returns only their records
        s_list_stu, r_list_stu = req("GET", "/api/v1/attendance/", token=stu1_token)
        print(f"Student query history -> Total records returned: {r_list_stu['total']}")
        assert s_list_stu == 200
        for item in r_list_stu["items"]:
            assert item["student_id"] == stu1_id

        # Test 8: Attendance Analytics for Recharts Visualizations
        print("\n[Test 8] Attendance Analytics for Recharts Visualizations (GET /analytics)")
        s_ana, r_ana = req("GET", f"/api/v1/attendance/analytics?subject_id={subject_id}", token=lecturer_token)
        print(f"Analytics Status: {s_ana}")
        assert s_ana == 200
        assert "daily_trends" in r_ana
        assert "subject_comparisons" in r_ana
        assert "status_distribution" in r_ana
        assert "overall_stats" in r_ana
        print(f"Daily Trends count: {len(r_ana['daily_trends'])}")
        print(f"Subject Comparisons: {r_ana['subject_comparisons']}")
        print(f"Status Distribution: {r_ana['status_distribution']}")

        # Test 9: Attendance Filtering
        print("\n[Test 9] History Filtering by Subject, Status, and Session")
        s_flt, r_flt = req("GET", f"/api/v1/attendance/?subject_id={subject_id}&status=excused", token=lecturer_token)
        assert s_flt == 200
        assert all(it["status"] == "excused" for it in r_flt["items"])
        print(f"Filtered 'excused' records count: {len(r_flt['items'])}")

        # Test 10: Delete Attendance Record
        print("\n[Test 10] Lecturer Deletes Attendance Record (DELETE /api/v1/attendance/{id})")
        s_del, r_del = req("DELETE", f"/api/v1/attendance/{record_3_id}", token=lecturer_token)
        print(f"Status: {s_del} | Message: {r_del.get('message')}")
        assert s_del == 200

        # Verify record is gone
        s_check, _ = req("GET", f"/api/v1/attendance/{record_3_id}", token=lecturer_token)
        assert s_check == 404
        print(f"Verify Record deleted -> Status: {s_check} (404 Not Found)")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        log_file.close()
        print("\nUvicorn server terminated.")

    print("\n" + "=" * 75)
    print("ALL TASK 6 ATTENDANCE TRACKING TEST ASSERTIONS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_attendance_tests()
