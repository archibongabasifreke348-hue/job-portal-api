def register_user(client):
    response = client.post(
        "/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    return response


def login_user(client):
    response = client.post(
        "/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    return response


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json["message"] == "Job Portal API Running"


def test_register(client):
    response = register_user(client)

    assert response.status_code == 201
    assert response.json["message"] == "User registered successfully"


def test_duplicate_register(client):
    register_user(client)

    response = register_user(client)

    assert response.status_code == 409


def test_login(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200
    assert "token" in response.json
    assert response.json["user_id"] == 1


def test_invalid_login(client):
    register_user(client)

    response = client.post(
        "/login",
        json={
            "email": "test@example.com",
            "password": "wrong-password"
        }
    )

    assert response.status_code == 401


def test_apply_requires_token(client):
    response = client.post(
        "/apply",
        json={
            "job_id": 1
        }
    )

    assert response.status_code == 401


def test_my_applications_requires_token(client):
    response = client.get("/my_applications")

    assert response.status_code == 401


def test_job_applications_requires_token(client):
    response = client.get("/job/1/applications")

    assert response.status_code == 401