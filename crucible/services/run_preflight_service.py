"""
Run preflight validation service.

Evaluates whether a proposed run configuration is ready to execute, applying
basic prerequisite checks (ProblemSpec, WorldModel) and heuristic warnings.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from crucible.db.repositories import (
    get_problem_spec,
    get_world_model,
)
from crucible.models.run_contracts import (
    RunBlockerCode,
    RunPreflightResult,
    RunWarningCode,
)


class RunPreflightService:
    """Service that validates run configurations prior to execution."""

    def __init__(self, session: Session):
        self.session = session

    def preflight(
        self,
        project_id: str,
        mode: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> RunPreflightResult:
        """Return readiness information for a prospective run."""
        parameters = parameters or {}
        normalized_config = self._normalize_parameters(parameters)

        blockers: list[RunBlockerCode] = []
        warnings: list[RunWarningCode] = []
        prerequisites = self._evaluate_prerequisites(project_id)

        if not prerequisites["problem_spec"]:
            blockers.append(RunBlockerCode.MISSING_PROBLEM_SPEC)
        if not prerequisites["world_model"]:
            blockers.append(RunBlockerCode.MISSING_WORLD_MODEL)

        if normalized_config["num_candidates"] > 20:
            warnings.append(RunWarningCode.LARGE_CANDIDATE_COUNT)
        if normalized_config["num_scenarios"] > 20:
            warnings.append(RunWarningCode.LARGE_CANDIDATE_COUNT)

        ready = len(blockers) == 0

        return RunPreflightResult(
            ready=ready,
            blockers=blockers,
            warnings=warnings,
            normalized_config=normalized_config,
            prerequisites=prerequisites,
            notes=[],
        )

    def _normalize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce numeric parameters into safe defaults."""
        num_candidates = parameters.get("num_candidates", 5)
        num_scenarios = parameters.get("num_scenarios", 8)

        def _clamp(value: Any, minimum: int, maximum: int) -> int:
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                numeric = minimum
            return max(minimum, min(maximum, numeric))

        num_candidates = _clamp(num_candidates, 1, 50)
        num_scenarios = _clamp(num_scenarios, 1, 50)

        return {
            "num_candidates": num_candidates,
            "num_scenarios": num_scenarios,
            "budget_tokens": parameters.get("budget_tokens"),
            "budget_usd": parameters.get("budget_usd"),
            "max_runtime_s": parameters.get("max_runtime_s"),
        }

    def _evaluate_prerequisites(self, project_id: str) -> Dict[str, bool]:
        """Check for required prerequisite artifacts."""
        problem_spec = get_problem_spec(self.session, project_id)
        world_model = get_world_model(self.session, project_id)

        return {
            "problem_spec": problem_spec is not None,
            "world_model": world_model is not None,
        }


