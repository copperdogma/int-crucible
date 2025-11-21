"""
Designer Service.

Service layer for Designer operations, orchestrating the agent
and database operations with provenance tracking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from crucible.agents.designer_agent import DesignerAgent
from crucible.db.repositories import (
    get_problem_spec,
    get_world_model,
    create_candidate,
    list_candidates,
    get_run,
    append_candidate_provenance_entry,
)
from crucible.db.models import CandidateOrigin, CandidateStatus
from crucible.core.provenance import build_provenance_entry
from crucible.utils.llm_usage import aggregate_usage

logger = logging.getLogger(__name__)


class DesignerService:
    """Service for Designer operations."""

    def __init__(self, session: Session):
        """
        Initialize Designer service.

        Args:
            session: Database session
        """
        self.session = session
        self.agent = DesignerAgent()

    def generate_candidates(
        self,
        run_id: str,
        project_id: str,
        num_candidates: int = 5
    ) -> Dict[str, Any]:
        """
        Generate candidates for a run.

        Args:
            run_id: Run ID
            project_id: Project ID
            num_candidates: Number of candidates to generate

        Returns:
            dict with:
                - candidates: List of created candidate dicts
                - reasoning: Agent reasoning
                - count: Number of candidates created
        """
        # Get ProblemSpec
        problem_spec = get_problem_spec(self.session, project_id)

        # Get WorldModel
        world_model = get_world_model(self.session, project_id)

        # Get existing candidates for this run (to avoid duplicates)
        existing_candidates = list_candidates(self.session, run_id=run_id)
        existing_candidate_ids = [c.id for c in existing_candidates]

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

        # Build WorldModel dict for agent
        world_model_dict = None
        if world_model:
            world_model_dict = world_model.model_data or {}

        # Call agent
        task = {
            "problem_spec": problem_spec_dict,
            "world_model": world_model_dict,
            "num_candidates": num_candidates,
            "existing_candidates": existing_candidate_ids
        }

        try:
            result = self.agent.execute(task)
            candidate_proposals = result.get("candidates", [])
            reasoning = result.get("reasoning", "")
            usage_entry = result.get("usage")
            usage_summary = aggregate_usage([usage_entry]) if usage_entry else None

            # Create candidates in database with provenance
            created_candidates = []
            for proposal in candidate_proposals:
                # Extract constraint compliance estimates
                constraint_compliance = proposal.get("constraint_compliance", {})
                
                # Create initial scores dict with constraint compliance
                scores = {
                    "constraint_satisfaction": {
                        constraint_id: {
                            "satisfied": bool(score) if isinstance(score, bool) else (score > 0.5),
                            "score": float(score) if not isinstance(score, bool) else (1.0 if score else 0.0),
                            "explanation": f"Initial estimate from designer"
                        }
                        for constraint_id, score in constraint_compliance.items()
                    }
                }

                parent_ids = proposal.get("parent_ids") or proposal.get("parents") or []
                if isinstance(parent_ids, str):
                    parent_ids = [parent_ids]

                # Create candidate
                candidate = create_candidate(
                    self.session,
                    run_id=run_id,
                    project_id=project_id,
                    origin=CandidateOrigin.SYSTEM.value,
                    mechanism_description=proposal.get("mechanism_description", ""),
                    predicted_effects=proposal.get("predicted_effects"),
                    parent_ids=parent_ids
                )

                # Update candidate with scores
                candidate.scores = scores
                candidate.status = CandidateStatus.NEW
                self.session.commit()
                self.session.refresh(candidate)

                provenance_entry = build_provenance_entry(
                    event_type="design",
                    actor="agent",
                    source=f"run:{run_id}",
                    description=proposal.get("reasoning", "Generated by Designer agent"),
                    reference_ids=[run_id, candidate.id],
                    metadata={
                        "constraint_compliance": constraint_compliance,
                        "parent_ids": parent_ids,
                    },
                )
                append_candidate_provenance_entry(self.session, candidate.id, provenance_entry)

                created_candidates.append({
                    "id": candidate.id,
                    "mechanism_description": candidate.mechanism_description,
                    "predicted_effects": candidate.predicted_effects,
                    "scores": candidate.scores,
                    "status": candidate.status.value if hasattr(candidate.status, "value") else str(candidate.status)
                })

            return {
                "candidates": created_candidates,
                "reasoning": reasoning,
                "count": len(created_candidates),
                "usage_summary": usage_summary
            }

        except Exception as e:
            logger.error(f"Error generating candidates: {e}", exc_info=True)
            raise

