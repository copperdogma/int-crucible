"""
Unit tests for SnapshotService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from crucible.services.snapshot_service import SnapshotService
from crucible.db.models import Snapshot


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    session.execute = Mock()
    session.commit = Mock()
    session.bind = Mock()
    return session


@pytest.fixture
def snapshot_service(mock_session):
    """Create SnapshotService with mocked session."""
    service = SnapshotService(mock_session)
    return service


@pytest.fixture
def sample_problem_spec_data():
    """Sample ProblemSpec data."""
    return {
        "constraints": [{"name": "constraint_1", "description": "Test", "weight": 80}],
        "goals": ["Goal 1"],
        "resolution": "medium",
        "mode": "full_search",
        "provenance_log": []
    }


@pytest.fixture
def sample_world_model_data():
    """Sample WorldModel data."""
    return {
        "model_data": {
            "actors": [{"id": "actor_1", "name": "Actor 1"}],
            "mechanisms": [],
            "resources": []
        }
    }


@pytest.fixture
def sample_snapshot_data(sample_problem_spec_data, sample_world_model_data):
    """Sample snapshot data structure."""
    return {
        "version": "1.0",
        "problem_spec": sample_problem_spec_data,
        "world_model": sample_world_model_data,
        "run_config": {
            "mode": "full_search",
            "config": {"num_candidates": 5, "num_scenarios": 8}
        }
    }


class TestCaptureSnapshotData:
    """Tests for capture_snapshot_data method."""

    def test_capture_snapshot_data_basic(self, snapshot_service, mock_session, sample_problem_spec_data, sample_world_model_data):
        """Test basic snapshot data capture."""
        project_id = "test-project-123"
        
        # Mock inspector
        inspector = Mock()
        inspector.get_columns = Mock(return_value=[
            {"name": "constraints"},
            {"name": "goals"},
            {"name": "resolution"},
            {"name": "mode"},
            {"name": "provenance_log"}
        ])
        
        with patch('sqlalchemy.inspect') as mock_inspect:
            mock_inspect.return_value = inspector
            
            # Mock SQL results
            problem_spec_row = Mock()
            problem_spec_row.__getitem__ = Mock(side_effect=lambda i: [
                json.dumps(sample_problem_spec_data["constraints"]),
                json.dumps(sample_problem_spec_data["goals"]),
                sample_problem_spec_data["resolution"],
                sample_problem_spec_data["mode"],
                json.dumps(sample_problem_spec_data["provenance_log"])
            ][i])
            
            world_model_row = Mock()
            world_model_row.__getitem__ = Mock(return_value=json.dumps(sample_world_model_data["model_data"]))
            
            mock_result = Mock()
            mock_result.fetchone = Mock(side_effect=[problem_spec_row, world_model_row])
            mock_session.execute.return_value = mock_result
            
            result = snapshot_service.capture_snapshot_data(project_id=project_id)
            
            assert result["version"] == "1.0"
            assert "problem_spec" in result
            assert "world_model" in result
            assert result["problem_spec"]["constraints"] == sample_problem_spec_data["constraints"]
            assert result["world_model"]["model_data"] == sample_world_model_data["model_data"]

    def test_capture_snapshot_data_with_run(self, snapshot_service, mock_session):
        """Test snapshot data capture with run reference."""
        project_id = "test-project-123"
        run_id = "test-run-456"
        
        # Mock inspector
        inspector = Mock()
        inspector.get_columns = Mock(return_value=[
            {"name": "constraints"},
            {"name": "goals"},
            {"name": "resolution"},
            {"name": "mode"},
            {"name": "provenance_log"}
        ])
        
        with patch('sqlalchemy.inspect') as mock_inspect, \
             patch('crucible.services.snapshot_service.get_run') as mock_get_run:
            mock_inspect.return_value = inspector
            
            # Mock run
            mock_run = Mock()
            mock_run.mode = Mock()
            mock_run.mode.value = "full_search"
            mock_run.config = {"num_candidates": 5, "num_scenarios": 8}
            mock_get_run.return_value = mock_run
            
            # Mock SQL results
            problem_spec_row = Mock()
            problem_spec_row.__getitem__ = Mock(side_effect=lambda i: [
                json.dumps([]),
                json.dumps([]),
                "medium",
                "full_search",
                json.dumps([])
            ][i])
            
            world_model_row = Mock()
            world_model_row.__getitem__ = Mock(return_value=json.dumps({}))
            
            mock_result = Mock()
            mock_result.fetchone = Mock(side_effect=[problem_spec_row, world_model_row])
            mock_session.execute.return_value = mock_result
            
            result = snapshot_service.capture_snapshot_data(project_id=project_id, run_id=run_id)
            
            assert "run_config" in result
            assert result["run_config"]["mode"] == "full_search"
            assert result["run_config"]["config"] == {"num_candidates": 5, "num_scenarios": 8}


class TestRestoreSnapshotData:
    """Tests for restore_snapshot_data method."""

    def test_restore_snapshot_data_new(self, snapshot_service, mock_session, sample_snapshot_data):
        """Test restoring snapshot data to new project."""
        project_id = "new-project-123"
        
        # Mock inspector
        inspector = Mock()
        inspector.get_columns = Mock(return_value=[
            {"name": "constraints"},
            {"name": "goals"},
            {"name": "resolution"},
            {"name": "mode"},
            {"name": "provenance_log"}
        ])
        
        with patch('sqlalchemy.inspect') as mock_inspect, \
             patch('crucible.services.snapshot_service.uuid') as mock_uuid:
            mock_inspect.return_value = inspector
            mock_uuid.uuid4.return_value.hex = "spec-id-123"
            mock_uuid.uuid4.return_value.__str__ = Mock(return_value="spec-id-123")
            
            # Mock SQL results (no existing spec/model)
            mock_result = Mock()
            mock_result.fetchone = Mock(return_value=None)
            mock_session.execute.return_value = mock_result
            
            snapshot_service.restore_snapshot_data(project_id, sample_snapshot_data)
            
            # Verify SQL was called to insert
            assert mock_session.execute.call_count >= 2  # ProblemSpec and WorldModel inserts
            mock_session.commit.assert_called()


class TestValidateInvariants:
    """Tests for validate_invariants method."""
    
    # Note: Full invariant validation tests require complex mocking of get_run_statistics
    # These are better suited for integration tests. Unit tests focus on simpler operations.


class TestCaptureReferenceMetrics:
    """Tests for capture_reference_metrics method."""

    def test_capture_reference_metrics(self, snapshot_service, mock_session):
        """Test capturing reference metrics from a run."""
        run_id = "test-run-123"
        
        # Mock run with metrics
        mock_run = Mock()
        mock_run.candidate_count = 5
        mock_run.scenario_count = 8
        mock_run.evaluation_count = 40
        mock_run.status = Mock()
        mock_run.status.value = "COMPLETED"
        mock_run.duration_seconds = 120.5
        mock_run.llm_usage = {"total_cost_usd": 0.50}
        mock_run.metrics = {"top_i_score": 0.75}
        
        with patch('crucible.services.snapshot_service.get_run', return_value=mock_run):
            result = snapshot_service.capture_reference_metrics(run_id)
            
            assert result["candidate_count"] == 5
            assert result["scenario_count"] == 8
            assert result["evaluation_count"] == 40
            assert result["status"] == "COMPLETED"
            assert result["duration_seconds"] == 120.5
            assert result["llm_usage"]["total_cost_usd"] == 0.50
            assert result["metrics"]["top_i_score"] == 0.75

