import os
import sys
import uuid
import httpx
import json
import asyncio
from datetime import datetime

# Setup path so we can import from backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force database port to connect to local docker container mapped port
os.environ["POSTGRES_PORT"] = "5433"

from app.core.config import settings
from app.core.security import hash_password
from app.models.models import SessionStatus

# Ensure environment variables are loaded
os.environ["EEYAN_BACKEND_URL"] = "http://localhost:8000"
os.environ["EEYAN_ROLL_NUMBER"] = "22BEC999"

async def setup_test_data():
    """Directly configures the database using SQLModel to insert demo data safely."""
    print("[1/6] Connecting to database and seeding mentor, assignment and configuration...")
    
    from sqlalchemy import text
    from app.models.models import Mentor, Assignment, AssignmentConfig, UserRole
    from app.db.session import AsyncSessionLocal
    
    # Mentor, Assignment and Config IDs
    mentor_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    assignment_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    config_id = uuid.uuid4()
    
    config_data = {
        "execution_constraints": {
            "timeout_seconds": 120
        },
        "validation_rules": [
            {
                "rule_id": "rule_file_exists",
                "type": "file_exists",
                "target": "sync_test.txt",
                "points": 50.0
            },
            {
                "rule_id": "rule_content_check",
                "type": "content",
                "target": "sync_test.txt",
                "points": 50.0,
                "metadata": {
                    "pattern": "EE-Yantra Sync Verified"
                }
            }
        ]
    }
    
    # 1. Purge existing data
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM certificates WHERE student_id IN (SELECT id FROM students WHERE roll_number = '22BEC999')"))
        await session.execute(text(f"DELETE FROM final_results WHERE student_id IN (SELECT id FROM students WHERE roll_number = '22BEC999')"))
        await session.execute(text(f"DELETE FROM proof_submissions WHERE student_id IN (SELECT id FROM students WHERE roll_number = '22BEC999')"))
        await session.execute(text(f"DELETE FROM grading_sessions WHERE student_id IN (SELECT id FROM students WHERE roll_number = '22BEC999')"))
        await session.execute(text(f"DELETE FROM used_nonces WHERE student_id IN (SELECT id FROM students WHERE roll_number = '22BEC999')"))
        await session.execute(text(f"DELETE FROM students WHERE roll_number = '22BEC999'"))
        
        await session.execute(text(f"DELETE FROM assignment_configs WHERE assignment_id = '{assignment_id}'"))
        await session.execute(text(f"DELETE FROM assignment_grader_mappings WHERE assignment_id = '{assignment_id}'"))
        await session.execute(text(f"DELETE FROM assignments WHERE id = '{assignment_id}'"))
        await session.execute(text(f"DELETE FROM mentors WHERE id = '{mentor_id}'"))
        await session.commit()
        
    # 2. Insert ORM structures safely (flushing mentor first to respect foreign key constraint)
    async with AsyncSessionLocal() as session:
        # Mentor
        mentor = Mentor(
            id=mentor_id,
            username="prof_demo",
            full_name="Demo Professor",
            email="prof_demo@example.com",
            hashed_password=hash_password("pass123"),
            role=UserRole.MENTOR,
            is_active=True
        )
        session.add(mentor)
        await session.flush() # Force write mentor first!
        
        # Assignment
        assignment = Assignment(
            id=assignment_id,
            slug="demo-sync-lab",
            title="Integration Sync Demonstration Lab",
            description="Lab checking filesystem sync.",
            category="artifact_validation",
            max_score=100.0,
            is_published=True,
            is_archived=False,
            created_by_id=mentor_id
        )
        session.add(assignment)
        
        # Assignment Config
        config = AssignmentConfig(
            id=config_id,
            assignment_id=assignment_id,
            config_data=json.dumps(config_data)
        )
        session.add(config)
        
        await session.commit()
        
    print("[1/6] Database seeding complete.")
    return assignment_id

