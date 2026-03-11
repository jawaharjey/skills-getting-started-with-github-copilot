import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Snapshot of the original activities state for test isolation
_original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities to original state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))


client = TestClient(app)


# --- GET / ---

def test_root_redirects_to_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# --- GET /activities ---

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_get_activities_structure():
    response = client.get("/activities")
    data = response.json()
    for name, details in data.items():
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)


# --- POST /activities/{name}/signup ---

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]
    # Verify participant was actually added
    act = client.get("/activities").json()
    assert "newstudent@mergington.edu" in act["Chess Club"]["participants"]


def test_signup_nonexistent_activity():
    response = client.post(
        "/activities/Nonexistent Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate():
    response = client.post(
        "/activities/Chess Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


# --- DELETE /activities/{name}/unregister ---

def test_unregister_success():
    response = client.delete(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]
    # Verify participant was actually removed
    act = client.get("/activities").json()
    assert "michael@mergington.edu" not in act["Chess Club"]["participants"]


def test_unregister_nonexistent_activity():
    response = client.delete(
        "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_email_not_found():
    response = client.delete(
        "/activities/Chess Club/unregister?email=nobody@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found in this activity"
