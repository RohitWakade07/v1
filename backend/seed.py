import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.models import Mentor, UserRole
from app.core.security import hash_password
from sqlmodel import select

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession)

async def seed():
    async with AsyncSessionLocal() as session:
        # Check if mentor exists
        existing = await session.execute(select(Mentor).where(Mentor.username == 'test_mentor'))
        if not existing.scalar_one_or_none():
            print("Seeding test_mentor...")
            mentor = Mentor(
                username='test_mentor',
                full_name='Test Mentor',
                email='mentor@test.com',
                hashed_password=hash_password('password123'),
                role=UserRole.MENTOR
            )
            session.add(mentor)
            await session.commit()
            print("Mentor seeded successfully!")
        else:
            print("Mentor already exists.")

if __name__ == "__main__":
    asyncio.run(seed())
