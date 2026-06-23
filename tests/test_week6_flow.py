"""
Full integration test for Week 6 Grader:
1. Admin login -> create week6 assignment
2. Student login -> submit ZIP with analyze.py
3. Poll submission status
"""
import requests
import json
import io
import zipfile
import time
import random
import sys

BASE = "http://localhost:8000/api/v1"

def divider(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check(resp, label, expect=200):
    ok = resp.status_code in ([expect] if isinstance(expect, int) else expect)
    status_icon = "[OK]" if ok else "[ERROR]"
    print(f"{status_icon} {label}: {resp.status_code}")
    if not ok:
        print(f"   ERROR: {resp.text[:300]}")
    return ok

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# STEP 1: Admin Login
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
divider("Step 1: Admin Login")
resp = requests.post(f"{BASE}/auth/mentor/login", json={"username": "admin", "password": "admin123"})
if not check(resp, "Admin login", 200):
    sys.exit(1)

admin_token = resp.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# STEP 2: Find or Create Assignment
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
divider("Step 2: Find or Create Week 6 Assignment")
resp = requests.get(f"{BASE}/assignments", headers=admin_headers)
assignments = resp.json() if resp.status_code == 200 else []
week6_assignment = next((a for a in assignments if a["slug"] == "week6"), None)

if week6_assignment:
    print(f"   Found existing Week 6 Assignment: {week6_assignment['id']}")
    assignment_id = week6_assignment["id"]
else:
    slug = "week6"
    create_payload = {
        "slug": slug,
        "title": f"Week 6 Test",
        "description": "Auto-generated test assignment for week 6",
        "category": "week6",
        "max_score": 100,
        "late_penalty_pct": 0,
        "resource_links": [],
        "submission_filename": "submission.zip",
        "submission_instructions": "Submit a zip file containing analyze.py, README.md, and requirements.txt",
    }
    resp = requests.post(f"{BASE}/assignments", json=create_payload, headers=admin_headers)
    if resp.status_code == 409:
        print("   Assignment already exists (409). Fetching from DB.")
        # If we get 409, it means it's already created. We can't proceed easily unless we know the ID, 
        # so let's use a raw db query or admin endpoint to find it.
        resp = requests.get(f"{BASE}/admin/assignments/all", headers=admin_headers)
        if resp.status_code == 200:
            assignment = next((a for a in resp.json() if a["slug"] == slug), None)
            if assignment:
                assignment_id = assignment["id"]
                print(f"   Found existing Week 6 Assignment: {assignment_id}")
            else:
                print("   Failed to find it via admin route.")
                sys.exit(1)
        else:
            print("   Admin route failed.")
            sys.exit(1)
    elif not check(resp, "Create assignment", 201):
        sys.exit(1)
    else:
        assignment = resp.json()
        assignment_id = assignment["id"]
        print(f"   Created: {assignment['title']} (ID={assignment_id})")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# STEP 3: Publish Assignment
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
divider("Step 3: Publish Assignment")
resp = requests.post(f"{BASE}/assignments/{assignment_id}/publish", headers=admin_headers)
check(resp, "Publish assignment", 200)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# STEP 4: Student Registration + Login
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
divider("Step 4: Student Registration + Login")
roll = f"W6STUD{random.randint(10000,99999)}"
requests.post(f"{BASE}/auth/student/register", json={
    "roll_number": roll,
    "full_name": "Week 6 Test Student",
    "email": f"{roll.lower()}@test.com",
    "password": "pass12345"
})

resp = requests.post(f"{BASE}/auth/student/login", json={"roll_number": roll, "password": "pass12345"})
if not check(resp, "Student login", 200):
    sys.exit(1)
student_token = resp.json()["access_token"]
student_headers = {"Authorization": f"Bearer {student_token}"}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# STEP 5: Approve Student (admin)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
divider("Step 5: Approve Student Enrollment")
resp = requests.get(f"{BASE}/classrooms", headers=admin_headers)
classrooms = resp.json() if resp.status_code == 200 else []

if not classrooms:
    print("   No classrooms found, creating one...")
    resp = requests.post(f"{BASE}/classrooms", json={"name": "Week 6 Test Classroom"}, headers=admin_headers)
    check(resp, "Create classroom", 201)
    if resp.status_code == 201:
        classrooms = [resp.json()]

if classrooms:
    classroom_id = classrooms[0]["id"]
    class_code = classrooms[0].get("class_code", "")
    j_resp = requests.post(f"{BASE}/classrooms/join", json={"class_code": class_code}, headers=student_headers)
    check(j_resp, "Join classroom", [200, 201])
    resp = requests.get(f"{BASE}/classrooms/{classroom_id}/enrollments", headers=admin_headers)
    enrollments = resp.json() if resp.status_code == 200 else []
    for e in enrollments:
        if e.get("status") == "PENDING":
            approve_resp = requests.post(f"{BASE}/classrooms/enrollments/{e['enrollment_id']}/approve", headers=admin_headers)
else:
    print("   [WARNING]  No classrooms found, student may not be approved. Continuing...")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# STEP 6: Submit a ZIP file
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
divider("Step 6: Submit ZIP File")

analyze_py_code = """import sys

def main():
    while True:
        try:
            line = input()
            if line.startswith("stats file1.txt"):
                print("words: 8 lines: 3 characters: 39")
            elif line.startswith("top 2 file2.txt"):
                print("python: 3")
            elif line.startswith("search world"):
                print("file1.txt")
            elif line.startswith("quit"):
                break
        except EOFError:
            break

if __name__ == "__main__":
    main()
"""

readme_md_code = """# Usage Example
```
python analyze.py
```
This requires requests, and is just a simple text analysis tool.
And we need some more words here to pass the 30 words count limit in the test wrapper.
One two three four five six seven eight nine ten
eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty
twenty-one twenty-two twenty-three twenty-four twenty-five twenty-six twenty-seven twenty-eight twenty-nine thirty
"""

requirements_txt_code = "requests\n"

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("analyze.py", analyze_py_code)
    zf.writestr("README.md", readme_md_code)
    zf.writestr("requirements.txt", requirements_txt_code)
zip_buffer.seek(0)
zip_bytes = zip_buffer.read()

resp = requests.post(
    f"{BASE}/submissions",
    data={"assignment_id": assignment_id, "source_type": "zip"},
    files={"file": ("submission.zip", zip_bytes, "application/zip")},
    headers=student_headers
)
check(resp, "Submit ZIP", [200, 201, 202])
if resp.status_code in (200, 201, 202):
    sub = resp.json()
    sub_id = sub.get("submission_id") or sub.get("id")
    print(f"   Submission ID: {sub_id}")
    
    # Poll status
    print("\n   [WAIT] Polling status (up to 30s)...")
    for _ in range(6):
        time.sleep(5)
        poll = requests.get(f"{BASE}/submissions/{sub_id}", headers=student_headers)
        if poll.status_code == 200:
            status = poll.json().get("status", "?")
            print(f"   Status: {status}")
            if status in ("COMPLETED", "FAILED", "TIMEOUT", "VALIDATION_ERROR", "CANCELLED"):
                sub_data = poll.json()
                print(f"   Final Result: score={sub_data.get('score')}/{sub_data.get('max_score')} passed={sub_data.get('passed')}")
                break
        else:
            print(f"   Poll error: {poll.status_code}")
            break

divider("All Tests Done")