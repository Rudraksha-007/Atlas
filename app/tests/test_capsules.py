import requests
import pytest
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# Test user data – use a unique email to avoid conflicts with previous runs
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "SecurePass123!"
TEST_USERNAME = f"tester_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def test_user():
    """Create a test user via /auth/local/signup and return credentials."""
    signup_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "user_name": TEST_USERNAME,
    }
    # If user already exists (e.g., from a previous run), ignore conflict and continue
    resp = requests.post(f"{BASE_URL}/auth/local/signup", json=signup_payload)
    if resp.status_code == 409:
        # User already exists – we'll still use the same credentials
        pass
    elif resp.status_code != 200:
        raise Exception(f"Signup failed: {resp.text}")
    return {"email": TEST_EMAIL, "password": TEST_PASSWORD, "username": TEST_USERNAME}


@pytest.fixture(scope="module")
def auth_token(test_user):
    """Login and return access token."""
    login_payload = {
        "email": test_user["email"],
        "password": test_user["password"],
    }
    resp = requests.post(f"{BASE_URL}/auth/local/login", json=login_payload)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]


def test_create_capsule(auth_token):
    """Test that a capsule is created with the proper email_list structure."""
    payload = {
        "subject": "Integration Test Capsule",
        "body": "This capsule was created by an automated test.",
        "del_time": (datetime.now() + timedelta(days=30)).isoformat() + "+05:30",
        "client_ip": "192.168.1.100",
        "api_ver": "v1.0",
        "email_list": [
            {"email": "friend1@example.com", "status": "due"},
            {"email": "friend2@example.com"},  # status omitted -> defaults to "due"
        ],
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = requests.post(f"{BASE_URL}/capsule/create", json=payload, headers=headers)
    assert resp.status_code == 200, f"Create capsule failed: {resp.text}"
    data = resp.json()

    # Check response contains expected fields
    assert "id" in data
    assert data["subject"] == payload["subject"]
    assert data["body"] == payload["body"]
    assert "created_at" in data
    assert "updated_at" in data

    # Verify email_list structure – each item must have exactly email and status
    email_list = data["email_list"]
    assert isinstance(email_list, list)
    for item in email_list:
        assert "email" in item
        assert "status" in item
        # Ensure no extra keys like "name"
        assert set(item.keys()) == {
            "email",
            "status",
        }, f"Extra keys found: {item.keys()}"

    # Optional: clean up – delete the capsule (if you have a delete endpoint) or just leave it.
    # Since this is a test, you might want to delete it afterward.
