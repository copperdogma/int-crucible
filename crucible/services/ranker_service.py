"""
I-Ranker Service.

Service layer for ranking candidates based on evaluations.
Aggregates evaluation results, computes I = P/R, and flags hard constraint violations.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from crucible.db.repositories import (
    get_problem_spec,
    list_candidates,
    list_evaluations,
    update_candidate,
    get_run,
)
from crucible.db.models import CandidateStatus

logger = logging.getLogger(__name__)


class RankerService:
    """Service for ranking candidates based on evaluations."""

    def __init__(self, session: Session):
        """
        Initialize Ranker service.

        Args:
            session: Database session
        """
        self.session = session

    def rank_candidates(
        self,
        run_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Rank all candidates in a run based on their evaluations.

        This method:
        - Aggregates evaluations for each candidate
        - Computes I = P/R for each candidate
        - Flags hard constraint violations (weight 100)
        - Updates candidate scores in the database
        - Returns ranked list with explanations

        Args:
            run_id: Run ID
            project_id: Project ID

        Returns:
            dict with:
                - ranked_candidates: List of candidate dicts sorted by I score (descending)
                - count: Number of candidates ranked
                - hard_constraint_violations: List of candidates that violate hard constraints
        """
        # Get run
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        # Get ProblemSpec for constraint weights
        problem_spec = get_problem_spec(self.session, project_id)
        if problem_spec is None:
            raise ValueError(f"ProblemSpec not found for project {project_id}")

        # Get all candidates for this run
        candidates = list_candidates(self.session, run_id=run_id)
        if not candidates:
            raise ValueError(f"No candidates found for run {run_id}")

        # Get all evaluations for this run
        evaluations = list_evaluations(self.session, run_id=run_id)
        if not evaluations:
            raise ValueError(f"No evaluations found for run {run_id}")

        # Build constraint weight map
        constraint_weights = {}
        for constraint in (problem_spec.constraints or []):
            constraint_id = constraint.get("name") or constraint.get("id", "unknown")
            weight = constraint.get("weight", 0)
            constraint_weights[constraint_id] = weight

        # Group evaluations by candidate
        evaluations_by_candidate = {}
        for evaluation in evaluations:
            candidate_id = evaluation.candidate_id
            if candidate_id not in evaluations_by_candidate:
                evaluations_by_candidate[candidate_id] = []
            evaluations_by_candidate[candidate_id].append(evaluation)

        # Aggregate scores for each candidate
        ranked_candidates = []
        hard_constraint_violations = []

        for candidate in candidates:
            candidate_id = candidate.id
            candidate_evaluations = evaluations_by_candidate.get(candidate_id, [])

            if not candidate_evaluations:
                logger.warning(f"No evaluations found for candidate {candidate_id}, skipping")
                continue

            # Aggregate P and R scores (average across all scenarios)
            P_scores = []
            R_scores = []
            constraint_satisfaction_aggregated = {}

            for evaluation in candidate_evaluations:
                # Extract P overall score
                if evaluation.P and isinstance(evaluation.P, dict):
                    P_overall = evaluation.P.get("overall", 0.5)
                    if isinstance(P_overall, (int, float)):
                        P_scores.append(float(P_overall))

                # Extract R overall score
                if evaluation.R and isinstance(evaluation.R, dict):
                    R_overall = evaluation.R.get("overall", 0.5)
                    if isinstance(R_overall, (int, float)):
                        R_scores.append(float(R_overall))

                # Aggregate constraint satisfaction
                if evaluation.constraint_satisfaction and isinstance(evaluation.constraint_satisfaction, dict):
                    for constraint_id, satisfaction in evaluation.constraint_satisfaction.items():
                        if constraint_id not in constraint_satisfaction_aggregated:
                            constraint_satisfaction_aggregated[constraint_id] = {
                                "satisfied": True,
                                "scores": [],
                                "explanations": []
                            }
                        
                        if isinstance(satisfaction, dict):
                            if satisfaction.get("satisfied") is False:
                                constraint_satisfaction_aggregated[constraint_id]["satisfied"] = False
                            
                            score = satisfaction.get("score", 0.5)
                            if isinstance(score, (int, float)):
                                constraint_satisfaction_aggregated[constraint_id]["scores"].append(float(score))
                            
                            explanation = satisfaction.get("explanation", "")
                            if explanation:
                                constraint_satisfaction_aggregated[constraint_id]["explanations"].append(explanation)

            # Compute aggregated P and R
            P_aggregated = sum(P_scores) / len(P_scores) if P_scores else 0.5
            R_aggregated = sum(R_scores) / len(R_scores) if R_scores else 0.5

            # Compute I = P/R (avoid division by zero)
            if R_aggregated > 0:
                I_score = P_aggregated / R_aggregated
            else:
                I_score = 0.0

            # Aggregate constraint satisfaction scores
            constraint_satisfaction_final = {}
            for constraint_id, agg_data in constraint_satisfaction_aggregated.items():
                avg_score = sum(agg_data["scores"]) / len(agg_data["scores"]) if agg_data["scores"] else 0.5
                constraint_satisfaction_final[constraint_id] = {
                    "satisfied": agg_data["satisfied"],
                    "score": avg_score,
                    "explanation": "; ".join(agg_data["explanations"][:3])  # Limit to first 3 explanations
                }

            # Check for hard constraint violations (weight 100)
            has_hard_violation = False
            for constraint_id, satisfaction in constraint_satisfaction_final.items():
                weight = constraint_weights.get(constraint_id, 0)
                if weight >= 100 and not satisfaction.get("satisfied", False):
                    has_hard_violation = True
                    break

            # Build final scores dict
            scores = {
                "P": {
                    "overall": P_aggregated,
                    "components": {
                        "prediction_accuracy": P_aggregated,  # Simplified for MVP
                        "scenario_coverage": len(candidate_evaluations) / len(evaluations) if evaluations else 0.0
                    }
                },
                "R": {
                    "overall": R_aggregated,
                    "components": {
                        "cost": R_aggregated,  # Simplified for MVP
                        "complexity": R_aggregated,
                        "resource_usage": R_aggregated
                    }
                },
                "I": I_score,
                "constraint_satisfaction": constraint_satisfaction_final
            }

            # Update candidate scores in database
            update_candidate(
                self.session,
                candidate_id=candidate_id,
                scores=scores
            )

            # Determine candidate status based on I score and violations
            if has_hard_violation:
                status = CandidateStatus.REJECTED
                hard_constraint_violations.append(candidate_id)
            elif I_score >= 0.8:
                status = CandidateStatus.PROMISING
            elif I_score >= 0.5:
                status = CandidateStatus.UNDER_TEST
            else:
                status = CandidateStatus.WEAK

            update_candidate(
                self.session,
                candidate_id=candidate_id,
                status=status.value
            )

            # Build ranked candidate entry
            ranked_candidates.append({
                "id": candidate_id,
                "mechanism_description": candidate.mechanism_description,
                "scores": scores,
                "status": status.value if hasattr(status, "value") else str(status),
                "has_hard_violation": has_hard_violation,
                "evaluation_count": len(candidate_evaluations)
            })

        # Sort by I score (descending)
        ranked_candidates.sort(key=lambda x: x["scores"].get("I", 0.0), reverse=True)

        # Commit all updates
        self.session.commit()

        return {
            "ranked_candidates": ranked_candidates,
            "count": len(ranked_candidates),
            "hard_constraint_violations": hard_constraint_violations
        }

