"""
Issue Service.

Service layer for issue management and remediation actions.
Handles issue creation, context gathering, and remediation execution.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from crucible.core.provenance import build_provenance_entry
from crucible.db.models import (
    CandidateStatus,
    IssueResolutionStatus,
    IssueSeverity,
    IssueType,
    RunMode,
)
from crucible.db.repositories import (
    append_candidate_provenance_entry,
    create_run,
    get_candidate,
    get_issue,
    get_problem_spec,
    get_project,
    get_run,
    get_world_model,
    list_evaluations,
    update_candidate,
)
from crucible.db.repositories import (
    create_issue as repo_create_issue,
)
from crucible.db.repositories import (
    update_issue as repo_update_issue,
)
from crucible.services.run_service import RunService

logger = logging.getLogger(__name__)


class IssueService:
    """Service for issue management and remediation."""

    def __init__(self, session: Session):
        """
        Initialize Issue service.

        Args:
            session: Database session
        """
        self.session = session
        self.run_service = RunService(session)

    def create_issue(
        self,
        project_id: str,
        issue_type: str,
        severity: str,
        description: str,
        run_id: str | None = None,
        candidate_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new issue with validation.

        Args:
            project_id: Project ID
            issue_type: Issue type (IssueType enum value)
            severity: Issue severity (IssueSeverity enum value)
            description: Issue description
            run_id: Optional run ID
            candidate_id: Optional candidate ID

        Returns:
            dict with created issue data
        """
        # Validate project exists
        project = get_project(self.session, project_id)
        if project is None:
            raise ValueError(f"Project not found: {project_id}")

        # Validate enums
        try:
            type_enum = IssueType(issue_type)
        except ValueError as err:
            raise ValueError(f"Invalid issue type: {issue_type}") from err

        try:
            severity_enum = IssueSeverity(severity)
        except ValueError as err:
            raise ValueError(f"Invalid severity: {severity}") from err

        # Validate optional references
        if run_id:
            run = get_run(self.session, run_id)
            if run is None:
                raise ValueError(f"Run not found: {run_id}")
            if run.project_id != project_id:
                raise ValueError(f"Run {run_id} does not belong to project {project_id}")

        if candidate_id:
            candidate = get_candidate(self.session, candidate_id)
            if candidate is None:
                raise ValueError(f"Candidate not found: {candidate_id}")
            if candidate.project_id != project_id:
                raise ValueError(
                    f"Candidate {candidate_id} does not belong to project {project_id}"
                )

        # Create issue
        issue = repo_create_issue(
            session=self.session,
            project_id=project_id,
            type=type_enum.value,
            severity=severity_enum.value,
            description=description,
            run_id=run_id,
            candidate_id=candidate_id,
        )

        # Record provenance entry
        problem_spec = get_problem_spec(self.session, project_id)
        if problem_spec:
            provenance_entry = build_provenance_entry(
                event_type="issue_created",
                actor="user",
                source="issue_service:create_issue",
                description=f"Issue created: {type_enum.value} - {severity_enum.value}",
                reference_ids=[issue.id, project_id],
                metadata={
                    "issue_type": type_enum.value,
                    "issue_severity": severity_enum.value,
                    "run_id": run_id,
                    "candidate_id": candidate_id,
                },
            )
            if problem_spec.provenance_log is None:
                problem_spec.provenance_log = []
            problem_spec.provenance_log.append(provenance_entry)
            self.session.commit()

        return {
            "id": issue.id,
            "project_id": issue.project_id,
            "run_id": issue.run_id,
            "candidate_id": issue.candidate_id,
            "type": issue.type.value,
            "severity": issue.severity.value,
            "description": issue.description,
            "resolution_status": issue.resolution_status.value,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
        }

    def get_issue_context(self, issue_id: str) -> dict[str, Any]:
        """
        Gather relevant context for an issue.

        Args:
            issue_id: Issue ID

        Returns:
            dict with context (ProblemSpec, WorldModel, candidate, evaluations, etc.)
        """
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        context = {
            "issue": {
                "id": issue.id,
                "type": issue.type.value,
                "severity": issue.severity.value,
                "description": issue.description,
                "project_id": issue.project_id,
                "run_id": issue.run_id,
                "candidate_id": issue.candidate_id,
            },
            "project": None,
            "problem_spec": None,
            "world_model": None,
            "run": None,
            "candidate": None,
            "evaluations": None,
        }

        # Get project
        project = get_project(self.session, issue.project_id)
        if project:
            context["project"] = {
                "id": project.id,
                "title": project.title,
                "description": project.description,
            }

        # Get ProblemSpec
        problem_spec = get_problem_spec(self.session, issue.project_id)
        if problem_spec:
            context["problem_spec"] = {
                "id": problem_spec.id,
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
                ),
            }

        # Get WorldModel
        world_model = get_world_model(self.session, issue.project_id)
        if world_model:
            context["world_model"] = {
                "id": world_model.id,
                "model_data": world_model.model_data or {},
            }

        # Get run if specified
        if issue.run_id:
            run = get_run(self.session, issue.run_id)
            if run:
                context["run"] = {
                    "id": run.id,
                    "mode": run.mode.value if hasattr(run.mode, "value") else str(run.mode),
                    "status": run.status.value if hasattr(run.status, "value") else str(run.status),
                    "candidate_count": run.candidate_count,
                    "scenario_count": run.scenario_count,
                }

        # Get candidate if specified
        if issue.candidate_id:
            candidate = get_candidate(self.session, issue.candidate_id)
            if candidate:
                context["candidate"] = {
                    "id": candidate.id,
                    "origin": candidate.origin.value if hasattr(candidate.origin, "value") else str(candidate.origin),
                    "mechanism_description": candidate.mechanism_description,
                    "scores": candidate.scores,
                    "status": candidate.status.value if hasattr(candidate.status, "value") else str(candidate.status),
                }

                # Get evaluations for candidate
                evaluations = list_evaluations(
                    self.session, candidate_id=issue.candidate_id, run_id=issue.run_id
                )
                if evaluations:
                    context["evaluations"] = [
                        {
                            "id": eval.id,
                            "scenario_id": eval.scenario_id,
                            "P": eval.P,
                            "R": eval.R,
                            "constraint_satisfaction": eval.constraint_satisfaction,
                            "explanation": eval.explanation,
                        }
                        for eval in evaluations
                    ]

        return context

    def apply_patch_and_rescore(
        self,
        issue_id: str,
        patch_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Apply a minor patch (update ProblemSpec/WorldModel) and re-run evaluation+ranking.

        Args:
            issue_id: Issue ID
            patch_data: Dict with updates to apply (e.g., {"problem_spec": {...}, "world_model": {...}})

        Returns:
            dict with remediation result
        """
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        if issue.severity != IssueSeverity.MINOR:
            logger.warning(
                f"Issue {issue_id} has severity {issue.severity.value}, but patch_and_rescore is typically for MINOR issues"
            )

        if not issue.run_id:
            raise ValueError(f"Issue {issue_id} has no associated run_id for rescoring")

        # Apply patches to ProblemSpec/WorldModel
        problem_spec = get_problem_spec(self.session, issue.project_id)
        world_model = get_world_model(self.session, issue.project_id)

        patches_applied = []

        if "problem_spec" in patch_data and problem_spec:
            from crucible.db.repositories import update_problem_spec

            updates = patch_data["problem_spec"]

            # Merge updates with existing spec (only update provided fields)
            current_constraints = problem_spec.constraints or []
            current_goals = problem_spec.goals or []
            current_resolution = problem_spec.resolution.value if hasattr(problem_spec.resolution, "value") else str(problem_spec.resolution)
            current_mode = problem_spec.mode.value if hasattr(problem_spec.mode, "value") else str(problem_spec.mode)

            # Apply updates (merge constraints/goals, replace resolution/mode if provided)
            new_constraints = updates.get("constraints", current_constraints)
            new_goals = updates.get("goals", current_goals)
            new_resolution = updates.get("resolution", current_resolution)
            new_mode = updates.get("mode", current_mode)

            # Update ProblemSpec
            updated_spec = update_problem_spec(
                self.session,
                project_id=issue.project_id,
                constraints=new_constraints,
                goals=new_goals,
                resolution=new_resolution,
                mode=new_mode
            )

            if updated_spec:
                patches_applied.append("problem_spec")

                # Record provenance
                provenance_entry = build_provenance_entry(
                    event_type="feedback_patch",
                    actor="system",
                    source="issue_service:apply_patch_and_rescore",
                    description=f"ProblemSpec patched due to issue {issue_id}",
                    reference_ids=[issue.id, issue.project_id],
                    metadata={"patch_type": "problem_spec", "updates": updates},
                )
                if updated_spec.provenance_log is None:
                    updated_spec.provenance_log = []
                updated_spec.provenance_log.append(provenance_entry)
                self.session.commit()
                problem_spec = updated_spec  # Update reference for later use

        if "world_model" in patch_data and world_model:
            from crucible.db.repositories import update_world_model

            updates = patch_data["world_model"]

            # Merge updates with existing model_data
            current_model_data = world_model.model_data or {}
            if not isinstance(current_model_data, dict):
                current_model_data = {}

            # Deep merge: update provided sections, keep others
            new_model_data = current_model_data.copy()
            for key, value in updates.items():
                if key == "provenance":
                    # Preserve existing provenance
                    if "provenance" not in new_model_data:
                        new_model_data["provenance"] = []
                    if isinstance(value, list):
                        new_model_data["provenance"].extend(value)
                elif isinstance(value, dict) and key in new_model_data and isinstance(new_model_data[key], dict):
                    # Merge nested dicts (e.g., actors, assumptions)
                    new_model_data[key] = {**new_model_data[key], **value}
                else:
                    # Replace or add new keys
                    new_model_data[key] = value

            # Update WorldModel
            updated_model = update_world_model(
                self.session,
                project_id=issue.project_id,
                model_data=new_model_data
            )

            if updated_model:
                patches_applied.append("world_model")

                # Record provenance in world model
                if isinstance(updated_model.model_data, dict):
                    if "provenance" not in updated_model.model_data:
                        updated_model.model_data["provenance"] = []
                    provenance_entry = build_provenance_entry(
                        event_type="feedback_patch",
                        actor="system",
                        source="issue_service:apply_patch_and_rescore",
                        description=f"WorldModel patched due to issue {issue_id}",
                        reference_ids=[issue.id, issue.project_id],
                        metadata={"patch_type": "world_model", "updates": updates},
                    )
                    updated_model.model_data["provenance"].append(provenance_entry)
                    # Save the updated model_data with provenance
                    update_world_model(
                        self.session,
                        project_id=issue.project_id,
                        model_data=updated_model.model_data
                    )
                    world_model = updated_model  # Update reference for later use

        self.session.commit()

        # Re-run evaluation and ranking phases
        try:
            result = self.run_service.execute_evaluate_and_rank_phase(issue.run_id)

            # Record provenance on run
            run = get_run(self.session, issue.run_id)
            if run:
                # Note: Run doesn't have provenance_log, but we can record in ProblemSpec
                if problem_spec:
                    provenance_entry = build_provenance_entry(
                        event_type="feedback_patch",
                        actor="system",
                        source="issue_service:apply_patch_and_rescore",
                        description=f"Re-scored run {issue.run_id} after patch",
                        reference_ids=[issue.id, issue.run_id],
                        metadata={"action": "patch_and_rescore", "patches_applied": patches_applied},
                    )
                    if problem_spec.provenance_log is None:
                        problem_spec.provenance_log = []
                    problem_spec.provenance_log.append(provenance_entry)
                    self.session.commit()

            # Mark issue as resolved
            repo_update_issue(
                self.session,
                issue_id=issue_id,
                resolution_status=IssueResolutionStatus.RESOLVED.value,
                resolved_at=datetime.utcnow(),
            )

            return {
                "status": "success",
                "action": "patch_and_rescore",
                "issue_id": issue_id,
                "patches_applied": patches_applied,
                "rerun_result": result,
            }
        except Exception as e:
            logger.error(f"Error in patch_and_rescore for issue {issue_id}: {e}", exc_info=True)
            raise

    def apply_partial_rerun(
        self,
        issue_id: str,
        patch_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Apply important fixes: update spec/model, re-run evaluation+ranking phases.

        Args:
            issue_id: Issue ID
            patch_data: Dict with updates to apply

        Returns:
            dict with remediation result
        """
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        if not issue.run_id:
            raise ValueError(f"Issue {issue_id} has no associated run_id for partial rerun")

        # Apply patches to ProblemSpec/WorldModel (same logic as patch_and_rescore)
        problem_spec = get_problem_spec(self.session, issue.project_id)
        world_model = get_world_model(self.session, issue.project_id)

        patches_applied = []

        if "problem_spec" in patch_data and problem_spec:
            from crucible.db.repositories import update_problem_spec

            updates = patch_data["problem_spec"]
            current_constraints = problem_spec.constraints or []
            current_goals = problem_spec.goals or []
            current_resolution = problem_spec.resolution.value if hasattr(problem_spec.resolution, "value") else str(problem_spec.resolution)
            current_mode = problem_spec.mode.value if hasattr(problem_spec.mode, "value") else str(problem_spec.mode)

            new_constraints = updates.get("constraints", current_constraints)
            new_goals = updates.get("goals", current_goals)
            new_resolution = updates.get("resolution", current_resolution)
            new_mode = updates.get("mode", current_mode)

            updated_spec = update_problem_spec(
                self.session,
                project_id=issue.project_id,
                constraints=new_constraints,
                goals=new_goals,
                resolution=new_resolution,
                mode=new_mode
            )

            if updated_spec:
                patches_applied.append("problem_spec")
                provenance_entry = build_provenance_entry(
                    event_type="feedback_patch",
                    actor="system",
                    source="issue_service:apply_partial_rerun",
                    description=f"ProblemSpec patched due to issue {issue_id}",
                    reference_ids=[issue.id, issue.project_id],
                    metadata={"patch_type": "problem_spec", "updates": updates},
                )
                if updated_spec.provenance_log is None:
                    updated_spec.provenance_log = []
                updated_spec.provenance_log.append(provenance_entry)
                self.session.commit()
                problem_spec = updated_spec

        if "world_model" in patch_data and world_model:
            from crucible.db.repositories import update_world_model

            updates = patch_data["world_model"]
            current_model_data = world_model.model_data or {}
            if not isinstance(current_model_data, dict):
                current_model_data = {}

            new_model_data = current_model_data.copy()
            for key, value in updates.items():
                if key == "provenance":
                    if "provenance" not in new_model_data:
                        new_model_data["provenance"] = []
                    if isinstance(value, list):
                        new_model_data["provenance"].extend(value)
                elif isinstance(value, dict) and key in new_model_data and isinstance(new_model_data[key], dict):
                    new_model_data[key] = {**new_model_data[key], **value}
                else:
                    new_model_data[key] = value

            updated_model = update_world_model(
                self.session,
                project_id=issue.project_id,
                model_data=new_model_data
            )

            if updated_model:
                patches_applied.append("world_model")
                if isinstance(updated_model.model_data, dict):
                    if "provenance" not in updated_model.model_data:
                        updated_model.model_data["provenance"] = []
                    provenance_entry = build_provenance_entry(
                        event_type="feedback_patch",
                        actor="system",
                        source="issue_service:apply_full_rerun",
                        description=f"WorldModel patched due to issue {issue_id}",
                        reference_ids=[issue.id, issue.project_id],
                        metadata={"patch_type": "world_model", "updates": updates},
                    )
                    updated_model.model_data["provenance"].append(provenance_entry)
                    update_world_model(
                        self.session,
                        project_id=issue.project_id,
                        model_data=updated_model.model_data
                    )
                    world_model = updated_model

        self.session.commit()

        # Re-run evaluation and ranking phases
        try:
            result = self.run_service.execute_evaluate_and_rank_phase(issue.run_id)

            # Record provenance
            if problem_spec:
                provenance_entry = build_provenance_entry(
                    event_type="feedback_patch",
                    actor="system",
                    source="issue_service:apply_partial_rerun",
                    description=f"Partial rerun executed for run {issue.run_id}",
                    reference_ids=[issue.id, issue.run_id],
                    metadata={"action": "partial_rerun", "patches_applied": patches_applied},
                )
                if problem_spec.provenance_log is None:
                    problem_spec.provenance_log = []
                problem_spec.provenance_log.append(provenance_entry)
                self.session.commit()

            # Mark issue as resolved
            repo_update_issue(
                self.session,
                issue_id=issue_id,
                resolution_status=IssueResolutionStatus.RESOLVED.value,
                resolved_at=datetime.utcnow(),
            )

            return {
                "status": "success",
                "action": "partial_rerun",
                "issue_id": issue_id,
                "patches_applied": patches_applied,
                "rerun_result": result,
            }
        except Exception as e:
            logger.error(f"Error in partial_rerun for issue {issue_id}: {e}", exc_info=True)
            raise

    def apply_full_rerun(
        self,
        issue_id: str,
        patch_data: dict[str, Any],
        run_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Apply catastrophic fixes: update spec/model, create new full run.

        Args:
            issue_id: Issue ID
            patch_data: Dict with updates to apply
            run_config: Optional run configuration for new run

        Returns:
            dict with remediation result
        """
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        # Apply patches
        problem_spec = get_problem_spec(self.session, issue.project_id)
        patches_applied = []

        if "problem_spec" in patch_data and problem_spec:
            patches_applied.append("problem_spec")
            # Record provenance
            provenance_entry = build_provenance_entry(
                event_type="feedback_patch",
                actor="system",
                source="issue_service:apply_full_rerun",
                description=f"ProblemSpec updated due to catastrophic issue {issue_id}",
                reference_ids=[issue.id, issue.project_id],
                metadata={"patch_type": "problem_spec"},
            )
            if problem_spec.provenance_log is None:
                problem_spec.provenance_log = []
            problem_spec.provenance_log.append(provenance_entry)

        if "world_model" in patch_data:
            world_model = get_world_model(self.session, issue.project_id)
            if world_model:
                patches_applied.append("world_model")
                if isinstance(world_model.model_data, dict):
                    if "provenance" not in world_model.model_data:
                        world_model.model_data["provenance"] = []
                    provenance_entry = build_provenance_entry(
                        event_type="feedback_patch",
                        actor="system",
                        source="issue_service:apply_full_rerun",
                        description=f"WorldModel updated due to catastrophic issue {issue_id}",
                        reference_ids=[issue.id, issue.project_id],
                        metadata={"patch_type": "world_model"},
                    )
                    world_model.model_data["provenance"].append(provenance_entry)

        self.session.commit()

        # Create new run
        config = run_config or {}
        mode = config.get("mode", RunMode.FULL_SEARCH.value)
        num_candidates = config.get("num_candidates", 5)
        num_scenarios = config.get("num_scenarios", 8)

        new_run = create_run(
            self.session,
            project_id=issue.project_id,
            mode=mode,
            config={
                "num_candidates": num_candidates,
                "num_scenarios": num_scenarios,
                **{k: v for k, v in config.items() if k not in ["mode", "num_candidates", "num_scenarios"]},
            },
        )

        # Execute full pipeline
        try:
            result = self.run_service.execute_full_pipeline(
                run_id=new_run.id,
                num_candidates=num_candidates,
                num_scenarios=num_scenarios,
            )

            # Record provenance
            if problem_spec:
                provenance_entry = build_provenance_entry(
                    event_type="feedback_patch",
                    actor="system",
                    source="issue_service:apply_full_rerun",
                    description=f"Full rerun executed due to issue {issue_id}",
                    reference_ids=[issue.id, new_run.id],
                    metadata={
                        "action": "full_rerun",
                        "patches_applied": patches_applied,
                        "new_run_id": new_run.id,
                    },
                )
                if problem_spec.provenance_log is None:
                    problem_spec.provenance_log = []
                problem_spec.provenance_log.append(provenance_entry)
                self.session.commit()

            # Mark issue as resolved
            repo_update_issue(
                self.session,
                issue_id=issue_id,
                resolution_status=IssueResolutionStatus.RESOLVED.value,
                resolved_at=datetime.utcnow(),
            )

            return {
                "status": "success",
                "action": "full_rerun",
                "issue_id": issue_id,
                "patches_applied": patches_applied,
                "new_run_id": new_run.id,
                "rerun_result": result,
            }
        except Exception as e:
            logger.error(f"Error in full_rerun for issue {issue_id}: {e}", exc_info=True)
            raise

    def invalidate_candidates(
        self,
        issue_id: str,
        candidate_ids: list[str],
        reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Mark candidates as rejected due to catastrophic issue.

        Args:
            issue_id: Issue ID
            candidate_ids: List of candidate IDs to invalidate
            reason: Optional reason for invalidation

        Returns:
            dict with remediation result
        """
        issue = get_issue(self.session, issue_id)
        if issue is None:
            raise ValueError(f"Issue not found: {issue_id}")

        invalidated = []
        for candidate_id in candidate_ids:
            candidate = get_candidate(self.session, candidate_id)
            if candidate is None:
                logger.warning(f"Candidate {candidate_id} not found, skipping")
                continue

            if candidate.project_id != issue.project_id:
                logger.warning(
                    f"Candidate {candidate_id} does not belong to project {issue.project_id}, skipping"
                )
                continue

            # Update candidate status
            update_candidate(
                self.session,
                candidate_id=candidate_id,
                status=CandidateStatus.REJECTED.value,
            )

            # Record provenance on candidate
            provenance_entry = build_provenance_entry(
                event_type="feedback_patch",
                actor="system",
                source="issue_service:invalidate_candidates",
                description=f"Candidate invalidated due to issue {issue_id}: {reason or 'Catastrophic issue'}",
                reference_ids=[issue.id, candidate_id],
                metadata={"reason": reason, "issue_id": issue_id},
            )
            append_candidate_provenance_entry(
                self.session,
                candidate_id=candidate_id,
                entry=provenance_entry,
            )
            invalidated.append(candidate_id)

        self.session.commit()

        # Mark issue as resolved
        repo_update_issue(
            self.session,
            issue_id=issue_id,
            resolution_status=IssueResolutionStatus.RESOLVED.value,
            resolved_at=datetime.utcnow(),
        )

        return {
            "status": "success",
            "action": "invalidate_candidates",
            "issue_id": issue_id,
            "invalidated_candidates": invalidated,
            "reason": reason,
        }

