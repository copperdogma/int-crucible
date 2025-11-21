"""
Run Service.

Service layer for Run orchestration, coordinating the full pipeline:
ProblemSpec → WorldModel → Designers → ScenarioGenerator → Evaluators → I-Ranker
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from crucible.db.repositories import (
    create_run,
    get_run,
    update_run_status,
    get_problem_spec,
    get_world_model,
    list_chat_sessions,
    create_message,
)
from crucible.db.models import RunStatus, RunMode, MessageRole
from crucible.models.run_contracts import RunSummary, RunSummaryCandidate
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
            update_run_status(
                self.session,
                run_id,
                RunStatus.FAILED.value
            )
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
            update_run_status(
                self.session,
                run_id,
                RunStatus.FAILED.value
            )
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

            refreshed_run = get_run(self.session, run_id)
            if refreshed_run:
                self._post_run_summary_message(
                    run=refreshed_run,
                    design_result=design_scenario_result,
                    evaluate_rank_result=evaluate_rank_result,
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

    def _post_run_summary_message(
        self,
        run,
        design_result: Dict[str, Any],
        evaluate_rank_result: Dict[str, Any],
    ) -> None:
        """Create a post-run summary chat message for the project."""
        try:
            chat_sessions = list_chat_sessions(self.session, project_id=run.project_id)
            if not chat_sessions:
                logger.info(
                    f"No chat sessions found for project {run.project_id}; skipping run summary message."
                )
                return

            summary = self._build_run_summary(run, design_result, evaluate_rank_result)
            metadata = {
                "agent_name": "Architect",
                "run_summary": summary.to_dict(),
            }
            content = self._format_run_summary_text(summary)

            message = create_message(
                self.session,
                chat_session_id=chat_sessions[0].id,
                role=MessageRole.AGENT.value,
                content=content,
                message_metadata=metadata,
            )

            run.run_summary_message_id = message.id
            self.session.commit()
        except Exception as exc:
            logger.warning(f"Failed to post run summary for run {run.id}: {exc}", exc_info=True)

    def _build_run_summary(
        self,
        run,
        design_result: Dict[str, Any],
        evaluate_rank_result: Dict[str, Any],
    ) -> RunSummary:
        """Assemble the structured run summary payload."""
        design_counts = design_result.get("candidates", {}).get("count", 0)
        scenario_counts = design_result.get("scenarios", {}).get("count", 0)
        evaluation_counts = evaluate_rank_result.get("evaluations", {}).get("count", 0)

        rankings = evaluate_rank_result.get("rankings", {})
        ranked_candidates = rankings.get("ranked_candidates", []) or []
        top_candidates: List[RunSummaryCandidate] = []
        for candidate in ranked_candidates[:3]:
            top_candidates.append(
                RunSummaryCandidate(
                    candidate_id=candidate.get("id"),
                    label=candidate.get("label")
                    or candidate.get("name")
                    or candidate.get("mechanism_description"),
                    I=candidate.get("I"),
                    P=candidate.get("P"),
                    R=candidate.get("R"),
                    notes=candidate.get("notes"),
                )
            )

        duration_seconds = None
        if run.started_at and run.completed_at:
            duration_seconds = (run.completed_at - run.started_at).total_seconds()

        return RunSummary(
            run_id=run.id,
            project_id=run.project_id,
            mode=run.mode.value if hasattr(run.mode, "value") else str(run.mode),
            status=run.status.value if hasattr(run.status, "value") else str(run.status),
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_seconds=duration_seconds,
            counts={
                "candidates": design_counts,
                "scenarios": scenario_counts,
                "evaluations": evaluation_counts,
            },
            top_candidates=top_candidates,
            links={"results_view": f"/runs/{run.id}"},
            summary_label=f"Run {run.id} summary",
        )

    def _format_run_summary_text(self, summary: RunSummary) -> str:
        """Render a concise textual summary for chat."""
        lines = [
            f"Run {summary.run_id} ({summary.mode}) completed.",
            "Counts: "
            f"{summary.counts.get('candidates', 0)} candidates, "
            f"{summary.counts.get('scenarios', 0)} scenarios, "
            f"{summary.counts.get('evaluations', 0)} evaluations.",
        ]
        if summary.top_candidates:
            lines.append("Top candidates:")
            for idx, candidate in enumerate(summary.top_candidates):
                label = candidate.label or candidate.candidate_id
                score = f"I={candidate.I:.2f}" if isinstance(candidate.I, (int, float)) else ""
                lines.append(f"{idx + 1}. {label} {score}".strip())
        lines.append("Open the Run panel to inspect full results and provenance.")
        return "\n".join(lines)

