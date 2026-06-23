import requests
import random
import time

BASE = "http://localhost:8000/api/v1"

# 1. Admin Login
admin_resp = requests.post(
    f"{BASE}/auth/mentor/login",
    json={"username": "admin", "password": "admin123"}
)
admin_token = admin_resp.json().get("access_token")
print("Admin Login:", admin_resp.status_code, admin_resp.json())
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# 2. Create Assignment
slug = f"quiz-assign-{random.randint(1000,9999)}"
create_assign_resp = requests.post(
    f"{BASE}/assignments",
    json={
        "slug": slug,
        "title": f"Quiz Assignment {slug}",
        "category": "filesystem_validation",
        "max_score": 100,
        "is_published": True
    },
    headers=admin_headers
)
if "id" not in create_assign_resp.json():
    print("Assignment Create Error:", create_assign_resp.json())
    exit(1)
assignment_id = create_assign_resp.json()["id"]
requests.post(f"{BASE}/assignments/{assignment_id}/publish", headers=admin_headers)

# 3. Create Quiz for Assignment
create_quiz_resp = requests.post(
    f"{BASE}/admin/assignments/{assignment_id}/quiz",
    json={
        "title": f"Quiz for {slug}",
        "marks_per_question": 10,
        "is_active": True
    },
    headers=admin_headers
)
quiz_id = create_quiz_resp.json()["id"]

# 4. Add Question to Quiz
add_q_resp = requests.post(
    f"{BASE}/admin/quizzes/{quiz_id}/questions",
    json={
        "question_text": "What is 2+2?",
        "type": "single_choice",
        "marks": 10,
        "options": [
            {"option_text": "3", "is_correct": False},
            {"option_text": "4", "is_correct": True}
        ]
    },
    headers=admin_headers
)

# 5. Student Registration & Login
student_roll = f"STUD{random.randint(10000, 99999)}"
requests.post(f"{BASE}/auth/student/register", json={
    "email": f"{student_roll.lower()}@student.example.com",
    "password": "password123",
    "full_name": f"Test {student_roll}",
    "roll_number": student_roll
})
stu_login = requests.post(f"{BASE}/auth/student/login", json={
    "roll_number": student_roll,
    "password": "password123"
})
stu_token = stu_login.json().get("access_token")
stu_headers = {"Authorization": f"Bearer {stu_token}"}

# 6. Student Join Classroom & Admin Approve
classrooms = requests.get(f"{BASE}/mentor/classrooms", headers=admin_headers).json()
if not isinstance(classrooms, list) or not classrooms:
    # Create a classroom
    requests.post(f"{BASE}/mentor/classrooms", json={"name": "Test Class", "description": "Auto-created"}, headers=admin_headers)
    classrooms = requests.get(f"{BASE}/mentor/classrooms", headers=admin_headers).json()

if isinstance(classrooms, list) and classrooms:
    classroom_id = classrooms[0]["id"]
    class_code = classrooms[0].get("class_code", "")
    requests.post(f"{BASE}/student/classrooms/join", json={"class_code": class_code}, headers=student_headers)
    
    enrollments = requests.get(f"{BASE}/mentor/classrooms/{classroom_id}/enrollments", headers=admin_headers).json()
    for e in enrollments:
        if e.get("status") == "PENDING":
            requests.patch(f"{BASE}/mentor/classrooms/{classroom_id}/enrollments/{e['enrollment_id']}/approve", headers=admin_headers)
else:
    print("WARNING: No classrooms available")

# 8. Try to fetch Quiz (Should be LOCKED because no submission yet)
quiz_get = requests.get(f"{BASE}/student/assignments/{assignment_id}/quiz", headers=stu_headers)
print("Quiz Get Before Submission:", quiz_get.status_code, quiz_get.json())

# 9. Submit Assignment
import io
dummy_zip = io.BytesIO(b"PK\x05\x06" + b"\x00"*18)
requests.post(
    f"{BASE}/submissions",
    data={"assignment_id": assignment_id, "source_type": "zip"},
    files={"file": ("test.zip", dummy_zip, "application/zip")},
    headers=stu_headers
)

# 10. Fetch Quiz (Should be UNLOCKED now)
quiz_get2 = requests.get(f"{BASE}/student/assignments/{assignment_id}/quiz", headers=stu_headers)
print("Quiz Get After Submission:", quiz_get2.status_code)

if quiz_get2.status_code == 200:
    questions = requests.get(f"{BASE}/student/quizzes/{quiz_id}/questions", headers=stu_headers).json()
    print("Questions:", questions)
    q_id = questions[0]["id"]
    correct_option_id = next(opt["id"] for opt in add_q_resp.json()["options"] if opt["is_correct"])

    # 11. Submit Quiz
    submit_q = requests.post(
        f"{BASE}/student/quizzes/{quiz_id}/attempt",
        json={"answers": {q_id: [correct_option_id]}},
        headers=stu_headers
    )
    print("Submit Quiz:", submit_q.status_code, submit_q.json())
