"""
Seed an admin user for the Admin Control Center.
Run: python seed_admin.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.models import Mentor, UserRole
from app.core.security import hash_password
from sqlmodel import select

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession)

async def seed_admin():
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Mentor).where(Mentor.username == 'admin'))
        if not existing.scalar_one_or_none():
            print("Seeding admin user...")
            admin = Mentor(
                username='admin',
                full_name='Platform Administrator',
                email='admin@eysip.local',
                hashed_password=hash_password('Admin@1234'),
                role=UserRole.ADMIN,
            )
            session.add(admin)
            await session.commit()
            print("Admin seeded!")
            print("  Username: admin")
            print("  Password: Admin@1234")
        else:
            print("Admin already exists.")

if __name__ == "__main__":
    asyncio.run(seed_admin())
