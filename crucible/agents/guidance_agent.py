"""
Guidance Agent.

An agent that provides interactive guidance and onboarding for users.
Explains the Int Crucible workflow, suggests next steps, and answers
questions about the system.

This agent uses tools to interact with the system dynamically, allowing it
to query for specific information as needed rather than receiving all context upfront.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Callable

from kosmos.agents.base import BaseAgent
from kosmos.core.llm import get_provider

logger = logging.getLogger(__name__)


class GuidanceAgent(BaseAgent):
    """
    Agent that provides guidance and onboarding for users.

    This agent:
    - Explains the Int Crucible workflow
    - Provides contextual help based on project state
    - Suggests next steps at appropriate moments
    - Answers questions about the system
    - Guides users through creating their first project and running their first pipeline
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tools: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize Guidance agent.
        
        Args:
            agent_id: Optional agent ID
            agent_type: Optional agent type name
            config: Optional configuration dict
            tools: Optional dict of tool functions the agent can call
                   Format: {"tool_name": callable_function}
        """
        super().__init__(agent_id, agent_type or "GuidanceAgent", config)
        self.llm_provider = get_provider()
        self.tools = tools or {}
        
        # Register tools if provided
        if self.tools:
            logger.info(f"GuidanceAgent initialized with {len(self.tools)} tools: {list(self.tools.keys())}")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute guidance task.

        This agent provides natural, conversational guidance. It can use tools
        to query the system dynamically for specific information as needed.

        Args:
            task: Task dict with:
                - user_query: Optional user question or request for help
                - project_id: Project ID (required if using tools)
                - project_state: Optional dict with basic state (used as fallback if tools unavailable)
                - workflow_stage: Optional current workflow stage
                - chat_context: Optional recent chat messages for context
                - chat_session_id: Optional chat session ID (for tool access)

        Returns:
            dict with:
                - guidance_message: Main guidance text (natural language, conversational)
                - suggested_actions: List of suggested next steps (extracted from guidance if possible)
                - workflow_progress: Dict showing current progress (computed from state)
        """
        try:
            user_query = task.get("user_query")
            project_id = task.get("project_id")
            project_state = task.get("project_state", {})
            workflow_stage = task.get("workflow_stage")
            chat_context = task.get("chat_context", [])
            
            # If we have tools and project_id, use tool-based approach
            # Otherwise fall back to context-based approach
            if self.tools and project_id:
                return self._execute_with_tools(
                    user_query=user_query,
                    project_id=project_id,
                    chat_context=chat_context,
                    initial_state=project_state
                )
            else:
                # Fallback to context-based approach
                return self._execute_with_context(
                    user_query=user_query,
                    project_state=project_state,
                    workflow_stage=workflow_stage,
                    chat_context=chat_context
                )

        except Exception as e:
            logger.error(f"Error in Guidance agent execution: {e}", exc_info=True)
            # Return a safe default response
            project_state = task.get("project_state", {})
            return {
                "guidance_message": "I'm here to help! Let me guide you through Int Crucible. Start by creating a project and chatting about your problem.",
                "suggested_actions": self._get_default_suggestions(project_state),
                "workflow_progress": self._compute_workflow_progress(project_state)
            }
    
    def _execute_with_tools(
        self,
        user_query: Optional[str],
        project_id: str,
        chat_context: List[Dict[str, Any]],
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute guidance using tools for dynamic information gathering.
        
        The agent can call tools to get specific information as needed,
        making it more efficient and accurate.
        """
        # Build initial prompt with tool descriptions
        tool_descriptions = self._describe_tools()
        
        prompt = self._build_tool_based_prompt(
            user_query=user_query,
            project_id=project_id,
            chat_context=chat_context,
            tool_descriptions=tool_descriptions,
            initial_state=initial_state
        )
        
        # For now, we'll do a simple single-pass approach
        # In a full implementation, we'd support multi-turn tool calling
        # where the agent can call tools, get results, and continue reasoning
        
        response = self.llm_provider.generate(
            prompt,
            system=self._get_system_prompt_with_tools(),
            temperature=0.8,
            max_tokens=2048
        )
        
        guidance_message = response.content.strip()
        
        # Get current state for workflow progress
        if "get_workflow_state" in self.tools:
            try:
                current_state = self.tools["get_workflow_state"](project_id)
            except Exception as e:
                logger.warning(f"Could not get workflow state via tool: {e}")
                current_state = initial_state
        else:
            current_state = initial_state
        
        suggested_actions = self._extract_suggested_actions(guidance_message, current_state)
        workflow_progress = self._compute_workflow_progress(current_state)
        
        return {
            "guidance_message": guidance_message,
            "suggested_actions": suggested_actions,
            "workflow_progress": workflow_progress
        }
    
    def _execute_with_context(
        self,
        user_query: Optional[str],
        project_state: Dict[str, Any],
        workflow_stage: Optional[str],
        chat_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute guidance using pre-gathered context (fallback approach)."""
        prompt = self._build_guidance_prompt(
            user_query,
            project_state,
            workflow_stage,
            chat_context
        )

        response = self.llm_provider.generate(
            prompt,
            system=self._get_system_prompt(),
            temperature=0.8,
            max_tokens=2048
        )

        guidance_message = response.content.strip()
        suggested_actions = self._extract_suggested_actions(guidance_message, project_state)
        workflow_progress = self._compute_workflow_progress(project_state)

        return {
            "guidance_message": guidance_message,
            "suggested_actions": suggested_actions,
            "workflow_progress": workflow_progress
        }
    
    def _describe_tools(self) -> str:
        """Describe available tools to the agent."""
        if not self.tools:
            return "No tools available."
        
        descriptions = []
        descriptions.append("Available tools:")
        descriptions.append("")
        
        tool_docs = {
            "get_workflow_state": "Get the current workflow state for a project. Returns: has_problem_spec, has_world_model, has_runs, run_count, project_title, project_description",
            "get_problem_spec": "Get the ProblemSpec for a project. Returns: constraints, goals, resolution, mode",
            "get_world_model": "Get the WorldModel for a project. Returns: model_data with actors, mechanisms, resources, etc.",
            "list_runs": "List all runs for a project. Returns: list of runs with status, mode, created_at",
            "get_chat_history": "Get recent chat messages from a chat session. Returns: list of messages with role and content",
        }
        
        for tool_name in self.tools.keys():
            desc = tool_docs.get(tool_name, f"Tool: {tool_name}")
            descriptions.append(f"- {tool_name}: {desc}")
        
        descriptions.append("")
        descriptions.append("You can use these tools to get specific information when needed.")
        descriptions.append("For example, if the user asks about their ProblemSpec constraints, call get_problem_spec to see the actual constraints.")
        
        return "\n".join(descriptions)
    
    def _build_tool_based_prompt(
        self,
        user_query: Optional[str],
        project_id: str,
        chat_context: List[Dict[str, Any]],
        tool_descriptions: str,
        initial_state: Dict[str, Any]
    ) -> str:
        """Build prompt for tool-based guidance."""
        prompt_parts = [
            "Provide helpful, conversational guidance to a user of Int Crucible.",
            "",
            f"Project ID: {project_id}",
            "",
            "Initial Project State (you can query for more details using tools):",
            f"- Has ProblemSpec: {initial_state.get('has_problem_spec', False)}",
            f"- Has WorldModel: {initial_state.get('has_world_model', False)}",
            f"- Has Runs: {initial_state.get('has_runs', False)}",
            f"- Number of Runs: {initial_state.get('run_count', 0)}",
            "",
            tool_descriptions,
        ]
        
        if user_query:
            prompt_parts.extend([
                "User is asking:",
                user_query,
                "",
                "Address their question directly. If you need specific details, you can use the available tools.",
            ])
        else:
            prompt_parts.append("User is requesting general guidance. Provide contextual guidance based on their current state.")
        
        if chat_context:
            prompt_parts.extend([
                "",
                "Recent conversation context:",
            ])
            for msg in chat_context[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
        
        prompt_parts.extend([
            "",
            "Provide natural, conversational guidance. Use tools if you need specific information to answer accurately.",
            "Write as if you're a knowledgeable colleague helping them out.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt_with_tools(self) -> str:
        """Get system prompt that includes tool usage instructions."""
        base_prompt = self._get_system_prompt()
        
        tool_instructions = """
        
Tool Usage:
- You have access to tools that let you query the system for specific information
- Use tools when you need accurate, real-time information (e.g., "What constraints are in my ProblemSpec?")
- You can call tools to get details that weren't in the initial context
- If a user asks a specific question, use tools to get the exact answer rather than guessing
- Tools help you provide more accurate, personalized guidance
"""
        
        return base_prompt + tool_instructions

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the guidance agent.
        
        This prompt gives the AI strong direction and knowledge, but lets it
        be adaptive and conversational rather than template-driven.
        """
        return """You are a helpful, knowledgeable guidance agent for Int Crucible, a multi-agent reasoning system.

Your personality:
- Friendly and encouraging, like a helpful colleague
- Adapts to the user's experience level (new users need more explanation)
- Provides context-aware guidance based on where they are in the workflow
- Answers questions clearly and thoroughly
- Suggests next steps naturally, not as a rigid checklist

The Int Crucible workflow:
1. Create a project
2. Chat to generate ProblemSpec (structured problem with constraints, goals, resolution level)
3. Generate WorldModel (structured world model with actors, mechanisms, resources)
4. Configure and run the pipeline (Designers → ScenarioGenerator → Evaluators → I-Ranker)
5. Review results (ranked candidates with I = P/R scores)

Key components you should understand:
- ProblemSpec: Structured problem specification with constraints (budget, deadline, performance, etc., weighted 0-100), goals, resolution level, and mode. This is where all problem constraints and goals are captured.
- WorldModel: Structured world model with actors, mechanisms, resources, constraints, assumptions, simplifications
- Run: An execution of the full pipeline
- Candidates: Solution candidates generated by Designers
- Scenarios: Test scenarios generated by ScenarioGenerator
- Evaluations: Candidate evaluations against scenarios
- I-Ranker: Ranks candidates by I = P/R (Prediction quality / Resource cost)

Guidance principles:
- Be conversational and natural, not robotic
- Explain concepts when relevant, but don't over-explain if they seem experienced
- Guide them to the next logical step based on their current state
- If they ask a question, answer it directly and helpfully
- If they're stuck, suggest concrete next actions
- Celebrate progress when appropriate (e.g., "Great! You've created a ProblemSpec...")

Write naturally, as if you're helping a colleague use the system."""

    def _build_guidance_prompt(
        self,
        user_query: Optional[str],
        project_state: Dict[str, Any],
        workflow_stage: Optional[str],
        chat_context: list
    ) -> str:
        """Build the prompt for guidance generation.
        
        This prompt gives the AI context and direction, but lets it be
        natural and adaptive rather than forcing a rigid structure.
        """
        
        prompt_parts = [
            "Provide helpful, conversational guidance to a user of Int Crucible.",
            "",
            "Current Project State:",
            f"- Has ProblemSpec: {project_state.get('has_problem_spec', False)}",
            f"- Has WorldModel: {project_state.get('has_world_model', False)}",
            f"- Has Runs: {project_state.get('has_runs', False)}",
            f"- Number of Runs: {project_state.get('run_count', 0)}",
            "",
        ]

        if workflow_stage:
            prompt_parts.append(f"Current Workflow Stage: {workflow_stage}")
            prompt_parts.append("")

        if user_query:
            prompt_parts.extend([
                "User is asking:",
                user_query,
                "",
                "Address their question directly and helpfully.",
            ])
        else:
            prompt_parts.append("User is requesting general guidance or help.")
            prompt_parts.append("Provide contextual guidance based on where they are in the workflow.")

        if chat_context:
            prompt_parts.extend([
                "",
                "Recent conversation context:",
            ])
            for msg in chat_context[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
            prompt_parts.append("")

        prompt_parts.extend([
            "",
            "Provide natural, conversational guidance that:",
            "- Addresses their question or current needs",
            "- Explains what they should do next in a friendly, encouraging way",
            "- Adapts to their experience level (they may be new or experienced)",
            "- Mentions specific next steps if relevant",
            "- Feels helpful, not robotic",
            "",
            "Write as if you're a knowledgeable colleague helping them out.",
            "Be concise but thorough. Use natural language, not templates.",
        ])

        return "\n".join(prompt_parts)

    def _extract_suggested_actions(
        self, 
        guidance_message: str, 
        project_state: Dict[str, Any]
    ) -> list[str]:
        """Extract suggested actions from guidance message.
        
        This is a best-effort extraction for UI display. The guidance_message
        is the primary output - this is just a convenience for structured display.
        """
        # Try to find numbered or bulleted lists in the guidance
        import re
        
        # Look for numbered lists (1., 2., etc.) or bullet points
        numbered = re.findall(r'\d+\.\s+([^\n]+)', guidance_message)
        bullets = re.findall(r'[-•]\s+([^\n]+)', guidance_message)
        
        if numbered:
            return [s.strip() for s in numbered[:4]]  # Max 4 suggestions
        elif bullets:
            return [s.strip() for s in bullets[:4]]
        else:
            # Fallback to default suggestions if we can't extract
            return self._get_default_suggestions(project_state)
    
    def _get_default_suggestions(self, project_state: Dict[str, Any]) -> list[str]:
        """Get default suggestions based on project state (fallback only)."""
        has_problem_spec = project_state.get("has_problem_spec", False)
        has_world_model = project_state.get("has_world_model", False)
        has_runs = project_state.get("has_runs", False)

        if not has_problem_spec:
            return [
                "Start chatting about your problem to generate a ProblemSpec",
                "Describe your problem, constraints, and goals in the chat"
            ]
        elif not has_world_model:
            return [
                "Generate a WorldModel based on your ProblemSpec",
                "The WorldModel will structure your problem domain"
            ]
        elif not has_runs:
            return [
                "Configure and start your first run",
                "Review the ranked candidates after the run completes"
            ]
        else:
            return [
                "Review your run results and ranked candidates",
                "Start a new run with different parameters if needed"
            ]

    def _compute_workflow_progress(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """Compute workflow progress based on project state."""
        has_problem_spec = project_state.get("has_problem_spec", False)
        has_world_model = project_state.get("has_world_model", False)
        has_runs = project_state.get("has_runs", False)

        completed_steps = []
        next_steps = []

        if has_problem_spec:
            completed_steps.append("ProblemSpec created")
            if not has_world_model:
                next_steps.append("Generate WorldModel")
        else:
            next_steps.append("Create ProblemSpec via chat")

        if has_world_model:
            completed_steps.append("WorldModel created")
            if not has_runs:
                next_steps.append("Configure and start a run")
        elif has_problem_spec:
            next_steps.append("Generate WorldModel")

        if has_runs:
            completed_steps.append("Run executed")
            next_steps.append("Review results and iterate")

        # Determine current stage
        if not has_problem_spec:
            current_stage = "setup"
        elif not has_world_model:
            current_stage = "setup"
        elif not has_runs:
            current_stage = "ready_to_run"
        else:
            current_stage = "completed"

        return {
            "current_stage": current_stage,
            "completed_steps": completed_steps,
            "next_steps": next_steps
        }

