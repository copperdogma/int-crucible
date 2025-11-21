"""
Guidance Service.

Service layer for guidance operations, orchestrating the guidance agent
and project state detection.
"""

import logging
from typing import Dict, Any, Optional, List, Callable

from sqlalchemy.orm import Session

from crucible.agents.guidance_agent import GuidanceAgent
from crucible.db.repositories import (
    get_project,
    get_problem_spec,
    get_world_model,
    list_runs,
    list_messages,
    get_chat_session,
)

logger = logging.getLogger(__name__)


class GuidanceService:
    """Service for guidance operations."""

    def __init__(self, session: Session):
        """
        Initialize Guidance service.

        Args:
            session: Database session
        """
        self.session = session
        
        # Create tools for the agent
        tools = self._create_tools()
        self.agent = GuidanceAgent(tools=tools)
    
    def _create_tools(self) -> Dict[str, Callable]:
        """
        Create tool functions for the guidance agent.
        
        These tools allow the agent to query the system dynamically
        for specific information as needed.
        """
        def get_workflow_state_tool(project_id: str) -> Dict[str, Any]:
            """Tool: Get workflow state for a project."""
            return self.get_workflow_state(project_id)
        
        def get_problem_spec_tool(project_id: str) -> Optional[Dict[str, Any]]:
            """Tool: Get ProblemSpec for a project."""
            spec = get_problem_spec(self.session, project_id)
            if spec is None:
                return None
            return {
                "constraints": spec.constraints or [],
                "goals": spec.goals or [],
                "resolution": (
                    spec.resolution.value
                    if hasattr(spec.resolution, "value")
                    else str(spec.resolution)
                ),
                "mode": (
                    spec.mode.value
                    if hasattr(spec.mode, "value")
                    else str(spec.mode)
                )
            }
        
        def get_world_model_tool(project_id: str) -> Optional[Dict[str, Any]]:
            """Tool: Get WorldModel for a project."""
            model = get_world_model(self.session, project_id)
            if model is None:
                return None
            return model.model_data
        
        def list_runs_tool(project_id: str) -> List[Dict[str, Any]]:
            """Tool: List runs for a project."""
            runs = list_runs(self.session, project_id)
            return [
                {
                    "id": r.id,
                    "status": (
                        r.status.value
                        if hasattr(r.status, "value")
                        else str(r.status)
                    ),
                    "mode": (
                        r.mode.value
                        if hasattr(r.mode, "value")
                        else str(r.mode)
                    ),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in runs
            ]
        
        def get_chat_history_tool(chat_session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
            """Tool: Get recent chat messages from a chat session."""
            messages = list_messages(self.session, chat_session_id)
            return [
                {
                    "role": (
                        msg.role.value
                        if hasattr(msg.role, "value")
                        else str(msg.role)
                    ),
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in messages[-limit:]
            ]
        
        return {
            "get_workflow_state": get_workflow_state_tool,
            "get_problem_spec": get_problem_spec_tool,
            "get_world_model": get_world_model_tool,
            "list_runs": list_runs_tool,
            "get_chat_history": get_chat_history_tool,
        }

    def get_workflow_state(self, project_id: str) -> Dict[str, Any]:
        """
        Get the current workflow state for a project.

        Args:
            project_id: Project ID

        Returns:
            dict with:
                - has_problem_spec: bool
                - has_world_model: bool
                - has_runs: bool
                - run_count: int
                - project_title: str
                - project_description: Optional[str]
        """
        project = get_project(self.session, project_id)
        if project is None:
            return {
                "has_problem_spec": False,
                "has_world_model": False,
                "has_runs": False,
                "run_count": 0,
                "project_title": None,
                "project_description": None
            }

        problem_spec = get_problem_spec(self.session, project_id)
        world_model = get_world_model(self.session, project_id)
        runs = list_runs(self.session, project_id)

        return {
            "has_problem_spec": problem_spec is not None,
            "has_world_model": world_model is not None,
            "has_runs": len(runs) > 0,
            "run_count": len(runs),
            "project_title": project.title,
            "project_description": project.description
        }

    def provide_guidance(
        self,
        project_id: str,
        user_query: Optional[str] = None,
        chat_session_id: Optional[str] = None,
        message_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Provide guidance based on project state and optional user query.

        Args:
            project_id: Project ID
            user_query: Optional user question or request for help
            chat_session_id: Optional chat session ID for context
            message_limit: Maximum number of recent messages to consider

        Returns:
            dict with:
                - guidance_message: Main guidance text
                - suggested_actions: List of suggested next steps
                - explanations: Dict explaining components
                - workflow_progress: Dict showing current progress
        """
        # Get project state
        project_state = self.get_workflow_state(project_id)

        # Determine workflow stage
        workflow_stage = self._determine_workflow_stage(project_state)

        # Get chat context if chat_session_id provided
        chat_context = []
        if chat_session_id:
            try:
                messages = list_messages(self.session, chat_session_id)
                chat_context = [
                    {
                        "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                        "content": msg.content
                    }
                    for msg in messages[-message_limit:]
                ]
            except Exception as e:
                logger.warning(f"Could not load chat context: {e}")

        # Call agent with project_id for tool-based approach
        task = {
            "user_query": user_query,
            "project_id": project_id,  # Required for tools
            "project_state": project_state,  # Fallback if tools unavailable
            "workflow_stage": workflow_stage,
            "chat_context": chat_context,
            "chat_session_id": chat_session_id
        }

        result = self.agent.execute(task)

        # Add structured metadata for conversational logging
        result["workflow_stage"] = workflow_stage
        result["guidance_type"] = self._determine_guidance_type(user_query, workflow_stage, project_state)
        
        return result

    def _determine_workflow_stage(self, project_state: Dict[str, Any]) -> str:
        """
        Determine the current workflow stage based on project state.

        Args:
            project_state: Project state dict

        Returns:
            Workflow stage string
        """
        has_problem_spec = project_state.get("has_problem_spec", False)
        has_world_model = project_state.get("has_world_model", False)
        has_runs = project_state.get("has_runs", False)

        if not has_problem_spec:
            return "setup"
        elif not has_world_model:
            return "setup"
        elif not has_runs:
            return "ready_to_run"
        else:
            return "completed"
    
    def _determine_guidance_type(
        self,
        user_query: Optional[str],
        workflow_stage: str,
        project_state: Dict[str, Any]
    ) -> str:
        """
        Determine the type of guidance being provided.

        Args:
            user_query: Optional user query
            workflow_stage: Current workflow stage
            project_state: Project state dict

        Returns:
            Guidance type string (e.g., 'spec_refinement', 'clarification', 'run_recommendation')
        """
        if not user_query:
            # No specific query - general contextual guidance
            if workflow_stage == "setup":
                return "setup_guidance"
            elif workflow_stage == "ready_to_run":
                return "run_recommendation"
            else:
                return "general_guidance"
        
        # Analyze user query to determine guidance type
        query_lower = user_query.lower()
        
        # Check for spec-related queries - focus on concrete constraint/goal terms
        spec_terms = [
            "problem", "spec", "specification", "constraint", "goal", "requirement",
            "budget", "deadline", "timeline", "cost", "limit", "maximum", "minimum",
            "add", "set", "update", "change", "modify", "include", "incorporate"
        ]
        if any(term in query_lower for term in spec_terms):
            return "spec_refinement"
        
        # Check for world model queries (but don't treat definitions as build requests)
        if "world model" in query_lower:
            if any(
                phrase in query_lower
                for phrase in [
                    "what is a",
                    "what's a",
                    "what is the",
                    "what's the",
                    "what is",
                    "what's"
                ]
            ):
                return "clarification"
            return "world_model_guidance"
        
        if any(term in query_lower for term in ["model", "actor", "mechanism"]):
            return "world_model_guidance"
        
        # Check for run-related queries
        if any(term in query_lower for term in ["run", "execute", "pipeline", "candidate", "evaluation"]):
            return "run_recommendation"
        
        # Check for clarification requests
        if any(term in query_lower for term in ["what", "how", "why", "explain", "help", "?"]):
            return "clarification"
        
        # Default to contextual guidance
        return "contextual_guidance"

