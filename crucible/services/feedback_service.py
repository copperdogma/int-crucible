"""
Feedback Service.

Service layer for feedback operations, orchestrating the feedback agent
and issue context gathering.
"""

import logging
from typing import Dict, Any, Optional, List, Callable

from sqlalchemy.orm import Session

from crucible.agents.feedback_agent import FeedbackAgent
from crucible.services.issue_service import IssueService

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for feedback operations."""

    def __init__(self, session: Session):
        """
        Initialize Feedback service.

        Args:
            session: Database session
        """
        self.session = session
        self.issue_service = IssueService(session)
        
        # Create tools for the agent
        tools = self._create_tools()
        self.agent = FeedbackAgent(tools=tools)
    
    def _create_tools(self) -> Dict[str, Callable]:
        """
        Create tool functions for the feedback agent.
        
        These tools allow the agent to query the system dynamically
        for specific information about issues and their context.
        """
        def get_issue_context_tool(issue_id: str) -> Dict[str, Any]:
            """Tool: Get full context for an issue."""
            try:
                return self.issue_service.get_issue_context(issue_id)
            except Exception as e:
                logger.error(f"Error in get_issue_context_tool: {e}", exc_info=True)
                return {"error": str(e)}
        
        return {
            "get_issue_context": get_issue_context_tool,
        }
    
    def propose_remediation(
        self,
        issue_id: str,
        user_clarification: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Propose remediation for an issue using the Feedback agent.

        Args:
            issue_id: Issue ID
            user_clarification: Optional user response to clarifying questions
            conversation_history: Optional conversation history

        Returns:
            dict with feedback message, questions, and remediation proposal
        """
        try:
            # Get issue context
            issue_context = self.issue_service.get_issue_context(issue_id)
            
            # Execute agent
            task = {
                "issue_id": issue_id,
                "issue_context": issue_context,
                "user_clarification": user_clarification,
                "conversation_history": conversation_history or [],
            }
            
            result = self.agent.execute(task)
            
            return {
                "issue_id": issue_id,
                "feedback_message": result.get("feedback_message", ""),
                "clarifying_questions": result.get("clarifying_questions", []),
                "remediation_proposal": result.get("remediation_proposal"),
                "needs_clarification": result.get("needs_clarification", False),
                "tool_call_audits": result.get("tool_call_audits", []),
            }
        except Exception as e:
            logger.error(f"Error proposing remediation for issue {issue_id}: {e}", exc_info=True)
            raise

