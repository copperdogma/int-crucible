"""
ProblemSpec Agent.

An agent that refines ProblemSpec objects based on chat context.
Consumes recent chat messages and current ProblemSpec, then proposes
structured updates and follow-up questions.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from kosmos.agents.base import BaseAgent
from kosmos.core.llm import get_provider

logger = logging.getLogger(__name__)


class ProblemSpecAgent(BaseAgent):
    """
    Agent that refines ProblemSpec objects based on chat context.

    This agent:
    - Reads recent chat messages and current ProblemSpec
    - Uses LLM to analyze context and propose structured updates
    - Generates follow-up questions to help complete the spec
    - Is conservative about overwriting user-provided constraints
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize ProblemSpec agent."""
        super().__init__(agent_id, agent_type or "ProblemSpecAgent", config)
        self.llm_provider = get_provider()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ProblemSpec refinement task.

        Args:
            task: Task dict with:
                - chat_messages: List of recent chat messages (dicts with role, content)
                - current_problem_spec: Current ProblemSpec dict (or None if new)
                - project_description: Optional project description

        Returns:
            dict with:
                - updated_spec: Proposed ProblemSpec updates (dict)
                - follow_up_questions: List of follow-up questions (strings)
                - reasoning: Explanation of proposed changes (string)
                - ready_to_run: Boolean indicating if spec is complete enough
        """
        try:
            chat_messages = task.get("chat_messages", [])
            current_spec = task.get("current_problem_spec")
            project_description = task.get("project_description")

            # Build context prompt
            prompt = self._build_refinement_prompt(
                chat_messages,
                current_spec,
                project_description
            )

            # Call LLM for structured response
            response = self.llm_provider.generate(
                prompt,
                system="You are a ProblemSpec refinement agent. Always respond with valid JSON only.",
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
                    "updated_spec": current_spec or {},
                    "follow_up_questions": ["Could you help refine the problem specification?"],
                    "reasoning": "Failed to parse agent response. Please try again.",
                    "ready_to_run": False
                }

            return {
                "updated_spec": result.get("updated_spec", {}),
                "follow_up_questions": result.get("follow_up_questions", []),
                "reasoning": result.get("reasoning", ""),
                "ready_to_run": result.get("ready_to_run", False)
            }

        except Exception as e:
            logger.error(f"Error in ProblemSpec agent execution: {e}", exc_info=True)
            raise

    def _build_refinement_prompt(
        self,
        chat_messages: List[Dict[str, Any]],
        current_spec: Optional[Dict[str, Any]],
        project_description: Optional[str]
    ) -> str:
        """Build the prompt for ProblemSpec refinement."""
        
        prompt_parts = [
            "You are a ProblemSpec refinement agent for Int Crucible.",
            "Your role is to help structure problem descriptions into a ProblemSpec.",
            "",
            "A ProblemSpec contains:",
            "- constraints: Array of {name, description, weight (0-100)}",
            "- goals: Array of goal descriptions (strings)",
            "- resolution: One of 'coarse', 'medium', 'fine'",
            "- mode: One of 'full_search', 'eval_only', 'seeded'",
            "",
            "IMPORTANT: Be conservative about overwriting user-provided constraints.",
            "Propose additions and refinements, but preserve user intent.",
            "",
        ]

        if project_description:
            prompt_parts.extend([
                f"Project Description: {project_description}",
                "",
            ])

        if current_spec:
            prompt_parts.extend([
                "Current ProblemSpec:",
                json.dumps(current_spec, indent=2),
                "",
            ])
        else:
            prompt_parts.append("No existing ProblemSpec (starting fresh).")
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
            "1. Propose an updated ProblemSpec (JSON structure)",
            "2. Generate 0-3 follow-up questions to help complete the spec",
            "3. Explain your reasoning",
            "4. Indicate if the spec is ready_to_run (has sufficient detail)",
            "",
            "Respond with a JSON object:",
            "{",
            '  "updated_spec": {',
            '    "constraints": [...],',
            '    "goals": [...],',
            '    "resolution": "medium",',
            '    "mode": "full_search"',
            "  },",
            '  "follow_up_questions": ["question1", "question2"],',
            '  "reasoning": "explanation of changes",',
            '  "ready_to_run": false',
            "}",
        ])

        return "\n".join(prompt_parts)

