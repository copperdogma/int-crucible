"""
Unit tests for run service improvements (error handling, logging, status reporting).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from crucible.services.run_service import RunService
from crucible.db.repositories import (
    create_project,
    create_problem_spec,
    create_world_model,
    create_run,
    get_run,
    update_run_status,
    list_projects,
)
from crucible.db.models import RunStatus


class TestRunServiceImprovements:
    """Test suite for run service improvements."""
    
    def test_execute_full_pipeline_missing_problem_spec(self, test_db_session):
        """Test that execute_full_pipeline raises clear error when ProblemSpec is missing."""
        project = create_project(test_db_session, "Test Project", "Test description")
        # Create WorldModel but not ProblemSpec
        create_world_model(test_db_session, project.id, model_data={})
        
        run = create_run(test_db_session, project.id, mode="full_search")
        service = RunService(test_db_session)
        
        with pytest.raises(ValueError) as exc_info:
            service.execute_full_pipeline(run.id, num_candidates=2, num_scenarios=2)
        
        error_msg = str(exc_info.value)
        assert "ProblemSpec not found" in error_msg
        assert project.id in error_msg
        # Should list available projects
        assert "Available projects" in error_msg or "available projects" in error_msg.lower()
        
        # Verify run status is set to failed
        updated_run = get_run(test_db_session, run.id)
        assert updated_run.status == RunStatus.FAILED.value
    
    def test_execute_full_pipeline_missing_world_model(self, test_db_session):
        """Test that execute_full_pipeline raises clear error when WorldModel is missing."""
        project = create_project(test_db_session, "Test Project", "Test description")
        # Create ProblemSpec but not WorldModel
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search"
        )
        
        run = create_run(test_db_session, project.id, mode="full_search")
        service = RunService(test_db_session)
        
        with pytest.raises(ValueError) as exc_info:
            service.execute_full_pipeline(run.id, num_candidates=2, num_scenarios=2)
        
        error_msg = str(exc_info.value)
        assert "WorldModel not found" in error_msg
        assert project.id in error_msg
        
        # Verify run status is set to failed
        updated_run = get_run(test_db_session, run.id)
        assert updated_run.status == RunStatus.FAILED.value
    
    def test_execute_full_pipeline_session_refresh(self, test_db_session):
        """Test that execute_full_pipeline refreshes session to see committed data."""
        project = create_project(test_db_session, "Test Project", "Test description")
        
        # Create prerequisites in same session
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search"
        )
        create_world_model(test_db_session, project.id, model_data={})
        test_db_session.commit()
        
        run = create_run(test_db_session, project.id, mode="full_search")
        test_db_session.commit()
        
        service = RunService(test_db_session)
        
        # Mock the phase methods to avoid actual execution
        with patch.object(service, 'execute_design_and_scenario_phase') as mock_design, \
             patch.object(service, 'execute_evaluate_and_rank_phase') as mock_eval:
            
            mock_design.return_value = {
                "candidates": {"count": 2},
                "scenarios": {"count": 2},
                "status": "completed"
            }
            mock_eval.return_value = {
                "evaluations": {"count": 4},
                "rankings": {"count": 2},
                "status": "completed"
            }
            
            result = service.execute_full_pipeline(run.id, num_candidates=2, num_scenarios=2)
            
            # Should not raise error about missing prerequisites
            assert result["status"] == "completed"
            assert "timing" in result
    
    def test_execute_full_pipeline_status_completed_on_success(self, test_db_session):
        """Test that run status is set to completed when pipeline succeeds."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search"
        )
        create_world_model(test_db_session, project.id, model_data={})
        
        run = create_run(test_db_session, project.id, mode="full_search")
        service = RunService(test_db_session)
        
        # Mock the phase methods
        with patch.object(service, 'execute_design_and_scenario_phase') as mock_design, \
             patch.object(service, 'execute_evaluate_and_rank_phase') as mock_eval:
            
            mock_design.return_value = {
                "candidates": {"count": 2},
                "scenarios": {"count": 2},
                "status": "completed"
            }
            mock_eval.return_value = {
                "evaluations": {"count": 4},
                "rankings": {"count": 2},
                "status": "completed"
            }
            
            service.execute_full_pipeline(run.id, num_candidates=2, num_scenarios=2)
            
            # Verify status is completed
            updated_run = get_run(test_db_session, run.id)
            assert updated_run.status == RunStatus.COMPLETED.value
            assert updated_run.completed_at is not None
    
    def test_execute_full_pipeline_status_failed_on_error(self, test_db_session):
        """Test that run status is set to failed when pipeline fails."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search"
        )
        create_world_model(test_db_session, project.id, model_data={})
        
        run = create_run(test_db_session, project.id, mode="full_search")
        service = RunService(test_db_session)
        
        # Mock the phase methods to raise an error
        with patch.object(service, 'execute_design_and_scenario_phase') as mock_design:
            mock_design.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                service.execute_full_pipeline(run.id, num_candidates=2, num_scenarios=2)
            
            # Verify status is failed
            updated_run = get_run(test_db_session, run.id)
            assert updated_run.status == RunStatus.FAILED.value
    
    def test_execute_full_pipeline_does_not_overwrite_completed_status(self, test_db_session):
        """Test that execute_full_pipeline doesn't overwrite completed status on error."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search"
        )
        create_world_model(test_db_session, project.id, model_data={})
        
        run = create_run(test_db_session, project.id, mode="full_search")
        # Set status to completed first
        update_run_status(
            test_db_session,
            run.id,
            RunStatus.COMPLETED.value,
            completed_at=datetime.utcnow()
        )
        
        service = RunService(test_db_session)
        
        # Mock to raise error
        with patch.object(service, 'execute_design_and_scenario_phase') as mock_design:
            mock_design.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                service.execute_full_pipeline(run.id, num_candidates=2, num_scenarios=2)
            
            # Verify status is still completed (not overwritten to failed)
            updated_run = get_run(test_db_session, run.id)
            assert updated_run.status == RunStatus.COMPLETED.value
    
    def test_execute_full_pipeline_includes_timing(self, test_db_session):
        """Test that execute_full_pipeline includes timing information in result."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search"
        )
        create_world_model(test_db_session, project.id, model_data={})
        
        run = create_run(test_db_session, project.id, mode="full_search")
        service = RunService(test_db_session)
        
        # Mock the phase methods
        with patch.object(service, 'execute_design_and_scenario_phase') as mock_design, \
             patch.object(service, 'execute_evaluate_and_rank_phase') as mock_eval:
            
            mock_design.return_value = {
                "candidates": {"count": 2},
                "scenarios": {"count": 2},
                "status": "completed"
            }
            mock_eval.return_value = {
                "evaluations": {"count": 4},
                "rankings": {"count": 2},
                "status": "completed"
            }
            
            result = service.execute_full_pipeline(run.id, num_candidates=2, num_scenarios=2)
            
            assert "timing" in result
            assert "total" in result["timing"]
            assert "phase1" in result["timing"]
            assert "phase2" in result["timing"]
            assert result["timing"]["total"] > 0
            assert result["timing"]["phase1"] >= 0
            assert result["timing"]["phase2"] >= 0

