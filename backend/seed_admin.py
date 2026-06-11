"""
seed_admin.py — Creates the initial admin account.

Run once after first deployment:
  railway run python seed_admin.py
  OR
  python seed_admin.py  (locally with .env set up)

Credentials seeded:
  username : eyantrastaff@gmail.com
  email    : eyantrastaff@gmail.com
  password : eyantrastaff@gmail.com
  role     : admin
"""

import asyncio
import os
import sys

# Load .env for local runs
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

# Must set PYTHONPATH=. or run from backend/ directory
from app.core.config import settings
from app.core.security import hash_password
from app.models.models import Mentor, UserRole


ADMIN_USERNAME = "eyantrastaff@gmail.com"
ADMIN_EMAIL    = "eyantrastaff@gmail.com"
ADMIN_PASSWORD = "eyantrastaff@gmail.com"
ADMIN_FULLNAME = "E-Yantra Staff"


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if already exists
        result = await session.execute(
            select(Mentor).where(Mentor.username == ADMIN_USERNAME)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[seed_admin] Admin '{ADMIN_USERNAME}' already exists — skipping.")
            await engine.dispose()
            return

        admin = Mentor(
            username=ADMIN_USERNAME,
            full_name=ADMIN_FULLNAME,
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print(f"[seed_admin] ✅ Admin account created successfully!")
        print(f"  Username : {ADMIN_USERNAME}")
        print(f"  Email    : {ADMIN_EMAIL}")
        print(f"  Role     : admin")
        print(f"  ID       : {admin.id}")
        print()
        print("  ⚠️  Change this password after first login!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
