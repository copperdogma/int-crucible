"""
ProblemSpec Service.

Service layer for ProblemSpec operations, orchestrating the agent
and database operations.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from crucible.agents.problemspec_agent import ProblemSpecAgent
from crucible.db.repositories import (
    get_problem_spec,
    update_problem_spec,
    create_problem_spec,
    list_messages,
    get_project,
    get_chat_session,
)
from crucible.db.models import ProblemSpec, ResolutionLevel, RunMode

logger = logging.getLogger(__name__)


class ProblemSpecService:
    """Service for ProblemSpec operations."""

    def __init__(self, session: Session):
        """
        Initialize ProblemSpec service.

        Args:
            session: Database session
        """
        self.session = session
        self.agent = ProblemSpecAgent()

    def refine_problem_spec(
        self,
        project_id: str,
        chat_session_id: Optional[str] = None,
        message_limit: int = 20
    ) -> Dict[str, Any]:
        """
        Refine ProblemSpec based on chat context.

        Args:
            project_id: Project ID
            chat_session_id: Optional chat session ID to use for context
            message_limit: Maximum number of recent messages to consider

        Returns:
            dict with:
                - updated_spec: Updated ProblemSpec data
                - follow_up_questions: List of follow-up questions
                - reasoning: Explanation of changes
                - ready_to_run: Whether spec is complete enough
                - applied: Whether updates were applied to database
        """
        # Get current ProblemSpec
        current_spec = get_problem_spec(self.session, project_id)

        # Get chat messages for context
        chat_messages = []
        if chat_session_id:
            messages = list_messages(self.session, chat_session_id)
            chat_messages = [
                {
                    "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                    "content": msg.content
                }
                for msg in messages[-message_limit:]
            ]

        # Get project description
        project = get_project(self.session, project_id)
        project_description = project.description if project else None

        # Build current spec dict for agent
        current_spec_dict = None
        if current_spec:
            current_spec_dict = {
                "constraints": current_spec.constraints or [],
                "goals": current_spec.goals or [],
                "resolution": (
                    current_spec.resolution.value
                    if hasattr(current_spec.resolution, "value")
                    else str(current_spec.resolution)
                ),
                "mode": (
                    current_spec.mode.value
                    if hasattr(current_spec.mode, "value")
                    else str(current_spec.mode)
                )
            }

        # Call agent
        task = {
            "chat_messages": chat_messages,
            "current_problem_spec": current_spec_dict,
            "project_description": project_description
        }

        try:
            result = self.agent.execute(task)
            updated_spec = result.get("updated_spec", {})

            # Compute delta before applying updates
            spec_delta = self._compute_spec_delta(current_spec_dict, updated_spec)

            # Apply updates to database (merge with existing, don't overwrite user constraints)
            applied = False
            if updated_spec:
                applied = self._apply_spec_updates(project_id, current_spec, updated_spec)

            return {
                "updated_spec": updated_spec,
                "follow_up_questions": result.get("follow_up_questions", []),
                "reasoning": result.get("reasoning", ""),
                "ready_to_run": result.get("ready_to_run", False),
                "applied": applied,
                "spec_delta": spec_delta
            }

        except Exception as e:
            logger.error(f"Error refining ProblemSpec: {e}", exc_info=True)
            raise

    def _apply_spec_updates(
        self,
        project_id: str,
        current_spec: Optional[ProblemSpec],
        updated_spec: Dict[str, Any]
    ) -> bool:
        """
        Apply spec updates to database (conservative merge).

        Args:
            project_id: Project ID
            current_spec: Current ProblemSpec or None
            updated_spec: Updated spec dict from agent

        Returns:
            True if updates were applied, False otherwise
        """
        try:
            # Merge updates conservatively
            constraints = updated_spec.get("constraints")
            goals = updated_spec.get("goals")
            resolution = updated_spec.get("resolution")
            mode = updated_spec.get("mode")

            # Validate and convert enums
            if resolution:
                try:
                    resolution = ResolutionLevel(resolution)
                except ValueError:
                    logger.warning(f"Invalid resolution level: {resolution}")
                    resolution = None

            if mode:
                try:
                    mode = RunMode(mode)
                except ValueError:
                    logger.warning(f"Invalid run mode: {mode}")
                    mode = None

            # Apply updates
            if current_spec:
                # Update existing spec (repositories expect strings)
                update_problem_spec(
                    self.session,
                    project_id,
                    constraints=constraints if constraints is not None else None,
                    goals=goals if goals is not None else None,
                    resolution=resolution if isinstance(resolution, str) else (resolution.value if resolution else None),
                    mode=mode if isinstance(mode, str) else (mode.value if mode else None)
                )
            else:
                # Create new spec (repositories expect strings)
                create_problem_spec(
                    self.session,
                    project_id,
                    constraints=constraints or [],
                    goals=goals or [],
                    resolution=resolution if isinstance(resolution, str) else (resolution.value if resolution else "medium"),
                    mode=mode if isinstance(mode, str) else (mode.value if mode else "full_search")
                )

            return True

        except Exception as e:
            logger.error(f"Error applying spec updates: {e}", exc_info=True)
            return False

    def _compute_spec_delta(
        self,
        current_spec: Optional[Dict[str, Any]],
        updated_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute delta between current and updated ProblemSpec.

        Args:
            current_spec: Current ProblemSpec dict or None
            updated_spec: Updated ProblemSpec dict from agent

        Returns:
            Delta structure with:
                - touched_sections: List of section names that changed
                - constraints: Dict with added/updated/removed constraint info
                - goals: Dict with added/updated/removed goal info
                - resolution_changed: bool
                - mode_changed: bool
        """
        delta = {
            "touched_sections": [],
            "constraints": {
                "added": [],
                "updated": [],
                "removed": []
            },
            "goals": {
                "added": [],
                "updated": [],
                "removed": []
            },
            "resolution_changed": False,
            "mode_changed": False
        }

        if not updated_spec:
            return delta

        # Compare constraints
        current_constraints = {c.get("name"): c for c in (current_spec.get("constraints", []) if current_spec else [])}
        updated_constraints = {c.get("name"): c for c in updated_spec.get("constraints", [])}

        # Find added/updated/removed constraints
        for name, constraint in updated_constraints.items():
            if name not in current_constraints:
                delta["constraints"]["added"].append({
                    "name": name,
                    "description": constraint.get("description", "")
                })
                delta["touched_sections"].append("constraints")
            else:
                # Check if constraint was updated (simple comparison)
                current = current_constraints[name]
                if (current.get("description") != constraint.get("description") or
                    current.get("weight") != constraint.get("weight")):
                    delta["constraints"]["updated"].append({
                        "name": name,
                        "description": constraint.get("description", "")
                    })
                    delta["touched_sections"].append("constraints")

        for name in current_constraints:
            if name not in updated_constraints:
                delta["constraints"]["removed"].append({
                    "name": name
                })
                delta["touched_sections"].append("constraints")

        # Compare goals
        current_goals = current_spec.get("goals", []) if current_spec else []
        updated_goals = updated_spec.get("goals", [])

        # Simple comparison: treat goals as a set
        current_goals_set = set(current_goals)
        updated_goals_set = set(updated_goals)

        added_goals = updated_goals_set - current_goals_set
        removed_goals = current_goals_set - updated_goals_set

        if added_goals:
            delta["goals"]["added"] = list(added_goals)
            delta["touched_sections"].append("goals")
        if removed_goals:
            delta["goals"]["removed"] = list(removed_goals)
            delta["touched_sections"].append("goals")

        # Check for updated goals (present in both but potentially modified)
        # Since goals are strings, we can't easily detect "updates" without semantic comparison
        # For now, we'll only track added/removed

        # Compare resolution
        current_resolution = current_spec.get("resolution") if current_spec else None
        updated_resolution = updated_spec.get("resolution")
        if current_resolution != updated_resolution and updated_resolution is not None:
            delta["resolution_changed"] = True
            delta["touched_sections"].append("resolution")

        # Compare mode
        current_mode = current_spec.get("mode") if current_spec else None
        updated_mode = updated_spec.get("mode")
        if current_mode != updated_mode and updated_mode is not None:
            delta["mode_changed"] = True
            delta["touched_sections"].append("mode")

        # Remove duplicates from touched_sections
        delta["touched_sections"] = list(set(delta["touched_sections"]))

        return delta

    def get_problem_spec(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get ProblemSpec for a project.

        Args:
            project_id: Project ID

        Returns:
            ProblemSpec dict or None
        """
        spec = get_problem_spec(self.session, project_id)
        if spec is None:
            return None

        return {
            "id": spec.id,
            "project_id": spec.project_id,
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
            ),
            "created_at": spec.created_at.isoformat() if spec.created_at else None,
            "updated_at": spec.updated_at.isoformat() if spec.updated_at else None
        }

