"""
Feedback Agent.

An agent that helps users understand and resolve issues they've flagged.
Asks clarifying questions and proposes remediation actions based on issue type and severity.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Callable

from kosmos.agents.base import BaseAgent
from kosmos.core.llm import get_provider
from crucible.core.tool_calling import ToolCallingExecutor

logger = logging.getLogger(__name__)


class FeedbackAgent(BaseAgent):
    """
    Agent that provides feedback and remediation guidance for issues.

    This agent:
    - Takes an issue and relevant context as input
    - Asks clarifying questions to understand the issue better
    - Proposes remediation actions based on issue type and severity
    - Returns structured remediation proposals
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tools: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize Feedback agent.
        
        Args:
            agent_id: Optional agent ID
            agent_type: Optional agent type name
            config: Optional configuration dict
            tools: Optional dict of tool functions the agent can call
                   Format: {"tool_name": callable_function}
        """
        super().__init__(agent_id, agent_type or "FeedbackAgent", config)
        self.llm_provider = get_provider()
        self.tools = tools or {}
        
        # Initialize tool calling executor if tools are available
        self.tool_executor: Optional[ToolCallingExecutor] = None
        if self.tools:
            try:
                max_iterations = config.get("max_tool_iterations", 10) if config else 10
                self.tool_executor = ToolCallingExecutor(
                    llm_provider=self.llm_provider,
                    tools=self.tools,
                    max_iterations=max_iterations
                )
                logger.info(f"FeedbackAgent initialized with {len(self.tools)} tools: {list(self.tools.keys())}")
            except Exception as e:
                logger.warning(f"Failed to initialize tool calling executor: {e}. Falling back to prompt-based tools.")
                self.tool_executor = None

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute feedback task.

        Args:
            task: Task dict with:
                - issue_id: Issue ID (required)
                - issue_context: Optional pre-gathered context (if available)
                - user_clarification: Optional user response to clarifying questions
                - conversation_history: Optional conversation history

        Returns:
            dict with:
                - feedback_message: Main feedback text (questions or proposal)
                - clarifying_questions: List of questions (if still gathering info)
                - remediation_proposal: Structured proposal (if ready)
                - needs_clarification: Boolean indicating if more info is needed
        """
        try:
            issue_id = task.get("issue_id")
            if not issue_id:
                raise ValueError("issue_id is required")
            
            issue_context = task.get("issue_context", {})
            user_clarification = task.get("user_clarification")
            conversation_history = task.get("conversation_history", [])
            
            # If we have tools, use tool-based approach
            if self.tools and self.tool_executor:
                return self._execute_with_tools(
                    issue_id=issue_id,
                    issue_context=issue_context,
                    user_clarification=user_clarification,
                    conversation_history=conversation_history
                )
            else:
                # Fallback to context-based approach
                return self._execute_with_context(
                    issue_id=issue_id,
                    issue_context=issue_context,
                    user_clarification=user_clarification,
                    conversation_history=conversation_history
                )
        except Exception as e:
            logger.error(f"Error in Feedback agent execution: {e}", exc_info=True)
            return {
                "feedback_message": f"I encountered an error while processing this issue: {str(e)}. Please try again or contact support.",
                "clarifying_questions": [],
                "remediation_proposal": None,
                "needs_clarification": False,
            }
    
    def _execute_with_tools(
        self,
        issue_id: str,
        issue_context: Dict[str, Any],
        user_clarification: Optional[str],
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute feedback using native LLM function calling for dynamic information gathering.
        """
        if self.tool_executor is None:
            return self._execute_with_context(
                issue_id=issue_id,
                issue_context=issue_context,
                user_clarification=user_clarification,
                conversation_history=conversation_history
            )
        
        try:
            # Build user message
            user_message_parts = []
            
            if user_clarification:
                # User is responding to clarifying questions
                user_message_parts.append(f"User clarification: {user_clarification}")
            else:
                # Initial issue analysis
                user_message_parts.append(f"Analyze issue {issue_id} and propose remediation.")
            
            # Add issue context
            if issue_context:
                user_message_parts.append("\n\nIssue Context:")
                user_message_parts.append(json.dumps(issue_context, indent=2))
            
            user_message = "\n".join(user_message_parts)
            
            # Convert conversation history
            conv_history = []
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conv_history.append({
                    "role": role if role != "agent" else "assistant",
                    "content": content
                })
            
            # Build system prompt
            system_prompt = self._get_system_prompt_with_tools()
            
            # Execute with tool calling
            feedback_message, tool_call_audits = self.tool_executor.execute_with_tools(
                user_message=user_message,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.7,
                conversation_history=conv_history
            )
            
            # Parse remediation proposal from message (structured extraction)
            remediation_proposal = self._extract_remediation_proposal(feedback_message, issue_context)
            clarifying_questions = self._extract_clarifying_questions(feedback_message)
            
            return {
                "feedback_message": feedback_message.strip(),
                "clarifying_questions": clarifying_questions,
                "remediation_proposal": remediation_proposal,
                "needs_clarification": len(clarifying_questions) > 0 and remediation_proposal is None,
                "tool_call_audits": [
                    {
                        "tool_name": audit.tool_name,
                        "arguments": audit.arguments,
                        "result_summary": audit.result_summary,
                        "duration_ms": audit.duration_ms,
                        "success": audit.success,
                        "error": audit.error
                    }
                    for audit in tool_call_audits
                ]
            }
        except Exception as e:
            logger.warning(f"Native tool calling failed: {e}. Falling back to prompt-based approach.", exc_info=True)
            return self._execute_with_context(
                issue_id=issue_id,
                issue_context=issue_context,
                user_clarification=user_clarification,
                conversation_history=conversation_history
            )
    
    def _execute_with_context(
        self,
        issue_id: str,
        issue_context: Dict[str, Any],
        user_clarification: Optional[str],
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute feedback using pre-gathered context (fallback approach)."""
        prompt = self._build_feedback_prompt(
            issue_id=issue_id,
            issue_context=issue_context,
            user_clarification=user_clarification,
            conversation_history=conversation_history
        )

        response = self.llm_provider.generate(
            prompt,
            system=self._get_system_prompt(),
            temperature=0.7,
            max_tokens=2048
        )

        feedback_message = response.content.strip()
        remediation_proposal = self._extract_remediation_proposal(feedback_message, issue_context)
        clarifying_questions = self._extract_clarifying_questions(feedback_message)

        return {
            "feedback_message": feedback_message,
            "clarifying_questions": clarifying_questions,
            "remediation_proposal": remediation_proposal,
            "needs_clarification": len(clarifying_questions) > 0 and remediation_proposal is None,
        }
    
    def _get_system_prompt_with_tools(self) -> str:
        """Get system prompt that includes tool usage instructions."""
        base_prompt = self._get_system_prompt()
        
        tool_instructions = """
        
Tool Usage:
- You have access to tools that let you query the system for specific information
- Use tools when you need accurate, real-time information about the issue context
- You can call tools to get details that weren't in the initial context
- Tools help you provide more accurate, personalized remediation proposals
"""
        
        return base_prompt + tool_instructions

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the feedback agent."""
        return """You are a helpful feedback agent for Int Crucible, a multi-agent reasoning system.

Your role:
- Help users understand issues they've flagged in their problem specifications, world models, or candidate solutions
- Ask 1-3 clarifying questions to understand the issue better (if needed)
- Propose appropriate remediation actions based on issue type and severity

Issue types:
- MODEL: Issues with the world model (assumptions, actors, mechanisms, etc.)
- CONSTRAINT: Issues with problem constraints (weights, definitions, etc.)
- EVALUATOR: Issues with how candidates were evaluated
- SCENARIO: Issues with test scenarios

Issue severities:
- MINOR: Small fixes that can be patched and re-scored (e.g., typo, wrong weight)
- IMPORTANT: Significant issues requiring partial rerun (e.g., missing constraint, wrong assumption)
- CATASTROPHIC: Fundamental issues requiring full rerun or candidate invalidation

Remediation actions:
1. patch_and_rescore: For MINOR issues - update spec/model, re-run evaluation+ranking only
2. partial_rerun: For IMPORTANT issues - update spec/model, re-run evaluation+ranking phases
3. full_rerun: For CATASTROPHIC issues - update spec/model, create new full run
4. invalidate_candidates: For CATASTROPHIC issues - mark specific candidates as rejected

Your process:
1. Understand the issue from the context provided
2. If unclear, ask 1-3 specific clarifying questions
3. Once clear, propose a remediation action with:
   - Action type (patch_and_rescore, partial_rerun, full_rerun, or invalidate_candidates)
   - Description of what will change
   - Estimated impact (which candidates/runs affected)
   - Rationale for why this action is appropriate

Be conversational and helpful. Explain your reasoning clearly."""

    def _build_feedback_prompt(
        self,
        issue_id: str,
        issue_context: Dict[str, Any],
        user_clarification: Optional[str],
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Build the prompt for feedback generation."""
        prompt_parts = [
            f"Analyze issue {issue_id} and provide feedback.",
            "",
            "Issue Context:",
            json.dumps(issue_context, indent=2),
        ]

        if user_clarification:
            prompt_parts.extend([
                "",
                "User clarification:",
                user_clarification,
            ])

        if conversation_history:
            prompt_parts.extend([
                "",
                "Conversation history:",
            ])
            for msg in conversation_history[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")

        prompt_parts.extend([
            "",
            "Provide feedback:",
            "- If you need more information, ask 1-3 clarifying questions",
            "- If you have enough information, propose a remediation action",
            "- Be specific about what will change and why",
        ])

        return "\n".join(prompt_parts)

    def _extract_clarifying_questions(self, message: str) -> List[str]:
        """Extract clarifying questions from the feedback message."""
        import re
        
        # Look for questions (ending with ?)
        questions = re.findall(r'[^.!?]*\?', message)
        # Filter out rhetorical questions or statements
        question_keywords = ['what', 'which', 'when', 'where', 'why', 'how', 'can you', 'could you', 'would you']
        filtered = [
            q.strip() for q in questions
            if any(kw in q.lower() for kw in question_keywords)
        ]
        return filtered[:3]  # Max 3 questions

    def _extract_remediation_proposal(
        self,
        message: str,
        issue_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract remediation proposal from the feedback message."""
        import re
        
        issue = issue_context.get("issue", {})
        issue_type = issue.get("type", "").lower()
        severity = issue.get("severity", "").lower()
        
        # Look for action keywords
        action_patterns = {
            "patch_and_rescore": r"(patch|fix|correct|update).*?(rescore|re-score|re-evaluate)",
            "partial_rerun": r"(partial|re-run|rerun).*?(evaluation|ranking)",
            "full_rerun": r"(full|complete).*?(rerun|re-run|new run)",
            "invalidate_candidates": r"(invalidate|reject|mark.*rejected).*?(candidate|solution)",
        }
        
        detected_action = None
        for action, pattern in action_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                detected_action = action
                break
        
        # If no action detected, infer from severity
        if not detected_action:
            if severity == "minor":
                detected_action = "patch_and_rescore"
            elif severity == "important":
                detected_action = "partial_rerun"
            elif severity == "catastrophic":
                detected_action = "full_rerun"
        
        if not detected_action:
            return None
        
        # Extract description and impact
        description_match = re.search(r'(?:description|what will change|action):\s*(.+?)(?:\.|$)', message, re.IGNORECASE)
        description = description_match.group(1).strip() if description_match else f"Apply {detected_action} remediation"
        
        impact_match = re.search(r'(?:impact|affected|will affect):\s*(.+?)(?:\.|$)', message, re.IGNORECASE)
        impact = impact_match.group(1).strip() if impact_match else "To be determined"
        
        return {
            "action_type": detected_action,
            "description": description,
            "estimated_impact": impact,
            "rationale": message[:200] + "..." if len(message) > 200 else message,
        }

