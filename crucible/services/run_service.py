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
from crucible.utils.llm_usage import aggregate_usage

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
            result["duration_seconds"] = duration
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
            result["duration_seconds"] = duration
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
            result["duration_seconds"] = duration
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
            result["duration_seconds"] = duration
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

        phase_timings: Dict[str, Dict[str, Any]] = {}
        resource_breakdown: Dict[str, Dict[str, Any]] = {}
        phase_usage: Dict[str, Dict[str, Any]] = {}
        notes: List[str] = [
            "Counts derive from phase service outputs.",
            "LLM usage only appears when providers emit token telemetry.",
        ]
        candidate_count: Optional[int] = None
        scenario_count: Optional[int] = None
        evaluation_count: Optional[int] = None
        design_scenario_result: Optional[Dict[str, Any]] = None
        evaluate_rank_result: Optional[Dict[str, Any]] = None

        def _record_phase(
            phase_name: str,
            started_at: datetime,
            duration_seconds: float,
            usage_summary: Optional[Dict[str, Any]],
            resources: Dict[str, Any],
        ) -> None:
            completed_at = datetime.utcnow()
            phase_timings[phase_name] = {
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "duration_seconds": duration_seconds,
            }
            resource_breakdown[phase_name] = resources
            if usage_summary:
                phase_usage[phase_name] = usage_summary

        try:
            # Design phase
            logger.info(f"[Phase] Design starting for run {run_id}")
            design_start_dt = datetime.utcnow()
            design_result = self.execute_design_phase(
                run_id=run_id,
                num_candidates=num_candidates,
            )
            candidate_count = design_result.get("count", candidate_count or 0)
            design_duration = design_result.get("duration_seconds") or 0.0
            design_usage = design_result.get("usage_summary")
            _record_phase(
                "design",
                design_start_dt,
                design_duration,
                design_usage,
                {
                    "requested_candidates": num_candidates,
                    "candidates_generated": design_result.get("count", 0),
                    "llm_calls": (design_usage or {}).get("call_count", 0),
                },
            )

            # Scenario phase
            logger.info(f"[Phase] Scenario generation starting for run {run_id}")
            scenario_start_dt = datetime.utcnow()
            scenario_result = self.execute_scenario_phase(
                run_id=run_id,
                num_scenarios=num_scenarios,
            )
            scenario_count = scenario_result.get("count", scenario_count or 0)
            scenario_duration = scenario_result.get("duration_seconds") or 0.0
            scenario_usage = scenario_result.get("usage_summary")
            _record_phase(
                "scenarios",
                scenario_start_dt,
                scenario_duration,
                scenario_usage,
                {
                    "requested_scenarios": num_scenarios,
                    "scenarios_generated": scenario_result.get("count", 0),
                    "llm_calls": (scenario_usage or {}).get("call_count", 0),
                },
            )

            design_scenario_result = {
                "candidates": design_result,
                "scenarios": scenario_result,
                "status": "completed",
            }

            # Evaluation phase
            logger.info(f"[Phase] Evaluation starting for run {run_id}")
            evaluation_start_dt = datetime.utcnow()
            evaluation_result = self.execute_evaluation_phase(run_id=run_id)
            evaluation_count = evaluation_result.get("count", evaluation_count or 0)
            evaluation_duration = evaluation_result.get("duration_seconds") or 0.0
            eval_usage = evaluation_result.get("usage_summary")
            _record_phase(
                "evaluation",
                evaluation_start_dt,
                evaluation_duration,
                eval_usage,
                {
                    "evaluations_created": evaluation_result.get("count", 0),
                    "candidates_evaluated": evaluation_result.get("candidates_evaluated"),
                    "scenarios_used": evaluation_result.get("scenarios_used"),
                    "attempted_pairs": evaluation_result.get("attempted_pairs"),
                    "skipped_existing": evaluation_result.get("skipped_existing"),
                    "llm_calls": evaluation_result.get("llm_call_count", 0),
                },
            )

            # Ranking phase
            logger.info(f"[Phase] Ranking starting for run {run_id}")
            ranking_start_dt = datetime.utcnow()
            ranking_result = self.execute_ranking_phase(run_id=run_id)
            ranking_duration = ranking_result.get("duration_seconds") or 0.0
            _record_phase(
                "ranking",
                ranking_start_dt,
                ranking_duration,
                None,
                {
                    "candidates_ranked": ranking_result.get("count", 0),
                    "hard_constraint_violations": len(ranking_result.get("hard_constraint_violations", [])),
                },
            )

            evaluate_rank_result = {
                "evaluations": evaluation_result,
                "rankings": ranking_result,
                "status": "completed",
            }

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
                f"Full pipeline completed for run {run_id} in {total_duration:.2f}s"
            )

            timing_payload = {
                "total": total_duration,
                "phase1": (design_duration + scenario_duration),
                "phase2": (evaluation_duration + ranking_duration),
                "design": design_duration,
                "scenarios": scenario_duration,
                "evaluation": evaluation_duration,
                "ranking": ranking_duration,
            }

            metrics_payload: Dict[str, Any] = {
                "phase_timings": phase_timings,
                "resource_breakdown": resource_breakdown,
            }
            if notes:
                metrics_payload["notes"] = notes

            llm_usage_payload = None
            if phase_usage:
                total_usage = aggregate_usage(list(phase_usage.values()))
                llm_usage_payload = {"phases": phase_usage}
                if total_usage:
                    llm_usage_payload["total"] = total_usage

            self._persist_run_observability(
                run_id=run_id,
                candidate_count=candidate_count,
                scenario_count=scenario_count,
                evaluation_count=evaluation_count,
                duration_seconds=total_duration,
                metrics_payload=metrics_payload,
                llm_usage_payload=llm_usage_payload,
                error_summary=None,
            )

            return {
                "candidates": design_scenario_result["candidates"],
                "scenarios": design_scenario_result["scenarios"],
                "evaluations": evaluate_rank_result["evaluations"],
                "rankings": evaluate_rank_result["rankings"],
                "status": "completed",
                "timing": timing_payload,
            }

        except Exception as e:
            logger.error(
                f"Error in full pipeline for run {run_id} (project {run.project_id}): {e}",
                exc_info=True
            )
            current_run = get_run(self.session, run_id)
            if current_run and current_run.status != RunStatus.COMPLETED.value:
                update_run_status(self.session, run_id, RunStatus.FAILED.value)

            metrics_payload = {
                "phase_timings": phase_timings,
                "resource_breakdown": resource_breakdown,
            }
            if notes:
                metrics_payload["notes"] = notes

            llm_usage_payload = None
            if phase_usage:
                total_usage = aggregate_usage(list(phase_usage.values()))
                llm_usage_payload = {"phases": phase_usage}
                if total_usage:
                    llm_usage_payload["total"] = total_usage

            self._persist_run_observability(
                run_id=run_id,
                candidate_count=candidate_count,
                scenario_count=scenario_count,
                evaluation_count=evaluation_count,
                duration_seconds=time.time() - start_time,
                metrics_payload=metrics_payload,
                llm_usage_payload=llm_usage_payload,
                error_summary=str(e),
            )
            raise

    def _persist_run_observability(
        self,
        run_id: str,
        candidate_count: Optional[int],
        scenario_count: Optional[int],
        evaluation_count: Optional[int],
        duration_seconds: Optional[float],
        metrics_payload: Optional[Dict[str, Any]],
        llm_usage_payload: Optional[Dict[str, Any]],
        error_summary: Optional[str],
    ) -> None:
        """Persist aggregated observability fields onto the Run row."""
        run = get_run(self.session, run_id)
        if run is None:
            return

        if duration_seconds is not None:
            run.duration_seconds = duration_seconds
        if candidate_count is not None:
            run.candidate_count = candidate_count
        if scenario_count is not None:
            run.scenario_count = scenario_count
        if evaluation_count is not None:
            run.evaluation_count = evaluation_count
        run.metrics = metrics_payload
        run.llm_usage = llm_usage_payload
        run.error_summary = (error_summary[:512] if error_summary else None)

        self.session.commit()

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

