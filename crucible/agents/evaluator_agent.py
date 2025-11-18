"""
Evaluator Agent.

An agent that evaluates candidates against scenarios.
Consumes a candidate and a scenario, then produces structured scores for:
- P (prediction quality)
- R (resource/complexity cost)
- Constraint satisfaction
"""

import json
import logging
from typing import Dict, Any, Optional

from kosmos.agents.base import BaseAgent
from kosmos.core.llm import get_provider

logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAgent):
    """
    Agent that evaluates candidates against scenarios.

    This agent:
    - Reads a candidate mechanism description and predicted effects
    - Reads a scenario description with initial state, events, and expected outcomes
    - Uses LLM to evaluate how well the candidate performs in the scenario
    - Produces structured scores for P (prediction quality), R (resource cost), and constraint satisfaction
    - Provides brief explanations for each score
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize Evaluator agent."""
        super().__init__(agent_id, agent_type or "EvaluatorAgent", config)
        self.llm_provider = get_provider()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute evaluation task.

        Args:
            task: Task dict with:
                - candidate: Candidate dict (mechanism_description, predicted_effects, etc.)
                - scenario: Scenario dict (id, name, description, type, focus, initial_state, events, expected_outcomes, weight)
                - problem_spec: Optional ProblemSpec dict (for constraint context)
                - world_model: Optional WorldModel dict (for context)

        Returns:
            dict with:
                - P: Dict with overall score (0.0-1.0) and optional components
                - R: Dict with overall score (0.0-1.0) and optional components
                - constraint_satisfaction: Dict mapping constraint IDs to satisfaction scores
                - explanation: Brief explanation of the evaluation
        """
        try:
            candidate = task.get("candidate")
            scenario = task.get("scenario")
            problem_spec = task.get("problem_spec")
            world_model = task.get("world_model")

            if not candidate or not scenario:
                raise ValueError("Both candidate and scenario are required for evaluation")

            # Build context prompt
            prompt = self._build_evaluation_prompt(
                candidate,
                scenario,
                problem_spec,
                world_model
            )

            # Call LLM for structured response
            response = self.llm_provider.generate(
                prompt,
                system="You are an Evaluator agent for Int Crucible. Always respond with valid JSON only.",
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=2048
            )

            # Parse LLM response (may need to extract JSON from markdown code blocks)
            content = response.content.strip()
            
            # Try to extract JSON from markdown code blocks if present
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end > start:
                    content = content[start:end].strip()
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response content: {content[:500]}")
                # Return a safe default
                result = {
                    "P": {"overall": 0.5},
                    "R": {"overall": 0.5},
                    "constraint_satisfaction": {},
                    "explanation": "Failed to parse agent response. Please try again."
                }

            # Ensure required fields exist
            if "P" not in result:
                result["P"] = {"overall": 0.5}
            if "R" not in result:
                result["R"] = {"overall": 0.5}
            if "constraint_satisfaction" not in result:
                result["constraint_satisfaction"] = {}
            if "explanation" not in result:
                result["explanation"] = "No explanation provided."

            return result

        except Exception as e:
            logger.error(f"Error in Evaluator agent execution: {e}", exc_info=True)
            raise

    def _build_evaluation_prompt(
        self,
        candidate: Dict[str, Any],
        scenario: Dict[str, Any],
        problem_spec: Optional[Dict[str, Any]],
        world_model: Optional[Dict[str, Any]]
    ) -> str:
        """Build the prompt for candidate evaluation."""
        
        prompt_parts = [
            "You are an Evaluator agent for Int Crucible.",
            "Your role is to evaluate how well a candidate solution performs in a given scenario.",
            "",
            "IMPORTANT:",
            "- Provide consistent, structured scores for P (prediction quality) and R (resource cost).",
            "- P should reflect how well the candidate's predictions match the scenario's expected outcomes.",
            "- R should reflect the resource/complexity cost of implementing or running this candidate.",
            "- Constraint satisfaction should be evaluated against all relevant constraints.",
            "- Scores should be in the range 0.0-1.0, where 1.0 is best.",
            "",
        ]

        if problem_spec:
            prompt_parts.extend([
                "ProblemSpec (for constraint context):",
                json.dumps(problem_spec, indent=2),
                "",
            ])

        if world_model:
            prompt_parts.extend([
                "WorldModel (for context):",
                json.dumps(world_model, indent=2),
                "",
            ])

        prompt_parts.extend([
            "Candidate to evaluate:",
            json.dumps(candidate, indent=2),
            "",
            "Scenario to evaluate against:",
            json.dumps(scenario, indent=2),
            "",
            "Evaluate this candidate in this scenario and provide:",
            "",
            "1. P (Prediction Quality):",
            "   - overall: 0.0-1.0 score for how well the candidate's predicted effects match the scenario's expected outcomes",
            "   - components (optional): breakdown of prediction accuracy, scenario coverage, etc.",
            "",
            "2. R (Resource Cost):",
            "   - overall: 0.0-1.0 score for resource/complexity cost (lower is better, so 0.0 = high cost, 1.0 = low cost)",
            "   - components (optional): breakdown of cost, complexity, resource_usage, etc.",
            "",
            "3. constraint_satisfaction:",
            "   - For each constraint in the ProblemSpec, provide:",
            "     - satisfied: boolean indicating if constraint is met",
            "     - score: 0.0-1.0 score for constraint satisfaction",
            "     - explanation: brief explanation",
            "",
            "4. explanation: Brief text explanation of the evaluation",
            "",
            "Respond with a JSON object:",
            "{",
            '  "P": {',
            '    "overall": 0.0-1.0,',
            '    "components": {',
            '      "prediction_accuracy": 0.0-1.0,',
            '      "scenario_coverage": 0.0-1.0',
            '    }',
            '  },',
            '  "R": {',
            '    "overall": 0.0-1.0,',
            '    "components": {',
            '      "cost": 0.0-1.0,',
            '      "complexity": 0.0-1.0,',
            '      "resource_usage": 0.0-1.0',
            '    }',
            '  },',
            '  "constraint_satisfaction": {',
            '    "constraint_id": {',
            '      "satisfied": true|false,',
            '      "score": 0.0-1.0,',
            '      "explanation": "why this constraint is satisfied or not"',
            '    }',
            '  },',
            '  "explanation": "brief explanation of the evaluation"',
            "}",
        ])

        return "\n".join(prompt_parts)

