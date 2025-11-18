"""
Run Service.

Service layer for Run orchestration, coordinating the full pipeline:
ProblemSpec → WorldModel → Designers → ScenarioGenerator → Evaluators → I-Ranker
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
from crucible.services.evaluator_service import EvaluatorService
from crucible.services.ranker_service import RankerService

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
        self.evaluator_service = EvaluatorService(session)
        self.ranker_service = RankerService(session)

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

    def execute_evaluation_phase(
        self,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Execute the evaluation phase of a run (evaluate all candidates against all scenarios).

        Args:
            run_id: Run ID

        Returns:
            dict with:
                - evaluations: List of evaluation dicts
                - count: Number of evaluations created
                - candidates_evaluated: Number of candidates evaluated
                - scenarios_used: Number of scenarios used
        """
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        try:
            # Evaluate all candidates
            result = self.evaluator_service.evaluate_all_candidates(
                run_id=run_id,
                project_id=run.project_id
            )

            logger.info(
                f"Evaluation phase completed for run {run_id}: "
                f"{result['count']} evaluations created for {result['candidates_evaluated']} candidates"
            )

            return result

        except Exception as e:
            logger.error(f"Error in evaluation phase for run {run_id}: {e}", exc_info=True)
            raise

    def execute_ranking_phase(
        self,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Execute the ranking phase of a run (rank candidates based on evaluations).

        Args:
            run_id: Run ID

        Returns:
            dict with:
                - ranked_candidates: List of candidate dicts sorted by I score
                - count: Number of candidates ranked
                - hard_constraint_violations: List of candidate IDs with hard constraint violations
        """
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        try:
            # Rank candidates
            result = self.ranker_service.rank_candidates(
                run_id=run_id,
                project_id=run.project_id
            )

            logger.info(
                f"Ranking phase completed for run {run_id}: "
                f"{result['count']} candidates ranked, {len(result['hard_constraint_violations'])} hard violations"
            )

            return result

        except Exception as e:
            logger.error(f"Error in ranking phase for run {run_id}: {e}", exc_info=True)
            raise

    def execute_evaluate_and_rank_phase(
        self,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Execute both evaluation and ranking phases.

        This is the "evaluate + rank" phase mentioned in the story.

        Args:
            run_id: Run ID

        Returns:
            dict with:
                - evaluations: Evaluation phase results
                - rankings: Ranking phase results
                - status: Overall status
        """
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        try:
            # Phase 1: Evaluate all candidates
            evaluation_result = self.execute_evaluation_phase(run_id=run_id)

            # Phase 2: Rank candidates
            ranking_result = self.execute_ranking_phase(run_id=run_id)

            logger.info(
                f"Evaluate + rank phase completed for run {run_id}: "
                f"{evaluation_result['count']} evaluations, {ranking_result['count']} candidates ranked"
            )

            return {
                "evaluations": evaluation_result,
                "rankings": ranking_result,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Error in evaluate + rank phase for run {run_id}: {e}", exc_info=True)
            update_run_status(self.session, run_id, RunStatus.FAILED.value)
            raise

    def execute_full_pipeline(
        self,
        run_id: str,
        num_candidates: int = 5,
        num_scenarios: int = 8
    ) -> Dict[str, Any]:
        """
        Execute the full pipeline: Design → Scenarios → Evaluation → Ranking.

        Args:
            run_id: Run ID
            num_candidates: Number of candidates to generate
            num_scenarios: Number of scenarios to generate

        Returns:
            dict with:
                - candidates: Design phase results
                - scenarios: Scenario phase results
                - evaluations: Evaluation phase results
                - rankings: Ranking phase results
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
            # Phase 1: Design + Scenarios
            design_scenario_result = self.execute_design_and_scenario_phase(
                run_id=run_id,
                num_candidates=num_candidates,
                num_scenarios=num_scenarios
            )

            # Phase 2: Evaluate + Rank
            evaluate_rank_result = self.execute_evaluate_and_rank_phase(run_id=run_id)

            # Mark run as completed
            update_run_status(
                self.session,
                run_id,
                RunStatus.COMPLETED.value,
                completed_at=datetime.utcnow()
            )

            logger.info(f"Full pipeline completed for run {run_id}")

            return {
                "candidates": design_scenario_result["candidates"],
                "scenarios": design_scenario_result["scenarios"],
                "evaluations": evaluate_rank_result["evaluations"],
                "rankings": evaluate_rank_result["rankings"],
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Error in full pipeline for run {run_id}: {e}", exc_info=True)
            update_run_status(self.session, run_id, RunStatus.FAILED.value)
            raise

