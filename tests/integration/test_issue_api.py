"""
Integration tests for Issue API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

# Import Issue model to ensure it's in metadata
from crucible.db.models import Issue, RunMode, RunStatus

from crucible.api.main import app
from crucible.db.repositories import create_project, create_run


@pytest.fixture
def test_client(integration_db_session):
    """Create a test client with database override."""
    from crucible.api.main import get_db
    
    def override_get_db():
        yield integration_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_project(integration_db_session):
    """Create a test project."""
    project = create_project(
        integration_db_session,
        title="Test Project",
        description="Test description"
    )
    return project


@pytest.fixture
def test_run(integration_db_session, test_project):
    """Create a test run."""
    run = create_run(
        integration_db_session,
        project_id=test_project.id,
        mode=RunMode.FULL_SEARCH.value,
        config={"num_candidates": 5}
    )
    return run


class TestIssueAPI:
    """Test cases for Issue API endpoints."""

    def test_create_issue(self, test_client, test_project):
        """Test creating an issue."""
        response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Test issue description"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == test_project.id
        assert data["type"] == "model"
        assert data["severity"] == "minor"
        assert data["description"] == "Test issue description"
        assert data["resolution_status"] == "open"

    def test_create_issue_with_run(self, test_client, test_project, test_run):
        """Test creating an issue with run context."""
        response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "constraint",
                "severity": "important",
                "description": "Constraint issue",
                "run_id": test_run.id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == test_run.id

    def test_create_issue_invalid_project(self, test_client):
        """Test creating an issue with invalid project."""
        response = test_client.post(
            "/projects/invalid-project/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Test issue"
            }
        )
        assert response.status_code == 404

    def test_create_issue_invalid_type(self, test_client, test_project):
        """Test creating an issue with invalid type."""
        response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "invalid_type",
                "severity": "minor",
                "description": "Test issue"
            }
        )
        assert response.status_code == 400

    def test_list_issues(self, test_client, test_project):
        """Test listing issues."""
        # Create a few issues
        for i in range(3):
            test_client.post(
                f"/projects/{test_project.id}/issues",
                json={
                    "type": "model",
                    "severity": "minor",
                    "description": f"Issue {i}"
                }
            )
        
        # List issues
        response = test_client.get(f"/projects/{test_project.id}/issues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_issues_with_filters(self, test_client, test_project):
        """Test listing issues with filters."""
        # Create issues with different severities
        test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Minor issue"
            }
        )
        test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "constraint",
                "severity": "catastrophic",
                "description": "Catastrophic issue"
            }
        )
        
        # Filter by severity
        response = test_client.get(
            f"/projects/{test_project.id}/issues",
            params={"severity": "minor"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "minor"

    def test_get_issue(self, test_client, test_project):
        """Test getting a single issue."""
        # Create issue
        create_response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Test issue"
            }
        )
        issue_id = create_response.json()["id"]
        
        # Get issue
        response = test_client.get(f"/issues/{issue_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == issue_id
        assert data["description"] == "Test issue"

    def test_update_issue(self, test_client, test_project):
        """Test updating an issue."""
        # Create issue
        create_response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Original description"
            }
        )
        issue_id = create_response.json()["id"]
        
        # Update issue
        response = test_client.patch(
            f"/issues/{issue_id}",
            json={
                "description": "Updated description",
                "resolution_status": "resolved"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["resolution_status"] == "resolved"

    def test_get_feedback(self, test_client, test_project):
        """Test getting feedback for an issue."""
        # Create issue
        create_response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Test issue for feedback"
            }
        )
        issue_id = create_response.json()["id"]
        
        # Get feedback
        response = test_client.post(f"/issues/{issue_id}/feedback")
        assert response.status_code == 200
        data = response.json()
        assert data["issue_id"] == issue_id
        assert "feedback_message" in data
        assert "clarifying_questions" in data
        assert "remediation_proposal" in data or "needs_clarification" in data

