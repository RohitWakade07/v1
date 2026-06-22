"""
Full integration test for:
1. Admin login → create assignment with resources, submission info
2. Admin edit assignment → update resources
3. Student login → list assignments → submit ZIP
4. Poll submission status
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

# ─────────────────────────────────────────────
# STEP 1: Admin Login
# ─────────────────────────────────────────────
divider("Step 1: Admin Login")
resp = requests.post(f"{BASE}/auth/mentor/login", json={"username": "admin", "password": "admin123"})
if not check(resp, "Admin login", 200):
    sys.exit(1)

admin_token = resp.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}
print(f"   Role: {resp.json().get('role')}")

# ─────────────────────────────────────────────
# STEP 2: Create Assignment (with full payload)
# ─────────────────────────────────────────────
divider("Step 2: Create Assignment via Admin API")
slug = f"test-assign-{random.randint(1000,9999)}"
resources = [
    {"title": "Week Tutorial", "url": "https://docs.python.org", "type": "link"},
    {"title": "Demo Video", "url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "type": "video"},
]
create_payload = {
    "slug": slug,
    "title": f"Test Assignment {slug}",
    "description": "Auto-generated test assignment",
    "category": "filesystem_validation",
    "max_score": 10,
    "late_penalty_pct": 20,
    "resource_links": resources,
    "submission_filename": "test_file.sh",
    "submission_instructions": "Step 1: Create the file\nStep 2: ZIP it\nStep 3: Submit",
}
resp = requests.post(f"{BASE}/assignments", json=create_payload, headers=admin_headers)
if not check(resp, "Create assignment", 201):
    sys.exit(1)

assignment = resp.json()
assignment_id = assignment["id"]
print(f"   Created: {assignment['title']} (ID={assignment_id[:8]}...)")
print(f"   Late Penalty: {assignment.get('late_penalty_pct')}%")
print(f"   Submission Filename: {assignment.get('submission_filename')}")
raw_resources = assignment.get('resource_links', '[]')
parsed = json.loads(raw_resources) if isinstance(raw_resources, str) else raw_resources
print(f"   Resources: {len(parsed)} item(s)")
for r in parsed:
    print(f"     - [{r.get('type','link')}] {r['title']}: {r['url']}")

# ─────────────────────────────────────────────
# STEP 3: Admin Edit (update resources via PATCH)
# ─────────────────────────────────────────────
divider("Step 3: Admin Edit Assignment (PATCH)")
updated_resources = [
    {"title": "Updated Tutorial", "url": "https://developer.mozilla.org", "type": "link"},
    {"title": "Architecture Diagram", "url": "https://picsum.photos/800/400", "type": "image"},
    {"title": "Demo Video", "url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "type": "video"},
]
resp = requests.patch(
    f"{BASE}/assignments/admin/{assignment_id}",
    json={"resource_links": updated_resources, "late_penalty_pct": 10},
    headers=admin_headers
)
check(resp, "Admin PATCH assignment", 200)
if resp.status_code == 200:
    a = resp.json()
    print(f"   Updated penalty: {a.get('late_penalty_pct')}%")
    raw2 = a.get('resource_links', '[]')
    p2 = json.loads(raw2) if isinstance(raw2, str) else raw2
    print(f"   Updated resources: {len(p2)} item(s)")

# ─────────────────────────────────────────────
# STEP 4: Publish Assignment
# ─────────────────────────────────────────────
divider("Step 4: Publish Assignment")
resp = requests.post(f"{BASE}/assignments/{assignment_id}/publish", headers=admin_headers)
check(resp, "Publish assignment", 200)

# ─────────────────────────────────────────────
# STEP 5: Student Registration + Login
# ─────────────────────────────────────────────
divider("Step 5: Student Registration + Login")
roll = f"STUD{random.randint(10000,99999)}"
resp = requests.post(f"{BASE}/auth/student/register", json={
    "roll_number": roll,
    "full_name": "Integration Test Student",
    "email": f"{roll.lower()}@test.com",
    "password": "pass12345"
})
check(resp, "Student register", 201)

resp = requests.post(f"{BASE}/auth/student/login", json={"roll_number": roll, "password": "pass12345"})
if not check(resp, "Student login", 200):
    sys.exit(1)
student_token = resp.json()["access_token"]
student_headers = {"Authorization": f"Bearer {student_token}"}
print(f"   Roll: {roll}")

# ─────────────────────────────────────────────
# STEP 6: Approve Student (admin)
# ─────────────────────────────────────────────
divider("Step 6: Approve Student Enrollment")
# List classrooms
resp = requests.get(f"{BASE}/mentor/classrooms", headers=admin_headers)
classrooms = resp.json() if resp.status_code == 200 else []
if classrooms:
    classroom_id = classrooms[0]["id"]
    class_code = classrooms[0].get("class_code", "")
    print(f"   Using classroom: {classrooms[0]['name']} (code={class_code})")
    # Student join classroom
    resp = requests.post(f"{BASE}/student/classrooms/join", json={"class_code": class_code}, headers=student_headers)
    print(f"   Student join classroom: {resp.status_code}")
    # Approve all pending
    resp = requests.get(f"{BASE}/mentor/classrooms/{classroom_id}/enrollments", headers=admin_headers)
    enrollments = resp.json() if resp.status_code == 200 else []
    for e in enrollments:
        if e.get("status") == "PENDING":
            approve_resp = requests.patch(
                f"{BASE}/mentor/classrooms/{classroom_id}/enrollments/{e['enrollment_id']}/approve",
                headers=admin_headers
            )
            print(f"   Approved {e.get('student_roll','?')}: {approve_resp.status_code}")
else:
    print("   [WARNING]  No classrooms found, student may not be approved. Continuing...")

# ─────────────────────────────────────────────
# STEP 7: Student Views Assignment
# ─────────────────────────────────────────────
divider("Step 7: Student Gets Assignment Detail")
resp = requests.get(f"{BASE}/assignments/{assignment_id}", headers=student_headers)
check(resp, "Get assignment detail", [200, 403])
if resp.status_code == 200:
    a = resp.json()
    print(f"   Title: {a['title']}")
    print(f"   Submission filename: {a.get('submission_filename')}")
    raw = a.get('resource_links', '[]')
    p = json.loads(raw) if isinstance(raw, str) else raw
    print(f"   Resources visible: {len(p)}")

# ─────────────────────────────────────────────
# STEP 8: Submit a ZIP file
# ─────────────────────────────────────────────
divider("Step 8: Submit ZIP File")

# Create an in-memory ZIP with test_file.sh
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("test_file.sh", "#!/bin/bash\necho 'Hello from test submission'\n")
zip_buffer.seek(0)
zip_bytes = zip_buffer.read()

print(f"   ZIP size: {len(zip_bytes)} bytes")
print(f"   Assignment ID: {assignment_id}")

resp = requests.post(
    f"{BASE}/submissions",
    data={"assignment_id": assignment_id, "source_type": "zip"},
    files={"file": ("submission.zip", zip_bytes, "application/zip")},
    headers=student_headers
)
check(resp, "Submit ZIP", [200, 201, 202, 403, 400])
if resp.status_code in (200, 201, 202):
    sub = resp.json()
    sub_id = sub.get("submission_id") or sub.get("id")
    print(f"   Submission ID: {sub_id}")
    print(f"   Status: {sub.get('status')}")
    print(f"   Attempt #: {sub.get('attempt_number')}")

    # Poll status
    print("\n   [WAIT] Polling status (up to 30s)...")
    for _ in range(6):
        time.sleep(5)
        poll = requests.get(f"{BASE}/submissions/{sub_id}", headers=student_headers)
        if poll.status_code == 200:
            status = poll.json().get("status", "?")
            print(f"   Status: {status}")
            if status in ("COMPLETED", "FAILED", "TIMEOUT", "VALIDATION_ERROR", "CANCELLED"):
                break
        else:
            print(f"   Poll error: {poll.status_code}")
            break
else:
    print(f"   Response body: {resp.text[:500]}")

divider("All Tests Done")
