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
        import time
        start_time = time.time()
        
        logger.info(f"[Design Phase] Starting for run {run_id}, generating {num_candidates} candidates")
        
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

            duration = time.time() - start_time
            logger.info(
                f"[Design Phase] Completed for run {run_id} in {duration:.2f}s: "
                f"{result['count']} candidates generated"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[Design Phase] Failed for run {run_id} after {duration:.2f}s: {e}",
                exc_info=True
            )
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
        import time
        start_time = time.time()
        
        logger.info(f"[Scenario Phase] Starting for run {run_id}, generating {num_scenarios} scenarios")
        
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

            duration = time.time() - start_time
            logger.info(
                f"[Scenario Phase] Completed for run {run_id} in {duration:.2f}s: "
                f"{result['count']} scenarios generated"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[Scenario Phase] Failed for run {run_id} after {duration:.2f}s: {e}",
                exc_info=True
            )
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
        import time
        start_time = time.time()
        
        logger.info(f"[Evaluation Phase] Starting for run {run_id}")
        
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        try:
            # Evaluate all candidates
            result = self.evaluator_service.evaluate_all_candidates(
                run_id=run_id,
                project_id=run.project_id
            )

            duration = time.time() - start_time
            logger.info(
                f"[Evaluation Phase] Completed for run {run_id} in {duration:.2f}s: "
                f"{result['count']} evaluations created for {result['candidates_evaluated']} candidates "
                f"across {result['scenarios_used']} scenarios"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[Evaluation Phase] Failed for run {run_id} after {duration:.2f}s: {e}",
                exc_info=True
            )
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
        import time
        start_time = time.time()
        
        logger.info(f"[Ranking Phase] Starting for run {run_id}")
        
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        try:
            # Rank candidates
            result = self.ranker_service.rank_candidates(
                run_id=run_id,
                project_id=run.project_id
            )

            duration = time.time() - start_time
            logger.info(
                f"[Ranking Phase] Completed for run {run_id} in {duration:.2f}s: "
                f"{result['count']} candidates ranked, {len(result['hard_constraint_violations'])} hard violations"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[Ranking Phase] Failed for run {run_id} after {duration:.2f}s: {e}",
                exc_info=True
            )
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
        import time
        start_time = time.time()
        
        logger.info(f"Starting full pipeline execution for run {run_id}")
        
        run = get_run(self.session, run_id)
        if run is None:
            logger.error(f"Run not found: {run_id}")
            raise ValueError(f"Run not found: {run_id}")

        logger.info(f"Run found: {run_id}, project_id: {run.project_id}, status: {run.status}")

        # Verify ProblemSpec and WorldModel exist with detailed logging
        logger.info(f"Checking prerequisites for project {run.project_id}")
        
        # Refresh session to ensure we see committed data
        self.session.expire_all()
        
        problem_spec = get_problem_spec(self.session, run.project_id)
        if problem_spec is None:
            # Try to list available projects to help debug
            from crucible.db.repositories import list_projects
            projects = list_projects(self.session)
            project_ids = [p.id for p in projects]
            logger.error(
                f"ProblemSpec not found for project {run.project_id}. "
                f"Available projects: {project_ids}"
            )
            raise ValueError(
                f"ProblemSpec not found for project {run.project_id}. "
                f"Available projects: {project_ids}"
            )
        logger.info(f"ProblemSpec found for project {run.project_id}: {problem_spec.id}")

        world_model = get_world_model(self.session, run.project_id)
        if world_model is None:
            logger.error(f"WorldModel not found for project {run.project_id}")
            raise ValueError(f"WorldModel not found for project {run.project_id}")
        logger.info(f"WorldModel found for project {run.project_id}: {world_model.id}")

        try:
            # Phase 1: Design + Scenarios
            logger.info(f"[Phase 1/2] Starting design + scenario phase for run {run_id}")
            phase1_start = time.time()
            
            design_scenario_result = self.execute_design_and_scenario_phase(
                run_id=run_id,
                num_candidates=num_candidates,
                num_scenarios=num_scenarios
            )
            
            phase1_duration = time.time() - phase1_start
            logger.info(
                f"[Phase 1/2] Design + scenario phase completed in {phase1_duration:.2f}s: "
                f"{design_scenario_result['candidates']['count']} candidates, "
                f"{design_scenario_result['scenarios']['count']} scenarios"
            )

            # Phase 2: Evaluate + Rank
            logger.info(f"[Phase 2/2] Starting evaluate + rank phase for run {run_id}")
            phase2_start = time.time()
            
            evaluate_rank_result = self.execute_evaluate_and_rank_phase(run_id=run_id)
            
            phase2_duration = time.time() - phase2_start
            logger.info(
                f"[Phase 2/2] Evaluate + rank phase completed in {phase2_duration:.2f}s: "
                f"{evaluate_rank_result['evaluations']['count']} evaluations, "
                f"{evaluate_rank_result['rankings']['count']} candidates ranked"
            )

            # Mark run as completed
            update_run_status(
                self.session,
                run_id,
                RunStatus.COMPLETED.value,
                completed_at=datetime.utcnow()
            )

            total_duration = time.time() - start_time
            logger.info(
                f"Full pipeline completed for run {run_id} in {total_duration:.2f}s "
                f"(phase1: {phase1_duration:.2f}s, phase2: {phase2_duration:.2f}s)"
            )

            return {
                "candidates": design_scenario_result["candidates"],
                "scenarios": design_scenario_result["scenarios"],
                "evaluations": evaluate_rank_result["evaluations"],
                "rankings": evaluate_rank_result["rankings"],
                "status": "completed",
                "timing": {
                    "total": total_duration,
                    "phase1": phase1_duration,
                    "phase2": phase2_duration
                }
            }

        except Exception as e:
            logger.error(
                f"Error in full pipeline for run {run_id} (project {run.project_id}): {e}",
                exc_info=True
            )
            # Only set failed if we haven't already set a status
            current_run = get_run(self.session, run_id)
            if current_run and current_run.status != RunStatus.COMPLETED.value:
                update_run_status(self.session, run_id, RunStatus.FAILED.value)
            raise

