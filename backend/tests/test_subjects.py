"""
Automated Integration Tests for Subject & Module Management (Task 5)
Tests: Subject Creation, Duplicate Code Prevention, Lecturer Assignment,
Student Enrollment, Enrolled Student Retrieval, Editing, Deactivation,
Unenrollment, Role-Based Access Control, and Deletion.
"""

from datetime import timedelta
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
from app.models.student import Student
from app.models.user import User


def seed_test_accounts():
    """Seed Admin, Lecturer, and Student accounts for testing."""
    with SessionLocal() as db:
        admin = db.query(User).filter(User.email == "admin_subject@university.edu").first()
        if not admin:
            admin = User(
                email="admin_subject@university.edu",
                hashed_password=get_password_hash("AdminPass2026!"),
                full_name="Subject System Admin",
                role="admin",
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)

        lecturer = db.query(User).filter(User.email == "prof_knuth@university.edu").first()
        if not lecturer:
            lecturer = User(
                email="prof_knuth@university.edu",
                hashed_password=get_password_hash("LecturerPass2026!"),
                full_name="Prof. Donald Knuth",
                role="lecturer",
                is_active=True,
                is_superuser=False,
            )
            db.add(lecturer)

        db.commit()


def run_subject_tests():
    print("=" * 70)
    print("STARTING TASK 5: SUBJECT & MODULE MANAGEMENT TEST SUITE")
    print("=" * 70)

    seed_test_accounts()

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2.5)

    def req(method, path, body=None, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=10)
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
        # 1. Login Admin and Lecturer
        s_adm, r_adm = req("POST", "/api/v1/auth/login", {
            "email": "admin_subject@university.edu",
            "password": "AdminPass2026!",
        })
        assert s_adm == 200
        admin_token = r_adm["access_token"]

        s_lec, r_lec = req("POST", "/api/v1/auth/login", {
            "email": "prof_knuth@university.edu",
            "password": "LecturerPass2026!",
        })
        assert s_lec == 200
        lecturer_token = r_lec["access_token"]
        lecturer_id = r_lec["user"]["id"]

        ts = int(time.time())
        subj_code = f"CS{ts % 10000}"

        # 2. Admin creates a subject
        print("\n[Test 1] Admin Creates Subject (POST /api/v1/subjects/)")
        s1, r1 = req("POST", "/api/v1/subjects/", body={
            "code": subj_code,
            "name": "Advanced Operating Systems",
            "description": "Kernel architectures, virtualization, and concurrency models.",
            "credits": 4,
            "department": "Computer Science",
            "semester": 4,
            "academic_year": "2025-2026",
            "is_active": True,
        }, token=admin_token)
        print(f"Status: {s1} | Code: {r1.get('code')} | ID: {r1.get('id')}")
        assert s1 == 201
        subject_id = r1["id"]
        assert r1["code"] == subj_code

        # 3. Duplicate subject code prevention
        print("\n[Test 2] Duplicate Subject Code Prevention (409 Conflict)")
        s_dup, r_dup = req("POST", "/api/v1/subjects/", body={
            "code": subj_code,
            "name": "Duplicate Course",
            "department": "Computer Science",
        }, token=admin_token)
        print(f"Status: {s_dup} | Detail: {r_dup.get('error', {}).get('message')}")
        assert s_dup == 409

        # 4. Assign Lecturer to Subject
        print("\n[Test 3] Assign Lecturer to Subject (POST /api/v1/subjects/{id}/lecturer)")
        s_assign, r_assign = req("POST", f"/api/v1/subjects/{subject_id}/lecturer", body={
            "lecturer_id": lecturer_id,
        }, token=admin_token)
        print(f"Status: {s_assign} | Assigned Lecturer: {r_assign.get('lecturer', {}).get('full_name')}")
        assert s_assign == 200
        assert r_assign["lecturer"]["id"] == lecturer_id

        # 5. Create a student to test enrollment
        s_stu_c, r_stu_c = req("POST", "/api/v1/students/", body={
            "student_id_number": f"STU_SUBJ_{ts}",
            "first_name": "Alan",
            "last_name": "Turing",
            "email": f"turing_{ts}@university.edu",
            "department": "Computer Science",
            "academic_year": "2025-2026",
            "class_name": "CS-4A",
            "current_semester": 4,
        }, token=lecturer_token)
        assert s_stu_c == 201
        test_student_id = r_stu_c["id"]

        # 6. Enroll Student in Subject
        print("\n[Test 4] Enroll Student into Subject (POST /api/v1/subjects/{id}/enroll)")
        s_enr, r_enr = req("POST", f"/api/v1/subjects/{subject_id}/enroll", body={
            "student_ids": [test_student_id],
            "academic_year": "2025-2026",
        }, token=lecturer_token)
        print(f"Status: {s_enr} | Message: {r_enr.get('message')}")
        assert s_enr == 200

        # 7. Get Enrolled Students for Subject
        print("\n[Test 5] Get Enrolled Students (GET /api/v1/subjects/{id}/students)")
        s_list_enr, r_list_enr = req("GET", f"/api/v1/subjects/{subject_id}/students", token=lecturer_token)
        print(f"Status: {s_list_enr} | Enrolled count: {len(r_list_enr)}")
        assert s_list_enr == 200
        assert any(stu["student_id"] == test_student_id for stu in r_list_enr)

        # 8. Edit Subject Details
        print("\n[Test 6] Edit Subject (PUT /api/v1/subjects/{id})")
        s_put, r_put = req("PUT", f"/api/v1/subjects/{subject_id}", body={
            "name": "Advanced Operating Systems & Distributed Systems",
            "credits": 5,
        }, token=admin_token)
        print(f"Status: {s_put} | New Name: {r_put.get('name')} | Credits: {r_put.get('credits')}")
        assert s_put == 200
        assert r_put["credits"] == 5

        # 9. Deactivate Subject
        print("\n[Test 7] Deactivate Subject (PATCH /api/v1/subjects/{id}/deactivate)")
        s_deact, r_deact = req("PATCH", f"/api/v1/subjects/{subject_id}/deactivate?is_active=false", token=admin_token)
        print(f"Status: {s_deact} | is_active: {r_deact.get('is_active')}")
        assert s_deact == 200
        assert r_deact["is_active"] is False

        # Reactivate Subject
        s_react, r_react = req("PATCH", f"/api/v1/subjects/{subject_id}/deactivate?is_active=true", token=admin_token)
        assert s_react == 200
        assert r_react["is_active"] is True

        # 10. Unenroll Student
        print("\n[Test 8] Unenroll Student (DELETE /api/v1/subjects/{id}/enroll/{student_id})")
        s_unenr, r_unenr = req("DELETE", f"/api/v1/subjects/{subject_id}/enroll/{test_student_id}", token=lecturer_token)
        print(f"Status: {s_unenr} | Message: {r_unenr.get('message')}")
        assert s_unenr == 200

        # Verify unenrollment
        s_check_enr, r_check_enr = req("GET", f"/api/v1/subjects/{subject_id}/students", token=lecturer_token)
        assert not any(stu["student_id"] == test_student_id for stu in r_check_enr)

        # 11. Role-Based Access Control
        print("\n[Test 9] RBAC Checks")
        # Lecturer attempts to create subject -> 403 Forbidden (Admin only)
        s_lec_create, _ = req("POST", "/api/v1/subjects/", body={
            "code": f"FAIL{ts % 1000}",
            "name": "Unauthorized Subject",
            "department": "CS",
        }, token=lecturer_token)
        print(f"Lecturer creating subject -> Status: {s_lec_create} (Forbidden)")
        assert s_lec_create == 403

        # Lecturer attempts to delete subject -> 403 Forbidden (Admin only)
        s_lec_del, _ = req("DELETE", f"/api/v1/subjects/{subject_id}", token=lecturer_token)
        print(f"Lecturer deleting subject -> Status: {s_lec_del} (Forbidden)")
        assert s_lec_del == 403

        # 12. Admin Deletes Subject
        print("\n[Test 10] Admin Deletes Subject (DELETE /api/v1/subjects/{id})")
        s_del, r_del = req("DELETE", f"/api/v1/subjects/{subject_id}", token=admin_token)
        print(f"Status: {s_del} | Message: {r_del.get('message')}")
        assert s_del == 200

        # Verify Subject is gone
        s_gone, _ = req("GET", f"/api/v1/subjects/{subject_id}", token=admin_token)
        assert s_gone == 404
        print(f"Verify Subject deleted -> Status: {s_gone} (404 Not Found)")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        print("\nUvicorn server terminated.")

    print("\n" + "=" * 70)
    print("ALL TASK 5 SUBJECT & MODULE TEST ASSERTIONS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_subject_tests()
