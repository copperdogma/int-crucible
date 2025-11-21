"""
Unit tests for RunPreflightService.
"""

from crucible.services.run_preflight_service import RunPreflightService
from crucible.db.repositories import (
    create_project,
    create_problem_spec,
    create_world_model,
)
from crucible.models.run_contracts import RunBlockerCode, RunWarningCode


class TestRunPreflightService:
    """Validate readiness and warning logic for run preflight."""

    def test_preflight_blocks_missing_prerequisites(self, test_db_session):
        project = create_project(test_db_session, "Preflight Test", "desc")
        service = RunPreflightService(test_db_session)

        result = service.preflight(
            project_id=project.id,
            mode="full_search",
            parameters={"num_candidates": 10, "num_scenarios": 5},
        )

        assert result.ready is False
        assert RunBlockerCode.MISSING_PROBLEM_SPEC in result.blockers
        assert RunBlockerCode.MISSING_WORLD_MODEL in result.blockers
        assert result.prerequisites["problem_spec"] is False
        assert result.prerequisites["world_model"] is False

    def test_preflight_ready_when_prerequisites_exist(self, test_db_session):
        project = create_project(test_db_session, "Preflight Ready", "desc")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search",
        )
        create_world_model(test_db_session, project.id, model_data={})

        service = RunPreflightService(test_db_session)
        result = service.preflight(
            project_id=project.id,
            mode="full_search",
            parameters={"num_candidates": 3, "num_scenarios": 4},
        )

        assert result.ready is True
        assert result.blockers == []
        assert result.prerequisites["problem_spec"] is True
        assert result.prerequisites["world_model"] is True
        assert result.normalized_config["num_candidates"] == 3

    def test_preflight_warns_on_large_candidate_counts(self, test_db_session):
        project = create_project(test_db_session, "Preflight Warn", "desc")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[],
            goals=[],
            resolution="medium",
            mode="full_search",
        )
        create_world_model(test_db_session, project.id, model_data={})

        service = RunPreflightService(test_db_session)
        result = service.preflight(
            project_id=project.id,
            mode="full_search",
            parameters={"num_candidates": 25, "num_scenarios": 8},
        )

        assert result.ready is True
        assert RunWarningCode.LARGE_CANDIDATE_COUNT in result.warnings
        assert result.normalized_config["num_candidates"] == 25


