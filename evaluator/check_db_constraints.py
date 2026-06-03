import os
import sys
import asyncio
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force database port to connect to local docker container mapped port
os.environ["POSTGRES_PORT"] = "5433"

from app.db.session import engine

async def check():
    print("Checking constraints and indices on final_results and certificates...")
    async with engine.begin() as conn:
        # Check indices on final_results
        print("\n--- Indices on final_results ---")
        idx_res = await conn.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'final_results'"))
        for row in idx_res.all():
            print(f"Index: {row[0]} | Def: {row[1]}")
            
        # Check constraints on final_results
        print("\n--- Constraints on final_results ---")
        con_res = await conn.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'final_results'::regclass"))
        for row in con_res.all():
            print(f"Constraint: {row[0]} | Def: {row[1]}")
            
        # Check indices on certificates
        print("\n--- Indices on certificates ---")
        idx_res2 = await conn.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'certificates'"))
        for row in idx_res2.all():
            print(f"Index: {row[0]} | Def: {row[1]}")
            
        # Check constraints on certificates
        print("\n--- Constraints on certificates ---")
        con_res2 = await conn.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'certificates'::regclass"))
        for row in con_res2.all():
            print(f"Constraint: {row[0]} | Def: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check())
