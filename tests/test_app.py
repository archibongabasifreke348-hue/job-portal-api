import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


# =========================================================
# HOME TEST
# =========================================================

def test_home(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Job Portal API Running"


# =========================================================
# REGISTER TEST
# =========================================================

def test_register(client):
    response = client.post(
        "/register",
        json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "password123"
        }
    )

    assert response.status_code in [201, 409]


# =========================================================
# REGISTER VALIDATION TEST
# =========================================================

def test_register_missing_data(client):
    response = client.post(
        "/register",
        json={}
    )

    assert response.status_code == 400


# =========================================================
# LOGIN TEST
# =========================================================

def test_login(client):
    email = "loginuser@example.com"
    password = "password123"

    # Register user first
    client.post(
        "/register",
        json={
            "name": "Login User",
            "email": email,
            "password": password
        }
    )

    # Login
    response = client.post(
        "/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Login successful"


# =========================================================
# WRONG PASSWORD TEST
# =========================================================

def test_login_wrong_password(client):
    email = "wrongpassword@example.com"

    client.post(
        "/register",
        json={
            "name": "Wrong Password",
            "email": email,
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        json={
            "email": email,
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


# =========================================================
# COMPANY TEST
# =========================================================

def test_add_company(client):
    response = client.post(
        "/company",
        json={
            "name": "Test Company",
            "location": "Lagos"
        }
    )

    assert response.status_code == 201


# =========================================================
# GET COMPANIES TEST
# =========================================================

def test_get_companies(client):
    response = client.get("/companies")

    assert response.status_code == 200

    assert isinstance(response.get_json(), list)


# =========================================================
# ADD JOB TEST
# =========================================================

def test_add_job(client):
    # Create company
    company_response = client.post(
        "/company",
        json={
            "name": "Job Test Company",
            "location": "Abuja"
        }
    )

    assert company_response.status_code == 201

    # Get company ID
    companies = client.get("/companies").get_json()

    company_id = companies[-1]["id"]

    # Create job
    response = client.post(
        "/add_job",
        json={
            "title": "Python Developer",
            "company_id": company_id,
            "location": "Abuja",
            "salary": "₦200,000",
            "job_type": "Full-time"
        }
    )

    assert response.status_code == 201


# =========================================================
# GET JOBS TEST
# =========================================================

def test_get_jobs(client):
    response = client.get("/jobs")

    assert response.status_code == 200

    assert isinstance(response.get_json(), list)


# =========================================================
# APPLY FOR JOB TEST
# =========================================================

def test_apply_for_job(client):
    # Create user
    email = "applicant@example.com"

    client.post(
        "/register",
        json={
            "name": "Applicant",
            "email": email,
            "password": "password123"
        }
    )

    # Login to get user ID
    login_response = client.post(
        "/login",
        json={
            "email": email,
            "password": "password123"
        }
    )

    user_id = login_response.get_json()["user_id"]

    # Create company
    client.post(
        "/company",
        json={
            "name": "Application Company",
            "location": "Uyo"
        }
    )

    companies = client.get("/companies").get_json()
    company_id = companies[-1]["id"]

    # Create job
    client.post(
        "/add_job",
        json={
            "title": "Flask Developer",
            "company_id": company_id,
            "location": "Uyo",
            "salary": "₦250,000",
            "job_type": "Full-time"
        }
    )

    jobs = client.get("/jobs").get_json()
    job_id = jobs[-1]["id"]

    # Apply
    response = client.post(
        "/apply",
        json={
            "user_id": user_id,
            "job_id": job_id
        }
    )

    assert response.status_code == 201


# =========================================================
# DUPLICATE APPLICATION TEST
# =========================================================

def test_duplicate_application(client):
    email = "duplicate@example.com"

    client.post(
        "/register",
        json={
            "name": "Duplicate User",
            "email": email,
            "password": "password123"
        }
    )

    login_response = client.post(
        "/login",
        json={
            "email": email,
            "password": "password123"
        }
    )

    user_id = login_response.get_json()["user_id"]

    client.post(
        "/company",
        json={
            "name": "Duplicate Company",
            "location": "Lagos"
        }
    )

    companies = client.get("/companies").get_json()
    company_id = companies[-1]["id"]

    client.post(
        "/add_job",
        json={
            "title": "Software Developer",
            "company_id": company_id,
            "location": "Lagos",
            "salary": "₦300,000",
            "job_type": "Full-time"
        }
    )

    jobs = client.get("/jobs").get_json()
    job_id = jobs[-1]["id"]

    # First application
    first = client.post(
        "/apply",
        json={
            "user_id": user_id,
            "job_id": job_id
        }
    )

    assert first.status_code == 201

    # Second application
    second = client.post(
        "/apply",
        json={
            "user_id": user_id,
            "job_id": job_id
        }
    )

    assert second.status_code == 409


# =========================================================
# MY APPLICATIONS TEST
# =========================================================

def test_my_applications(client):
    response = client.get(
        "/my_applications?user_id=1"
    )

    assert response.status_code == 200

    assert isinstance(response.get_json(), list)