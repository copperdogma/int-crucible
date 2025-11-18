"""
Run Service.

Service layer for Run orchestration, coordinating the full pipeline:
ProblemSpec → WorldModel → Designers → ScenarioGenerator → (future: Evaluators → I-Ranker)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from crucible.db.repositories import (
    create_run,
    get_run,
    update_run_status,
    get_problem_spec,
    get_world_model,
)
from crucible.db.models import RunStatus, RunMode
from crucible.services.designer_service import DesignerService
from crucible.services.scenario_service import ScenarioService

logger = logging.getLogger(__name__)


class RunService:
    """Service for Run orchestration."""

    def __init__(self, session: Session):
        """
        Initialize Run service.

        Args:
            session: Database session
        """
        self.session = session
        self.designer_service = DesignerService(session)
        self.scenario_service = ScenarioService(session)

    def execute_design_phase(
        self,
        run_id: str,
        num_candidates: int = 5
    ) -> Dict[str, Any]:
        """
        Execute the design phase of a run (generate candidates).

        Args:
            run_id: Run ID
            num_candidates: Number of candidates to generate

        Returns:
            dict with:
                - candidates: List of created candidate dicts
                - reasoning: Designer reasoning
                - count: Number of candidates created
        """
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        # Update run status to running
        update_run_status(
            self.session,
            run_id,
            RunStatus.RUNNING.value,
            started_at=datetime.utcnow() if run.started_at is None else None
        )

        try:
            # Generate candidates
            result = self.designer_service.generate_candidates(
                run_id=run_id,
                project_id=run.project_id,
                num_candidates=num_candidates
            )

            logger.info(f"Design phase completed for run {run_id}: {result['count']} candidates generated")

            return result

        except Exception as e:
            logger.error(f"Error in design phase for run {run_id}: {e}", exc_info=True)
            update_run_status(self.session, run_id, RunStatus.FAILED.value)
            raise

    def execute_scenario_phase(
        self,
        run_id: str,
        num_scenarios: int = 8
    ) -> Dict[str, Any]:
        """
        Execute the scenario generation phase of a run.

        Args:
            run_id: Run ID
            num_scenarios: Number of scenarios to generate

        Returns:
            dict with:
                - scenario_suite: ScenarioSuite dict
                - scenarios: List of scenario dicts
                - reasoning: ScenarioGenerator reasoning
                - count: Number of scenarios created
        """
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        try:
            # Generate scenario suite
            result = self.scenario_service.generate_scenario_suite(
                run_id=run_id,
                project_id=run.project_id,
                num_scenarios=num_scenarios
            )

            logger.info(f"Scenario phase completed for run {run_id}: {result['count']} scenarios generated")

            return result

        except Exception as e:
            logger.error(f"Error in scenario phase for run {run_id}: {e}", exc_info=True)
            raise

    def execute_design_and_scenario_phase(
        self,
        run_id: str,
        num_candidates: int = 5,
        num_scenarios: int = 8
    ) -> Dict[str, Any]:
        """
        Execute both design and scenario generation phases.

        This is the "design + scenario generation" phase mentioned in the story.

        Args:
            run_id: Run ID
            num_candidates: Number of candidates to generate
            num_scenarios: Number of scenarios to generate

        Returns:
            dict with:
                - candidates: Design phase results
                - scenarios: Scenario phase results
                - status: Overall status
        """
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        # Verify ProblemSpec and WorldModel exist
        problem_spec = get_problem_spec(self.session, run.project_id)
        if problem_spec is None:
            raise ValueError(f"ProblemSpec not found for project {run.project_id}")

        world_model = get_world_model(self.session, run.project_id)
        if world_model is None:
            raise ValueError(f"WorldModel not found for project {run.project_id}")

        try:
            # Phase 1: Generate candidates
            design_result = self.execute_design_phase(
                run_id=run_id,
                num_candidates=num_candidates
            )

            # Phase 2: Generate scenarios (can use candidates for targeting)
            scenario_result = self.execute_scenario_phase(
                run_id=run_id,
                num_scenarios=num_scenarios
            )

            logger.info(
                f"Design + scenario phase completed for run {run_id}: "
                f"{design_result['count']} candidates, {scenario_result['count']} scenarios"
            )

            return {
                "candidates": design_result,
                "scenarios": scenario_result,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Error in design + scenario phase for run {run_id}: {e}", exc_info=True)
            update_run_status(self.session, run_id, RunStatus.FAILED.value)
            raise

