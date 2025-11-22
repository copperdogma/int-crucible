"""
Integration tests for Issue API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

# Import Issue model to ensure it's in metadata
from crucible.db.models import Issue, RunMode, RunStatus

from crucible.api.main import app
from crucible.db.repositories import create_project, create_run, create_issue


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
def db_session(test_client, integration_db_session):
    """Provide database session for direct database operations in tests."""
    return integration_db_session


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

    def test_resolve_issue_auto_upgrade_patch_and_rescore_no_run_id(self, test_client, test_project, db_session):
        """Test that patch_and_rescore auto-upgrades to full_rerun when issue has no run_id."""
        from unittest.mock import patch
        
        # Create issue without run_id
        issue = create_issue(
            db_session,
            project_id=test_project.id,
            type="model",
            severity="minor",
            description="Test issue without run",
            run_id=None
        )
        
        # Mock the full_rerun to avoid actual execution
        with patch('crucible.services.issue_service.IssueService.apply_full_rerun') as mock_full_rerun:
            mock_full_rerun.return_value = {
                "status": "success",
                "action": "full_rerun",
                "patches_applied": []
            }
            
            response = test_client.post(
                f"/issues/{issue.id}/resolve",
                json={
                    "remediation_action": "patch_and_rescore",
                    "remediation_metadata": {"problem_spec": {}}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["remediation_action"] == "full_rerun"  # Auto-upgraded
            assert data["original_remediation_action"] == "patch_and_rescore"
            assert data["action_upgraded"] is True
            assert "auto-upgraded" in data["message"].lower()
            
            # Verify full_rerun was called, not patch_and_rescore
            mock_full_rerun.assert_called_once()

    def test_resolve_issue_auto_upgrade_partial_rerun_no_run_id(self, test_client, test_project, db_session):
        """Test that partial_rerun auto-upgrades to full_rerun when issue has no run_id."""
        from unittest.mock import patch
        
        # Create issue without run_id
        issue = create_issue(
            db_session,
            project_id=test_project.id,
            type="constraint",
            severity="important",
            description="Test issue without run",
            run_id=None
        )
        
        # Mock the full_rerun to avoid actual execution
        with patch('crucible.services.issue_service.IssueService.apply_full_rerun') as mock_full_rerun:
            mock_full_rerun.return_value = {
                "status": "success",
                "action": "full_rerun",
                "patches_applied": []
            }
            
            response = test_client.post(
                f"/issues/{issue.id}/resolve",
                json={
                    "remediation_action": "partial_rerun",
                    "remediation_metadata": {"problem_spec": {}}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["remediation_action"] == "full_rerun"  # Auto-upgraded
            assert data["original_remediation_action"] == "partial_rerun"
            assert data["action_upgraded"] is True
            
            # Verify full_rerun was called
            mock_full_rerun.assert_called_once()

    def test_resolve_issue_no_upgrade_with_run_id(self, test_client, test_project, test_run, db_session):
        """Test that patch_and_rescore works normally when issue has run_id."""
        from unittest.mock import patch
        
        # Create issue with run_id
        issue = create_issue(
            db_session,
            project_id=test_project.id,
            type="model",
            severity="minor",
            description="Test issue with run",
            run_id=test_run.id
        )
        
        # Mock patch_and_rescore (full_rerun should NOT be called)
        with patch('crucible.services.issue_service.IssueService.apply_patch_and_rescore') as mock_patch:
            with patch('crucible.services.issue_service.IssueService.apply_full_rerun') as mock_full:
                mock_patch.return_value = {
                    "status": "success",
                    "action": "patch_and_rescore",
                    "patches_applied": ["problem_spec"]
                }
                
                response = test_client.post(
                    f"/issues/{issue.id}/resolve",
                    json={
                        "remediation_action": "patch_and_rescore",
                        "remediation_metadata": {"problem_spec": {}}
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["remediation_action"] == "patch_and_rescore"  # Not upgraded
                assert data["action_upgraded"] is False
                assert data.get("original_remediation_action") is None
                
                # Verify patch_and_rescore was called, not full_rerun
                mock_patch.assert_called_once()
                mock_full.assert_not_called()

    def test_resolve_issue_full_rerun_no_upgrade_needed(self, test_client, test_project, db_session):
        """Test that full_rerun doesn't require run_id and works normally."""
        from unittest.mock import patch
        
        # Create issue without run_id
        issue = create_issue(
            db_session,
            project_id=test_project.id,
            type="model",
            severity="catastrophic",
            description="Test issue for full rerun",
            run_id=None
        )
        
        # Mock full_rerun
        with patch('crucible.services.issue_service.IssueService.apply_full_rerun') as mock_full_rerun:
            mock_full_rerun.return_value = {
                "status": "success",
                "action": "full_rerun",
                "patches_applied": []
            }
            
            response = test_client.post(
                f"/issues/{issue.id}/resolve",
                json={
                    "remediation_action": "full_rerun",
                    "remediation_metadata": {"problem_spec": {}}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["remediation_action"] == "full_rerun"
            assert data["action_upgraded"] is False  # No upgrade needed

