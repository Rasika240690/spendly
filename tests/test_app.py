import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        yield client


def test_register_and_login_flow(client):
    response = client.post(
        "/register",
        data={
            "name": "Alice User",
            "email": "alice@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome back" in response.data

    response = client.post(
        "/login",
        data={
            "email": "alice@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Profile" in response.data


def test_profile_page_shows_expenses(client):
    client.post(
        "/login",
        data={
            "email": "demo@spendly.com",
            "password": "demo123",
        },
        follow_redirects=True,
    )

    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Demo User" in response.data
    assert b"Food" in response.data
