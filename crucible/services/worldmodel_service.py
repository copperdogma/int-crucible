"""
WorldModel Service.

Service layer for WorldModel operations, orchestrating the agent
and database operations with provenance tracking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from crucible.agents.worldmodeller_agent import WorldModellerAgent
from crucible.db.repositories import (
    get_world_model,
    update_world_model,
    create_world_model,
    get_problem_spec,
    list_messages,
    get_project,
    get_chat_session,
)

logger = logging.getLogger(__name__)


class WorldModelService:
    """Service for WorldModel operations."""

    def __init__(self, session: Session):
        """
        Initialize WorldModel service.

        Args:
            session: Database session
        """
        self.session = session
        self.agent = WorldModellerAgent()

    def generate_or_refine_world_model(
        self,
        project_id: str,
        chat_session_id: Optional[str] = None,
        message_limit: int = 20
    ) -> Dict[str, Any]:
        """
        Generate or refine WorldModel based on ProblemSpec and chat context.

        Args:
            project_id: Project ID
            chat_session_id: Optional chat session ID to use for context
            message_limit: Maximum number of recent messages to consider

        Returns:
            dict with:
                - updated_model: Updated WorldModel data
                - changes: List of proposed changes with provenance
                - reasoning: Explanation of changes
                - ready_to_run: Whether model is complete enough
                - applied: Whether updates were applied to database
        """
        # Get current WorldModel
        current_world_model = get_world_model(self.session, project_id)

        # Get ProblemSpec
        problem_spec = get_problem_spec(self.session, project_id)

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

        # Build ProblemSpec dict for agent
        problem_spec_dict = None
        if problem_spec:
            problem_spec_dict = {
                "constraints": problem_spec.constraints or [],
                "goals": problem_spec.goals or [],
                "resolution": (
                    problem_spec.resolution.value
                    if hasattr(problem_spec.resolution, "value")
                    else str(problem_spec.resolution)
                ),
                "mode": (
                    problem_spec.mode.value
                    if hasattr(problem_spec.mode, "value")
                    else str(problem_spec.mode)
                )
            }

        # Build current model dict for agent
        current_model_dict = None
        if current_world_model:
            current_model_dict = current_world_model.model_data or {}

        # Call agent
        task = {
            "problem_spec": problem_spec_dict,
            "current_world_model": current_model_dict,
            "chat_messages": chat_messages,
            "project_description": project_description
        }

        try:
            result = self.agent.execute(task)
            updated_model = result.get("updated_model", {})
            changes = result.get("changes", [])

            # Compute structured delta
            world_model_delta = self._compute_world_model_delta(
                current_model_dict,
                updated_model,
                changes
            )

            # Apply updates to database with provenance tracking
            applied = False
            if updated_model:
                applied = self._apply_model_updates(
                    project_id,
                    current_world_model,
                    updated_model,
                    changes,
                    chat_session_id
                )

            return {
                "updated_model": updated_model,
                "changes": changes,
                "reasoning": result.get("reasoning", ""),
                "ready_to_run": result.get("ready_to_run", False),
                "applied": applied,
                "world_model_delta": world_model_delta
            }

        except Exception as e:
            logger.error(f"Error generating/refining WorldModel: {e}", exc_info=True)
            raise

    def _apply_model_updates(
        self,
        project_id: str,
        current_world_model: Optional[Any],
        updated_model: Dict[str, Any],
        changes: List[Dict[str, Any]],
        chat_session_id: Optional[str] = None
    ) -> bool:
        """
        Apply model updates to database with provenance tracking.

        Args:
            project_id: Project ID
            current_world_model: Current WorldModel or None
            updated_model: Updated model dict from agent
            changes: List of changes with provenance info
            chat_session_id: Optional chat session ID for provenance

        Returns:
            True if updates were applied, False otherwise
        """
        try:
            # Ensure model has provenance array
            if "provenance" not in updated_model:
                updated_model["provenance"] = []

            # Add provenance entries for each change
            timestamp = datetime.utcnow().isoformat()
            for change in changes:
                provenance_entry = {
                    "type": change.get("type", "update"),
                    "entity_type": change.get("entity_type", "unknown"),
                    "entity_id": change.get("entity_id", ""),
                    "timestamp": timestamp,
                    "actor": "agent",
                    "source": f"chat_session:{chat_session_id}" if chat_session_id else "agent_run",
                    "description": change.get("description", "Model update")
                }
                updated_model["provenance"].append(provenance_entry)

            # Apply updates
            if current_world_model:
                # Update existing model
                update_world_model(
                    self.session,
                    project_id,
                    model_data=updated_model
                )
            else:
                # Create new model
                create_world_model(
                    self.session,
                    project_id,
                    model_data=updated_model
                )

            return True

        except Exception as e:
            logger.error(f"Error applying model updates: {e}", exc_info=True)
            return False

    def _compute_world_model_delta(
        self,
        current_model: Optional[Dict[str, Any]],
        updated_model: Dict[str, Any],
        changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute delta between current and updated WorldModel.

        Args:
            current_model: Current WorldModel dict or None
            updated_model: Updated WorldModel dict from agent
            changes: List of change descriptions from agent

        Returns:
            Delta structure with:
                - touched_sections: List of section names that changed
                - sections: Dict mapping section names to change classifications
        """
        delta = {
            "touched_sections": [],
            "sections": {}
        }

        if not updated_model:
            return delta

        # World model sections to check
        sections = ["actors", "mechanisms", "resources", "assumptions", "constraints", "simplifications"]

        # If we have structured changes from the agent, use those
        if changes:
            for change in changes:
                entity_type = change.get("entity_type", "").lower()
                change_type = change.get("type", "update").lower()
                
                # Map entity types to sections
                section_map = {
                    "actor": "actors",
                    "mechanism": "mechanisms",
                    "resource": "resources",
                    "assumption": "assumptions",
                    "constraint": "constraints",
                    "simplification": "simplifications"
                }
                
                section = section_map.get(entity_type, entity_type)
                if section in sections:
                    if section not in delta["sections"]:
                        delta["sections"][section] = {
                            "added": [],
                            "modified": [],
                            "removed": []
                        }
                    
                    entity_id = change.get("entity_id", "")
                    entity_name = change.get("name", entity_id)
                    
                    if change_type in ["add", "added", "create"]:
                        delta["sections"][section]["added"].append({
                            "id": entity_id,
                            "name": entity_name
                        })
                        if section not in delta["touched_sections"]:
                            delta["touched_sections"].append(section)
                    elif change_type in ["remove", "removed", "delete"]:
                        delta["sections"][section]["removed"].append({
                            "id": entity_id,
                            "name": entity_name
                        })
                        if section not in delta["touched_sections"]:
                            delta["touched_sections"].append(section)
                    else:  # update, modify, etc.
                        delta["sections"][section]["modified"].append({
                            "id": entity_id,
                            "name": entity_name
                        })
                        if section not in delta["touched_sections"]:
                            delta["touched_sections"].append(section)
        else:
            # Fallback: compare current vs updated model sections directly
            current_data = current_model or {}
            for section in sections:
                current_items = current_data.get(section, [])
                updated_items = updated_model.get(section, [])
                
                if current_items != updated_items:
                    # Simple comparison: if lengths differ or items changed
                    if len(current_items) < len(updated_items):
                        # Likely additions
                        delta["sections"][section] = {
                            "added": [{"name": "items"}],
                            "modified": [],
                            "removed": []
                        }
                        delta["touched_sections"].append(section)
                    elif len(current_items) > len(updated_items):
                        # Likely removals
                        delta["sections"][section] = {
                            "added": [],
                            "modified": [],
                            "removed": [{"name": "items"}]
                        }
                        delta["touched_sections"].append(section)
                    else:
                        # Likely modifications
                        delta["sections"][section] = {
                            "added": [],
                            "modified": [{"name": "items"}],
                            "removed": []
                        }
                        delta["touched_sections"].append(section)

        return delta

    def update_world_model_manual(
        self,
        project_id: str,
        model_data: Dict[str, Any],
        source: str = "manual_edit"
    ) -> bool:
        """
        Manually update WorldModel (e.g., from UI edits).

        Args:
            project_id: Project ID
            model_data: Updated model data
            source: Source of the update (e.g., "manual_edit", "user_edit")

        Returns:
            True if update was successful, False otherwise
        """
        try:
            current_world_model = get_world_model(self.session, project_id)

            # Ensure model has provenance array
            if "provenance" not in model_data:
                model_data["provenance"] = []

            # Add provenance entry for manual update
            provenance_entry = {
                "type": "update",
                "entity_type": "world_model",
                "entity_id": "all",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "user",
                "source": source,
                "description": "Manual update via UI or API"
            }
            model_data["provenance"].append(provenance_entry)

            # Apply update
            if current_world_model:
                update_world_model(
                    self.session,
                    project_id,
                    model_data=model_data
                )
            else:
                create_world_model(
                    self.session,
                    project_id,
                    model_data=model_data
                )

            return True

        except Exception as e:
            logger.error(f"Error manually updating WorldModel: {e}", exc_info=True)
            return False

    def get_world_model(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get WorldModel for a project.

        Args:
            project_id: Project ID

        Returns:
            WorldModel dict or None
        """
        world_model = get_world_model(self.session, project_id)
        if world_model is None:
            return None

        return {
            "id": world_model.id,
            "project_id": world_model.project_id,
            "model_data": world_model.model_data or {},
            "created_at": world_model.created_at.isoformat() if world_model.created_at else None,
            "updated_at": world_model.updated_at.isoformat() if world_model.updated_at else None
        }

