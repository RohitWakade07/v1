import asyncio
import os
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlmodel import select
from app.db.session import AsyncSessionLocal
from app.models.models import Assignment, AssignmentCategory

mentor_id = uuid.UUID("43c18c21-fb72-45a4-abb0-159ada17837c")

async def seed_assignments():
    async with AsyncSessionLocal() as db:
        # Delete existing data
        await db.execute(text("DELETE FROM certificates"))
        await db.execute(text("DELETE FROM final_results"))
        await db.execute(text("DELETE FROM submission_results"))
        await db.execute(text("DELETE FROM submissions"))
        await db.execute(text("DELETE FROM proof_submissions"))
        await db.execute(text("DELETE FROM grading_sessions"))
        await db.execute(text(f"DELETE FROM assignments WHERE created_by_id = '{mentor_id}'"))
        
        # Week 1
        w1 = Assignment(
            id=uuid.uuid4(),
            slug="week1",
            title="Week 1: Workspace Setup",
            description="Write a plain text file commands.txt containing shell commands that build a developer workspace. When run, the commands must: create 12 weekly directories (week-01 to week-12) under eep-software/, create notes/, scripts/, capstone/ directories, add a README.md in each weekly folder, create workspace-report.txt with the directory tree, and create a .bashrc with at least 2 aliases.",
            instructions="Your command file (`commands.txt`) will be executed in a fresh workspace. The automated evaluator will verify the exit status and ensure all 12 weekly directories, the structural directories (notes, scripts, capstone), weekly READMEs, workspace-report.txt, and a .bashrc with aliases have been created exactly as specified.",
            category=AssignmentCategory.FILESYSTEM_VALIDATION,
            max_score=5.0,
            deadline=datetime(2026, 6, 20),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Week 2
        w2 = Assignment(
            id=uuid.uuid4(),
            slug="week2",
            title="Week 2: Command-Line Log Analyzer",
            description="Build a small toolkit of one-liner pipelines that analyses a server log file and produces a short report (report.txt) with top IP addresses, top URLs, status code distribution, and total request count.",
            instructions="Your script (`analyze.sh`) will be executed against a sample `server.log` file provided in the workspace. The evaluator will verify that your script completes successfully and that it correctly generates a `report.txt` file containing the expected log analysis metrics.",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 6, 27),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Week 3
        w3 = Assignment(
            id=uuid.uuid4(),
            slug="week3",
            title="Week 3: Automated File Organizer",
            description="Write a Bash script organize.sh that takes a directory path as an argument and automatically sorts its contents into sub-folders by file type (Documents/, Images/, Code/, Other/). Validate the input directory exists, move files based on extension, and print a summary.",
            instructions="Your script (`organize.sh`) will be run against a target directory (`test_mixed`) containing 15 various files. The evaluator will verify that all files are correctly moved into their respective subfolders (Documents/, Images/, Code/, Other/) based on their file extensions, and that the root directory is cleared.",
            category=AssignmentCategory.FILESYSTEM_VALIDATION,
            max_score=5.0,
            deadline=datetime(2026, 7, 4),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        # Week 4
        w4 = Assignment(
            id=uuid.uuid4(),
            slug="week4",
            title="Week 4: Local Repository Recovery Challenge",
            description="You are provided with a 'broken' repository archive containing files that should have been ignored, a commit with a typo, and two branches that need merging. You must hand back a cleaned repository with a sensible .gitignore, a clean git log, and a RECOVERY.md file documenting every Git command you ran.",
            instructions="Your submission must be a ZIP archive of your cleaned Git repository. The automated evaluator will verify that the `.git` folder exists, that `RECOVERY.md` and `.gitignore` are present, that large/log files have been successfully untracked, and that the commit history shows a successful amend and merge.",
            category=AssignmentCategory.GIT_VALIDATION,
            max_score=5.0,
            deadline=datetime(2026, 7, 11),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add_all([w1, w2, w3, w4])
        await db.commit()
        print("Successfully seeded assignments.")

if __name__ == "__main__":
    asyncio.run(seed_assignments())

