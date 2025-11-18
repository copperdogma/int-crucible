"""
Run verification utilities.

Provides functions to verify run completeness, data integrity, and statistics.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from crucible.db.repositories import (
    get_run,
    list_candidates,
    get_scenario_suite,
    list_evaluations,
    get_problem_spec,
    get_world_model,
)
from crucible.db.models import RunStatus

logger = logging.getLogger(__name__)


def verify_run_completeness(
    session: Session,
    run_id: str
) -> Dict[str, Any]:
    """
    Verify that a run has all expected entities and relationships.

    Args:
        session: Database session
        run_id: Run ID to verify

    Returns:
        dict with:
            - is_complete: bool indicating if run is complete
            - run_status: Current run status
            - has_problem_spec: bool
            - has_world_model: bool
            - candidate_count: int
            - scenario_count: int
            - evaluation_count: int
            - expected_evaluations: int (candidates * scenarios)
            - missing_evaluations: int
            - issues: List of issue descriptions
    """
    run = get_run(session, run_id)
    if run is None:
        return {
            "is_complete": False,
            "run_status": None,
            "error": f"Run not found: {run_id}",
            "issues": [f"Run {run_id} not found"]
        }

    issues: List[str] = []
    
    # Check prerequisites
    has_problem_spec = get_problem_spec(session, run.project_id) is not None
    has_world_model = get_world_model(session, run.project_id) is not None
    
    if not has_problem_spec:
        issues.append(f"ProblemSpec not found for project {run.project_id}")
    if not has_world_model:
        issues.append(f"WorldModel not found for project {run.project_id}")

    # Count entities
    candidates = list_candidates(session, run_id=run_id)
    candidate_count = len(candidates)
    
    scenario_suite = get_scenario_suite(session, run_id)
    scenario_count = len(scenario_suite.scenarios) if scenario_suite else 0
    
    evaluations = list_evaluations(session, run_id=run_id)
    evaluation_count = len(evaluations)

    # Check expected evaluations
    expected_evaluations = candidate_count * scenario_count if scenario_count > 0 else 0
    missing_evaluations = max(0, expected_evaluations - evaluation_count)
    
    if missing_evaluations > 0:
        issues.append(
            f"Missing {missing_evaluations} evaluations "
            f"(expected {expected_evaluations}, found {evaluation_count})"
        )

    # Check run status
    is_complete = (
        run.status == RunStatus.COMPLETED.value and
        has_problem_spec and
        has_world_model and
        candidate_count > 0 and
        scenario_count > 0 and
        missing_evaluations == 0
    )

    if run.status != RunStatus.COMPLETED.value and not issues:
        issues.append(f"Run status is {run.status}, expected 'completed'")

    return {
        "is_complete": is_complete,
        "run_status": run.status,
        "has_problem_spec": has_problem_spec,
        "has_world_model": has_world_model,
        "candidate_count": candidate_count,
        "scenario_count": scenario_count,
        "evaluation_count": evaluation_count,
        "expected_evaluations": expected_evaluations,
        "missing_evaluations": missing_evaluations,
        "issues": issues
    }


def verify_data_integrity(
    session: Session,
    run_id: str
) -> Dict[str, Any]:
    """
    Verify data integrity of run entities and relationships.

    Args:
        session: Database session
        run_id: Run ID to verify

    Returns:
        dict with:
            - is_valid: bool indicating if data is valid
            - issues: List of integrity issues
            - candidate_issues: List of candidate-specific issues
            - evaluation_issues: List of evaluation-specific issues
    """
    run = get_run(session, run_id)
    if run is None:
        return {
            "is_valid": False,
            "issues": [f"Run not found: {run_id}"],
            "candidate_issues": [],
            "evaluation_issues": []
        }

    issues: List[str] = []
    candidate_issues: List[str] = []
    evaluation_issues: List[str] = []

    # Check candidates
    candidates = list_candidates(session, run_id=run_id)
    for candidate in candidates:
        if candidate.run_id != run_id:
            candidate_issues.append(
                f"Candidate {candidate.id} has incorrect run_id: {candidate.run_id}"
            )
        if candidate.project_id != run.project_id:
            candidate_issues.append(
                f"Candidate {candidate.id} has incorrect project_id: {candidate.project_id}"
            )

    # Check evaluations
    evaluations = list_evaluations(session, run_id=run_id)
    candidate_ids = {c.id for c in candidates}
    
    for evaluation in evaluations:
        if evaluation.run_id != run_id:
            evaluation_issues.append(
                f"Evaluation {evaluation.id} has incorrect run_id: {evaluation.run_id}"
            )
        if evaluation.candidate_id not in candidate_ids:
            evaluation_issues.append(
                f"Evaluation {evaluation.id} references non-existent candidate: {evaluation.candidate_id}"
            )

    # Check scenario suite
    scenario_suite = get_scenario_suite(session, run_id)
    if scenario_suite and scenario_suite.run_id != run_id:
        issues.append(
            f"ScenarioSuite {scenario_suite.id} has incorrect run_id: {scenario_suite.run_id}"
        )

    all_issues = issues + candidate_issues + evaluation_issues
    is_valid = len(all_issues) == 0

    return {
        "is_valid": is_valid,
        "issues": issues,
        "candidate_issues": candidate_issues,
        "evaluation_issues": evaluation_issues
    }


def get_run_statistics(
    session: Session,
    run_id: str
) -> Dict[str, Any]:
    """
    Get statistics about a run.

    Args:
        session: Database session
        run_id: Run ID

    Returns:
        dict with:
            - run_id: str
            - project_id: str
            - status: str
            - created_at: datetime
            - started_at: datetime
            - completed_at: datetime
            - duration_seconds: float (if completed)
            - candidate_count: int
            - scenario_count: int
            - evaluation_count: int
            - has_rankings: bool (if candidates have scores)
    """
    run = get_run(session, run_id)
    if run is None:
        return {"error": f"Run not found: {run_id}"}

    candidates = list_candidates(session, run_id=run_id)
    scenario_suite = get_scenario_suite(session, run_id)
    evaluations = list_evaluations(session, run_id=run_id)

    # Check if candidates have rankings (scores)
    has_rankings = any(
        c.scores is not None and len(c.scores) > 0
        for c in candidates
    )

    duration_seconds = None
    if run.started_at and run.completed_at:
        duration_seconds = (run.completed_at - run.started_at).total_seconds()

    return {
        "run_id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "duration_seconds": duration_seconds,
        "candidate_count": len(candidates),
        "scenario_count": len(scenario_suite.scenarios) if scenario_suite else 0,
        "evaluation_count": len(evaluations),
        "has_rankings": has_rankings
    }

