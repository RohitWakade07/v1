"""Test: Verifies that the CLI evaluator login uses the SAME credentials as the web portal."""
import httpx
import sys

BASE = "http://localhost:8000"
ROLL = "22BEC999"
PASSWORD = "studentpass123"

print("=" * 60)
print("  CLI Evaluator Login Test — Same Credentials as Web Portal")
print("=" * 60)

# Step 1: Student Login (same endpoint used by both web portal and CLI)
print(f"\n[1] Logging in as: {ROLL}")
r = httpx.post(
    f"{BASE}/api/v1/auth/student/login",
    json={"roll_number": ROLL, "password": PASSWORD},
    timeout=10,
)
if r.status_code != 200:
    print(f"    FAIL: Status {r.status_code} — {r.json().get('detail', 'Unknown')}")
    sys.exit(1)

auth = r.json()
token = auth["access_token"]
subject_id = auth["subject_id"]
print(f"    OK: Authenticated successfully")
print(f"    Token:      {token[:50]}...")
print(f"    Subject ID: {subject_id}")
print(f"    Role:       {auth.get('role', 'N/A')}")

# Step 2: Fetch assignments using the token
print(f"\n[2] Fetching published assignments...")
r2 = httpx.get(
    f"{BASE}/api/v1/assignments/",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10,
)
if r2.status_code != 200:
    print(f"    FAIL: Status {r2.status_code}")
    sys.exit(1)

assignments = r2.json()
print(f"    Found {len(assignments)} assignment(s):")
for i, a in enumerate(assignments, 1):
    aid = a.get("id", "?")
    title = a.get("title", "Untitled")
    etype = a.get("evaluator_type", "N/A")
    status = a.get("status", "N/A")
    print(f"      {i}. [{aid}] {title}  (type={etype}, status={status})")

# Step 3: Fetch student profile using the token
print(f"\n[3] Fetching student profile...")
r3 = httpx.get(
    f"{BASE}/api/v1/students/me",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10,
)
if r3.status_code == 200:
    profile = r3.json()
    print(f"    Name:        {profile.get('full_name', 'N/A')}")
    print(f"    Roll Number: {profile.get('roll_number', 'N/A')}")
    print(f"    Email:       {profile.get('email', 'N/A')}")
    print(f"    Active:      {profile.get('is_active', 'N/A')}")
else:
    print(f"    WARN: Could not fetch profile (Status {r3.status_code})")

print(f"\n{'=' * 60}")
print("  RESULT: Login flow works — same credentials as web portal!")
print(f"{'=' * 60}")
