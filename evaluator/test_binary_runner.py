import os
import sys
import httpx
import subprocess

def test_compiled_binary():
    print("[1/4] Authenticating student '22BEC999' against local FastAPI backend...")
    client = httpx.Client(base_url="http://localhost:8001", timeout=15)
    
    # 1. Login
    resp = client.post("/api/v1/auth/student/login", json={
        "roll_number": "22BEC999",
        "password": "studentpass123"
    })
    if resp.status_code != 200:
        print(f"Error: Login failed! Response: {resp.text}")
        sys.exit(1)
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  Successfully logged in and obtained token.")
    
    # 2. Find Demo Assignment
    print("[2/4] Fetching demo assignment slug 'demo-sync-lab'...")
    resp = client.get("/api/v1/assignments/", headers=headers)
    if resp.status_code != 200:
        print(f"Error: Failed to fetch assignments! Response: {resp.text}")
        sys.exit(1)
        
    assignments = resp.json()
    demo_assignment = None
    for a in assignments:
        if a["slug"] == "demo-sync-lab":
            demo_assignment = a
            break
            
    if not demo_assignment:
        print("Error: Could not find assignment 'demo-sync-lab' in the database.")
        sys.exit(1)
        
    assignment_id = demo_assignment["id"]
    print(f"  Found assignment '{demo_assignment['title']}' with ID: {assignment_id}")
    
    # 3. Create Session (or get active one)
    print("[3/4] Requesting a grading session on backend...")
    resp = client.post("/api/v1/sessions/", json={"assignment_id": assignment_id}, headers=headers)
    if resp.status_code == 409:
        print("  Active session already exists. Fetching session details...")
        resp = client.get("/api/v1/sessions/", headers=headers)
        active_sessions = resp.json()
        session_id = None
        for s in active_sessions:
            if str(s["assignment_id"]) == str(assignment_id) and s["status"] in ("CREATED", "CHALLENGE_ISSUED", "RUNNING", "PROOF_GENERATED", "STARTED", "IN_PROGRESS"):
                session_id = s["session_id"]
                break
        if not session_id:
            print("Error: Could not retrieve active session.")
            sys.exit(1)
    elif resp.status_code not in (200, 201):
        print(f"Error: Failed to create session! Response: {resp.text}")
        sys.exit(1)
    else:
        session_id = resp.json()["session_id"]
        
    print(f"  Session established. Session ID: {session_id}")
    
    # Create the test file required by the rule config in the local directory
    target_file_path = "sync_test.txt"
    with open(target_file_path, "w") as f:
        f.write("EE-Yantra Sync Verified\n")
    print(f"  Ensured '{target_file_path}' exists in workspace.")
    
    # 4. Run Executable
    binary_path = os.path.abspath(os.path.join("dist", "artifact_evaluator.exe"))
    print(f"[4/4] Executing compiled binary: {binary_path}")
    
    cmd = [
        binary_path,
        "--session-id", session_id,
        "--token", token,
        "--roll", "22BEC999",
        "--backend-url", "http://localhost:8001"
    ]
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("\n---------------------- BINARY EXECUTION OUTPUT ----------------------")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print("---------------------------------------------------------------------")
    
    # Clean up test file
    if os.path.exists(target_file_path):
        os.remove(target_file_path)
        
    if result.returncode == 0:
        print("\n======================================================================")
        print("      SUCCESS: Packed Binary is fully operational and verified!        ")
        print("======================================================================")
        sys.exit(0)
    else:
        print(f"\nError: Compiled binary failed with exit code: {result.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    test_compiled_binary()
