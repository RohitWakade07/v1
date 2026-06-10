from fastapi import FastAPI
from pydantic import BaseModel


from app.api.routes.submissions import router as submissions_router
from app.core.config import settings
from app.db.database import Base, engine

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


app.include_router(submissions_router)

# Mock Auth Endpoints for V1 Frontend Integration
class LoginRequest(BaseModel):
    roll_number: str
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    roll_number: str
    password: str
    class_code: str = None

@app.post("/api/v1/auth/student/register")
def mock_register(request: RegisterRequest):
    return {"message": "Account created successfully"}

@app.post("/api/v1/auth/student/login")
def mock_login(request: LoginRequest):
    return {"access_token": "mock-jwt-token", "token_type": "bearer"}

@app.get("/api/v1/students/me")
def mock_profile():
    return {
        "id": 1,
        "full_name": "Test Student",
        "email": "student@test.com",
        "roll_number": "2024CSE001",
        "role": "student",
        "classroom_status": "APPROVED",
        "classroom_name": "Test Classroom",
        "mentor_name": "Test Mentor"
    }