async def run_sync_test():
    """Performs the complete integration check."""
    assignment_id = await setup_test_data()
    
    print("[2/6] Registering student and logging in via HTTP APIs...")
    client = httpx.AsyncClient(base_url="http://localhost:8000", timeout=15)
    
    # 1. Register Student
    try:
        resp = await client.post("/api/v1/auth/student/register", json={
            "roll_number": "22BEC999",
            "full_name": "Demo Student",
            "email": "student_demo@example.com",
            "password": "studentpass123"
        })
        if resp.status_code == 201:
            print("  Student registered successfully.")
        else:
            print(f"  Register response: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  Register error: {e}")
        
    # 2. Login Student
    resp = await client.post("/api/v1/auth/student/login", json={
        "roll_number": "22BEC999",
        "password": "studentpass123"
    })
    if resp.status_code != 200:
        print(f"  Login failed: {resp.text}")
        sys.exit(1)
        
    token = resp.json()["access_token"]
    print("  Login successful. Token fetched.")
    
    # 3. Create Session
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/sessions/", json={"assignment_id": str(assignment_id)}, headers=headers)
    if resp.status_code != 201:
        print(f"  Session opening failed: {resp.text}")
        sys.exit(1)
        
    session_id = resp.json()["session_id"]
    print(f"  Session created. Session ID: {session_id}")
    
    print("[3/6] Preparing local workspace with target validation files...")
    # Create the test file required by the rule config in the local directory
    target_file_path = "sync_test.txt"
    with open(target_file_path, "w") as f:
        f.write("EE-Yantra Sync Verified\n")
    print(f"  Created '{target_file_path}' containing keyword verification.")

    print("[4/6] Launching Python Evaluator Orchestrator directly...")
    from evaluator.configuration import Configuration
    from evaluator.main import run_evaluation_flow
    
    eval_config = Configuration()
    eval_config.session_id = session_id
    eval_config.student_token = token
    eval_config.roll_number = "22BEC999"
    eval_config.workspace_dir = os.getcwd()
    
    exit_code = run_evaluation_flow(eval_config)
    if exit_code != 0:
        print("  Local evaluator returned an execution failure.")
        sys.exit(1)
        
    print("[5/6] Local grading complete. Querying database for sync confirmation...")
    
    from app.db.session import engine
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Check Final Results table
        res_stmt = text(f"SELECT * FROM final_results WHERE session_id = '{session_id}'")
        result = (await conn.execute(res_stmt)).first()
        
        # Check Certificates table
        cert_stmt = text(f"SELECT * FROM certificates WHERE student_id = (SELECT id FROM students WHERE roll_number = '22BEC999')")
        certificate = (await conn.execute(cert_stmt)).first()
        
    print("[6/6] Asserting backend grades database synchronization...")
    assert result is not None, "Error: No FinalResult was written to the database."
    assert float(result.score) == 100.0, f"Error: Expected score 100.0, got {result.score}"
    assert result.passed is True, "Error: Student should have passed."
    print("  [OK] FinalResult verified. Persisted grade score: 100.0")
    
    assert certificate is not None, "Error: No Certificate was generated."
    print(f"  [OK] Certificate verified. Code: {certificate.certificate_code} Issued At: {certificate.issued_at}")
    
    print("======================================================================")
    print("      SUCCESS: Artifact Validator end-to-end sync is working!       ")
    print("      Both Student and Mentor frontend dashboards will display        ")
    print(f"      Score 100.0 and Certificate: {certificate.certificate_code}    ")
    print("======================================================================")
    
    # Cleanup target files
    if os.path.exists(target_file_path):
        os.remove(target_file_path)
    if os.path.exists("proof.json"):
        os.remove("proof.json")
    if os.path.exists("challenge.json"):
        os.remove("challenge.json")
    if os.path.exists(".evaluator_state.json"):
        os.remove(".evaluator_state.json")

if __name__ == "__main__":
    asyncio.run(run_sync_test())
