"""
Automated End-to-End and Integration Tests for Student Management (Task 4)
Tests: Profile Creation, Retrieval, Update, Deletion, Search, Filtering,
Pagination, Sorting, Duplicate Prevention, and Role-Based Access Control.
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
from app.models.user import User


def seed_test_accounts():
    """Ensure Admin and Lecturer accounts exist for test suite execution."""
    with SessionLocal() as db:
        admin = db.query(User).filter(User.email == "admin_crud@university.edu").first()
        if not admin:
            admin = User(
                email="admin_crud@university.edu",
                hashed_password=get_password_hash("AdminPass2026!"),
                full_name="CRUD System Admin",
                role="admin",
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)

        lecturer = db.query(User).filter(User.email == "lecturer_crud@university.edu").first()
        if not lecturer:
            lecturer = User(
                email="lecturer_crud@university.edu",
                hashed_password=get_password_hash("LecturerPass2026!"),
                full_name="Prof. Donald Knuth",
                role="lecturer",
                is_active=True,
                is_superuser=False,
            )
            db.add(lecturer)

        db.commit()


def run_student_crud_tests():
    print("=" * 70)
    print("STUDENT MANAGEMENT (TASK 4) TEST SUITE")
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
            "email": "admin_crud@university.edu",
            "password": "AdminPass2026!",
        })
        assert s_adm == 200
        admin_token = r_adm["access_token"]

        s_lec, r_lec = req("POST", "/api/v1/auth/login", {
            "email": "lecturer_crud@university.edu",
            "password": "LecturerPass2026!",
        })
        assert s_lec == 200
        lecturer_token = r_lec["access_token"]

        ts = int(time.time())
        stu1_id = f"STU_T1_{ts}"
        stu1_email = f"t1_student_{ts}@university.edu"

        # 2. Test Student Creation
        print("\n[1] Create Student Profile (POST /api/v1/students/)")
        s1, r1 = req("POST", "/api/v1/students/", body={
            "student_id_number": stu1_id,
            "first_name": "Alan",
            "last_name": "Turing",
            "email": stu1_email,
            "department": "Computer Science",
            "academic_year": "2025-2026",
            "class_name": "CS-3A",
            "current_semester": 3,
            "enrollment_year": 2024,
            "gender": "Male",
            "status": "active",
        }, token=lecturer_token)
        assert s1 == 201
        student_1_pk = r1["id"]
        print(f"Status: {s1} | Created ID: {student_1_pk}")

        # 3. Test Duplicate Student ID Prevention
        print("\n[2] Duplicate Student ID Prevention (409 Conflict)")
        s_dup_id, r_dup_id = req("POST", "/api/v1/students/", body={
            "student_id_number": stu1_id,
            "first_name": "Duplicate",
            "last_name": "Student",
            "email": f"diff_{ts}@univ.edu",
            "department": "Physics",
        }, token=lecturer_token)
        assert s_dup_id == 409
        print(f"Status: {s_dup_id} | Detail: {r_dup_id.get('error', {}).get('message')}")

        # 4. Test Duplicate Email Prevention
        print("\n[3] Duplicate Email Prevention (409 Conflict)")
        s_dup_em, r_dup_em = req("POST", "/api/v1/students/", body={
            "student_id_number": f"UNIQUE_ID_{ts}",
            "first_name": "Duplicate",
            "last_name": "Email",
            "email": stu1_email,
            "department": "Physics",
        }, token=lecturer_token)
        assert s_dup_em == 409
        print(f"Status: {s_dup_em} | Detail: {r_dup_em.get('error', {}).get('message')}")

        # 5. Test Details Retrieval API
        print("\n[4] Student Details Retrieval (GET /api/v1/students/{id})")
        s_get, r_get = req("GET", f"/api/v1/students/{student_1_pk}", token=lecturer_token)
        assert s_get == 200
        assert r_get["id"] == student_1_pk
        print(f"Status: {s_get} | Name: {r_get['first_name']} {r_get['last_name']}")

        # 6. Test Student Update API
        print("\n[5] Student Profile Update (PUT /api/v1/students/{id})")
        s_put, r_put = req("PUT", f"/api/v1/students/{student_1_pk}", body={
            "class_name": "CS-4A-Advanced",
            "current_semester": 4,
            "status": "at_risk",
        }, token=lecturer_token)
        assert s_put == 200
        assert r_put["class_name"] == "CS-4A-Advanced"
        assert r_put["current_semester"] == 4
        print(f"Status: {s_put} | New Class: {r_put['class_name']}")

        # 7. Create Student 2 for Search & Filter
        stu2_id = f"STU_T2_{ts}"
        stu2_email = f"ada_lovelace_{ts}@university.edu"
        s2, r2 = req("POST", "/api/v1/students/", body={
            "student_id_number": stu2_id,
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": stu2_email,
            "department": "Mathematics",
            "academic_year": "2025-2026",
            "class_name": "MATH-1B",
            "current_semester": 1,
            "enrollment_year": 2026,
            "status": "at_risk",
        }, token=lecturer_token)
        assert s2 == 201
        student_2_pk = r2["id"]

        # 8. Test Search and Filtering
        print("\n[6] Search & Filtering")
        s_search, r_search = req("GET", "/api/v1/students/?search=Lovelace", token=lecturer_token)
        assert s_search == 200
        assert any(item["last_name"] == "Lovelace" for item in r_search["items"])
        print(f"Search 'Lovelace' -> Status: {s_search} | Found: {r_search['total']}")

        s_dept, r_dept = req("GET", "/api/v1/students/?department=Mathematics", token=lecturer_token)
        assert s_dept == 200
        assert all(item["department"] == "Mathematics" for item in r_dept["items"])
        print(f"Filter dept='Mathematics' -> Status: {s_dept} | Found: {r_dept['total']}")

        # 9. Test Pagination and Sorting
        print("\n[7] Pagination & Sorting")
        s_page, r_page = req("GET", "/api/v1/students/?page=1&size=1&sort_by=first_name&sort_order=asc", token=lecturer_token)
        assert s_page == 200
        assert len(r_page["items"]) == 1
        assert r_page["total"] >= 2
        print(f"Pagination -> Status: {s_page} | Total: {r_page['total']} | Pages: {r_page['pages']}")

        # 10. Test RBAC & Object-Level Access
        print("\n[8] Role-Based & Object-Level Access Control")
        # Login as Student 1
        s_stu_log, r_stu_log = req("POST", "/api/v1/auth/login", {
            "email": stu1_email,
            "password": "StudentPass2026!",
        })
        assert s_stu_log == 200
        stu1_token = r_stu_log["access_token"]

        # Student 1 attempts to list all students -> 403 Forbidden
        s_list_forbid, _ = req("GET", "/api/v1/students/", token=stu1_token)
        assert s_list_forbid == 403
        print(f"Student calling GET /students/ -> Status: {s_list_forbid} (Forbidden)")

        # Student 1 attempts to view Student 2 -> 403 Forbidden
        s_view_forbid, _ = req("GET", f"/api/v1/students/{student_2_pk}", token=stu1_token)
        assert s_view_forbid == 403
        print(f"Student 1 accessing Student 2 -> Status: {s_view_forbid} (Forbidden)")

        # Student 1 views own record -> 200 OK
        s_view_own, r_view_own = req("GET", f"/api/v1/students/{student_1_pk}", token=stu1_token)
        assert s_view_own == 200
        print(f"Student 1 accessing own record -> Status: {s_view_own} (Allowed)")

        # Lecturer attempts to delete -> 403 Forbidden (Admin only)
        s_lec_del, _ = req("DELETE", f"/api/v1/students/{student_2_pk}", token=lecturer_token)
        assert s_lec_del == 403
        print(f"Lecturer calling DELETE /students/{student_2_pk} -> Status: {s_lec_del} (Forbidden)")

        # 11. Test Admin Deletion
        print("\n[9] Admin Student Deletion (DELETE /api/v1/students/{id})")
        s_del, r_del = req("DELETE", f"/api/v1/students/{student_2_pk}", token=admin_token)
        assert s_del == 200
        print(f"Status: {s_del} | Message: {r_del.get('message')}")

        # Verify Student 2 is gone
        s_gone, _ = req("GET", f"/api/v1/students/{student_2_pk}", token=admin_token)
        assert s_gone == 404
        print(f"Verify Student 2 deleted -> Status: {s_gone} (404 Not Found)")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        print("\nUvicorn server terminated.")

    print("\n" + "=" * 70)
    print("ALL STUDENT MANAGEMENT TEST SUITE ASSERTIONS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_student_crud_tests()
