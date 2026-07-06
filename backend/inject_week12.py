import asyncio
import uuid
from datetime import datetime
from sqlmodel import select
from app.db.session import AsyncSessionLocal
from app.models.models import Assignment, AssignmentCategory, Mentor, UserRole

async def inject_week12():
    async with AsyncSessionLocal() as db:
        # Fetch the admin user dynamically
        result = await db.execute(select(Mentor).where(Mentor.role == UserRole.ADMIN))
        admin = result.scalars().first()
        if not admin:
            print("Error: No admin user found.")
            return
        
        mentor_id = admin.id

        # Check if week 12 exists
        result = await db.execute(select(Assignment).where(Assignment.slug == "week12"))
        existing = result.scalars().first()
        if existing:
            print("Week 12 already exists.")
            return

        w12 = Assignment(
            expected_structure="build_index.py\nmain.py\nquery.py\nREADME.md\nrequirements.txt\ncorpus/doc0.json\ncorpus/doc1.json\ncorpus/doc2.json\nengine/__init__.py",
            id=uuid.uuid4(),
            slug="week12",
            title="Week 12: Final Capstone Demonstration",
            description="Finalization and live demonstration of the complete Intelligent Wikipedia Search Engine system.",
            instructions="Submit your final repository ZIP. Ensure your search engine is fully functional, properly documented with a README, and handles complex multi-word queries correctly.",
            category=AssignmentCategory.MANUAL_REVIEW,
            max_score=5.0,
            deadline=datetime(2026, 9, 5),
            is_published=True,
            created_by_id=mentor_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(w12)
        await db.commit()
        print("Successfully injected Week 12 assignment!")

if __name__ == "__main__":
    asyncio.run(inject_week12())
