import requests
import time
import random

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register a student
roll_no = f"TEST{random.randint(10000, 99999)}"
print(f"Registering student: {roll_no}")
reg_resp = requests.post(f"{BASE_URL}/auth/student/register", json={
    "roll_number": roll_no,
    "full_name": "Test Student",
    "email": f"{roll_no}@test.com",
    "password": "password123"
})
print("Register response:", reg_resp.status_code, reg_resp.text)

# 2. Login
login_resp = requests.post(f"{BASE_URL}/auth/student/login", json={
    "roll_number": roll_no,
    "password": "password123"
})
print("Login response:", login_resp.status_code)

if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    print("Obtained Token")

    # 3. Test the quiz endpoint
    headers = {"Authorization": f"Bearer {token}"}
    quiz_resp = requests.get(f"{BASE_URL}/student/quizzes/results", headers=headers)
    
    print("Quiz Results Endpoint Status:", quiz_resp.status_code)
    if quiz_resp.status_code == 200:
        print("Quiz Results Data:", quiz_resp.json())
    else:
        print("Quiz Results Error:", quiz_resp.text)
else:
    print("Login failed, cannot test endpoint")
