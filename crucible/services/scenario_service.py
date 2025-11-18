"""
Scenario Service.

Service layer for ScenarioGenerator operations, orchestrating the agent
and database operations.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from crucible.agents.scenario_generator_agent import ScenarioGeneratorAgent
from crucible.db.repositories import (
    get_problem_spec,
    get_world_model,
    create_scenario_suite,
    get_scenario_suite,
    list_candidates,
    get_run,
)

logger = logging.getLogger(__name__)


class ScenarioService:
    """Service for ScenarioGenerator operations."""

    def __init__(self, session: Session):
        """
        Initialize Scenario service.

        Args:
            session: Database session
        """
        self.session = session
        self.agent = ScenarioGeneratorAgent()

    def generate_scenario_suite(
        self,
        run_id: str,
        project_id: str,
        num_scenarios: int = 8
    ) -> Dict[str, Any]:
        """
        Generate scenario suite for a run.

        Args:
            run_id: Run ID
            project_id: Project ID
            num_scenarios: Number of scenarios to generate

        Returns:
            dict with:
                - scenario_suite: ScenarioSuite dict
                - scenarios: List of scenario dicts
                - reasoning: Agent reasoning
        """
        # Get ProblemSpec
        problem_spec = get_problem_spec(self.session, project_id)

        # Get WorldModel
        world_model = get_world_model(self.session, project_id)

        # Get candidates for this run (for scenario targeting)
        candidates = list_candidates(self.session, run_id=run_id)
        candidate_dicts = [
            {
                "id": c.id,
                "mechanism_description": c.mechanism_description,
                "predicted_effects": c.predicted_effects
            }
            for c in candidates
        ]

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
            "problem_spec": problem_spec_dict,
            "world_model": world_model_dict,
            "candidates": candidate_dicts,
            "num_scenarios": num_scenarios
        }

        try:
            result = self.agent.execute(task)
            scenarios = result.get("scenarios", [])
            reasoning = result.get("reasoning", "")

            # Check if scenario suite already exists
            existing_suite = get_scenario_suite(self.session, run_id)
            
            if existing_suite:
                # Update existing suite
                existing_suite.scenarios = scenarios
                self.session.commit()
                self.session.refresh(existing_suite)
                scenario_suite = existing_suite
            else:
                # Create new scenario suite
                scenario_suite = create_scenario_suite(
                    self.session,
                    run_id=run_id,
                    scenarios=scenarios
                )

            return {
                "scenario_suite": {
                    "id": scenario_suite.id,
                    "run_id": scenario_suite.run_id,
                    "scenarios": scenario_suite.scenarios,
                    "created_at": scenario_suite.created_at.isoformat() if scenario_suite.created_at else None
                },
                "scenarios": scenarios,
                "reasoning": reasoning,
                "count": len(scenarios)
            }

        except Exception as e:
            logger.error(f"Error generating scenario suite: {e}", exc_info=True)
            raise

