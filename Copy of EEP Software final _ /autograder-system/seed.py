from app.db.database import SessionLocal, engine
from app.db.models import Base, User, Assignment
import time

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Seed User
if not db.query(User).first():
    db.add(User(full_name="Test Student", email="student@test.com", role="student"))

# Seed Assignment
if not db.query(Assignment).first():
    db.add(Assignment(title="Fibonacci", description="Return nth fibonacci", language="python"))

db.commit()
db.close()
print("Seeded DB!")
