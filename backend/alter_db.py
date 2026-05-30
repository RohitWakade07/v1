import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def alter_db():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE assignments ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;"))
            print("Successfully added is_archived to assignments")
        except Exception as e:
            print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(alter_db())
