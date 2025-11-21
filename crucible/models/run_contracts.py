"""
Shared run-contract data structures.

These dataclasses and enums capture the structured metadata shared between
backend services, API responses, and frontend consumers for the run advisor
workflow (recommended configs, UI triggers, summaries, and preflight results).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
import enum
import uuid
from typing import Any, Dict, List, Optional


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime to ISO format if needed."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _deserialize_datetime(value: Optional[str]) -> Optional[datetime]:
    """Best-effort conversion from ISO string to datetime."""
    if value is None or isinstance(value, datetime):
        return value
    # Handle trailing Z (Zulu) by converting to +00:00
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class RunTriggerSource(str, enum.Enum):
    """Origin of a run trigger."""

    RUN_CONFIG_PANEL = "run_config_panel"
    API_CLIENT = "api_client"
    INTEGRATION_TEST = "integration_test"
    CLI_TOOL = "cli_tool"


class RunRecommendationStatus(str, enum.Enum):
    """Availability status for a recommended run config."""

    READY = "ready"
    BLOCKED = "blocked"
    INFO = "info"


class RunBlockerCode(str, enum.Enum):
    """Codes describing why a run cannot start."""

    MISSING_PROBLEM_SPEC = "missing_problem_spec"
    MISSING_WORLD_MODEL = "missing_world_model"
    INSUFFICIENT_CANDIDATES = "insufficient_candidates"
    VALIDATION_ERROR = "validation_error"


class RunWarningCode(str, enum.Enum):
    """Non-blocking warnings about proposed run settings."""

    HIGH_BUDGET = "high_budget"
    LARGE_CANDIDATE_COUNT = "large_candidate_count"
    DEPRECATED_MODE = "deprecated_mode"


@dataclass
class RunRecommendationParameters:
    """Core numeric parameters used within a run recommendation."""

    num_candidates: Optional[int] = None
    num_scenarios: Optional[int] = None
    seed_candidate_ids: List[str] = field(default_factory=list)
    budget_tokens: Optional[int] = None
    budget_usd: Optional[float] = None
    max_runtime_s: Optional[int] = None


@dataclass
class RecommendedRunConfig:
    """Structured metadata the Architect surfaces when advising a run."""

    version: int = 1
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    chat_session_id: Optional[str] = None
    source_message_id: Optional[str] = None
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: RunRecommendationStatus = RunRecommendationStatus.READY
    mode: Optional[str] = None
    parameters: RunRecommendationParameters = field(default_factory=RunRecommendationParameters)
    prerequisites: Dict[str, bool] = field(default_factory=dict)
    estimated_cost: Dict[str, Optional[float]] = field(default_factory=dict)
    rationale: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    blockers: List[RunBlockerCode] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        data = asdict(self)
        data["generated_at"] = _serialize_datetime(self.generated_at)
        data["expires_at"] = _serialize_datetime(self.expires_at)
        data["status"] = self.status.value
        data["blockers"] = [blocker.value for blocker in self.blockers]
        return data

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RecommendedRunConfig":
        """Instantiate from a dict (e.g., stored JSON)."""
        payload = dict(payload or {})
        generated_at = _deserialize_datetime(payload.get("generated_at"))
        expires_at = _deserialize_datetime(payload.get("expires_at"))
        status = RunRecommendationStatus(payload.get("status", RunRecommendationStatus.READY.value))
        blockers = [
            RunBlockerCode(item)
            for item in payload.get("blockers", [])
            if item in RunBlockerCode._value2member_map_
        ]
        parameters = RunRecommendationParameters(**payload.get("parameters", {}))
        return cls(
            version=payload.get("version", 1),
            recommendation_id=payload.get("recommendation_id", str(uuid.uuid4())),
            project_id=payload.get("project_id"),
            chat_session_id=payload.get("chat_session_id"),
            source_message_id=payload.get("source_message_id"),
            generated_at=generated_at,
            expires_at=expires_at,
            status=status,
            mode=payload.get("mode"),
            parameters=parameters,
            prerequisites=payload.get("prerequisites", {}),
            estimated_cost=payload.get("estimated_cost", {}),
            rationale=payload.get("rationale"),
            notes=payload.get("notes", []),
            blockers=blockers,
            details=payload.get("details", {}),
        )


@dataclass
class RunSummaryCandidate:
    """Top candidate summary included in post-run metadata."""

    candidate_id: str
    label: Optional[str] = None
    I: Optional[float] = None
    P: Optional[float] = None
    R: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class RunSummary:
    """Structured payload stored in post-run summary chat messages."""

    run_id: str
    project_id: str
    mode: Optional[str] = None
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    counts: Dict[str, int] = field(default_factory=dict)
    top_candidates: List[RunSummaryCandidate] = field(default_factory=list)
    links: Dict[str, str] = field(default_factory=dict)
    summary_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["started_at"] = _serialize_datetime(self.started_at)
        data["completed_at"] = _serialize_datetime(self.completed_at)
        data["top_candidates"] = [asdict(candidate) for candidate in self.top_candidates]
        return data

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RunSummary":
        payload = dict(payload or {})
        top_candidates = [
            RunSummaryCandidate(**candidate) for candidate in payload.get("top_candidates", [])
        ]
        return cls(
            run_id=payload.get("run_id"),
            project_id=payload.get("project_id"),
            mode=payload.get("mode"),
            status=payload.get("status"),
            started_at=_deserialize_datetime(payload.get("started_at")),
            completed_at=_deserialize_datetime(payload.get("completed_at")),
            duration_seconds=payload.get("duration_seconds"),
            counts=payload.get("counts", {}),
            top_candidates=top_candidates,
            links=payload.get("links", {}),
            summary_label=payload.get("summary_label"),
        )


@dataclass
class RunPreflightResult:
    """Response envelope for run configuration preflight checks."""

    ready: bool
    blockers: List[RunBlockerCode] = field(default_factory=list)
    warnings: List[RunWarningCode] = field(default_factory=list)
    normalized_config: Dict[str, Any] = field(default_factory=dict)
    prerequisites: Dict[str, bool] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "blockers": [b.value for b in self.blockers],
            "warnings": [w.value for w in self.warnings],
            "normalized_config": self.normalized_config,
            "prerequisites": self.prerequisites,
            "notes": self.notes,
        }


