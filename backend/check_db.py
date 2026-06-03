import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.db.session import init_db
import app.models.models

async def check_db():
    await init_db()
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]
        print("Tables in DB:", tables)

if __name__ == "__main__":
    asyncio.run(check_db())
