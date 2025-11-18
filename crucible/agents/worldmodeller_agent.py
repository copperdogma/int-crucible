"""
WorldModeller Agent.

An agent that builds and refines WorldModel objects from ProblemSpec and chat context.
Consumes ProblemSpec and recent chat messages, then proposes structured world model
updates (actors, mechanisms, resources, constraints, assumptions, simplifications).
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from kosmos.agents.base import BaseAgent
from kosmos.core.llm import get_provider

logger = logging.getLogger(__name__)


class WorldModellerAgent(BaseAgent):
    """
    Agent that builds and refines WorldModel objects from ProblemSpec and chat context.

    This agent:
    - Reads ProblemSpec and recent chat messages
    - Uses LLM to analyze context and propose structured world model updates
    - Identifies actors, mechanisms, resources, constraints, assumptions, simplifications
    - Maintains provenance information for changes
    - Is conservative about overwriting existing model elements
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize WorldModeller agent."""
        super().__init__(agent_id, agent_type or "WorldModellerAgent", config)
        self.llm_provider = get_provider()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute WorldModel generation/refinement task.

        Args:
            task: Task dict with:
                - problem_spec: ProblemSpec dict (constraints, goals, resolution, mode)
                - current_world_model: Current WorldModel dict (or None if new)
                - chat_messages: List of recent chat messages (dicts with role, content)
                - project_description: Optional project description

        Returns:
            dict with:
                - updated_model: Proposed WorldModel updates (dict with actors, mechanisms, etc.)
                - changes: List of proposed changes with provenance info
                - reasoning: Explanation of proposed changes (string)
                - ready_to_run: Boolean indicating if model is complete enough
        """
        try:
            problem_spec = task.get("problem_spec")
            current_model = task.get("current_world_model")
            chat_messages = task.get("chat_messages", [])
            project_description = task.get("project_description")

            # Build context prompt
            prompt = self._build_modeling_prompt(
                problem_spec,
                current_model,
                chat_messages,
                project_description
            )

            # Call LLM for structured response
            response = self.llm_provider.generate(
                prompt,
                system="You are a WorldModeller agent for Int Crucible. Always respond with valid JSON only.",
                temperature=0.3,  # Lower temperature for more consistent structured output
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
                    "updated_model": current_model or self._empty_model(),
                    "changes": [],
                    "reasoning": "Failed to parse agent response. Please try again.",
                    "ready_to_run": False
                }

            return {
                "updated_model": result.get("updated_model", current_model or self._empty_model()),
                "changes": result.get("changes", []),
                "reasoning": result.get("reasoning", ""),
                "ready_to_run": result.get("ready_to_run", False)
            }

        except Exception as e:
            logger.error(f"Error in WorldModeller agent execution: {e}", exc_info=True)
            raise

    def _empty_model(self) -> Dict[str, Any]:
        """Return an empty WorldModel structure."""
        return {
            "actors": [],
            "mechanisms": [],
            "resources": [],
            "constraints": [],
            "assumptions": [],
            "simplifications": [],
            "provenance": []
        }

    def _build_modeling_prompt(
        self,
        problem_spec: Optional[Dict[str, Any]],
        current_model: Optional[Dict[str, Any]],
        chat_messages: List[Dict[str, Any]],
        project_description: Optional[str]
    ) -> str:
        """Build the prompt for WorldModel generation/refinement."""
        
        prompt_parts = [
            "You are a WorldModeller agent for Int Crucible.",
            "Your role is to build a structured world model from a ProblemSpec and chat context.",
            "",
            "A WorldModel contains:",
            "- actors: Entities that act in the system (people, systems, organizations)",
            "- mechanisms: Processes, systems, or algorithms that transform inputs to outputs",
            "- resources: Materials, energy, information, time, or other resources needed",
            "- constraints: Limitations or requirements (can reference ProblemSpec constraints)",
            "- assumptions: Things we assume to be true",
            "- simplifications: What we're simplifying or approximating",
            "",
            "IMPORTANT:",
            "- Be conservative about overwriting existing model elements.",
            "- Propose additions and refinements, but preserve existing structure.",
            "- Focus on elements that are most relevant for scenario generation and evaluation.",
            "- For MVP, aim for 'usable but not exhaustive' - include key elements, skip less-critical details.",
            "",
        ]

        if project_description:
            prompt_parts.extend([
                f"Project Description: {project_description}",
                "",
            ])

        if problem_spec:
            prompt_parts.extend([
                "ProblemSpec:",
                json.dumps(problem_spec, indent=2),
                "",
            ])
        else:
            prompt_parts.append("No ProblemSpec available (starting fresh).")
            prompt_parts.append("")

        if current_model:
            prompt_parts.extend([
                "Current WorldModel:",
                json.dumps(current_model, indent=2),
                "",
            ])
        else:
            prompt_parts.append("No existing WorldModel (starting fresh).")
            prompt_parts.append("")

        if chat_messages:
            prompt_parts.extend([
                "Recent Chat Messages:",
            ])
            for msg in chat_messages[-10:]:  # Last 10 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")
        else:
            prompt_parts.append("No chat messages yet.")
            prompt_parts.append("")

        prompt_parts.extend([
            "Based on the above context:",
            "1. Propose an updated WorldModel (JSON structure)",
            "2. Generate a list of changes with provenance info",
            "3. Explain your reasoning",
            "4. Indicate if the model is ready_to_run (has sufficient detail for scenario generation)",
            "",
            "Respond with a JSON object:",
            "{",
            '  "updated_model": {',
            '    "actors": [...],',
            '    "mechanisms": [...],',
            '    "resources": [...],',
            '    "constraints": [...],',
            '    "assumptions": [...],',
            '    "simplifications": [...]',
            "  },",
            '  "changes": [',
            '    {',
            '      "type": "add|update|remove",',
            '      "entity_type": "actor|mechanism|resource|constraint|assumption|simplification",',
            '      "entity_id": "id",',
            '      "description": "what changed and why"',
            '    }',
            "  ],",
            '  "reasoning": "explanation of changes",',
            '  "ready_to_run": false',
            "}",
        ])

        return "\n".join(prompt_parts)

