"""
Evaluator Service.

Service layer for Evaluator operations, orchestrating the agent
and database operations with evaluation tracking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from crucible.agents.evaluator_agent import EvaluatorAgent
from crucible.db.repositories import (
    get_problem_spec,
    get_world_model,
    get_candidate,
    list_candidates,
    get_scenario_suite,
    create_evaluation,
    list_evaluations,
    get_run,
)

logger = logging.getLogger(__name__)


class EvaluatorService:
    """Service for Evaluator operations."""

    def __init__(self, session: Session):
        """
        Initialize Evaluator service.

        Args:
            session: Database session
        """
        self.session = session
        self.agent = EvaluatorAgent()

    def evaluate_candidate_against_scenario(
        self,
        candidate_id: str,
        scenario: Dict[str, Any],
        run_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single candidate against a single scenario.

        Args:
            candidate_id: Candidate ID
            scenario: Scenario dict from scenario suite
            run_id: Run ID
            project_id: Project ID

        Returns:
            dict with:
                - evaluation: Created evaluation dict
                - P: Prediction quality score
                - R: Resource cost score
                - constraint_satisfaction: Constraint satisfaction scores
                - explanation: Evaluation explanation
        """
        # Get candidate
        candidate = get_candidate(self.session, candidate_id)
        if candidate is None:
            raise ValueError(f"Candidate not found: {candidate_id}")

        # Get ProblemSpec and WorldModel for context
        problem_spec = get_problem_spec(self.session, project_id)
        world_model = get_world_model(self.session, project_id)

        # Build candidate dict for agent
        candidate_dict = {
            "id": candidate.id,
            "mechanism_description": candidate.mechanism_description,
            "predicted_effects": candidate.predicted_effects or {},
            "scores": candidate.scores or {}
        }

        # Build ProblemSpec dict for agent
        problem_spec_dict = None
        if problem_spec:
            problem_spec_dict = {
                "constraints": problem_spec.constraints or [],
                "goals": problem_spec.goals or [],
                "resolution": (
                    problem_spec.resolution.value
                    if hasattr(problem_spec.resolution, "value")
                    else str(problem_spec.resolution)
                ),
                "mode": (
                    problem_spec.mode.value
                    if hasattr(problem_spec.mode, "value")
                    else str(problem_spec.mode)
                )
            }

        # Build WorldModel dict for agent
        world_model_dict = None
        if world_model:
            world_model_dict = world_model.model_data or {}

        # Call agent
        task = {
            "candidate": candidate_dict,
            "scenario": scenario,
            "problem_spec": problem_spec_dict,
            "world_model": world_model_dict
        }

        try:
            result = self.agent.execute(task)
            P = result.get("P", {"overall": 0.5})
            R = result.get("R", {"overall": 0.5})
            constraint_satisfaction = result.get("constraint_satisfaction", {})
            explanation = result.get("explanation", "")

            # Create evaluation in database
            evaluation = create_evaluation(
                self.session,
                candidate_id=candidate_id,
                run_id=run_id,
                scenario_id=scenario.get("id", "unknown"),
                P=P,
                R=R,
                constraint_satisfaction=constraint_satisfaction,
                explanation=explanation
            )

            return {
                "evaluation": {
                    "id": evaluation.id,
                    "candidate_id": evaluation.candidate_id,
                    "scenario_id": evaluation.scenario_id,
                    "P": evaluation.P,
                    "R": evaluation.R,
                    "constraint_satisfaction": evaluation.constraint_satisfaction,
                    "explanation": evaluation.explanation
                },
                "P": P,
                "R": R,
                "constraint_satisfaction": constraint_satisfaction,
                "explanation": explanation
            }

        except Exception as e:
            logger.error(f"Error evaluating candidate {candidate_id} against scenario {scenario.get('id')}: {e}", exc_info=True)
            raise

    def evaluate_all_candidates(
        self,
        run_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate all candidates in a run against all scenarios in the scenario suite.

        Args:
            run_id: Run ID
            project_id: Project ID

        Returns:
            dict with:
                - evaluations: List of evaluation dicts
                - count: Number of evaluations created
                - candidates_evaluated: Number of candidates evaluated
                - scenarios_used: Number of scenarios used
        """
        # Get run
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        # Get all candidates for this run
        candidates = list_candidates(self.session, run_id=run_id)
        if not candidates:
            raise ValueError(f"No candidates found for run {run_id}")

        # Get scenario suite
        scenario_suite = get_scenario_suite(self.session, run_id)
        if scenario_suite is None:
            raise ValueError(f"Scenario suite not found for run {run_id}")

        scenarios = scenario_suite.scenarios or []
        if not scenarios:
            raise ValueError(f"No scenarios found in scenario suite for run {run_id}")

        # Check for existing evaluations to avoid duplicates
        existing_evaluations = list_evaluations(self.session, run_id=run_id)
        existing_keys = {
            (e.candidate_id, e.scenario_id) for e in existing_evaluations
        }

        # Evaluate each candidate against each scenario
        evaluations_created = []
        for candidate in candidates:
            for scenario in scenarios:
                scenario_id = scenario.get("id", "unknown")
                
                # Skip if evaluation already exists
                if (candidate.id, scenario_id) in existing_keys:
                    logger.debug(f"Skipping existing evaluation: candidate={candidate.id}, scenario={scenario_id}")
                    continue

                try:
                    result = self.evaluate_candidate_against_scenario(
                        candidate_id=candidate.id,
                        scenario=scenario,
                        run_id=run_id,
                        project_id=project_id
                    )
                    evaluations_created.append(result["evaluation"])
                except Exception as e:
                    logger.error(f"Failed to evaluate candidate {candidate.id} against scenario {scenario_id}: {e}")
                    # Continue with other evaluations
                    continue

        return {
            "evaluations": evaluations_created,
            "count": len(evaluations_created),
            "candidates_evaluated": len(candidates),
            "scenarios_used": len(scenarios)
        }

