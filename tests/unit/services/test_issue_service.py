"""
Unit tests for IssueService.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from crucible.services.issue_service import IssueService
from crucible.db.models import (
    IssueType,
    IssueSeverity,
    IssueResolutionStatus,
    RunMode,
    RunStatus,
    CandidateStatus,
)
from crucible.db.repositories import create_project, create_run, create_candidate


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = Mock()
    session.commit = Mock()
    return session


@pytest.fixture
def issue_service(mock_session):
    """Create an IssueService instance."""
    return IssueService(mock_session)


@pytest.fixture
def sample_project(mock_session):
    """Create a sample project."""
    from crucible.db.repositories import create_project as repo_create_project
    project = repo_create_project(
        mock_session,
        title="Test Project",
        description="Test description"
    )
    return project


class TestIssueService:
    """Test cases for IssueService."""

    def test_create_issue_success(self, issue_service, mock_session, sample_project):
        """Test successful issue creation."""
        from crucible.db.repositories import (
            get_project,
            create_issue as repo_create_issue,
            get_problem_spec,
        )
        from crucible.db.models import ProblemSpec
        
        # Mock repository calls
        mock_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        # Mock ProblemSpec
        problem_spec = Mock(spec=ProblemSpec)
        problem_spec.provenance_log = []
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            sample_project,  # get_project
            problem_spec,    # get_problem_spec
        ]
        
        # Mock create_issue
        with patch('crucible.services.issue_service.repo_create_issue') as mock_create:
            mock_issue = Mock()
            mock_issue.id = "issue-123"
            mock_issue.project_id = sample_project.id
            mock_issue.run_id = None
            mock_issue.candidate_id = None
            mock_issue.type = Mock(value=IssueType.MODEL.value)
            mock_issue.severity = Mock(value=IssueSeverity.MINOR.value)
            mock_issue.description = "Test issue"
            mock_issue.resolution_status = Mock(value=IssueResolutionStatus.OPEN.value)
            mock_issue.created_at = datetime.utcnow()
            mock_create.return_value = mock_issue
            
            result = issue_service.create_issue(
                project_id=sample_project.id,
                issue_type=IssueType.MODEL.value,
                severity=IssueSeverity.MINOR.value,
                description="Test issue"
            )
            
            assert result["id"] == "issue-123"
            assert result["project_id"] == sample_project.id
            assert result["type"] == IssueType.MODEL.value
            assert result["severity"] == IssueSeverity.MINOR.value
            mock_create.assert_called_once()

    def test_create_issue_invalid_project(self, issue_service, mock_session):
        """Test issue creation with invalid project."""
        from crucible.db.repositories import get_project
        
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Project not found"):
            issue_service.create_issue(
                project_id="invalid-project",
                issue_type=IssueType.MODEL.value,
                severity=IssueSeverity.MINOR.value,
                description="Test issue"
            )

    def test_create_issue_invalid_type(self, issue_service, mock_session, sample_project):
        """Test issue creation with invalid type."""
        from crucible.db.repositories import get_project
        
        mock_session.query.return_value.filter.return_value.first.return_value = sample_project
        
        with pytest.raises(ValueError, match="Invalid issue type"):
            issue_service.create_issue(
                project_id=sample_project.id,
                issue_type="invalid_type",
                severity=IssueSeverity.MINOR.value,
                description="Test issue"
            )

    def test_get_issue_context(self, issue_service, mock_session):
        """Test getting issue context."""
        from crucible.db.repositories import get_issue, get_project, get_problem_spec, get_world_model
        
        # Mock issue
        mock_issue = Mock()
        mock_issue.id = "issue-123"
        mock_issue.project_id = "project-123"
        mock_issue.run_id = None
        mock_issue.candidate_id = None
        mock_issue.type = Mock(value=IssueType.MODEL.value)
        mock_issue.severity = Mock(value=IssueSeverity.MINOR.value)
        mock_issue.description = "Test issue"
        
        # Mock project
        mock_project = Mock()
        mock_project.id = "project-123"
        mock_project.title = "Test Project"
        mock_project.description = "Test"
        
        # Mock ProblemSpec
        mock_problem_spec = Mock()
        mock_problem_spec.id = "spec-123"
        mock_problem_spec.constraints = []
        mock_problem_spec.goals = []
        mock_problem_spec.resolution = Mock(value="medium")
        mock_problem_spec.mode = Mock(value="full_search")
        
        # Mock WorldModel
        mock_world_model = Mock()
        mock_world_model.id = "model-123"
        mock_world_model.model_data = {}
        
        # Setup mocks
        with patch('crucible.services.issue_service.get_issue', return_value=mock_issue), \
             patch('crucible.services.issue_service.get_project', return_value=mock_project), \
             patch('crucible.services.issue_service.get_problem_spec', return_value=mock_problem_spec), \
             patch('crucible.services.issue_service.get_world_model', return_value=mock_world_model):
            
            context = issue_service.get_issue_context("issue-123")
            
            assert context["issue"]["id"] == "issue-123"
            assert context["project"]["id"] == "project-123"
            assert context["problem_spec"]["id"] == "spec-123"
            assert context["world_model"]["id"] == "model-123"

    def test_get_issue_context_not_found(self, issue_service):
        """Test getting context for non-existent issue."""
        with patch('crucible.services.issue_service.get_issue', return_value=None):
            with pytest.raises(ValueError, match="Issue not found"):
                issue_service.get_issue_context("invalid-issue")

    def test_invalidate_candidates(self, issue_service, mock_session):
        """Test invalidating candidates."""
        from crucible.db.repositories import get_issue, get_candidate, update_candidate, append_candidate_provenance_entry
        
        # Mock issue
        mock_issue = Mock()
        mock_issue.id = "issue-123"
        mock_issue.project_id = "project-123"
        
        # Mock candidate
        mock_candidate = Mock()
        mock_candidate.id = "candidate-123"
        mock_candidate.project_id = "project-123"
        mock_candidate.provenance_log = []
        
        with patch('crucible.services.issue_service.get_issue', return_value=mock_issue), \
             patch('crucible.services.issue_service.get_candidate', return_value=mock_candidate), \
             patch('crucible.services.issue_service.update_candidate') as mock_update, \
             patch('crucible.services.issue_service.append_candidate_provenance_entry') as mock_append, \
             patch('crucible.services.issue_service.repo_update_issue') as mock_update_issue:
            
            result = issue_service.invalidate_candidates(
                issue_id="issue-123",
                candidate_ids=["candidate-123"],
                reason="Test invalidation"
            )
            
            assert result["status"] == "success"
            assert result["action"] == "invalidate_candidates"
            assert "candidate-123" in result["invalidated_candidates"]
            mock_update.assert_called_once()
            mock_append.assert_called_once()

