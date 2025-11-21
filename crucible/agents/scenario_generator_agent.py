"""
ScenarioGenerator Agent.

An agent that generates scenario suites from a WorldModel and candidate set.
Consumes ProblemSpec, WorldModel, and candidates, then produces scenarios
that stress high-weight constraints and fragile assumptions.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from kosmos.agents.base import BaseAgent
from kosmos.core.llm import get_provider

from crucible.utils.llm_usage import usage_stats_to_dict

logger = logging.getLogger(__name__)


class ScenarioGeneratorAgent(BaseAgent):
    """
    Agent that generates scenario suites from a WorldModel and candidate set.

    This agent:
    - Reads ProblemSpec, WorldModel, and candidate set
    - Uses LLM to generate scenarios that stress critical constraints and assumptions
    - Produces structured scenarios in a format evaluators can consume
    - Focuses on high-weight constraints and fragile assumptions
    - Generates minimal but effective scenario suites for MVP
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize ScenarioGenerator agent."""
        super().__init__(agent_id, agent_type or "ScenarioGeneratorAgent", config)
        self.llm_provider = get_provider()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scenario generation task.

        Args:
            task: Task dict with:
                - problem_spec: ProblemSpec dict (constraints, goals, resolution, mode)
                - world_model: WorldModel dict (actors, mechanisms, resources, constraints, assumptions)
                - candidates: Optional list of candidate dicts (for scenario targeting)
                - num_scenarios: Optional number of scenarios to generate (default: 5-10)

        Returns:
            dict with:
                - scenarios: List of scenario dicts, each with:
                    - id: Unique scenario ID
                    - name: Human-readable name
                    - description: Detailed description
                    - type: stress_test|edge_case|normal_operation|failure_mode
                    - focus: Dict with constraints, assumptions, actors, resources to stress
                    - initial_state: Dict describing initial state
                    - events: List of event steps
                    - expected_outcomes: Dict with success_criteria and failure_modes
                    - weight: Importance weight (0.0-1.0)
                - reasoning: Explanation of scenario selection strategy
        """
        try:
            problem_spec = task.get("problem_spec")
            world_model = task.get("world_model")
            candidates = task.get("candidates", [])
            num_scenarios = task.get("num_scenarios", 8)

            # Build context prompt
            prompt = self._build_scenario_prompt(
                problem_spec,
                world_model,
                candidates,
                num_scenarios
            )

            # Call LLM for structured response
            response = self.llm_provider.generate(
                prompt,
                system="You are a ScenarioGenerator agent for Int Crucible. Always respond with valid JSON only.",
                temperature=0.5,  # Moderate temperature for balanced creativity and consistency
                max_tokens=4096
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
                    "scenarios": [],
                    "reasoning": "Failed to parse agent response. Please try again."
                }

            usage = usage_stats_to_dict(response)

            return {
                "scenarios": result.get("scenarios", []),
                "reasoning": result.get("reasoning", ""),
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Error in ScenarioGenerator agent execution: {e}", exc_info=True)
            raise

    def _build_scenario_prompt(
        self,
        problem_spec: Optional[Dict[str, Any]],
        world_model: Optional[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        num_scenarios: int
    ) -> str:
        """Build the prompt for scenario generation."""
        
        prompt_parts = [
            "You are a ScenarioGenerator agent for Int Crucible.",
            "Your role is to generate scenarios that stress-test candidates against critical constraints and assumptions.",
            "",
            "IMPORTANT:",
            "- Focus on scenarios that stress HIGH-WEIGHT constraints and FRAGILE assumptions.",
            "- Generate scenarios that will reveal weaknesses in candidate solutions.",
            "- Include a mix of: stress tests, edge cases, normal operation, and failure modes.",
            "- For MVP, aim for 5-10 well-targeted scenarios.",
            "- Each scenario should be structured enough for evaluators to consume.",
            "",
        ]

        if problem_spec:
            prompt_parts.extend([
                "ProblemSpec:",
                json.dumps(problem_spec, indent=2),
                "",
            ])
        else:
            prompt_parts.append("No ProblemSpec available.")
            prompt_parts.append("")

        if world_model:
            prompt_parts.extend([
                "WorldModel:",
                json.dumps(world_model, indent=2),
                "",
            ])
        else:
            prompt_parts.append("No WorldModel available.")
            prompt_parts.append("")

        if candidates:
            prompt_parts.extend([
                f"Candidates to test ({len(candidates)} candidates):",
            ])
            for i, candidate in enumerate(candidates[:5]):  # Show first 5 candidates
                prompt_parts.append(f"Candidate {i+1}: {candidate.get('mechanism_description', 'N/A')[:200]}")
            prompt_parts.append("")
        else:
            prompt_parts.append("No candidates available yet (generating scenarios for future candidates).")
            prompt_parts.append("")

        prompt_parts.extend([
            f"Generate {num_scenarios} scenarios that will effectively test candidates.",
            "",
            "For each scenario, provide:",
            "1. id: Unique identifier (e.g., 'scenario_1')",
            "2. name: Human-readable name",
            "3. description: Detailed description of what the scenario tests",
            "4. type: One of 'stress_test', 'edge_case', 'normal_operation', 'failure_mode'",
            "5. focus: What this scenario stresses (constraints, assumptions, actors, resources)",
            "6. initial_state: Starting state of actors, resources, mechanisms",
            "7. events: Sequence of events/steps that occur",
            "8. expected_outcomes: Success criteria and potential failure modes",
            "9. weight: Importance weight (0.0-1.0) for this scenario",
            "",
            "Respond with a JSON object:",
            "{",
            '  "scenarios": [',
            "    {",
            '      "id": "scenario_1",',
            '      "name": "Scenario Name",',
            '      "description": "detailed description",',
            '      "type": "stress_test|edge_case|normal_operation|failure_mode",',
            '      "focus": {',
            '        "constraints": ["constraint_id"],',
            '        "assumptions": ["assumption_id"],',
            '        "actors": ["actor_id"],',
            '        "resources": ["resource_id"]',
            "      },",
            '      "initial_state": {',
            '        "actors": {"actor_id": {"state": "..."}},',
            '        "resources": {"resource_id": {"quantity": 100, "units": "units"}},',
            '        "mechanisms": {"mechanism_id": {"state": "..."}}',
            "      },",
            '      "events": [',
            '        {"step": 1, "description": "...", "actor": "actor_id", "action": "..."}',
            "      ],",
            '      "expected_outcomes": {',
            '        "success_criteria": ["criterion 1", "criterion 2"],',
            '        "failure_modes": ["what could go wrong"]',
            "      },",
            '      "weight": 0.8',
            "    }",
            "  ],",
            '  "reasoning": "explanation of scenario selection strategy"',
            "}",
        ])

        return "\n".join(prompt_parts)

