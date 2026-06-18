import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Student
from app.api.v1.dependencies import get_approved_student
import uuid

client = TestClient(app)

def override_get_approved_student():
    return Student(
        id=uuid.uuid4(),
        roll_number="TEST_001",
        full_name="Test Student",
        email="test@example.com",
        hashed_password="fake",
    )

app.dependency_overrides[get_approved_student] = override_get_approved_student

def test_get_all_quiz_results_student():
    response = client.get("/api/v1/student/quizzes/results")
    assert response.status_code == 200
    # Expected to be an empty list if no results yet, or a list of summaries
    data = response.json()
    assert isinstance(data, list)
    print("Quiz Results Endpoint response:", data)

if __name__ == "__main__":
    test_get_all_quiz_results_student()
    print("Test passed successfully!")
