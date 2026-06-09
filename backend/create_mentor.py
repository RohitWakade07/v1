import argparse
import asyncio

from sqlmodel import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.models import Mentor, UserRole


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a mentor or admin user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", choices=["mentor", "admin"], default="mentor")
    parser.add_argument("--inactive", action="store_true")
    return parser.parse_args()


async def create_mentor(args: argparse.Namespace) -> int:
    async with AsyncSessionLocal() as session:
        existing_username = await session.execute(
            select(Mentor).where(Mentor.username == args.username)
        )
        if existing_username.scalar_one_or_none():
            print(f"Mentor username already exists: {args.username}")
            return 1

        existing_email = await session.execute(
            select(Mentor).where(Mentor.email == args.email)
        )
        if existing_email.scalar_one_or_none():
            print(f"Mentor email already exists: {args.email}")
            return 1

        mentor = Mentor(
            username=args.username,
            full_name=args.full_name,
            email=args.email,
            hashed_password=hash_password(args.password),
            role=UserRole.ADMIN if args.role == "admin" else UserRole.MENTOR,
            is_active=not args.inactive,
        )
        session.add(mentor)
        await session.commit()

        print(
            "Created mentor: "
            f"username={mentor.username} role={mentor.role} active={mentor.is_active}"
        )
        return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(create_mentor(args))


if __name__ == "__main__":
    raise SystemExit(main())
