"""
End-to-end tests for remediation approval flow.

Tests the complete user flow:
1. Create an issue
2. Get feedback/remediation proposal
3. Approve remediation (with auto-upgrade scenario)
4. Verify remediation was applied
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from crucible.api.main import app
from crucible.db.repositories import create_project, create_issue, create_run
from crucible.db.models import RunMode, IssueResolutionStatus


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
def db_session(integration_db_session):
    """Provide database session for direct database operations in tests."""
    return integration_db_session


class TestRemediationE2E:
    """End-to-end tests for remediation flow."""

    def test_remediation_flow_with_auto_upgrade(self, test_client, test_project):
        """
        Test complete remediation flow with auto-upgrade scenario.
        
        Scenario:
        1. Create issue without run_id
        2. Get feedback (receives patch_and_rescore proposal)
        3. Approve remediation
        4. Verify auto-upgrade to full_rerun
        5. Verify remediation was applied
        """
        # Step 1: Create issue without run_id
        create_response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Issue without run context"
            }
        )
        assert create_response.status_code == 200
        issue_id = create_response.json()["id"]

        # Step 2: Get feedback/remediation proposal
        feedback_response = test_client.post(f"/issues/{issue_id}/feedback")
        assert feedback_response.status_code == 200
        feedback_data = feedback_response.json()
        
        # Should have remediation proposal
        assert "remediation_proposal" in feedback_data or "needs_clarification" in feedback_data
        
        # Step 3 & 4: Approve remediation (mock to avoid actual execution)
        with patch('crucible.services.issue_service.IssueService.apply_full_rerun') as mock_full_rerun:
            mock_full_rerun.return_value = {
                "status": "success",
                "action": "full_rerun",
                "patches_applied": [],
            }
            
            # Assume proposal suggests patch_and_rescore
            resolve_response = test_client.post(
                f"/issues/{issue_id}/resolve",
                json={
                    "remediation_action": "patch_and_rescore",
                    "remediation_metadata": {"problem_spec": {}}
                }
            )
            
            assert resolve_response.status_code == 200
            resolve_data = resolve_response.json()
            
            # Verify auto-upgrade happened
            assert resolve_data["status"] == "success"
            assert resolve_data["remediation_action"] == "full_rerun"
            assert resolve_data["action_upgraded"] is True
            assert resolve_data["original_remediation_action"] == "patch_and_rescore"
            assert "auto-upgraded" in resolve_data["message"].lower()
            
            # Verify full_rerun was called
            mock_full_rerun.assert_called_once()

        # Step 5: Verify issue is resolved
        get_response = test_client.get(f"/issues/{issue_id}")
        assert get_response.status_code == 200
        issue_data = get_response.json()
        assert issue_data["resolution_status"] == IssueResolutionStatus.RESOLVED.value

    def test_remediation_flow_without_auto_upgrade(self, test_client, test_project):
        """
        Test complete remediation flow without auto-upgrade.
        
        Scenario:
        1. Create issue with run_id
        2. Get feedback
        3. Approve remediation (patch_and_rescore)
        4. Verify no auto-upgrade
        5. Verify remediation was applied
        """
    def test_remediation_flow_without_auto_upgrade(self, test_client, test_project, db_session):
        """
        Test complete remediation flow without auto-upgrade.
        
        Scenario:
        1. Create issue with run_id
        2. Get feedback
        3. Approve remediation (patch_and_rescore)
        4. Verify no auto-upgrade
        5. Verify remediation was applied
        """
        # Step 1: Create run and issue with run_id
        run = create_run(
            db_session,
            project_id=test_project.id,
            mode=RunMode.FULL_SEARCH.value,
            config={"num_candidates": 5}
        )
        
        create_response = test_client.post(
            f"/projects/{test_project.id}/issues",
            json={
                "type": "model",
                "severity": "minor",
                "description": "Issue with run context",
                "run_id": run.id
            }
        )
        assert create_response.status_code == 200
        issue_id = create_response.json()["id"]

        # Step 2: Get feedback
        feedback_response = test_client.post(f"/issues/{issue_id}/feedback")
        assert feedback_response.status_code == 200

        # Step 3 & 4: Approve remediation (mock to avoid actual execution)
        with patch('crucible.services.issue_service.IssueService.apply_patch_and_rescore') as mock_patch:
            mock_patch.return_value = {
                "status": "success",
                "action": "patch_and_rescore",
                "patches_applied": ["problem_spec"],
            }
            
            resolve_response = test_client.post(
                f"/issues/{issue_id}/resolve",
                json={
                    "remediation_action": "patch_and_rescore",
                    "remediation_metadata": {"problem_spec": {}}
                }
            )
            
            assert resolve_response.status_code == 200
            resolve_data = resolve_response.json()
            
            # Verify no auto-upgrade
            assert resolve_data["status"] == "success"
            assert resolve_data["remediation_action"] == "patch_and_rescore"
            assert resolve_data["action_upgraded"] is False
            
            # Verify patch_and_rescore was called
            mock_patch.assert_called_once()

        # Step 5: Verify issue is resolved
        get_response = test_client.get(f"/issues/{issue_id}")
        assert get_response.status_code == 200
        issue_data = get_response.json()
        assert issue_data["resolution_status"] == IssueResolutionStatus.RESOLVED.value
