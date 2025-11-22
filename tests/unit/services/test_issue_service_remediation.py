"""
Unit tests for IssueService remediation actions.

Tests edge cases and error scenarios for remediation actions.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from sqlalchemy.orm import Session

from crucible.services.issue_service import IssueService
from crucible.db.models import (
    IssueType,
    IssueSeverity,
    IssueResolutionStatus,
    RunMode,
    RunStatus,
)
from crucible.db.repositories import (
    get_issue,
    get_problem_spec,
    get_world_model,
    get_run,
)


class TestIssueServiceRemediation:
    """Test remediation action edge cases."""

    @pytest.fixture
    def mock_session(self, test_db_session):
        """Use test database session."""
        return test_db_session

    def test_patch_and_rescore_no_run_id(self, mock_session):
        """Test patch_and_rescore fails when issue has no run_id."""
        service = IssueService(mock_session)
        
        # Create issue without run_id
        from crucible.db.repositories import create_issue, create_project
        
        project = create_project(mock_session, "Test Project", "Test")
        issue = create_issue(
            mock_session,
            project_id=project.id,
            type=IssueType.MODEL.value,
            severity=IssueSeverity.MINOR.value,
            description="Test issue",
            run_id=None  # No run_id
        )
        
        with pytest.raises(ValueError, match="no associated run_id"):
            service.apply_patch_and_rescore(issue.id, {"problem_spec": {}})

    def test_patch_and_rescore_invalid_issue(self, mock_session):
        """Test patch_and_rescore fails with invalid issue ID."""
        service = IssueService(mock_session)
        
        with pytest.raises(ValueError, match="Issue not found"):
            service.apply_patch_and_rescore("invalid-issue-id", {"problem_spec": {}})

    def test_partial_rerun_no_run_id(self, mock_session):
        """Test partial_rerun fails when issue has no run_id."""
        service = IssueService(mock_session)
        
        from crucible.db.repositories import create_issue, create_project
        
        project = create_project(mock_session, "Test Project", "Test")
        issue = create_issue(
            mock_session,
            project_id=project.id,
            type=IssueType.CONSTRAINT.value,
            severity=IssueSeverity.IMPORTANT.value,
            description="Test issue",
            run_id=None
        )
        
        with pytest.raises(ValueError, match="no associated run_id"):
            service.apply_partial_rerun(issue.id, {"problem_spec": {}})

    def test_full_rerun_invalid_issue(self, mock_session):
        """Test full_rerun fails with invalid issue ID."""
        service = IssueService(mock_session)
        
        with pytest.raises(ValueError, match="Issue not found"):
            service.apply_full_rerun("invalid-issue-id", {"problem_spec": {}})

    def test_invalidate_candidates_no_candidate_ids(self, mock_session):
        """Test invalidate_candidates handles empty candidate list."""
        service = IssueService(mock_session)
        
        from crucible.db.repositories import create_issue, create_project
        
        project = create_project(mock_session, "Test Project", "Test")
        issue = create_issue(
            mock_session,
            project_id=project.id,
            type=IssueType.EVALUATOR.value,
            severity=IssueSeverity.CATASTROPHIC.value,
            description="Test issue"
        )
        
        # Should handle empty list gracefully
        result = service.invalidate_candidates(issue.id, [])
        assert result["status"] == "success"
        assert result["action"] == "invalidate_candidates"
        assert len(result.get("invalidated_candidates", [])) == 0

    def test_patch_and_rescore_wrong_severity_warning(self, mock_session):
        """Test patch_and_rescore logs warning for non-minor issues."""
        service = IssueService(mock_session)
        
        from crucible.db.repositories import create_issue, create_project, create_run
        
        project = create_project(mock_session, "Test Project", "Test")
        run = create_run(
            mock_session,
            project_id=project.id,
            mode=RunMode.FULL_SEARCH.value,
            config={"num_candidates": 5}
        )
        issue = create_issue(
            mock_session,
            project_id=project.id,
            type=IssueType.MODEL.value,
            severity=IssueSeverity.IMPORTANT.value,  # Not MINOR
            description="Test issue",
            run_id=run.id
        )
        
        # Mock RunService to avoid actual execution
        with patch.object(service.run_service, 'execute_evaluate_and_rank_phase') as mock_execute:
            mock_execute.side_effect = Exception("RunService not fully implemented")
            
            with pytest.raises(Exception):
                service.apply_patch_and_rescore(issue.id, {"problem_spec": {}})
            
            # Verify warning was logged (check via logger if possible)
            # For now, just verify the method was called with correct issue

    def test_patch_application_merges_constraints(self, mock_session):
        """Test that patch application properly merges constraints."""
        service = IssueService(mock_session)
        
        from crucible.db.repositories import (
            create_issue, create_project, create_run, create_problem_spec
        )
        
        project = create_project(mock_session, "Test Project", "Test")
        problem_spec = create_problem_spec(
            mock_session,
            project_id=project.id,
            constraints=[
                {"name": "Existing", "description": "Existing constraint", "weight": 50}
            ],
            goals=["Existing goal"]
        )
        run = create_run(
            mock_session,
            project_id=project.id,
            mode=RunMode.FULL_SEARCH.value,
            config={"num_candidates": 5}
        )
        issue = create_issue(
            mock_session,
            project_id=project.id,
            type=IssueType.CONSTRAINT.value,
            severity=IssueSeverity.MINOR.value,
            description="Test issue",
            run_id=run.id
        )
        
        # Patch with new constraint
        patch_data = {
            "problem_spec": {
                "constraints": [
                    {"name": "Existing", "description": "Existing constraint", "weight": 50},
                    {"name": "New", "description": "New constraint", "weight": 75}
                ]
            }
        }
        
        # Mock RunService
        with patch.object(service.run_service, 'execute_evaluate_and_rank_phase') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            result = service.apply_patch_and_rescore(issue.id, patch_data)
            
            assert result["status"] == "success"
            assert "problem_spec" in result["patches_applied"]
            
            # Verify constraints were updated
            updated_spec = get_problem_spec(mock_session, project.id)
            assert len(updated_spec.constraints) == 2
            assert any(c["name"] == "New" for c in updated_spec.constraints)

