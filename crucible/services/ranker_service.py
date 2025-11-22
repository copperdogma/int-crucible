"""
I-Ranker Service.

Service layer for ranking candidates based on evaluations.
Aggregates evaluation results, computes I = P/R, and flags hard constraint violations.
"""

import logging
from typing import Dict, Any, List, Optional
import statistics

from sqlalchemy.orm import Session

from crucible.db.repositories import (
    get_problem_spec,
    list_candidates,
    list_evaluations,
    update_candidate,
    get_run,
    append_candidate_provenance_entry,
)
from crucible.db.models import CandidateStatus
from crucible.core.provenance import build_provenance_entry

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

            i_score_display = f"{I_score:.2f}" if isinstance(I_score, (int, float)) else str(I_score)
            provenance_entry = build_provenance_entry(
                event_type="ranking",
                actor="system",
                source=f"run:{run_id}",
                description=f"Ranker computed I={i_score_display} and set status to {status.value}",
                reference_ids=[run_id, candidate_id],
                metadata={
                    "scores": scores,
                    "has_hard_violation": has_hard_violation,
                    "evaluation_count": len(candidate_evaluations),
                },
            )
            append_candidate_provenance_entry(self.session, candidate_id, provenance_entry)

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

        # Generate ranking explanations for each candidate (after sorting, when we have all candidates)
        # Build candidate lookup map for efficient access
        candidates_by_id = {c.id: c for c in candidates}
        
        for rank_index, ranked_entry in enumerate(ranked_candidates):
            candidate_id = ranked_entry["id"]
            candidate = candidates_by_id.get(candidate_id)
            if candidate is None:
                logger.warning(f"Candidate {candidate_id} not found for explanation generation")
                continue

            # Generate explanation
            explanation_data = self._generate_ranking_explanation(
                candidate=candidate,
                rank_index=rank_index,
                all_ranked_candidates=ranked_candidates,
                constraint_weights=constraint_weights,
                problem_spec=problem_spec
            )

            # Update scores with explanation
            current_scores = ranked_entry["scores"].copy()
            current_scores["ranking_explanation"] = explanation_data["ranking_explanation"]
            current_scores["ranking_factors"] = explanation_data["ranking_factors"]

            # Update candidate in database with new scores
            update_candidate(
                self.session,
                candidate_id=candidate_id,
                scores=current_scores
            )

            # Update ranked_entry for return value
            ranked_entry["scores"] = current_scores

        # Commit all updates
        self.session.commit()

        return {
            "ranked_candidates": ranked_candidates,
            "count": len(ranked_candidates),
            "hard_constraint_violations": hard_constraint_violations
        }

    def _generate_ranking_explanation(
        self,
        candidate: Any,
        rank_index: int,
        all_ranked_candidates: List[Dict[str, Any]],
        constraint_weights: Dict[str, int],
        problem_spec: Any
    ) -> Dict[str, Any]:
        """
        Generate ranking explanation and factors for a candidate.

        Args:
            candidate: Candidate model instance
            rank_index: 0-based rank (0 = first place)
            all_ranked_candidates: All ranked candidates in order
            constraint_weights: Map of constraint_id -> weight
            problem_spec: ProblemSpec model instance

        Returns:
            dict with:
                - ranking_explanation: str (1-3 sentences)
                - ranking_factors: dict with top_positive_factors and top_negative_factors lists
        """
        candidate_scores = candidate.scores or {}
        I_score = candidate_scores.get("I", 0.0)
        P_aggregated = candidate_scores.get("P", {}).get("overall", 0.5) if isinstance(candidate_scores.get("P"), dict) else 0.5
        R_aggregated = candidate_scores.get("R", {}).get("overall", 0.5) if isinstance(candidate_scores.get("R"), dict) else 0.5
        constraint_satisfaction = candidate_scores.get("constraint_satisfaction", {})

        # Build constraint name map from ProblemSpec
        constraint_name_map = {}
        for constraint in (problem_spec.constraints or []):
            constraint_id = constraint.get("name") or constraint.get("id", "unknown")
            constraint_name = constraint.get("name", constraint_id)
            constraint_name_map[constraint_id] = constraint_name

        # Compute median P and R values across all candidates
        P_values = []
        R_values = []
        for ranked_cand in all_ranked_candidates:
            cand_scores = ranked_cand.get("scores", {})
            cand_P = cand_scores.get("P", {}).get("overall", 0.5) if isinstance(cand_scores.get("P"), dict) else 0.5
            cand_R = cand_scores.get("R", {}).get("overall", 0.5) if isinstance(cand_scores.get("R"), dict) else 0.5
            P_values.append(cand_P)
            R_values.append(cand_R)

        median_P = statistics.median(P_values) if P_values else 0.5
        median_R = statistics.median(R_values) if R_values else 0.5

        # Determine relative position
        rank_number = rank_index + 1
        relative_position_parts = [f"Ranked #{rank_number}"]
        
        if rank_number == 1 and len(all_ranked_candidates) > 1:
            # Compare to #2
            next_cand = all_ranked_candidates[1]
            next_I = next_cand.get("scores", {}).get("I", 0.0)
            if next_I > 0:
                percent_diff = ((I_score - next_I) / next_I) * 100
                relative_position_parts.append(f"with I={I_score:.2f}, {abs(percent_diff):.0f}% higher than #2")
            else:
                relative_position_parts.append(f"with I={I_score:.2f}")
        elif rank_number > 1:
            # Compare to previous candidate
            prev_cand = all_ranked_candidates[rank_index - 1]
            prev_I = prev_cand.get("scores", {}).get("I", 0.0)
            if prev_I > 0:
                percent_diff = ((prev_I - I_score) / prev_I) * 100
                relative_position_parts.append(f"with I={I_score:.2f}, {percent_diff:.0f}% lower than #{rank_number - 1}")
            else:
                relative_position_parts.append(f"with I={I_score:.2f}")

        # Identify hard-constraint violations
        hard_violations = []
        for constraint_id, satisfaction in constraint_satisfaction.items():
            weight = constraint_weights.get(constraint_id, 0)
            if weight >= 100 and isinstance(satisfaction, dict) and not satisfaction.get("satisfied", False):
                constraint_name = constraint_name_map.get(constraint_id, constraint_id)
                hard_violations.append(constraint_name)

        # Identify top positive and negative factors
        positive_factors = []
        negative_factors = []

        # Hard constraint violations (highest priority for negative)
        for constraint_name in hard_violations:
            negative_factors.append(f"Violates hard constraint '{constraint_name}'")

        # Constraint satisfaction analysis
        for constraint_id, satisfaction in constraint_satisfaction.items():
            if not isinstance(satisfaction, dict):
                continue
            
            weight = constraint_weights.get(constraint_id, 0)
            satisfied = satisfaction.get("satisfied", True)
            score = satisfaction.get("score", 0.5)
            constraint_name = constraint_name_map.get(constraint_id, constraint_id)

            # High-weight constraints (weight >= 50)
            if weight >= 50:
                if satisfied and score > 0.8:
                    if weight >= 100:
                        positive_factors.append(f"Satisfies hard constraint '{constraint_name}'")
                    else:
                        positive_factors.append(f"Satisfies high-weight constraint '{constraint_name}'")
                elif not satisfied or score < 0.5:
                    if weight >= 100 and constraint_name not in hard_violations:
                        negative_factors.append(f"Violates hard constraint '{constraint_name}'")
                    elif weight >= 50:
                        negative_factors.append(f"Weak on constraint '{constraint_name}'")

        # Performance factors (P/R relative to median)
        if P_aggregated > median_P:
            positive_factors.append("High prediction quality")
        elif P_aggregated < median_P:
            negative_factors.append("Low prediction quality")

        if R_aggregated < median_R:
            positive_factors.append("Low resource cost")
        elif R_aggregated > median_R:
            negative_factors.append("High resource cost")

        # Limit factors to 2-4 each, prioritizing by weight and impact
        # Sort negative factors: hard violations first, then by weight
        negative_factors_sorted = sorted(
            negative_factors,
            key=lambda x: (not x.startswith("Violates hard"), x)
        )[:4]
        positive_factors_sorted = positive_factors[:4]

        # Build explanation string (1-3 sentences)
        explanation_parts = []

        # Start with relative position
        explanation_parts.append(". ".join(relative_position_parts) + ".")

        # Hard violations (always mention first if present)
        if hard_violations:
            violation_names = ", ".join([f"'{v}'" for v in hard_violations])
            if len(hard_violations) == 1:
                explanation_parts.append(f"Violates hard constraint {violation_names}.")
            else:
                explanation_parts.append(f"Violates hard constraints {violation_names}.")

        # P/R tradeoff
        if P_aggregated > 0.7 and R_aggregated < 0.4:
            explanation_parts.append(f"High prediction quality (P={P_aggregated:.2f}) with low cost (R={R_aggregated:.2f}).")
        elif P_aggregated > 0.7:
            explanation_parts.append(f"High prediction quality (P={P_aggregated:.2f}) with moderate cost (R={R_aggregated:.2f}).")
        elif P_aggregated < 0.4:
            explanation_parts.append(f"Low prediction quality (P={P_aggregated:.2f}) but low cost (R={R_aggregated:.2f}).")

        # Constraint strengths (top 1-2)
        constraint_strengths = [
            f for f in positive_factors_sorted 
            if "constraint" in f.lower() and "Satisfies" in f
        ]
        if constraint_strengths:
            constraint_text = constraint_strengths[0].replace("Satisfies ", "").replace(" high-weight constraint ", "").replace(" hard constraint ", "").strip("'")
            explanation_parts.append(f"Excels at satisfying constraint '{constraint_text}'.")

        # Join into final explanation (limit to 3 sentences max)
        ranking_explanation = " ".join(explanation_parts[:3])

        return {
            "ranking_explanation": ranking_explanation,
            "ranking_factors": {
                "top_positive_factors": positive_factors_sorted,
                "top_negative_factors": negative_factors_sorted
            }
        }

