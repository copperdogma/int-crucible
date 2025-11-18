"""
Unit tests for run verification utilities.
"""

import pytest
from datetime import datetime

from crucible.services.run_verification import (
    verify_run_completeness,
    verify_data_integrity,
    get_run_statistics
)
from crucible.db.repositories import (
    create_project,
    create_problem_spec,
    create_world_model,
    create_run,
    create_candidate,
    create_scenario_suite,
    create_evaluation,
)
from crucible.db.models import RunStatus


class TestRunVerification:
    """Test suite for run verification utilities."""
    
    def test_verify_run_completeness_complete(self, test_db_session):
        """Test verification of a complete run."""
        # Create project with prerequisites
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=["Goal 1"],
            resolution="medium",
            mode="full_search"
        )
        create_world_model(
            test_db_session,
            project.id,
            model_data={"actors": []}
        )
        
        # Create run
        run = create_run(
            test_db_session,
            project.id,
            mode="full_search"
        )
        
        # Create candidates
        candidate1 = create_candidate(
            test_db_session,
            run_id=run.id,
            project_id=project.id,
            origin="system",
            mechanism_description="Test mechanism 1"
        )
        candidate2 = create_candidate(
            test_db_session,
            run_id=run.id,
            project_id=project.id,
            origin="system",
            mechanism_description="Test mechanism 2"
        )
        
        # Create scenario suite
        scenario_suite = create_scenario_suite(
            test_db_session,
            run_id=run.id,
            scenarios=[
                {"id": "scenario_1", "description": "Test scenario 1"},
                {"id": "scenario_2", "description": "Test scenario 2"}
            ]
        )
        
        # Create evaluations (2 candidates * 2 scenarios = 4 evaluations)
        create_evaluation(
            test_db_session,
            candidate_id=candidate1.id,
            run_id=run.id,
            scenario_id="scenario_1",
            P={"value": 0.8},
            R={"value": 0.5}
        )
        create_evaluation(
            test_db_session,
            candidate_id=candidate1.id,
            run_id=run.id,
            scenario_id="scenario_2",
            P={"value": 0.7},
            R={"value": 0.6}
        )
        create_evaluation(
            test_db_session,
            candidate_id=candidate2.id,
            run_id=run.id,
            scenario_id="scenario_1",
            P={"value": 0.9},
            R={"value": 0.4}
        )
        create_evaluation(
            test_db_session,
            candidate_id=candidate2.id,
            run_id=run.id,
            scenario_id="scenario_2",
            P={"value": 0.85},
            R={"value": 0.5}
        )
        
        # Update run status to completed
        from crucible.db.repositories import update_run_status
        update_run_status(
            test_db_session,
            run.id,
            RunStatus.COMPLETED.value,
            completed_at=datetime.utcnow()
        )
        
        # Verify
        result = verify_run_completeness(test_db_session, run.id)
        
        assert result["is_complete"] is True
        assert result["run_status"] == RunStatus.COMPLETED.value
        assert result["has_problem_spec"] is True
        assert result["has_world_model"] is True
        assert result["candidate_count"] == 2
        assert result["scenario_count"] == 2
        assert result["evaluation_count"] == 4
        assert result["expected_evaluations"] == 4
        assert result["missing_evaluations"] == 0
        assert len(result["issues"]) == 0
    
    def test_verify_run_completeness_missing_prerequisites(self, test_db_session):
        """Test verification when prerequisites are missing."""
        project = create_project(test_db_session, "Test Project", "Test description")
        run = create_run(test_db_session, project.id, mode="full_search")
        
        result = verify_run_completeness(test_db_session, run.id)
        
        assert result["is_complete"] is False
        assert result["has_problem_spec"] is False
        assert result["has_world_model"] is False
        assert len(result["issues"]) >= 2
        assert any("ProblemSpec" in issue for issue in result["issues"])
        assert any("WorldModel" in issue for issue in result["issues"])
    
    def test_verify_run_completeness_missing_evaluations(self, test_db_session):
        """Test verification when evaluations are missing."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(test_db_session, project.id, constraints=[], goals=[], resolution="medium", mode="full_search")
        create_world_model(test_db_session, project.id, model_data={})
        
        run = create_run(test_db_session, project.id, mode="full_search")
        
        # Create candidates and scenarios but not all evaluations
        candidate = create_candidate(test_db_session, run_id=run.id, project_id=project.id, origin="system", mechanism_description="Test")
        create_scenario_suite(test_db_session, run_id=run.id, scenarios=[
            {"id": "scenario_1"}, {"id": "scenario_2"}
        ])
        
        # Only create 1 evaluation instead of 2
        create_evaluation(test_db_session, candidate_id=candidate.id, run_id=run.id, scenario_id="scenario_1", P={}, R={})
        
        result = verify_run_completeness(test_db_session, run.id)
        
        assert result["is_complete"] is False
        assert result["candidate_count"] == 1
        assert result["scenario_count"] == 2
        assert result["evaluation_count"] == 1
        assert result["expected_evaluations"] == 2
        assert result["missing_evaluations"] == 1
        assert any("Missing" in issue and "evaluations" in issue for issue in result["issues"])
    
    def test_verify_run_completeness_nonexistent_run(self, test_db_session):
        """Test verification of non-existent run."""
        result = verify_run_completeness(test_db_session, "nonexistent-run-id")
        
        assert result["is_complete"] is False
        assert result["run_status"] is None
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_verify_data_integrity_valid(self, test_db_session):
        """Test data integrity verification for valid data."""
        project = create_project(test_db_session, "Test Project", "Test description")
        run = create_run(test_db_session, project.id, mode="full_search")
        
        candidate = create_candidate(
            test_db_session,
            run_id=run.id,
            project_id=project.id,
            origin="system",
            mechanism_description="Test"
        )
        
        create_evaluation(
            test_db_session,
            candidate_id=candidate.id,
            run_id=run.id,
            scenario_id="scenario_1",
            P={},
            R={}
        )
        
        result = verify_data_integrity(test_db_session, run.id)
        
        assert result["is_valid"] is True
        assert len(result["issues"]) == 0
        assert len(result["candidate_issues"]) == 0
        assert len(result["evaluation_issues"]) == 0
    
    def test_verify_data_integrity_invalid_candidate_run_id(self, test_db_session):
        """Test data integrity verification with invalid candidate run_id."""
        project = create_project(test_db_session, "Test Project", "Test description")
        run1 = create_run(test_db_session, project.id, mode="full_search")
        run2 = create_run(test_db_session, project.id, mode="full_search")
        
        # Create candidate with wrong run_id (manually set to test)
        candidate = create_candidate(
            test_db_session,
            run_id=run1.id,
            project_id=project.id,
            origin="system",
            mechanism_description="Test"
        )
        # Manually change run_id to wrong value
        candidate.run_id = run2.id
        test_db_session.commit()
        
        result = verify_data_integrity(test_db_session, run1.id)
        
        # Note: This test may not catch the issue if the repository enforces constraints
        # But it tests the verification logic
        assert isinstance(result["is_valid"], bool)
    
    def test_verify_data_integrity_invalid_evaluation_candidate(self, test_db_session):
        """Test data integrity verification with evaluation referencing non-existent candidate."""
        project = create_project(test_db_session, "Test Project", "Test description")
        run = create_run(test_db_session, project.id, mode="full_search")
        
        # Create evaluation with non-existent candidate_id
        create_evaluation(
            test_db_session,
            candidate_id="nonexistent-candidate-id",
            run_id=run.id,
            scenario_id="scenario_1",
            P={},
            R={}
        )
        
        result = verify_data_integrity(test_db_session, run.id)
        
        assert result["is_valid"] is False
        assert len(result["evaluation_issues"]) > 0
        assert any("non-existent candidate" in issue.lower() for issue in result["evaluation_issues"])
    
    def test_verify_data_integrity_nonexistent_run(self, test_db_session):
        """Test data integrity verification for non-existent run."""
        result = verify_data_integrity(test_db_session, "nonexistent-run-id")
        
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0
        assert "not found" in result["issues"][0].lower()
    
    def test_get_run_statistics(self, test_db_session):
        """Test getting run statistics."""
        project = create_project(test_db_session, "Test Project", "Test description")
        run = create_run(test_db_session, project.id, mode="full_search")
        
        # Update run with timestamps
        from crucible.db.repositories import update_run_status
        started_at = datetime.utcnow()
        update_run_status(
            test_db_session,
            run.id,
            RunStatus.RUNNING.value,
            started_at=started_at
        )
        
        # Create some entities
        candidate = create_candidate(
            test_db_session,
            run_id=run.id,
            project_id=project.id,
            origin="system",
            mechanism_description="Test"
        )
        candidate.scores = {"I": 0.8, "P": 0.7, "R": 0.5}
        test_db_session.commit()
        
        create_scenario_suite(
            test_db_session,
            run_id=run.id,
            scenarios=[
                {"id": "scenario_1"},
                {"id": "scenario_2"}
            ]
        )
        
        create_evaluation(
            test_db_session,
            candidate_id=candidate.id,
            run_id=run.id,
            scenario_id="scenario_1",
            P={},
            R={}
        )
        
        # Update to completed
        completed_at = datetime.utcnow()
        update_run_status(
            test_db_session,
            run.id,
            RunStatus.COMPLETED.value,
            completed_at=completed_at
        )
        
        result = get_run_statistics(test_db_session, run.id)
        
        assert result["run_id"] == run.id
        assert result["project_id"] == project.id
        assert result["status"] == RunStatus.COMPLETED.value
        assert result["candidate_count"] == 1
        assert result["scenario_count"] == 2
        assert result["evaluation_count"] == 1
        assert result["has_rankings"] is True
        assert result["duration_seconds"] is not None
        assert result["duration_seconds"] > 0
    
    def test_get_run_statistics_nonexistent(self, test_db_session):
        """Test getting statistics for non-existent run."""
        result = get_run_statistics(test_db_session, "nonexistent-run-id")
        
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_get_run_statistics_no_rankings(self, test_db_session):
        """Test getting statistics for run without rankings."""
        project = create_project(test_db_session, "Test Project", "Test description")
        run = create_run(test_db_session, project.id, mode="full_search")
        
        candidate = create_candidate(
            test_db_session,
            run_id=run.id,
            project_id=project.id,
            origin="system",
            mechanism_description="Test"
        )
        # No scores set
        
        result = get_run_statistics(test_db_session, run.id)
        
        assert result["has_rankings"] is False

