"""
Designer Agent.

An agent that generates diverse candidate solutions from a WorldModel.
Consumes ProblemSpec and WorldModel, then proposes multiple distinct
candidate mechanisms with predicted effects and constraint compliance estimates.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from kosmos.agents.base import BaseAgent
from kosmos.core.llm import get_provider

from crucible.utils.llm_usage import usage_stats_to_dict

logger = logging.getLogger(__name__)


class DesignerAgent(BaseAgent):
    """
    Agent that generates diverse candidate solutions from a WorldModel.

    This agent:
    - Reads ProblemSpec and WorldModel
    - Uses LLM to generate multiple, diverse candidate mechanisms
    - Provides predicted effects on actors/resources
    - Estimates rough constraint compliance for each candidate
    - Focuses on diversity over completeness (distinct approaches)
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize Designer agent."""
        super().__init__(agent_id, agent_type or "DesignerAgent", config)
        self.llm_provider = get_provider()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute candidate generation task.

        Args:
            task: Task dict with:
                - problem_spec: ProblemSpec dict (constraints, goals, resolution, mode)
                - world_model: WorldModel dict (actors, mechanisms, resources, constraints, assumptions)
                - num_candidates: Optional number of candidates to generate (default: 3-5)
                - existing_candidates: Optional list of existing candidate IDs to avoid duplicates

        Returns:
            dict with:
                - candidates: List of candidate dicts, each with:
                    - mechanism_description: Text description
                    - predicted_effects: Dict with actors_affected, resources_impacted, mechanisms_modified
                    - constraint_compliance: Dict mapping constraint IDs to compliance estimates
                    - reasoning: Explanation of why this candidate was proposed
                - reasoning: Overall explanation of candidate diversity strategy
        """
        try:
            problem_spec = task.get("problem_spec")
            world_model = task.get("world_model")
            num_candidates = task.get("num_candidates", 5)
            existing_candidates = task.get("existing_candidates", [])

            # Build context prompt
            prompt = self._build_design_prompt(
                problem_spec,
                world_model,
                num_candidates,
                existing_candidates
            )

            # Call LLM for structured response
            response = self.llm_provider.generate(
                prompt,
                system="You are a Designer agent for Int Crucible. Always respond with valid JSON only.",
                temperature=0.7,  # Higher temperature for more diverse outputs
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
                    "candidates": [],
                    "reasoning": "Failed to parse agent response. Please try again."
                }

            usage = usage_stats_to_dict(response)

            return {
                "candidates": result.get("candidates", []),
                "reasoning": result.get("reasoning", ""),
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Error in Designer agent execution: {e}", exc_info=True)
            raise

    def _build_design_prompt(
        self,
        problem_spec: Optional[Dict[str, Any]],
        world_model: Optional[Dict[str, Any]],
        num_candidates: int,
        existing_candidates: List[str]
    ) -> str:
        """Build the prompt for candidate generation."""
        
        prompt_parts = [
            "You are a Designer agent for Int Crucible.",
            "Your role is to generate diverse candidate solutions from a WorldModel.",
            "",
            "IMPORTANT:",
            "- Generate multiple DISTINCT approaches, not small variants of the same idea.",
            "- Each candidate should represent a fundamentally different mechanism or strategy.",
            "- Focus on diversity over completeness.",
            "- For MVP, aim for 3-5 clearly distinct candidates.",
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

        if existing_candidates:
            prompt_parts.extend([
                f"Existing candidates (avoid similar approaches): {len(existing_candidates)} candidates already exist.",
                "",
            ])

        prompt_parts.extend([
            f"Generate {num_candidates} diverse candidate solutions.",
            "",
            "For each candidate, provide:",
            "1. mechanism_description: A clear description of how this candidate works",
            "2. predicted_effects: Expected effects on actors, resources, and mechanisms",
            "3. constraint_compliance: Rough estimates for each constraint (0.0-1.0 or boolean)",
            "4. reasoning: Why this candidate is distinct and worth considering",
            "",
            "Respond with a JSON object:",
            "{",
            '  "candidates": [',
            "    {",
            '      "mechanism_description": "detailed description",',
            '      "predicted_effects": {',
            '        "actors_affected": [',
            '          {"actor_id": "id", "impact": "positive|negative|neutral|mixed", "description": "..."}',
            "        ],",
            '        "resources_impacted": [',
            '          {"resource_id": "id", "change": "increase|decrease|no_change", "magnitude": "small|medium|large", "description": "..."}',
            "        ],",
            '        "mechanisms_modified": [',
            '          {"mechanism_id": "id", "change_type": "enhanced|replaced|removed|new", "description": "..."}',
            "        ]",
            "      },",
            '      "constraint_compliance": {',
            '        "constraint_id": 0.0-1.0 or true/false',
            "      },",
            '      "reasoning": "why this candidate is distinct"',
            "    }",
            "  ],",
            '  "reasoning": "overall strategy for candidate diversity"',
            "}",
        ])

        return "\n".join(prompt_parts)

