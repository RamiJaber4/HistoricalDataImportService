import io

import pytest
from fastapi.testclient import TestClient

from app import app
from deps import CurrentContext, get_current_context


def make_context(role="staff", company_id=1):
    return CurrentContext(user_id=1, username="test_user", role=role, company_id=company_id)


@pytest.fixture
def authed_client():
    # Swap the real auth dependency for a fake one via FastAPI's dependency_overrides,
    # instead of hand-faking a JWT + a real DB user for every test.
    app.dependency_overrides[get_current_context] = lambda: make_context()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_upload_file_accepts_valid_csv(authed_client):
    csv_content = b"recipient_name,address,status\nJohn Doe,123 Main St,active\n"
    response = authed_client.post(
        "/upload_file",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
    )

    assert response.status_code == 200
    assert "file_tracking_id" in response.json()


def test_upload_file_rejects_non_csv(authed_client):
    response = authed_client.post(
        "/upload_file",
        files={"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")},
    )

    assert response.status_code == 400


def test_upload_file_requires_auth():
    # No override here: this goes through the real get_current_context, proving
    # the dependency actually gates the route rather than the override masking it.
    with TestClient(app) as client:
        response = client.post(
            "/upload_file",
            files={"file": ("test.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")},
        )

    assert response.status_code == 401
