import asyncio
import os
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlmodel import select
from app.db.session import AsyncSessionLocal
from app.models.models import Assignment, AssignmentCategory, Mentor, UserRole

async def seed_assignments():
    async with AsyncSessionLocal() as db:
        # Fetch the admin user dynamically
        result = await db.execute(select(Mentor).where(Mentor.role == UserRole.ADMIN))
        admin = result.scalars().first()
        if not admin:
            print("Error: No admin user found. Please run seed_admin.py first.")
            return
        
        mentor_id = admin.id

        # Delete existing data
        await db.execute(text("DELETE FROM certificates"))
        await db.execute(text("DELETE FROM final_results"))
        await db.execute(text("DELETE FROM submission_results"))
        await db.execute(text("DELETE FROM grading_jobs"))
        await db.execute(text("DELETE FROM execution_metrics"))
        await db.execute(text("DELETE FROM execution_logs"))
        await db.execute(text("DELETE FROM submission_outbox"))
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
        
        # Week 5
        w5 = Assignment(
            id=uuid.uuid4(),
            slug="week5",
            title="Week 5: GitHub Collaboration",
            description="Resolve merge conflicts and push a clean main branch with a shared TEAMWORK.md.",
            instructions="Submit the zip.",
            category=AssignmentCategory.GIT_VALIDATION,
            max_score=5.0,
            deadline=datetime(2026, 7, 18),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Week 6
        w6 = Assignment(
            id=uuid.uuid4(),
            slug="week6",
            title="Week 6: Text Corpus Analyzer",
            description="Build an interactive Python CLI that provides word stats.",
            instructions="Submit analyze.py zip.",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 7, 25),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Week 7
        w7 = Assignment(
            id=uuid.uuid4(),
            slug="week7",
            title="Week 7: Wikipedia Collector",
            description="Build a web scraper that fetches Wikipedia pages from a list of URLs and saves each article as a structured JSON file.",
            instructions="Submit a ZIP containing `collect_wiki.py` and `requirements.txt`. Your script must generate a `corpus/` directory with at least 3 JSON files, each containing 'title', 'url', and 'text' keys with non-trivial text content (>=50 words).",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 8, 1),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Week 8
        w8 = Assignment(
            id=uuid.uuid4(),
            slug="week8",
            title="Week 8: Metadata Organizer",
            description="Build a modular Python package that processes the Week 7 corpus and computes per-document and corpus-level metadata.",
            instructions="Submit a ZIP containing `main.py` and a `metadata_organizer/` package with `loader.py`, `tokenizer.py`, and `writer.py`. Your code must output `metadata.json` containing total_documents, average_length, vocabulary_size, and per-document metrics (word_count, top_10_terms).",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 8, 8),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Week 9
        w9 = Assignment(
            id=uuid.uuid4(),
            slug="week9",
            title="Week 9: Inverted Index",
            description="Build an inverted index from the document corpus and a lookup tool to query terms.",
            instructions="Submit a ZIP containing `build_index.py` and `lookup.py`. The build script must generate `index.json` (term -> doc -> frequency). The lookup script must accept a term via standard input and print the corresponding documents.",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 8, 15),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Week 10
        w10 = Assignment(
            id=uuid.uuid4(),
            slug="week10",
            title="Week 10: Indexing & Search Architecture",
            description="Integrate the inverted index into a complete query engine that returns top-ranked documents.",
            instructions="Submit your repository ZIP. The engine should accept a query, process it, look up terms in the index, rank results by total frequency or TF-IDF, and return the relevant documents in order.",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 8, 22),
            is_published=False,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Week 11
        w11 = Assignment(
            id=uuid.uuid4(),
            slug="week11",
            title="Week 11: Final Capstone Development",
            description="Build a full intelligent search engine with dataset cleaning, NLP techniques, inverted index, ranking, and a CLI interface.",
            instructions="Submit your repository ZIP. Must include a corpus/ of articles, a modular package with data processing, an inverted index implementation, a robust query runner, and a main entrypoint.",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 8, 29),
            is_published=False,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Week 12
        w12 = Assignment(
            id=uuid.uuid4(),
            slug="week12",
            title="Week 12: Final Capstone Demonstration",
            description="Finalization and live demonstration of the complete Intelligent Wikipedia Search Engine system.",
            instructions="Submit your final repository ZIP. Ensure your search engine is fully functional, properly documented with a README, and handles complex multi-word queries correctly.",
            category=AssignmentCategory.DETERMINISTIC_EXECUTION,
            max_score=5.0,
            deadline=datetime(2026, 9, 5),
            is_published=False,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add_all([w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12])
        await db.commit()
        print("Successfully seeded assignments.")

if __name__ == "__main__":
    asyncio.run(seed_assignments())

