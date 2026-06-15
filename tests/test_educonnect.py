import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.database.mongodb import get_database


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def clean_db():
    # Setup: Clean test database collections before running each test
    try:
        db = get_database()
        await db.users.delete_many({})
        await db.schools.delete_many({})
        await db.assignments.delete_many({})
        await db.submissions.delete_many({})
        await db.grades.delete_many({})
        await db.events.delete_many({})
        await db.announcements.delete_many({})
    except Exception:
        pass
    yield


@pytest.mark.asyncio
async def test_school_crud(client):
    # 1. Register Admin
    reg_res = await client.post("/api/v1/auth/register", json={
        "first_name": "Admin",
        "last_name": "User",
        "username": "adminuser",
        "email": "admin@university.edu",
        "password": "Password123!",
        "role": "admin",
        "school": "MIT",
    })
    assert reg_res.status_code == 200
    admin_token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create School
    school_res = await client.post("/api/v1/schools", json={
        "name": "MIT University",
        "address": "Cambridge, MA",
        "website": "mit.edu",
        "domain": "mit.edu"
    }, headers=headers)
    assert school_res.status_code == 200
    school_data = school_res.json()
    assert school_data["name"] == "MIT University"
    school_id = school_data["id"]

    # 3. Get School
    get_res = await client.get(f"/api/v1/schools/{school_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "MIT University"

    # 4. List Schools
    list_res = await client.get("/api/v1/schools")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1


@pytest.mark.asyncio
async def test_auth_recovery_and_verification(client):
    # 1. Register
    reg_res = await client.post("/api/v1/auth/register", json={
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "email": "test@university.edu",
        "password": "Password123!",
        "role": "student",
        "school": "Stanford",
    })
    assert reg_res.status_code == 200
    
    # Check that is_verified is False initially
    db = get_database()
    user_doc = await db.users.find_one({"email": "test@university.edu"})
    assert user_doc is not None
    assert user_doc["is_verified"] is False
    assert "verification_token" in user_doc
    verify_token = user_doc["verification_token"]

    # 2. Verify Email
    verify_res = await client.post("/api/v1/auth/verify-email", json={"token": verify_token})
    assert verify_res.status_code == 200
    
    updated_user = await db.users.find_one({"email": "test@university.edu"})
    assert updated_user["is_verified"] is True

    # 3. Forgot Password
    forgot_res = await client.post("/api/v1/auth/forgot-password", json={"email": "test@university.edu"})
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["reset_token"]

    # 4. Reset Password
    reset_res = await client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewPassword123!"
    })
    assert reset_res.status_code == 200

    # 5. Verify login with new password
    login_res = await client.post("/api/v1/auth/login/json", json={
        "identifier": "testuser",
        "password": "NewPassword123!"
    })
    assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_assignments_submissions_grading(client):
    # 1. Register Teacher & Student
    reg_t = await client.post("/api/v1/auth/register", json={
        "first_name": "Teacher",
        "last_name": "Jane",
        "username": "teacherjane",
        "email": "jane@university.edu",
        "password": "Password123!",
        "role": "teacher",
        "school": "Harvard",
    })
    teacher_token = reg_t.json()["access_token"]

    reg_s = await client.post("/api/v1/auth/register", json={
        "first_name": "Student",
        "last_name": "Bob",
        "username": "studentbob",
        "email": "bob@university.edu",
        "password": "Password123!",
        "role": "student",
        "school": "Harvard",
    })
    student_token = reg_s.json()["access_token"]
    student_id = reg_s.json().get("user_id")  # Or retrieve via db / users/me
    
    # Let's get student ID from users/me
    me_res = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {student_token}"})
    student_id = me_res.json()["id"]

    # 2. Teacher creates Assignment
    assignment_res = await client.post("/api/v1/assignments", json={
        "title": "Quantum Physics Homework 1",
        "description": "Solve exercises 1 to 5.",
        "instructions_url": "http://harvard.edu/qp1.pdf",
        "course_id": "qp-101",
        "deadline": "2026-12-31T23:59:59Z",
        "max_score": 100.0
    }, headers={"Authorization": f"Bearer {teacher_token}"})
    assert assignment_res.status_code == 200
    assignment_id = assignment_res.json()["id"]

    # 3. Student submits Assignment
    sub_res = await client.post(f"/api/v1/assignments/{assignment_id}/submissions", json={
        "document_url": "http://harvard.edu/bob_submission.pdf"
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert sub_res.status_code == 200
    submission_id = sub_res.json()["id"]

    # 4. Teacher views submissions
    subs_res = await client.get(f"/api/v1/assignments/{assignment_id}/submissions", headers={"Authorization": f"Bearer {teacher_token}"})
    assert subs_res.status_code == 200
    assert subs_res.json()["total"] == 1

    # 5. Teacher grades submission
    grade_res = await client.post(f"/api/v1/submissions/{submission_id}/grade", json={
        "score": 95.0,
        "feedback": "Excellent work, Bob!"
    }, headers={"Authorization": f"Bearer {teacher_token}"})
    assert grade_res.status_code == 200
    assert grade_res.json()["status"] == "graded"
    assert grade_res.json()["grade"]["score"] == 95.0


@pytest.mark.asyncio
async def test_calendar_events(client):
    # Register teacher
    reg_t = await client.post("/api/v1/auth/register", json={
        "first_name": "Teacher",
        "last_name": "Jane",
        "username": "teacherjane2",
        "email": "jane2@university.edu",
        "password": "Password123!",
        "role": "teacher",
        "school": "Harvard",
    })
    teacher_token = reg_t.json()["access_token"]
    headers = {"Authorization": f"Bearer {teacher_token}"}

    # Create Event
    event_res = await client.post("/api/v1/events", json={
        "title": "Quantum Mechanics Lecture",
        "description": "Lecture on Wave-Particle Duality",
        "start_time": "2026-09-01T10:00:00Z",
        "end_time": "2026-09-01T12:00:00Z",
        "event_type": "event",
        "reference_id": "course_physics"
    }, headers=headers)
    assert event_res.status_code == 200
    event_id = event_res.json()["id"]

    # List Events
    list_res = await client.get("/api/v1/events", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # Get Upcoming
    upcoming_res = await client.get("/api/v1/events/upcoming", headers=headers)
    assert upcoming_res.status_code == 200


@pytest.mark.asyncio
async def test_parent_child_relationship(client):
    # 1. Register Parent & Student child
    reg_p = await client.post("/api/v1/auth/register", json={
        "first_name": "Parent",
        "last_name": "John",
        "username": "parentjohn",
        "email": "john@family.com",
        "password": "Password123!",
        "role": "parent",
    })
    parent_token = reg_p.json()["access_token"]
    parent_headers = {"Authorization": f"Bearer {parent_token}"}

    reg_c = await client.post("/api/v1/auth/register", json={
        "first_name": "Child",
        "last_name": "Billy",
        "username": "childbilly",
        "email": "billy@school.edu",
        "password": "Password123!",
        "role": "student",
    })
    child_id = "" # Will verify child profile retrieval
    
    # 2. Add child to Parent
    add_res = await client.post("/api/v1/parent/children?child_username_or_email=childbilly", headers=parent_headers)
    assert add_res.status_code == 200
    child_id = add_res.json()["child"]["id"]

    # 3. Retrieve Children list
    list_res = await client.get("/api/v1/parent/children", headers=parent_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["username"] == "childbilly"

    # 4. Get Child Progress
    progress_res = await client.get(f"/api/v1/parent/children/{child_id}/progress", headers=parent_headers)
    assert progress_res.status_code == 200
    assert "posts_this_month" in progress_res.json()
