"""
FastAPI application for Int Crucible backend.

Provides HTTP API endpoints for the Int Crucible system, integrating
with Kosmos for agent orchestration and infrastructure.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import Generator
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field
import json
import asyncio

from crucible.config import get_config
from crucible.db.session import get_session
from crucible.services.problemspec_service import ProblemSpecService
from crucible.services.worldmodel_service import WorldModelService
from crucible.services.designer_service import DesignerService
from crucible.services.scenario_service import ScenarioService
from crucible.services.evaluator_service import EvaluatorService
from crucible.services.ranker_service import RankerService
from crucible.services.run_service import RunService
from crucible.services.guidance_service import GuidanceService
from crucible.services.run_preflight_service import RunPreflightService
from crucible.services.snapshot_service import SnapshotService
from sqlalchemy.orm import Session
from sqlalchemy import func
from crucible.models.run_contracts import RunTriggerSource
from crucible.db.models import Run, RunStatus
from crucible.core.provenance import summarize_provenance_log

# Initialize logging
logging.basicConfig(
    level=get_config().log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting Int Crucible API server")
    
    # Initialize Kosmos database connection
    try:
        from kosmos.db import init_from_config
        init_from_config()
        logger.info("Kosmos database initialized successfully")
        
        # Force Crucible metadata refresh to sync with database schema
        # This ensures SQLAlchemy sees columns added by migrations
        try:
            from crucible.db.session import init_from_config as crucible_init
            crucible_init()
            logger.info("Crucible database models initialized and metadata refreshed")
        except Exception as e:
            logger.warning(f"Could not refresh Crucible metadata: {e}")
    except Exception as e:
        logger.warning(f"Could not initialize Kosmos database: {e}")
        logger.warning("Some features may not be available")
    
    yield
    
    # Shutdown (if needed)
    logger.info("Shutting down Int Crucible API server")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Int Crucible API",
    description="A general multi-agent reasoning system",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
# Allow all origins in development (for local network access)
# In production, this should be restricted to specific domains
# Note: When using allow_origins=["*"], allow_credentials must be False
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers to ensure CORS headers are added to error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

from sqlalchemy.exc import SQLAlchemyError

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy exceptions with CORS headers."""
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "name": "Int Crucible",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "int-crucible"
    }


@app.get("/kosmos/agents")
async def list_kosmos_agents() -> Dict[str, Any]:
    """
    List available Kosmos agents.
    
    This is a smoke test to verify Kosmos integration is working.
    """
    try:
        from kosmos.agents.registry import AgentRegistry
        
        registry = AgentRegistry()
        agents = registry.list_agents()
        
        return {
            "status": "success",
            "agents": agents,
            "count": len(agents)
        }
    except ImportError as e:
        logger.error(f"Failed to import Kosmos: {e}")
        raise HTTPException(
            status_code=503,
            detail="Kosmos integration not available. Ensure Kosmos is installed."
        )
    except Exception as e:
        logger.error(f"Error listing Kosmos agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error accessing Kosmos agents: {str(e)}"
        )


@app.post("/kosmos/test")
async def test_kosmos_agent() -> Dict[str, Any]:
    """
    Test endpoint that invokes a simple Kosmos operation.
    
    This performs a minimal smoke test to verify Kosmos integration.
    """
    try:
        from kosmos.config import get_config as get_kosmos_config
        from kosmos.agents.registry import AgentRegistry
        
        # Get Kosmos config to verify it's accessible
        kosmos_config = get_kosmos_config()
        
        # Get agent registry
        registry = AgentRegistry()
        agents = registry.list_agents()
        
        return {
            "status": "success",
            "message": "Kosmos integration is working",
            "kosmos_config_loaded": True,
            "available_agents": agents,
            "llm_provider": kosmos_config.llm.provider if hasattr(kosmos_config, 'llm') else "unknown"
        }
    except ImportError as e:
        logger.error(f"Failed to import Kosmos: {e}")
        raise HTTPException(
            status_code=503,
            detail="Kosmos integration not available. Ensure Kosmos is installed with: pip install -e vendor/kosmos"
        )
    except Exception as e:
        logger.error(f"Error testing Kosmos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error testing Kosmos integration: {str(e)}"
        )


# Dependency injection for database session
def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    with get_session() as session:
        yield session


# Pydantic models for Project API
class ProjectCreateRequest(BaseModel):
    """Request model for project creation."""
    title: str
    description: Optional[str] = None


class ProjectCreateFromDescriptionRequest(BaseModel):
    """Request model for creating project from description (chat-first flow)."""
    description: str
    suggested_title: Optional[str] = None


class ProjectResponse(BaseModel):
    """Response model for Project."""
    id: str
    title: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Pydantic models for ChatSession API
class ChatSessionCreateRequest(BaseModel):
    """Request model for chat session creation."""
    project_id: str
    title: Optional[str] = None
    mode: str = "setup"
    run_id: Optional[str] = None
    candidate_id: Optional[str] = None


class ChatSessionUpdateRequest(BaseModel):
    """Request model for chat session update."""
    title: Optional[str] = None
    mode: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Response model for ChatSession."""
    id: str
    project_id: str
    title: Optional[str] = None
    mode: str
    run_id: Optional[str] = None
    candidate_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Pydantic models for Message API
class MessageCreateRequest(BaseModel):
    """Request model for message creation."""
    content: str
    role: str = "user"
    message_metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    """Response model for Message."""
    id: str
    chat_session_id: str
    role: str
    content: str
    message_metadata: Optional[dict] = None
    created_at: Optional[str] = None


# Pydantic models for Run API
class RunCreateRequest(BaseModel):
    """Request model for run creation."""
    project_id: str
    mode: str = "full_search"
    config: Optional[dict] = None
    chat_session_id: Optional[str] = None
    recommended_message_id: Optional[str] = None
    recommended_config_snapshot: Optional[dict] = None
    ui_trigger_id: str
    ui_trigger_source: RunTriggerSource = RunTriggerSource.RUN_CONFIG_PANEL
    ui_trigger_metadata: Optional[dict] = None


class RunResponse(BaseModel):
    """Response model for Run."""
    id: str
    project_id: str
    mode: str
    config: Optional[dict] = None
    recommended_message_id: Optional[str] = None
    recommended_config_snapshot: Optional[dict] = None
    ui_trigger_id: Optional[str] = None
    ui_trigger_source: Optional[str] = None
    ui_trigger_metadata: Optional[dict] = None
    ui_triggered_at: Optional[str] = None
    run_summary_message_id: Optional[str] = None
    chat_session_id: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    candidate_count: Optional[int] = None
    scenario_count: Optional[int] = None
    evaluation_count: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    llm_usage: Optional[Dict[str, Any]] = None
    error_summary: Optional[str] = None


class RunSummaryListResponse(BaseModel):
    """Paginated response for run history."""
    runs: List[RunResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
    next_offset: Optional[int] = None


class RunPreflightRequest(BaseModel):
    """Request model for run preflight validation."""
    mode: str = "full_search"
    parameters: Optional[dict] = None
    chat_session_id: Optional[str] = None
    recommended_message_id: Optional[str] = None


class RunPreflightResponse(BaseModel):
    """Response model for run preflight validation."""
    ready: bool
    blockers: List[str]
    warnings: List[str]
    normalized_config: Dict[str, Any]
    prerequisites: Dict[str, bool]
    notes: List[str]


def _serialize_enum(value):
    """Convert Enum-like values to primitive types."""
    if hasattr(value, "value"):
        return value.value
    return value


def _serialize_dt(value):
    return value.isoformat() if value else None


def _serialize_run(run) -> RunResponse:
    """Convert SQLAlchemy Run model to RunResponse."""
    # Handle chat_session_id gracefully - it might not exist in older runs or if column is missing
    chat_session_id = getattr(run, 'chat_session_id', None)

    return RunResponse(
        id=run.id,
        project_id=run.project_id,
        mode=_serialize_enum(run.mode),
        config=run.config,
        recommended_message_id=run.recommended_message_id,
        recommended_config_snapshot=run.recommended_config_snapshot,
        ui_trigger_id=run.ui_trigger_id,
        ui_trigger_source=_serialize_enum(run.ui_trigger_source),
        ui_trigger_metadata=run.ui_trigger_metadata,
        ui_triggered_at=_serialize_dt(run.ui_triggered_at),
        run_summary_message_id=run.run_summary_message_id,
        chat_session_id=chat_session_id,
        status=_serialize_enum(run.status),
        created_at=_serialize_dt(run.created_at),
        started_at=_serialize_dt(run.started_at),
        completed_at=_serialize_dt(run.completed_at),
        duration_seconds=getattr(run, "duration_seconds", None),
        candidate_count=getattr(run, "candidate_count", None),
        scenario_count=getattr(run, "scenario_count", None),
        evaluation_count=getattr(run, "evaluation_count", None),
        metrics=getattr(run, "metrics", None),
        llm_usage=getattr(run, "llm_usage", None),
        error_summary=getattr(run, "error_summary", None),
    )


class ProvenanceEventSummary(BaseModel):
    """Summary of the latest provenance event for quick display."""
    type: Optional[str] = None
    timestamp: Optional[str] = None
    actor: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None


class CandidateProvenanceSummary(BaseModel):
    """Summary information about a candidate's provenance log."""
    event_count: int
    last_event: Optional[ProvenanceEventSummary] = None


class CandidateParentSummary(BaseModel):
    """Basic info about a parent candidate."""
    id: str
    mechanism_description: Optional[str] = None
    status: Optional[str] = None


class CandidateProvenanceEntry(BaseModel):
    """Full provenance entry information."""
    type: str
    timestamp: str
    actor: str
    source: Optional[str] = None
    description: Optional[str] = None
    reference_ids: Optional[List[str]] = None
    metadata: Optional[dict] = None


class EvaluationSummary(BaseModel):
    """Summary of an evaluation for candidate detail view."""
    id: str
    scenario_id: str
    P: Optional[dict] = None
    R: Optional[dict] = None
    constraint_satisfaction: Optional[dict] = None
    explanation: Optional[str] = None


class CandidateDetailResponse(BaseModel):
    """Detailed candidate response with provenance and evaluations.
    
    The `scores` dict may contain:
    - P, R, I: Prediction quality, resource cost, and intelligence metric scores
    - ranking_explanation: Optional string (1-3 sentences) explaining the candidate's rank
    - ranking_factors: Optional dict with top_positive_factors and top_negative_factors lists
    """
    id: str
    run_id: str
    project_id: str
    origin: str
    status: Optional[str] = None
    mechanism_description: str
    predicted_effects: Optional[dict] = None
    scores: Optional[dict] = None
    constraint_flags: Optional[List[str]] = None
    parent_ids: List[str] = Field(default_factory=list)
    parent_summaries: List[CandidateParentSummary] = Field(default_factory=list)
    provenance_log: List[CandidateProvenanceEntry] = Field(default_factory=list)
    evaluations: List[EvaluationSummary] = Field(default_factory=list)


class CandidateResponse(BaseModel):
    """Response model for Candidate.
    
    The `scores` dict may contain:
    - P, R, I: Prediction quality, resource cost, and intelligence metric scores
    - ranking_explanation: Optional string (1-3 sentences) explaining the candidate's rank
    - ranking_factors: Optional dict with top_positive_factors and top_negative_factors lists
    """
    id: str
    run_id: str
    project_id: str
    origin: str
    status: Optional[str] = None
    mechanism_description: str
    predicted_effects: Optional[dict] = None
    scores: Optional[dict] = None
    constraint_flags: Optional[List[str]] = None
    parent_ids: List[str] = Field(default_factory=list)
    provenance_summary: Optional[CandidateProvenanceSummary] = None


def _to_candidate_provenance_summary(
    provenance_log: list[dict] | None,
) -> CandidateProvenanceSummary | None:
    """Convert a provenance log into the summary model."""
    summary_data = summarize_provenance_log(provenance_log)
    if not summary_data:
        return None

    last_event_data = summary_data.get("last_event") or {}
    last_event = None
    if last_event_data:
        last_event = ProvenanceEventSummary(
            type=last_event_data.get("type"),
            timestamp=last_event_data.get("timestamp"),
            actor=last_event_data.get("actor"),
            source=last_event_data.get("source"),
            description=last_event_data.get("description"),
        )

    return CandidateProvenanceSummary(
        event_count=summary_data["event_count"],
        last_event=last_event,
    )


class ProjectProvenanceResponse(BaseModel):
    """Aggregated provenance data for a project."""
    project_id: str
    problem_spec: List[dict]
    world_model: List[dict]
    candidates: List[dict]


# Pydantic models for ProblemSpec API
class ProblemSpecRefineRequest(BaseModel):
    """Request model for ProblemSpec refinement."""
    chat_session_id: Optional[str] = None
    message_limit: int = 20


class ProblemSpecResponse(BaseModel):
    """Response model for ProblemSpec."""
    id: str
    project_id: str
    constraints: List[dict]
    goals: List[str]
    resolution: str
    mode: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    provenance_log: List[dict] = Field(default_factory=list)


class ProblemSpecRefineResponse(BaseModel):
    """Response model for ProblemSpec refinement."""
    updated_spec: dict
    follow_up_questions: List[str]
    reasoning: str
    ready_to_run: bool
    applied: bool
    spec_delta: Optional[dict] = None


# Pydantic models for WorldModel API
class WorldModelRefineRequest(BaseModel):
    """Request model for WorldModel refinement."""
    chat_session_id: Optional[str] = None
    message_limit: int = 20


class WorldModelResponse(BaseModel):
    """Response model for WorldModel."""
    id: str
    project_id: str
    model_data: dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorldModelRefineResponse(BaseModel):
    """Response model for WorldModel refinement."""
    updated_model: dict
    changes: List[dict]
    reasoning: str
    ready_to_run: bool
    applied: bool
    world_model_delta: Optional[dict] = None


class WorldModelUpdateRequest(BaseModel):
    """Request model for manual WorldModel update."""
    model_data: dict
    source: str = "manual_edit"


# Pydantic models for Designer API
class DesignerGenerateRequest(BaseModel):
    """Request model for candidate generation."""
    num_candidates: int = 5


class DesignerGenerateResponse(BaseModel):
    """Response model for candidate generation."""
    candidates: List[dict]
    reasoning: str
    count: int


# Pydantic models for Scenario API
class ScenarioGenerateRequest(BaseModel):
    """Request model for scenario suite generation."""
    num_scenarios: int = 8


class ScenarioGenerateResponse(BaseModel):
    """Response model for scenario suite generation."""
    scenario_suite: dict
    scenarios: List[dict]
    reasoning: str
    count: int


# Pydantic models for Run orchestration API
class RunDesignScenarioRequest(BaseModel):
    """Request model for design + scenario generation."""
    num_candidates: int = 5
    num_scenarios: int = 8


class RunDesignScenarioResponse(BaseModel):
    """Response model for design + scenario generation."""
    candidates: dict
    scenarios: dict
    status: str


# Pydantic models for Evaluator API
class EvaluatorEvaluateRequest(BaseModel):
    """Request model for evaluation (no parameters needed, uses existing candidates and scenarios)."""


class EvaluatorEvaluateResponse(BaseModel):
    """Response model for evaluation."""
    evaluations: List[dict]
    count: int
    candidates_evaluated: int
    scenarios_used: int


# Pydantic models for Ranker API
class RankerRankRequest(BaseModel):
    """Request model for ranking (no parameters needed, uses existing evaluations)."""


class RankerRankResponse(BaseModel):
    """Response model for ranking."""
    ranked_candidates: List[dict]
    count: int
    hard_constraint_violations: List[str]


# Pydantic models for full pipeline API
class RunEvaluateRankRequest(BaseModel):
    """Request model for evaluate + rank phase (no parameters needed)."""


class RunEvaluateRankResponse(BaseModel):
    """Response model for evaluate + rank phase."""
    evaluations: dict
    rankings: dict
    status: str


class RunFullPipelineRequest(BaseModel):
    """Request model for full pipeline execution."""
    num_candidates: int = 5
    num_scenarios: int = 8


class RunFullPipelineResponse(BaseModel):
    """Response model for full pipeline execution."""
    candidates: dict
    scenarios: dict
    evaluations: dict
    rankings: dict
    status: str


# Pydantic models for Guidance API
class GuidanceRequest(BaseModel):
    """Request model for guidance."""
    user_query: Optional[str] = None
    message_limit: int = 5


class GuidanceResponse(BaseModel):
    """Response model for guidance."""
    guidance_message: str
    suggested_actions: List[str]
    workflow_progress: Dict[str, Any]


class WorkflowStateResponse(BaseModel):
    """Response model for workflow state."""
    has_problem_spec: bool
    has_world_model: bool
    has_runs: bool
    run_count: int
    project_title: Optional[str]
    project_description: Optional[str]


# Pydantic models for Snapshot API
class SnapshotCreateRequest(BaseModel):
    """Request model for snapshot creation."""
    project_id: str
    run_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    invariants: Optional[List[Dict[str, Any]]] = None
    include_chat_context: bool = True
    max_chat_messages: int = 10


class SnapshotResponse(BaseModel):
    """Response model for snapshot."""
    id: str
    name: str
    description: Optional[str]
    tags: List[str]
    project_id: str
    run_id: Optional[str]
    snapshot_data: Dict[str, Any]
    reference_metrics: Optional[Dict[str, Any]]
    invariants: List[Dict[str, Any]]
    version: str
    created_at: Optional[str]
    updated_at: Optional[str]


class SnapshotReplayRequest(BaseModel):
    """Request model for snapshot replay."""
    phases: str = "full"  # "full", "design", "evaluate"
    num_candidates: Optional[int] = None
    num_scenarios: Optional[int] = None
    reuse_project: bool = False


class SnapshotReplayResponse(BaseModel):
    """Response model for snapshot replay."""
    replay_run_id: str
    project_id: str
    status: str
    results: Dict[str, Any]


class SnapshotTestRequest(BaseModel):
    """Request model for snapshot test run."""
    snapshot_ids: Optional[List[str]] = None  # None = all snapshots
    options: Optional[Dict[str, Any]] = None


class SnapshotTestResponse(BaseModel):
    """Response model for snapshot test run."""
    summary: Dict[str, Any]
    results: List[Dict[str, Any]]
    total_cost_usd: float


# Project endpoints
@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db)
) -> List[ProjectResponse]:
    """
    List all projects.
    
    Returns:
        List of projects
    """
    try:
        from crucible.db.repositories import list_projects as repo_list_projects
        
        projects = repo_list_projects(db)
        return [
            ProjectResponse(
                id=p.id,
                title=p.title,
                description=p.description,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
            for p in projects
        ]
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing projects: {str(e)}"
        )


def _infer_project_title(description: str) -> str:
    """
    Infer a project title from a description.
    
    Uses a simple heuristic: take the first sentence or first 50 characters,
    clean it up, and use as title. Falls back to "New Project" if description is empty.
    
    Args:
        description: Project description text
        
    Returns:
        Inferred project title
    """
    if not description or not description.strip():
        return "New Project"
    
    # Clean up the description
    desc = description.strip()
    
    # Try to extract first sentence (up to first period, exclamation, or question mark)
    import re
    sentence_match = re.match(r'^([^.!?]+[.!?]?)', desc)
    if sentence_match:
        title = sentence_match.group(1).strip()
        # Remove trailing punctuation if it's just one character
        if len(title) > 1 and title[-1] in '.!?':
            title = title[:-1].strip()
    else:
        # No sentence boundary found, take first 50 characters
        title = desc[:50].strip()
    
    # Clean up: remove extra whitespace, limit length
    title = re.sub(r'\s+', ' ', title)
    if len(title) > 60:
        title = title[:57] + "..."
    
    # Ensure we have something
    if not title or len(title) < 3:
        return "New Project"
    
    return title


@app.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    Create a new project.
    
    Args:
        request: Project creation request
        db: Database session
        
    Returns:
        Created project
    """
    try:
        from crucible.db.repositories import create_project as repo_create_project
        
        project = repo_create_project(
            db,
            title=request.title,
            description=request.description
        )
        
        return ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating project: {str(e)}"
        )


@app.post("/projects/from-description", response_model=ProjectResponse)
async def create_project_from_description(
    request: ProjectCreateFromDescriptionRequest,
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    Create a new project from a free-text description (chat-first flow).
    
    Infers a project title from the description if not provided.
    Also creates an initial chat session for the project.
    
    Args:
        request: Project creation request with description
        db: Database session
        
    Returns:
        Created project with initial chat session
    """
    try:
        from crucible.db.repositories import (
            create_project as repo_create_project,
            update_project as repo_update_project,
            get_project as repo_get_project,
            create_chat_session as repo_create_chat_session,
            create_message as repo_create_message
        )
        from crucible.db.models import MessageRole
        from crucible.services.guidance_service import GuidanceService
        from crucible.services.problemspec_service import ProblemSpecService
        
        # Create temporary project (we'll update it with generated name/description)
        temp_project = repo_create_project(
            db,
            title="New Project",
            description=request.description
        )
        
        # Create initial chat session
        chat_session = repo_create_chat_session(
            db,
            project_id=temp_project.id,
            title="Main Chat",
            mode="setup"
        )
        
        # Create user's initial message
        user_message = repo_create_message(
            db,
            chat_session_id=chat_session.id,
            role="user",
            content=request.description
        )
        
        # Generate better project name and description using LLM
        title = request.suggested_title
        description = request.description
        
        if not title:
            try:
                from kosmos.core.llm import get_provider
                import json
                import re
                
                llm_provider = get_provider()
                naming_prompt = f"""Based on this project description, generate a concise, professional project name (2-6 words) and a brief description (1-2 sentences) that summarizes the project goals.

User description: "{request.description[:500]}"

Respond with JSON only:
{{
    "title": "concise project name",
    "description": "brief project description"
}}"""
                
                response = llm_provider.generate(
                    naming_prompt,
                    system="You are a helpful assistant that creates clear, concise project names and descriptions.",
                    temperature=0.7,
                    max_tokens=200
                )
                
                # Parse JSON response (may be in code blocks)
                content = response.content.strip()
                # Try to extract JSON from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                
                parsed = json.loads(content)
                title = parsed.get("title", _infer_project_title(request.description))
                description = parsed.get("description", request.description)
            except Exception as e:
                logger.warning(f"Could not generate LLM project name/description: {e}. Using fallback.")
                title = _infer_project_title(request.description)
                description = request.description
        
        # Update project with generated title and description
        repo_update_project(
            db,
            project_id=temp_project.id,
            title=title,
            description=description
        )
        
        project = repo_get_project(db, temp_project.id)
        
        return ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating project from description: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating project from description: {str(e)}"
        )


class ProjectUpdateRequest(BaseModel):
    """Request model for project update."""
    title: Optional[str] = None
    description: Optional[str] = None


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    Get a project by ID.
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        Project data
    """
    try:
        from crucible.db.repositories import get_project as repo_get_project
        
        project = repo_get_project(db, project_id)
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )
        
        return ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting project: {str(e)}"
        )


@app.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    Update a project.
    
    Args:
        project_id: Project ID
        request: Project update request
        db: Database session
        
    Returns:
        Updated project
    """
    try:
        from crucible.db.repositories import update_project as repo_update_project
        
        project = repo_update_project(
            db,
            project_id=project_id,
            title=request.title,
            description=request.description
        )
        
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )
        
        return ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating project: {str(e)}"
        )


# ChatSession endpoints
@app.get("/chat-sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[ChatSessionResponse]:
    """
    List chat sessions, optionally filtered by project.
    
    Args:
        project_id: Optional project ID filter
        db: Database session
        
    Returns:
        List of chat sessions
    """
    try:
        from crucible.db.repositories import list_chat_sessions as repo_list_chat_sessions
        
        sessions = repo_list_chat_sessions(db, project_id)
        return [
            ChatSessionResponse(
                id=s.id,
                project_id=s.project_id,
                title=s.title,
                mode=s.mode.value if hasattr(s.mode, 'value') else str(s.mode),
                run_id=s.run_id,
                candidate_id=s.candidate_id,
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing chat sessions: {str(e)}"
        )


@app.get("/projects/{project_id}/chat-sessions", response_model=List[ChatSessionResponse])
async def list_project_chat_sessions(
    project_id: str,
    db: Session = Depends(get_db)
) -> List[ChatSessionResponse]:
    """
    List chat sessions for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        List of chat sessions
    """
    return await list_chat_sessions(project_id=project_id, db=db)


@app.post("/chat-sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionCreateRequest,
    db: Session = Depends(get_db)
) -> ChatSessionResponse:
    """
    Create a new chat session.
    
    Args:
        request: Chat session creation request
        db: Database session
        
    Returns:
        Created chat session
    """
    try:
        from crucible.db.repositories import create_chat_session as repo_create_chat_session
        
        session = repo_create_chat_session(
            db,
            project_id=request.project_id,
            title=request.title,
            mode=request.mode,
            run_id=request.run_id,
            candidate_id=request.candidate_id
        )
        
        return ChatSessionResponse(
            id=session.id,
            project_id=session.project_id,
            title=session.title,
            mode=session.mode.value if hasattr(session.mode, 'value') else str(session.mode),
            run_id=session.run_id,
            candidate_id=session.candidate_id,
            created_at=session.created_at.isoformat() if session.created_at else None,
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating chat session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating chat session: {str(e)}"
        )


@app.put("/chat-sessions/{chat_session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    chat_session_id: str,
    request: ChatSessionUpdateRequest,
    db: Session = Depends(get_db)
) -> ChatSessionResponse:
    """
    Update a chat session's title and/or mode.
    
    Args:
        chat_session_id: Chat session ID
        request: Update request with optional title and mode
        db: Database session
        
    Returns:
        Updated chat session
    """
    try:
        from crucible.db.repositories import update_chat_session as repo_update_chat_session
        
        session = repo_update_chat_session(
            db,
            chat_session_id=chat_session_id,
            title=request.title,
            mode=request.mode,
        )
        
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session not found: {chat_session_id}"
            )
        
        return ChatSessionResponse(
            id=session.id,
            project_id=session.project_id,
            title=session.title,
            mode=session.mode.value if hasattr(session.mode, 'value') else str(session.mode),
            run_id=session.run_id,
            candidate_id=session.candidate_id,
            created_at=session.created_at.isoformat() if session.created_at else None,
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating chat session: {str(e)}"
        )


@app.get("/chat-sessions/{chat_session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    chat_session_id: str,
    db: Session = Depends(get_db)
) -> ChatSessionResponse:
    """
    Get a chat session by ID.
    
    Args:
        chat_session_id: Chat session ID
        db: Database session
        
    Returns:
        Chat session data
    """
    try:
        from crucible.db.repositories import get_chat_session as repo_get_chat_session
        
        session = repo_get_chat_session(db, chat_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session not found: {chat_session_id}"
            )
        
        return ChatSessionResponse(
            id=session.id,
            project_id=session.project_id,
            title=session.title,
            mode=session.mode.value if hasattr(session.mode, 'value') else str(session.mode),
            run_id=session.run_id,
            candidate_id=session.candidate_id,
            created_at=session.created_at.isoformat() if session.created_at else None,
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting chat session: {str(e)}"
        )


# Message endpoints
@app.get("/chat-sessions/{chat_session_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    chat_session_id: str,
    db: Session = Depends(get_db)
) -> List[MessageResponse]:
    """
    List messages for a chat session.
    
    Args:
        chat_session_id: Chat session ID
        db: Database session
        
    Returns:
        List of messages
    """
    try:
        from crucible.db.repositories import list_messages as repo_list_messages
        
        messages = repo_list_messages(db, chat_session_id)
        return [
            MessageResponse(
                id=m.id,
                chat_session_id=m.chat_session_id,
                role=m.role,
                content=m.content,
                message_metadata=m.message_metadata,
                created_at=m.created_at.isoformat() if m.created_at else None,
            )
            for m in messages
        ]
    except Exception as e:
        logger.error(f"Error listing messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing messages: {str(e)}"
        )


@app.post("/chat-sessions/{chat_session_id}/messages", response_model=MessageResponse)
async def create_message(
    chat_session_id: str,
    request: MessageCreateRequest,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Create a new message in a chat session.
    
    Args:
        chat_session_id: Chat session ID
        request: Message creation request
        db: Database session
        
    Returns:
        Created message
    """
    try:
        from crucible.db.repositories import create_message as repo_create_message
        
        message = repo_create_message(
            db,
            chat_session_id=chat_session_id,
            role=request.role,
            content=request.content,
            message_metadata=request.message_metadata
        )
        
        return MessageResponse(
            id=message.id,
            chat_session_id=message.chat_session_id,
            role=message.role,
            content=message.content,
            message_metadata=message.message_metadata,
            created_at=message.created_at.isoformat() if message.created_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating message: {str(e)}"
        )


# Run endpoints
@app.get("/runs", response_model=List[RunResponse])
async def list_runs(
    project_id: Optional[str] = None,
    chat_session_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[RunResponse]:
    """
    List runs, optionally filtered by project and/or chat session.
    
    Args:
        project_id: Optional project ID filter
        chat_session_id: Optional chat session ID filter
        db: Database session
        
    Returns:
        List of runs
    """
    try:
        from crucible.db.repositories import list_runs as repo_list_runs
        
        runs = repo_list_runs(db, project_id=project_id, chat_session_id=chat_session_id)
        return [_serialize_run(r) for r in runs]
    except Exception as e:
        logger.error(f"Error listing runs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing runs: {str(e)}"
        )


@app.get("/projects/{project_id}/runs", response_model=List[RunResponse])
async def list_project_runs(
    project_id: str,
    chat_session_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[RunResponse]:
    """
    List runs for a project, optionally filtered by chat session.
    
    Args:
        project_id: Project ID
        chat_session_id: Optional chat session ID filter
        db: Database session
        
    Returns:
        List of runs
    """
    return await list_runs(project_id=project_id, chat_session_id=chat_session_id, db=db)


@app.get("/projects/{project_id}/runs/summary", response_model=RunSummaryListResponse)
async def get_project_run_summary(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[List[str]] = Query(default=None),
    chat_session_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> RunSummaryListResponse:
    """
    Return a paginated summary of recent runs for a project with observability fields.
    Optionally filtered by status and/or chat session.
    """
    try:
        from sqlalchemy import text
        from crucible.db.models import RunStatus
        
        # Use raw SQL to work around SQLAlchemy metadata cache issue
        # The metadata refresh should fix this, but using raw SQL as a reliable workaround
        # Build WHERE clause with named parameters for SQLAlchemy 2.0
        where_clauses = ["project_id = :project_id"]
        query_params = {"project_id": project_id}
        param_counter = 1
        
        if status:
            normalized_statuses = []
            for status_value in status:
                try:
                    normalized_statuses.append(RunStatus(status_value))
                except ValueError:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Invalid status filter: {status_value}",
                    )
            if normalized_statuses:
                status_values = [s.value for s in normalized_statuses]
                status_placeholders = ",".join([f":status_{i}" for i in range(len(status_values))])
                where_clauses.append(f"status IN ({status_placeholders})")
                for i, val in enumerate(status_values):
                    query_params[f"status_{i}"] = val
        
        if chat_session_id is not None:
            where_clauses.append("chat_session_id = :chat_session_id")
            query_params["chat_session_id"] = chat_session_id
        
        where_sql = " AND ".join(where_clauses)
        
        # Count total
        count_sql = f"SELECT COUNT(*) FROM crucible_runs WHERE {where_sql}"
        total = db.execute(text(count_sql), query_params).scalar()
        
        # Get runs - explicitly list columns including chat_session_id
        query_params["limit_param"] = limit
        query_params["offset_param"] = offset
        select_sql = f"""
            SELECT id, project_id, mode, config, status, created_at, started_at, completed_at,
                   recommended_message_id, recommended_config_snapshot, ui_trigger_id,
                   ui_trigger_source, ui_trigger_metadata, ui_triggered_at, run_summary_message_id,
                   chat_session_id, duration_seconds, candidate_count, scenario_count, evaluation_count, 
                   metrics, llm_usage, error_summary
            FROM crucible_runs
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit_param OFFSET :offset_param
        """
        
        rows = db.execute(text(select_sql), query_params).fetchall()
        
        # Convert rows to Run-like objects for serialization
        from datetime import datetime
        import json
        
        class RunProxy:
            def __init__(self, row_data):
                self.id = row_data[0]
                self.project_id = row_data[1]
                self.mode = row_data[2]
                self.config = self._parse_json(row_data[3])
                self.status = row_data[4]
                # Parse datetime strings to datetime objects if needed
                self.created_at = self._parse_datetime(row_data[5])
                self.started_at = self._parse_datetime(row_data[6])
                self.completed_at = self._parse_datetime(row_data[7])
                self.recommended_message_id = row_data[8]
                self.recommended_config_snapshot = self._parse_json(row_data[9])
                self.ui_trigger_id = row_data[10]
                self.ui_trigger_source = row_data[11]
                self.ui_trigger_metadata = self._parse_json(row_data[12])
                self.ui_triggered_at = self._parse_datetime(row_data[13])
                self.run_summary_message_id = row_data[14]
                self.chat_session_id = row_data[15]  # Now included
                self.duration_seconds = row_data[16]
                self.candidate_count = row_data[17]
                self.scenario_count = row_data[18]
                self.evaluation_count = row_data[19]
                self.metrics = self._parse_json(row_data[20])
                self.llm_usage = self._parse_json(row_data[21])
                self.error_summary = row_data[22]
            
            @staticmethod
            def _parse_datetime(value):
                """Parse datetime value - handles both datetime objects and ISO format strings."""
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        return None
                return value
            
            @staticmethod
            def _parse_json(value):
                """Parse JSON value - handles both dict/list objects and JSON strings."""
                if value is None:
                    return None
                if isinstance(value, (dict, list)):
                    return value
                if isinstance(value, str):
                    if value.lower() == 'null':
                        return None
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, ValueError):
                        return None
                return value
        
        runs = [RunProxy(row) for row in rows]

        has_more = offset + len(runs) < total
        next_offset = offset + len(runs) if has_more else None

        return RunSummaryListResponse(
            runs=[_serialize_run(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
            next_offset=next_offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project run summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting run summary: {str(e)}"
        )


@app.post("/projects/{project_id}/runs/preflight", response_model=RunPreflightResponse)
async def preflight_run(
    project_id: str,
    request: RunPreflightRequest,
    db: Session = Depends(get_db)
) -> RunPreflightResponse:
    """
    Validate whether a run configuration is ready to execute.
    """
    try:
        service = RunPreflightService(db)
        result = service.preflight(
            project_id=project_id,
            mode=request.mode,
            parameters=request.parameters,
        )
        return RunPreflightResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error during run preflight for project {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error validating run configuration: {str(e)}"
        )


@app.post("/runs", response_model=RunResponse)
async def create_run(
    request: RunCreateRequest,
    db: Session = Depends(get_db)
) -> RunResponse:
    """
    Create a new run.
    
    Args:
        request: Run creation request
        db: Database session
        
    Returns:
        Created run
    """
    try:
        from crucible.db.repositories import (
            create_run as repo_create_run,
            get_chat_session,
            get_message as repo_get_message,
        )

        if not request.ui_trigger_id:
            raise HTTPException(
                status_code=422,
                detail="ui_trigger_id is required to create a run."
            )

        trigger_source = request.ui_trigger_source
        if isinstance(trigger_source, str):
            try:
                trigger_source = RunTriggerSource(trigger_source)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid ui_trigger_source: {request.ui_trigger_source}"
                )

        if request.chat_session_id:
            chat_session = get_chat_session(db, request.chat_session_id)
            if chat_session is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chat session not found: {request.chat_session_id}"
                )
            if chat_session.project_id != request.project_id:
                raise HTTPException(
                    status_code=400,
                    detail="Chat session does not belong to the specified project."
                )

        if request.recommended_message_id:
            message = repo_get_message(db, request.recommended_message_id)
            if message is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Recommended message not found: {request.recommended_message_id}"
                )
            message_project_id = (
                message.chat_session.project_id if message.chat_session else None
            )
            if message_project_id and message_project_id != request.project_id:
                raise HTTPException(
                    status_code=400,
                    detail="Recommended message does not belong to the specified project."
                )
            if request.chat_session_id and message.chat_session_id != request.chat_session_id:
                raise HTTPException(
                    status_code=400,
                    detail="Recommended message does not belong to the provided chat session."
                )

        run = repo_create_run(
            db,
            project_id=request.project_id,
            mode=request.mode,
            config=request.config,
            recommended_message_id=request.recommended_message_id,
            recommended_config_snapshot=request.recommended_config_snapshot,
            ui_trigger_id=request.ui_trigger_id,
            ui_trigger_source=trigger_source.value if trigger_source else None,
            ui_trigger_metadata=request.ui_trigger_metadata,
            ui_triggered_at=datetime.utcnow(),
            chat_session_id=request.chat_session_id,
        )
        
        return _serialize_run(run)
    except Exception as e:
        logger.error(f"Error creating run: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating run: {str(e)}"
        )


@app.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    db: Session = Depends(get_db)
) -> RunResponse:
    """
    Get a run by ID.
    
    Args:
        run_id: Run ID
        db: Database session
        
    Returns:
        Run data
    """
    try:
        from crucible.db.repositories import get_run as repo_get_run
        
        run = repo_get_run(db, run_id)
        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}"
            )
        
        return _serialize_run(run)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting run: {str(e)}"
        )


@app.get("/runs/{run_id}/candidates", response_model=List[CandidateResponse])
async def list_run_candidates(
    run_id: str,
    db: Session = Depends(get_db)
) -> List[CandidateResponse]:
    """
    List candidates for a run.
    
    Args:
        run_id: Run ID
        db: Database session
        
    Returns:
        List of candidates with scores
    """
    try:
        from crucible.db.repositories import list_candidates as repo_list_candidates, get_run
        from crucible.services.ranker_service import RankerService
        
        # Verify run exists
        run = get_run(db, run_id)
        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}"
            )
        
        # Get candidates
        candidates = repo_list_candidates(db, run_id)
        
        # Ensure candidates are ranked (this will compute scores and explanations if not already computed)
        ranker_service = RankerService(db)
        try:
            # This will update candidate.scores in the database with explanations if ranking hasn't been done yet
            ranker_service.rank_candidates(run_id, run.project_id)
            # Refresh candidates to get updated scores
            candidates = repo_list_candidates(db, run_id)
        except Exception as e:
            # If ranking fails, just return candidates with existing scores
            logger.warning(f"Could not rank candidates for run {run_id}: {e}")
        
        # Build constraint flags from scores
        def _build_constraint_flags(scores: dict | None) -> List[str] | None:
            if not scores:
                return None
            constraint_satisfaction = scores.get("constraint_satisfaction", {})
            if not isinstance(constraint_satisfaction, dict):
                return None
            flags = [
                constraint_id
                for constraint_id, data in constraint_satisfaction.items()
                if isinstance(data, dict) and not data.get("satisfied", True)
            ]
            return flags or None
        
        return [
            CandidateResponse(
                id=c.id,
                run_id=c.run_id,
                project_id=c.project_id,
                origin=_serialize_enum(c.origin),
                status=_serialize_enum(c.status),
                mechanism_description=c.mechanism_description,
                predicted_effects=c.predicted_effects,
                scores=c.scores,  # Use candidate.scores directly (includes ranking_explanation and ranking_factors)
                constraint_flags=_build_constraint_flags(c.scores),
                parent_ids=c.parent_ids or [],
                provenance_summary=_to_candidate_provenance_summary(c.provenance_log),
            )
            for c in candidates
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing run candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing run candidates: {str(e)}"
        )


@app.get(
    "/runs/{run_id}/candidates/{candidate_id}",
    response_model=CandidateDetailResponse,
)
async def get_candidate_detail(
    run_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> CandidateDetailResponse:
    """
    Retrieve candidate detail including provenance and evaluations.
    """
    try:
        from crucible.db.repositories import (
            get_run as repo_get_run,
            get_candidate as repo_get_candidate,
            list_evaluations as repo_list_evaluations,
        )

        run = repo_get_run(db, run_id)
        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}",
            )

        candidate = repo_get_candidate(db, candidate_id)
        if candidate is None or candidate.run_id != run_id:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate {candidate_id} not found for run {run_id}",
            )

        evaluations = repo_list_evaluations(db, candidate_id=candidate.id)

        parent_summaries: List[CandidateParentSummary] = []
        if candidate.parent_ids:
            for parent_id in candidate.parent_ids:
                parent = repo_get_candidate(db, parent_id)
                if parent:
                    parent_summaries.append(
                        CandidateParentSummary(
                            id=parent.id,
                            mechanism_description=parent.mechanism_description,
                            status=_serialize_enum(parent.status),
                        )
                    )

        def _build_constraint_flags(scores: dict | None) -> List[str] | None:
            if not scores:
                return None
            constraint_satisfaction = scores.get("constraint_satisfaction", {})
            if not isinstance(constraint_satisfaction, dict):
                return None
            flags = [
                constraint_id
                for constraint_id, data in constraint_satisfaction.items()
                if isinstance(data, dict) and not data.get("satisfied", True)
            ]
            return flags or None

        evaluation_summaries = [
            EvaluationSummary(
                id=ev.id,
                scenario_id=ev.scenario_id,
                P=ev.P,
                R=ev.R,
                constraint_satisfaction=ev.constraint_satisfaction,
                explanation=ev.explanation,
            )
            for ev in evaluations
        ]

        return CandidateDetailResponse(
            id=candidate.id,
            run_id=candidate.run_id,
            project_id=candidate.project_id,
            origin=_serialize_enum(candidate.origin),
            status=_serialize_enum(candidate.status),
            mechanism_description=candidate.mechanism_description,
            predicted_effects=candidate.predicted_effects,
            scores=candidate.scores,
            constraint_flags=_build_constraint_flags(candidate.scores),
            parent_ids=candidate.parent_ids or [],
            parent_summaries=parent_summaries,
            provenance_log=candidate.provenance_log or [],
            evaluations=evaluation_summaries,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidate detail {candidate_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving candidate detail: {str(e)}",
        )


# ProblemSpec endpoints
# ProblemSpec endpoints
@app.get("/projects/{project_id}/problem-spec", response_model=ProblemSpecResponse)
async def get_problem_spec(
    project_id: str,
    db: Session = Depends(get_db)
) -> ProblemSpecResponse:
    """
    Get ProblemSpec for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        ProblemSpec data
    """
    try:
        service = ProblemSpecService(db)
        spec = service.get_problem_spec(project_id)
        
        if spec is None:
            raise HTTPException(
                status_code=404,
                detail=f"ProblemSpec not found for project {project_id}"
            )
        
        return ProblemSpecResponse(**spec)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ProblemSpec: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting ProblemSpec: {str(e)}"
        )


@app.post("/projects/{project_id}/problem-spec/refine", response_model=ProblemSpecRefineResponse)
async def refine_problem_spec(
    project_id: str,
    request: ProblemSpecRefineRequest,
    db: Session = Depends(get_db)
) -> ProblemSpecRefineResponse:
    """
    Refine ProblemSpec based on chat context.
    
    This endpoint:
    - Reads recent chat messages from the specified chat session
    - Uses the ProblemSpec agent to propose updates
    - Optionally applies updates to the database
    
    Args:
        project_id: Project ID
        request: Refinement request with optional chat_session_id
        db: Database session
        
    Returns:
        Refinement result with updated spec, questions, and reasoning
    """
    try:
        service = ProblemSpecService(db)
        result = service.refine_problem_spec(
            project_id=project_id,
            chat_session_id=request.chat_session_id,
            message_limit=request.message_limit
        )
        
        return ProblemSpecRefineResponse(**result)
        
    except Exception as e:
        logger.error(f"Error refining ProblemSpec: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error refining ProblemSpec: {str(e)}"
        )


# WorldModel endpoints
@app.get("/projects/{project_id}/world-model", response_model=WorldModelResponse)
async def get_world_model(
    project_id: str,
    db: Session = Depends(get_db)
) -> WorldModelResponse:
    """
    Get WorldModel for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        WorldModel data
    """
    try:
        service = WorldModelService(db)
        world_model = service.get_world_model(project_id)
        
        if world_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"WorldModel not found for project {project_id}"
            )
        
        return WorldModelResponse(**world_model)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting WorldModel: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting WorldModel: {str(e)}"
        )


@app.post("/projects/{project_id}/world-model/refine", response_model=WorldModelRefineResponse)
async def refine_world_model(
    project_id: str,
    request: WorldModelRefineRequest,
    db: Session = Depends(get_db)
) -> WorldModelRefineResponse:
    """
    Generate or refine WorldModel based on ProblemSpec and chat context.
    
    This endpoint:
    - Reads ProblemSpec and recent chat messages
    - Uses the WorldModeller agent to propose updates
    - Applies updates to the database with provenance tracking
    
    Args:
        project_id: Project ID
        request: Refinement request with optional chat_session_id
        db: Database session
        
    Returns:
        Refinement result with updated model, changes, and reasoning
    """
    try:
        service = WorldModelService(db)
        result = service.generate_or_refine_world_model(
            project_id=project_id,
            chat_session_id=request.chat_session_id,
            message_limit=request.message_limit
        )
        
        return WorldModelRefineResponse(**result)
        
    except Exception as e:
        logger.error(f"Error refining WorldModel: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error refining WorldModel: {str(e)}"
        )


@app.put("/projects/{project_id}/world-model", response_model=WorldModelResponse)
async def update_world_model(
    project_id: str,
    request: WorldModelUpdateRequest,
    db: Session = Depends(get_db)
) -> WorldModelResponse:
    """
    Manually update WorldModel (e.g., from UI edits).
    
    This endpoint allows direct updates to the WorldModel, typically from
    user edits in the UI. Provenance tracking is automatically added.
    
    Args:
        project_id: Project ID
        request: Update request with model_data and optional source
        db: Database session
        
    Returns:
        Updated WorldModel data
    """
    try:
        service = WorldModelService(db)
        success = service.update_world_model_manual(
            project_id=project_id,
            model_data=request.model_data,
            source=request.source
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update WorldModel"
            )
        
        # Return updated model
        world_model = service.get_world_model(project_id)
        if world_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"WorldModel not found for project {project_id}"
            )
        
        return WorldModelResponse(**world_model)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating WorldModel: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating WorldModel: {str(e)}"
        )


# Designer endpoints
@app.post("/runs/{run_id}/generate-candidates", response_model=DesignerGenerateResponse)
async def generate_candidates(
    run_id: str,
    request: DesignerGenerateRequest,
    db: Session = Depends(get_db)
) -> DesignerGenerateResponse:
    """
    Generate candidates for a run.
    
    This endpoint:
    - Reads ProblemSpec and WorldModel for the run's project
    - Uses the Designer agent to generate diverse candidate solutions
    - Creates candidates in the database with provenance tracking
    
    Args:
        run_id: Run ID
        request: Generation request with optional num_candidates
        db: Database session
        
    Returns:
        Generation result with candidates, reasoning, and count
    """
    try:
        # Get run to find project_id
        from crucible.db.repositories import get_run
        run = get_run(db, run_id)
        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}"
            )
        
        service = DesignerService(db)
        result = service.generate_candidates(
            run_id=run_id,
            project_id=run.project_id,
            num_candidates=request.num_candidates
        )
        
        return DesignerGenerateResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating candidates: {str(e)}"
        )


# Scenario endpoints
@app.post("/runs/{run_id}/generate-scenarios", response_model=ScenarioGenerateResponse)
async def generate_scenarios(
    run_id: str,
    request: ScenarioGenerateRequest,
    db: Session = Depends(get_db)
) -> ScenarioGenerateResponse:
    """
    Generate scenario suite for a run.
    
    This endpoint:
    - Reads ProblemSpec and WorldModel for the run's project
    - Optionally reads existing candidates for scenario targeting
    - Uses the ScenarioGenerator agent to create scenarios
    - Creates or updates scenario suite in the database
    
    Args:
        run_id: Run ID
        request: Generation request with optional num_scenarios
        db: Database session
        
    Returns:
        Generation result with scenario suite, scenarios, reasoning, and count
    """
    try:
        # Get run to find project_id
        from crucible.db.repositories import get_run
        run = get_run(db, run_id)
        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}"
            )
        
        service = ScenarioService(db)
        result = service.generate_scenario_suite(
            run_id=run_id,
            project_id=run.project_id,
            num_scenarios=request.num_scenarios
        )
        
        return ScenarioGenerateResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating scenarios: {str(e)}"
        )


# Run orchestration endpoints
@app.post("/runs/{run_id}/design-and-scenarios", response_model=RunDesignScenarioResponse)
async def execute_design_and_scenarios(
    run_id: str,
    request: RunDesignScenarioRequest,
    db: Session = Depends(get_db)
) -> RunDesignScenarioResponse:
    """
    Execute design + scenario generation phase for a run.
    
    This endpoint orchestrates the full "design + scenario generation" phase:
    - Generates diverse candidates from WorldModel
    - Generates scenario suite that stresses critical constraints and assumptions
    - Creates all entities in the database with provenance tracking
    
    Args:
        run_id: Run ID
        request: Request with optional num_candidates and num_scenarios
        db: Database session
        
    Returns:
        Result with candidates, scenarios, and status
    """
    try:
        service = RunService(db)
        result = service.execute_design_and_scenario_phase(
            run_id=run_id,
            num_candidates=request.num_candidates,
            num_scenarios=request.num_scenarios
        )
        
        return RunDesignScenarioResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in design + scenario phase for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing design + scenario phase: {str(e)}"
        )


# Evaluator endpoints
@app.post("/runs/{run_id}/evaluate", response_model=EvaluatorEvaluateResponse)
async def evaluate_candidates(
    run_id: str,
    request: EvaluatorEvaluateRequest,
    db: Session = Depends(get_db)
) -> EvaluatorEvaluateResponse:
    """
    Evaluate all candidates in a run against all scenarios.
    
    This endpoint:
    - Reads all candidates and scenarios for the run
    - Uses the Evaluator agent to evaluate each candidate against each scenario
    - Creates evaluation records in the database
    
    Args:
        run_id: Run ID
        request: Evaluation request (no parameters needed)
        db: Database session
        
    Returns:
        Evaluation result with evaluations, count, and statistics
    """
    try:
        service = RunService(db)
        result = service.execute_evaluation_phase(run_id=run_id)
        
        return EvaluatorEvaluateResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in evaluation phase for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing evaluation phase: {str(e)}"
        )


# Ranker endpoints
@app.post("/runs/{run_id}/rank", response_model=RankerRankResponse)
async def rank_candidates(
    run_id: str,
    request: RankerRankRequest,
    db: Session = Depends(get_db)
) -> RankerRankResponse:
    """
    Rank all candidates in a run based on their evaluations.
    
    This endpoint:
    - Aggregates evaluations for each candidate
    - Computes I = P/R for each candidate
    - Flags hard constraint violations (weight 100)
    - Updates candidate scores in the database
    - Returns ranked list with explanations
    
    Args:
        run_id: Run ID
        request: Ranking request (no parameters needed)
        db: Database session
        
    Returns:
        Ranking result with ranked candidates, count, and hard violations
    """
    try:
        service = RunService(db)
        result = service.execute_ranking_phase(run_id=run_id)
        
        return RankerRankResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in ranking phase for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing ranking phase: {str(e)}"
        )


# Run orchestration endpoints (evaluate + rank)
@app.post("/runs/{run_id}/evaluate-and-rank", response_model=RunEvaluateRankResponse)
async def execute_evaluate_and_rank(
    run_id: str,
    request: RunEvaluateRankRequest,
    db: Session = Depends(get_db)
) -> RunEvaluateRankResponse:
    """
    Execute evaluate + rank phase for a run.
    
    This endpoint orchestrates the full "evaluate + rank" phase:
    - Evaluates all candidates against all scenarios
    - Ranks candidates based on evaluations
    - Updates candidate scores and statuses
    
    Args:
        run_id: Run ID
        request: Evaluate + rank request (no parameters needed)
        db: Database session
        
    Returns:
        Result with evaluations, rankings, and status
    """
    try:
        service = RunService(db)
        result = service.execute_evaluate_and_rank_phase(run_id=run_id)
        
        return RunEvaluateRankResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in evaluate + rank phase for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing evaluate + rank phase: {str(e)}"
        )


# Full pipeline endpoint
@app.post("/runs/{run_id}/full-pipeline", response_model=RunFullPipelineResponse)
async def execute_full_pipeline(
    run_id: str,
    request: RunFullPipelineRequest,
    db: Session = Depends(get_db)
) -> RunFullPipelineResponse:
    """
    Execute the full pipeline: Design → Scenarios → Evaluation → Ranking.
    
    This endpoint orchestrates the complete pipeline:
    - Generates diverse candidates from WorldModel
    - Generates scenario suite
    - Evaluates all candidates against all scenarios
    - Ranks candidates based on evaluations
    - Marks run as completed
    
    Args:
        run_id: Run ID
        request: Full pipeline request with optional num_candidates and num_scenarios
        db: Database session
        
    Returns:
        Result with candidates, scenarios, evaluations, rankings, and status
    """
    try:
        service = RunService(db)
        result = service.execute_full_pipeline(
            run_id=run_id,
            num_candidates=request.num_candidates,
            num_scenarios=request.num_scenarios
        )
        
        return RunFullPipelineResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in full pipeline for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing full pipeline: {str(e)}"
        )


# Snapshot endpoints
@app.post("/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    request: SnapshotCreateRequest,
    db: Session = Depends(get_db)
) -> SnapshotResponse:
    """
    Create a snapshot from a project (and optionally a run).
    
    Args:
        request: Snapshot creation request
        db: Database session
        
    Returns:
        Created snapshot
    """
    try:
        from crucible.db.repositories import create_snapshot as repo_create_snapshot
        
        service = SnapshotService(db)
        
        # Capture snapshot data
        snapshot_data = service.capture_snapshot_data(
            project_id=request.project_id,
            run_id=request.run_id,
            include_chat_context=request.include_chat_context,
            max_chat_messages=request.max_chat_messages
        )
        
        # Capture reference metrics if run_id provided
        reference_metrics = None
        if request.run_id:
            reference_metrics = service.capture_reference_metrics(request.run_id)
        
        # Create snapshot
        snapshot = repo_create_snapshot(
            session=db,
            project_id=request.project_id,
            run_id=request.run_id,
            name=request.name,
            description=request.description,
            tags=request.tags,
            invariants=request.invariants,
            snapshot_data=snapshot_data,
            reference_metrics=reference_metrics
        )
        
        return SnapshotResponse(
            id=snapshot.id,
            name=snapshot.name,
            description=snapshot.description,
            tags=snapshot.tags or [],
            project_id=snapshot.project_id,
            run_id=snapshot.run_id,
            snapshot_data=snapshot.snapshot_data,
            reference_metrics=snapshot.reference_metrics,
            invariants=snapshot.invariants or [],
            version=snapshot.version,
            created_at=snapshot.created_at.isoformat() if snapshot.created_at else None,
            updated_at=snapshot.updated_at.isoformat() if snapshot.updated_at else None,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating snapshot: {str(e)}"
        )


@app.get("/snapshots", response_model=List[SnapshotResponse])
async def list_snapshots(
    project_id: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated tags
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[SnapshotResponse]:
    """
    List snapshots with optional filters.
    
    Args:
        project_id: Filter by project ID
        tags: Filter by tags (comma-separated)
        name: Filter by name (partial match)
        db: Database session
        
    Returns:
        List of snapshots
    """
    try:
        from crucible.db.repositories import list_snapshots as repo_list_snapshots
        
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        
        snapshots = repo_list_snapshots(
            session=db,
            project_id=project_id,
            tags=tag_list,
            name=name
        )
        
        return [
            SnapshotResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                tags=s.tags or [],
                project_id=s.project_id,
                run_id=s.run_id,
                snapshot_data=s.snapshot_data,
                reference_metrics=s.reference_metrics,
                invariants=s.invariants or [],
                version=s.version,
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
            for s in snapshots
        ]
        
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing snapshots: {str(e)}"
        )


@app.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db)
) -> SnapshotResponse:
    """
    Get a snapshot by ID.
    
    Args:
        snapshot_id: Snapshot ID
        db: Database session
        
    Returns:
        Snapshot details
    """
    try:
        from crucible.db.repositories import get_snapshot as repo_get_snapshot
        
        snapshot = repo_get_snapshot(db, snapshot_id)
        if snapshot is None:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot not found: {snapshot_id}"
            )
        
        return SnapshotResponse(
            id=snapshot.id,
            name=snapshot.name,
            description=snapshot.description,
            tags=snapshot.tags or [],
            project_id=snapshot.project_id,
            run_id=snapshot.run_id,
            snapshot_data=snapshot.snapshot_data,
            reference_metrics=snapshot.reference_metrics,
            invariants=snapshot.invariants or [],
            version=snapshot.version,
            created_at=snapshot.created_at.isoformat() if snapshot.created_at else None,
            updated_at=snapshot.updated_at.isoformat() if snapshot.updated_at else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting snapshot: {str(e)}"
        )


@app.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a snapshot.
    
    Args:
        snapshot_id: Snapshot ID
        db: Database session
        
    Returns:
        Success message
    """
    try:
        from crucible.db.repositories import delete_snapshot as repo_delete_snapshot
        
        success = repo_delete_snapshot(db, snapshot_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot not found: {snapshot_id}"
            )
        
        return {"status": "deleted", "snapshot_id": snapshot_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting snapshot: {str(e)}"
        )


@app.post("/snapshots/{snapshot_id}/replay", response_model=SnapshotReplayResponse)
async def replay_snapshot(
    snapshot_id: str,
    request: SnapshotReplayRequest,
    db: Session = Depends(get_db)
) -> SnapshotReplayResponse:
    """
    Replay a snapshot by creating a new run and executing the pipeline.
    
    Args:
        snapshot_id: Snapshot ID to replay
        request: Replay options
        db: Database session
        
    Returns:
        Replay results
    """
    try:
        service = SnapshotService(db)
        
        options = {
            "reuse_project": request.reuse_project,
            "phases": request.phases,
            "num_candidates": request.num_candidates,
            "num_scenarios": request.num_scenarios,
        }
        
        result = service.replay_snapshot(snapshot_id, options)
        
        return SnapshotReplayResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error replaying snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error replaying snapshot: {str(e)}"
        )


@app.post("/snapshots/run-tests", response_model=SnapshotTestResponse)
async def run_snapshot_tests(
    request: SnapshotTestRequest,
    db: Session = Depends(get_db)
) -> SnapshotTestResponse:
    """
    Run tests for one or more snapshots.
    
    Args:
        request: Test request with snapshot IDs and options
        db: Database session
        
    Returns:
        Test results summary and details
    """
    try:
        service = SnapshotService(db)
        
        result = service.run_snapshot_tests(
            snapshot_ids=request.snapshot_ids,
            options=request.options or {}
        )
        
        return SnapshotTestResponse(**result)
        
    except Exception as e:
        logger.error(f"Error running snapshot tests: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error running snapshot tests: {str(e)}"
        )


# Guidance endpoints
@app.post("/chat-sessions/{chat_session_id}/guidance", response_model=GuidanceResponse)
async def request_guidance(
    chat_session_id: str,
    request: GuidanceRequest,
    db: Session = Depends(get_db)
) -> GuidanceResponse:
    """
    Request guidance for a chat session.
    
    This endpoint:
    - Gets the project state for the chat session's project
    - Uses the Guidance agent to provide contextual help
    - Returns guidance message, suggested actions, and workflow progress
    
    Args:
        chat_session_id: Chat session ID
        request: Guidance request with optional user_query
        db: Database session
        
    Returns:
        Guidance response with message, actions, and progress
    """
    try:
        from crucible.db.repositories import get_chat_session
        
        # Get chat session to find project_id
        session = get_chat_session(db, chat_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session not found: {chat_session_id}"
            )
        
        service = GuidanceService(db)
        result = service.provide_guidance(
            project_id=session.project_id,
            user_query=request.user_query,
            chat_session_id=chat_session_id,
            message_limit=request.message_limit
        )
        
        return GuidanceResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error providing guidance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error providing guidance: {str(e)}"
        )


@app.post("/chat-sessions/{chat_session_id}/architect-reply", response_model=MessageResponse)
async def generate_architect_reply(
    chat_session_id: str,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Automatically generate an Architect reply after a user message.
    
    This endpoint:
    - Gets the latest user message from the chat session
    - Uses the Guidance service to generate an Architect response
    - Stores the Architect response as a message with structured metadata
    - Returns the created message
    
    Args:
        chat_session_id: Chat session ID
        db: Database session
        
    Returns:
        Created Architect message with metadata
    """
    try:
        from crucible.db.repositories import get_chat_session, list_messages, create_message as repo_create_message
        
        # Get chat session to find project_id
        session = get_chat_session(db, chat_session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session not found: {chat_session_id}"
            )
        
        # Get the latest user message to use as context
        messages = list_messages(db, chat_session_id)
        from crucible.db.models import MessageRole
        user_messages = [m for m in messages if (m.role.value if hasattr(m.role, "value") else str(m.role)) == "user"]
        latest_user_message = user_messages[-1] if user_messages else None
        user_query = latest_user_message.content if latest_user_message else None
        
        # Check if we should refine ProblemSpec or WorldModel based on user query
        # This captures deltas even if refinement happens as part of Architect flow
        spec_delta = None
        world_model_delta = None
        touched_sections = []
        
        # Determine if refinement is needed based on guidance type and workflow stage
        guidance_service = GuidanceService(db)
        guidance_result = guidance_service.provide_guidance(
            project_id=session.project_id,
            user_query=user_query,
            chat_session_id=chat_session_id,
            message_limit=5
        )
        
        guidance_type = guidance_result.get("guidance_type", "general_guidance")
        workflow_stage = guidance_result.get("workflow_stage", "setup")
        
        # Refine ProblemSpec if it seems appropriate (spec-related query or early stage)
        # Note: Frontend may have already called refine, so we check if spec was recently updated
        allow_spec_refine = _should_refine_problem_spec(user_query, guidance_type, workflow_stage)
        if guidance_type in ["spec_refinement", "setup_guidance"] or (workflow_stage == "setup" and allow_spec_refine):
            try:
                from crucible.db.repositories import get_problem_spec
                from datetime import datetime, timedelta
                
                current_spec = get_problem_spec(db, session.project_id)
                # Only refine if spec wasn't updated in the last 2 seconds (to avoid duplicate refinement)
                should_refine = True
                if current_spec and current_spec.updated_at:
                    time_since_update = (datetime.utcnow() - current_spec.updated_at.replace(tzinfo=None)).total_seconds()
                    if time_since_update < 2:
                        # Spec was just updated, try to get delta from the refine endpoint response
                        # by checking the most recent refine call result
                        should_refine = False
                        logger.info(f"Spec was updated {time_since_update:.1f}s ago, skipping duplicate refine")
                
                if should_refine:
                    spec_service = ProblemSpecService(db)
                    spec_result = spec_service.refine_problem_spec(
                        project_id=session.project_id,
                        chat_session_id=chat_session_id,
                        message_limit=20
                    )
                    spec_delta = spec_result.get("spec_delta")
                else:
                    # Spec was just updated, still call refine to get delta (even if empty)
                    spec_service = ProblemSpecService(db)
                    spec_result = spec_service.refine_problem_spec(
                        project_id=session.project_id,
                        chat_session_id=chat_session_id,
                        message_limit=20
                    )
                    spec_delta = spec_result.get("spec_delta")
                
                # Apply fallback logic if delta is empty (applies to both should_refine and !should_refine cases)
                if spec_delta:
                    # Check if delta exists but has no touched sections, OR if delta is None/empty
                    delta_is_empty = ((not spec_delta.get("touched_sections") or len(spec_delta.get("touched_sections", [])) == 0) and
                                     not any(spec_delta.get("constraints", {}).get(k, []) for k in ["added", "updated", "removed"]) and
                                     not any(spec_delta.get("goals", {}).get(k, []) for k in ["added", "updated", "removed"]) and
                                     not spec_delta.get("resolution_changed") and
                                     not spec_delta.get("mode_changed"))
                else:
                    delta_is_empty = True
                    spec_delta = {}
                
                # Always try fallback if delta is empty and we have a user query
                if delta_is_empty and user_query:
                    logger.info(f"Delta is empty, attempting fallback for query: {user_query}")
                    # Generic fallback: match query against actual constraint/goal names in ProblemSpec
                    from crucible.db.repositories import get_problem_spec
                    problem_spec = get_problem_spec(db, session.project_id)
                    
                    if problem_spec:
                        query_lower = user_query.lower()
                        query_words = set(query_lower.split())
                        matched_constraint_names = []
                        matched_goals = []
                        
                        # Match constraints: check if any word from constraint name appears in query
                        if problem_spec.constraints:
                            for constraint in problem_spec.constraints:
                                constraint_name = constraint.get("name", "")
                                constraint_name_lower = constraint_name.lower()
                                constraint_words = set(constraint_name_lower.split())
                                
                                # Check if any significant word from constraint name is in query
                                # Skip very common words
                                common_words = {"the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at", "by"}
                                significant_constraint_words = constraint_words - common_words
                                
                                if significant_constraint_words and (significant_constraint_words & query_words):
                                    matched_constraint_names.append(constraint_name)
                                    logger.info(f"Matched constraint '{constraint_name}' from query")
                        
                        # Match goals: check if query mentions "goal" and any goal text appears in query
                        if "goal" in query_lower and problem_spec.goals:
                            for goal in problem_spec.goals:
                                goal_lower = goal.lower()
                                goal_words = set(goal_lower.split())
                                significant_goal_words = goal_words - common_words
                                
                                # If query has significant overlap with goal text, or just mentions "goal"
                                if significant_goal_words and (significant_goal_words & query_words):
                                    matched_goals.append(goal)
                                    logger.info(f"Matched goal '{goal[:50]}...' from query")
                        
                        # Create delta if we found matches
                        if matched_constraint_names:
                            logger.info(f"Creating fallback delta for constraints: {matched_constraint_names}")
                            spec_delta = {
                                "touched_sections": ["constraints"],
                                "constraints": {
                                    "added": [],
                                    "updated": [{"name": name} for name in matched_constraint_names],
                                    "removed": []
                                },
                                "goals": {"added": [], "updated": [], "removed": []},
                                "resolution_changed": False,
                                "mode_changed": False
                            }
                        elif matched_goals:
                            logger.info(f"Creating fallback delta for goals: {len(matched_goals)} goals")
                            spec_delta = {
                                "touched_sections": ["goals"],
                                "constraints": {"added": [], "updated": [], "removed": []},
                                "goals": {
                                    "added": matched_goals,
                                    "updated": [],
                                    "removed": []
                                },
                                "resolution_changed": False,
                                "mode_changed": False
                            }
                
                # Log final delta state
                if spec_delta:
                    logger.info(f"Final spec_delta - touched_sections: {spec_delta.get('touched_sections')}, constraints updated: {spec_delta.get('constraints', {}).get('updated', [])}")
                
                if spec_delta and spec_delta.get("touched_sections"):
                    touched_sections.extend(spec_delta["touched_sections"])
            except Exception as e:
                logger.warning(f"Could not refine ProblemSpec for delta capture: {e}")
        
        # Refine WorldModel if ProblemSpec exists and it seems appropriate
        if guidance_type in ["world_model_guidance"] or (workflow_stage == "setup" and guidance_result.get("workflow_stage") != "setup"):
            try:
                from crucible.db.repositories import get_problem_spec
                problem_spec = get_problem_spec(db, session.project_id)
                if problem_spec:  # Only refine if ProblemSpec exists
                    world_model_service = WorldModelService(db)
                    world_model_result = world_model_service.generate_or_refine_world_model(
                        project_id=session.project_id,
                        chat_session_id=chat_session_id,
                        message_limit=20
                    )
                    world_model_delta = world_model_result.get("world_model_delta")
                    if world_model_delta and world_model_delta.get("touched_sections"):
                        touched_sections.extend(world_model_delta["touched_sections"])
            except Exception as e:
                logger.warning(f"Could not refine WorldModel for delta capture: {e}")
        
        # Build message metadata
        message_metadata = {
            "agent_name": "Architect",
            "workflow_stage": workflow_stage,
            "guidance_type": guidance_type,
        }
        
        # Always save spec_delta if it exists (even if empty)
        # This ensures frontend can check for deltas and display summaries
        if spec_delta is not None:
            message_metadata["spec_delta"] = spec_delta
        if world_model_delta:
            message_metadata["world_model_delta"] = world_model_delta
        if touched_sections:
            # Remove duplicates and create aggregated summary
            message_metadata["touched_sections"] = list(set(touched_sections))
        
        # Add suggested actions to metadata if present
        if guidance_result.get("suggested_actions"):
            message_metadata["suggested_actions"] = guidance_result["suggested_actions"]

        if guidance_result.get("recommended_run_config"):
            message_metadata["recommended_run_config"] = guidance_result["recommended_run_config"]
        
        # Add tool call audits to metadata if present (for provenance and analysis)
        if guidance_result.get("tool_call_audits"):
            message_metadata["tool_call_audits"] = guidance_result["tool_call_audits"]
        
        result = guidance_result
        
        # Combine guidance message with suggested actions if needed
        content = result.get("guidance_message", "")
        if result.get("suggested_actions") and len(result["suggested_actions"]) > 0:
            # Append suggested actions to the message
            actions_text = "\n\nSuggested next steps:\n" + "\n".join(
                f"{idx + 1}. {action}" for idx, action in enumerate(result["suggested_actions"])
            )
            content += actions_text
        
        # Create and store the Architect message
        from crucible.db.models import MessageRole
        architect_message = repo_create_message(
            db,
            chat_session_id=chat_session_id,
            role=MessageRole.AGENT,
            content=content,
            message_metadata=message_metadata
        )
        
        return MessageResponse(
            id=architect_message.id,
            chat_session_id=architect_message.chat_session_id,
            role=architect_message.role.value,
            content=architect_message.content,
            message_metadata=architect_message.message_metadata,
            created_at=architect_message.created_at.isoformat() if architect_message.created_at else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Architect reply: {e}", exc_info=True)
        # Create a system error message instead of raising
        try:
            from crucible.db.repositories import create_message as repo_create_message
            from crucible.db.models import MessageRole
            
            error_message = repo_create_message(
                db,
                chat_session_id=chat_session_id,
                role=MessageRole.SYSTEM,
                content=f"I encountered an error while generating a response. Please try again or continue with your conversation.",
                message_metadata={"error": str(e), "error_type": "architect_reply_failed"}
            )
            
            return MessageResponse(
                id=error_message.id,
                chat_session_id=error_message.chat_session_id,
                role=error_message.role.value,
                content=error_message.content,
                message_metadata=error_message.message_metadata,
                created_at=error_message.created_at.isoformat() if error_message.created_at else None,
            )
        except Exception as inner_e:
            logger.error(f"Error creating error message: {inner_e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error generating Architect reply: {str(e)}"
            )


# Heuristic to decide whether we should auto-refine the ProblemSpec after a user message
def _should_refine_problem_spec(
    user_query: Optional[str],
    guidance_type: str,
    workflow_stage: str
) -> bool:
    """
    Avoid mutating the ProblemSpec when the user is only asking for clarification
    (e.g., “What is a world model?”) instead of providing new requirements.
    """
    if guidance_type == "spec_refinement":
        return True

    if workflow_stage != "setup":
        return False

    if not user_query:
        # Initial description still needs ProblemSpec generation
        return True

    text = user_query.strip().lower()
    if not text:
        return True

    clarification_phrases = [
        "what is", "what's", "what does", "what do", "tell me about",
        "can you explain", "help me understand", "how does", "why does", "what are"
    ]
    spec_signal_terms = [
        "constraint", "goal", "add", "include", "update", "change",
        "requirement", "target", "should be", "need to", "set", "weight", "priority"
    ]

    looks_like_question = text.endswith("?") or text.startswith(("what", "how", "why", "can", "should"))
    has_clarification_phrase = any(phrase in text for phrase in clarification_phrases)
    has_spec_terms = any(term in text for term in spec_signal_terms)

    if (looks_like_question or has_clarification_phrase) and not has_spec_terms:
        return False

    return True


@app.post("/chat-sessions/{chat_session_id}/architect-reply-stream")
async def generate_architect_reply_stream(
    chat_session_id: str,
    db: Session = Depends(get_db)
):
    """
    Stream an Architect reply after a user message using Server-Sent Events (SSE).
    
    This endpoint:
    - Gets the latest user message from the chat session
    - Uses the Guidance service to generate an Architect response with streaming
    - Streams content as it is generated by the LLM
    - Persists the full reply as a message once streaming completes
    
    Args:
        chat_session_id: Chat session ID
        db: Database session
        
    Returns:
        StreamingResponse with SSE format:
        - data: {"type": "chunk", "content": "text chunk"}
        - data: {"type": "done", "message_id": "..."}
        - data: {"type": "error", "error": "..."}
    """
    def generate_stream():
        """Generator for SSE streaming (sync because Anthropic stream is sync)."""
        def build_update_summary(spec_delta: Optional[dict], world_model_delta: Optional[dict]) -> str:
            summary_parts: List[str] = []

            def pluralize(count: int, singular: str) -> str:
                return f"{count} {singular}" + ("" if count == 1 else "s")

            if spec_delta:
                constraint_adds = len(spec_delta.get("constraints", {}).get("added", []))
                goal_adds = len(spec_delta.get("goals", {}).get("added", []))
                resolution_changed = spec_delta.get("resolution_changed")
                mode_changed = spec_delta.get("mode_changed")

                if constraint_adds:
                    summary_parts.append(f"added {pluralize(constraint_adds, 'constraint')}")
                if goal_adds:
                    summary_parts.append(f"added {pluralize(goal_adds, 'goal')}")
                if resolution_changed:
                    summary_parts.append("adjusted the resolution")
                if mode_changed:
                    summary_parts.append("updated the workflow mode")

            if world_model_delta and world_model_delta.get("touched_sections"):
                summary_parts.append("updated the world model")

            if summary_parts:
                if len(summary_parts) == 1:
                    updates_summary = summary_parts[0]
                elif len(summary_parts) == 2:
                    updates_summary = " and ".join(summary_parts)
                else:
                    updates_summary = ", ".join(summary_parts[:-1]) + f", and {summary_parts[-1]}"
                summary_text = f"\n\nAll set — {updates_summary}."
            else:
                summary_text = "\n\nAll set with those updates."

            summary_text += " Next, I can start outlining the WorldModel or help you explore another aspect—just let me know what you'd like to do."
            return summary_text

        try:
            from crucible.db.repositories import get_chat_session, list_messages, create_message as repo_create_message
            from crucible.db.models import MessageRole
            from crucible.agents.guidance_agent import GuidanceAgent
            from kosmos.core.llm import get_provider
            import os
            
            # Get chat session to find project_id
            session = get_chat_session(db, chat_session_id)
            if session is None:
                yield f"data: {json.dumps({'type': 'error', 'error': f'Chat session not found: {chat_session_id}'})}\n\n"
                return
            
            # Get the latest user message to use as context
            messages = list_messages(db, chat_session_id)
            user_messages = [m for m in messages if (m.role.value if hasattr(m.role, "value") else str(m.role)) == "user"]
            latest_user_message = user_messages[-1] if user_messages else None
            user_query = latest_user_message.content if latest_user_message else None
            
            # Get guidance service to build the prompt (reuse existing logic)
            guidance_service = GuidanceService(db)
            
            # Get project state and workflow stage
            project_state = guidance_service.get_workflow_state(session.project_id)
            workflow_stage = guidance_service._determine_workflow_stage(project_state)
            
            # Get chat context
            chat_context = []
            try:
                messages_list = list_messages(db, chat_session_id)
                chat_context = [
                    {
                        "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                        "content": msg.content
                    }
                    for msg in messages_list[-5:]
                ]
            except Exception as e:
                logger.warning(f"Could not load chat context: {e}")
            
            # Build the prompt using guidance agent's logic
            guidance_agent = GuidanceAgent(tools=guidance_service._create_tools())
            
            # For new project setup, enhance the prompt with project info and future tense instructions
            is_new_project_setup = (workflow_stage == "setup" and not project_state.get("has_problem_spec", False))
            
            if is_new_project_setup:
                # Get project details for greeting
                from crucible.db.repositories import get_project
                project = get_project(db, session.project_id)
                project_title = project.title if project else "New Project"
                project_description = project.description if project else None
                
                # Enhance the prompt with project info and future tense instructions
                base_prompt = guidance_agent._build_tool_based_prompt(
                    user_query=user_query,
                    project_id=session.project_id,
                    chat_context=chat_context,
                    tool_descriptions=guidance_agent._describe_tools(),
                    initial_state=project_state
                )
                
                # Add special instructions for new project greeting
                greeting_instructions = f"""

IMPORTANT: This is a new project setup. The user just provided their initial description.
- Project title: "{project_title}"
- Project description: "{project_description if project_description else 'User provided initial description'}"
- The user can change the title/description above by clicking the pencil icon.

Your response should:
1. Greet them warmly as the Architect
2. Acknowledge their project idea
3. Tell them you're CREATING a project called "{project_title}" with description "{project_description if project_description else 'their initial description'}" (mention they can change it above)
4. Use FUTURE TENSE - say "I'm going to..." or "I'll..." not "I've done..." because the updates will happen next
5. Tell them what you're GOING TO DO NEXT: analyze their description and add initial goals and constraints to the ProblemSpec
6. Explain that they'll see working indicators as you do this, and then you'll give them a summary
7. Suggest next steps after setup is complete

Be concise, friendly, and conversational. Remember: use future tense, not past tense.
"""
                
                prompt = base_prompt + greeting_instructions
                system_prompt = guidance_agent._get_system_prompt_with_tools()
            else:
                prompt = guidance_agent._build_tool_based_prompt(
                    user_query=user_query,
                    project_id=session.project_id,
                    chat_context=chat_context,
                    tool_descriptions=guidance_agent._describe_tools(),
                    initial_state=project_state
                )
                system_prompt = guidance_agent._get_system_prompt_with_tools()
            
            # Get LLM provider and check if it supports streaming
            llm_provider = get_provider()
            # Get provider name - check class name or provider_name attribute
            if hasattr(llm_provider, 'provider_name'):
                provider_name = llm_provider.provider_name
            elif hasattr(llm_provider, '__class__'):
                class_name = llm_provider.__class__.__name__
                if 'Anthropic' in class_name:
                    provider_name = 'anthropic'
                elif 'OpenAI' in class_name:
                    provider_name = 'openai'
                else:
                    provider_name = 'unknown'
            else:
                provider_name = 'unknown'
            
            # Try to stream using the configured provider
            full_content = ""
            try:
                # Check provider type and use appropriate streaming method
                if provider_name == 'anthropic':
                    # Use Anthropic SDK for streaming
                    from anthropic import Anthropic
                    api_key = os.environ.get('ANTHROPIC_API_KEY')
                    if api_key and not api_key.replace('9', ''):  # CLI mode
                        raise NotImplementedError("CLI mode doesn't support streaming")
                    
                    anthropic_client = Anthropic(api_key=api_key)
                    model = getattr(llm_provider, 'model', 'claude-3-5-sonnet-20241022')
                    
                    # Convert chat context to Anthropic message format
                    anthropic_messages = []
                    for msg in chat_context[-10:]:  # Last 10 messages for context
                        role = msg.get("role", "user")
                        if role == "user":
                            anthropic_messages.append({"role": "user", "content": msg.get("content", "")})
                        elif role == "agent":
                            anthropic_messages.append({"role": "assistant", "content": msg.get("content", "")})
                    
                    # Build final messages list
                    final_messages = anthropic_messages.copy()
                    if prompt:
                        final_messages.append({"role": "user", "content": prompt})
                    
                    with anthropic_client.messages.stream(
                        model=model,
                        max_tokens=2048,
                        temperature=0.8,
                        system=system_prompt,
                        messages=final_messages,
                    ) as stream:
                        for text_event in stream.text_stream:
                            if text_event:
                                full_content += text_event
                                chunk_data = json.dumps({'type': 'chunk', 'content': text_event})
                                yield f"data: {chunk_data}\n\n"
                                
                elif provider_name == 'openai':
                    # Use OpenAI SDK for streaming
                    from openai import OpenAI
                    api_key = os.environ.get('OPENAI_API_KEY')
                    base_url = getattr(llm_provider, 'base_url', None)
                    model = getattr(llm_provider, 'model', 'gpt-4-turbo')
                    
                    openai_client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
                    
                    # Convert chat context to OpenAI message format
                    openai_messages = []
                    if system_prompt:
                        openai_messages.append({"role": "system", "content": system_prompt})
                    for msg in chat_context[-10:]:  # Last 10 messages for context
                        role = msg.get("role", "user")
                        if role == "user":
                            openai_messages.append({"role": "user", "content": msg.get("content", "")})
                        elif role == "agent":
                            openai_messages.append({"role": "assistant", "content": msg.get("content", "")})
                    
                    # Add the current prompt
                    if prompt:
                        openai_messages.append({"role": "user", "content": prompt})
                    
                    # Stream from OpenAI
                    stream = openai_client.chat.completions.create(
                        model=model,
                        messages=openai_messages,
                        max_tokens=2048,
                        temperature=0.8,
                        stream=True,
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            text_chunk = chunk.choices[0].delta.content
                            full_content += text_chunk
                            chunk_data = json.dumps({'type': 'chunk', 'content': text_chunk})
                            yield f"data: {chunk_data}\n\n"
                else:
                    # Provider doesn't support streaming or is unknown
                    raise NotImplementedError(f"Streaming not implemented for provider: {provider_name}")
                
                # Streaming completed successfully
                # Now do refinement logic (similar to non-streaming endpoint)
                spec_delta = None
                world_model_delta = None
                touched_sections = []
                
                # Determine guidance type
                guidance_type = guidance_service._determine_guidance_type(user_query, workflow_stage, project_state)
                
                # Refine ProblemSpec if needed (same logic as non-streaming)
                allow_spec_refine = _should_refine_problem_spec(user_query, guidance_type, workflow_stage)
                if guidance_type in ["spec_refinement", "setup_guidance"] or (workflow_stage == "setup" and allow_spec_refine):
                    try:
                        # Send event indicating we're updating the spec
                        yield f"data: {json.dumps({'type': 'updating', 'what': 'ProblemSpec'})}\n\n"
                        
                        from crucible.db.repositories import get_problem_spec
                        from datetime import datetime
                        
                        current_spec = get_problem_spec(db, session.project_id)
                        should_refine = True
                        if current_spec and current_spec.updated_at:
                            time_since_update = (datetime.utcnow() - current_spec.updated_at.replace(tzinfo=None)).total_seconds()
                            if time_since_update < 2:
                                should_refine = False
                        
                        if should_refine:
                            spec_service = ProblemSpecService(db)
                            spec_result = spec_service.refine_problem_spec(
                                project_id=session.project_id,
                                chat_session_id=chat_session_id,
                                message_limit=20
                            )
                            spec_delta = spec_result.get("spec_delta")
                        else:
                            spec_service = ProblemSpecService(db)
                            spec_result = spec_service.refine_problem_spec(
                                project_id=session.project_id,
                                chat_session_id=chat_session_id,
                                message_limit=20
                            )
                            spec_delta = spec_result.get("spec_delta")
                        
                        # Apply fallback logic if delta is empty (same as non-streaming endpoint)
                        if spec_delta:
                            delta_is_empty = ((not spec_delta.get("touched_sections") or len(spec_delta.get("touched_sections", [])) == 0) and
                                            (not spec_delta.get("constraints", {}).get("updated") or len(spec_delta.get("constraints", {}).get("updated", [])) == 0) and
                                            (not spec_delta.get("constraints", {}).get("added") or len(spec_delta.get("constraints", {}).get("added", [])) == 0) and
                                            (not spec_delta.get("goals", {}).get("added") or len(spec_delta.get("goals", {}).get("added", [])) == 0) and
                                            not spec_delta.get("resolution_changed") and
                                            not spec_delta.get("mode_changed"))
                        else:
                            delta_is_empty = True
                        
                        # Always try fallback if delta is empty and we have a user query
                        if delta_is_empty and user_query:
                            logger.info(f"Delta is empty in streaming, attempting fallback for query: {user_query}")
                            # Generic fallback: match query against actual constraint/goal names in ProblemSpec
                            from crucible.db.repositories import get_problem_spec
                            problem_spec = get_problem_spec(db, session.project_id)
                            
                            if problem_spec:
                                query_lower = user_query.lower()
                                query_words = set(query_lower.split())
                                matched_constraint_names = []
                                matched_goals = []
                                
                                # Match constraints: check if any word from constraint name appears in query
                                if problem_spec.constraints:
                                    for constraint in problem_spec.constraints:
                                        constraint_name = constraint.get("name", "")
                                        constraint_name_lower = constraint_name.lower()
                                        constraint_words = set(constraint_name_lower.split())
                                        
                                        # Check if any significant word from constraint name is in query
                                        # Skip very common words
                                        common_words = {"the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at", "by"}
                                        significant_constraint_words = constraint_words - common_words
                                        
                                        if significant_constraint_words and (significant_constraint_words & query_words):
                                            matched_constraint_names.append(constraint_name)
                                            logger.info(f"Matched constraint '{constraint_name}' from query")
                                
                                # Match goals: check if query mentions "goal" and any goal text appears in query
                                if "goal" in query_lower and problem_spec.goals:
                                    for goal in problem_spec.goals:
                                        goal_lower = goal.lower()
                                        goal_words = set(goal_lower.split())
                                        significant_goal_words = goal_words - common_words
                                        
                                        # If query has significant overlap with goal text, or just mentions "goal"
                                        if significant_goal_words and (significant_goal_words & query_words):
                                            matched_goals.append(goal)
                                            logger.info(f"Matched goal '{goal[:50]}...' from query")
                                
                                # Create delta if we found matches
                                if matched_constraint_names:
                                    logger.info(f"Creating fallback delta for constraints in streaming: {matched_constraint_names}")
                                    spec_delta = {
                                        "touched_sections": ["constraints"],
                                        "constraints": {
                                            "added": [],
                                            "updated": [{"name": name} for name in matched_constraint_names],
                                            "removed": []
                                        },
                                        "goals": {"added": [], "updated": [], "removed": []},
                                        "resolution_changed": False,
                                        "mode_changed": False
                                    }
                                elif matched_goals:
                                    logger.info(f"Creating fallback delta for goals in streaming: {len(matched_goals)} goals")
                                    spec_delta = {
                                        "touched_sections": ["goals"],
                                        "constraints": {"added": [], "updated": [], "removed": []},
                                        "goals": {
                                            "added": matched_goals,
                                            "updated": [],
                                            "removed": []
                                        },
                                        "resolution_changed": False,
                                        "mode_changed": False
                                    }
                        
                        if spec_delta:
                            # Extract touched_sections if present
                            if spec_delta.get("touched_sections"):
                                touched_sections.extend(spec_delta["touched_sections"])
                            # Always send event with delta (even if touched_sections is empty)
                            # This ensures frontend can display the delta summary and apply highlighting
                            yield f"data: {json.dumps({'type': 'updated', 'delta': spec_delta, 'what': 'ProblemSpec'})}\n\n"
                    except Exception as e:
                        logger.warning(f"Could not refine ProblemSpec: {e}")
                
                # Refine WorldModel if needed
                if guidance_type in ["world_model_guidance"]:
                    try:
                        from crucible.db.repositories import get_problem_spec
                        problem_spec = get_problem_spec(db, session.project_id)
                        if problem_spec:
                            world_model_service = WorldModelService(db)
                            world_model_result = world_model_service.generate_or_refine_world_model(
                                project_id=session.project_id,
                                chat_session_id=chat_session_id,
                                message_limit=20
                            )
                            world_model_delta = world_model_result.get("world_model_delta")
                            if world_model_delta and world_model_delta.get("touched_sections"):
                                touched_sections.extend(world_model_delta["touched_sections"])
                    except Exception as e:
                        logger.warning(f"Could not refine WorldModel: {e}")
                
                # Extract suggested actions from content
                import re
                numbered = re.findall(r'\d+\.\s+([^\n]+)', full_content)
                bullets = re.findall(r'[-•]\s+([^\n]+)', full_content)
                suggested_actions = [s.strip() for s in (numbered[:4] if numbered else bullets[:4])] if (numbered or bullets) else []
                
                # Build message metadata
                message_metadata = {
                    "agent_name": "Architect",
                    "workflow_stage": workflow_stage,
                    "guidance_type": guidance_type,
                }
                
                # Always save spec_delta if it exists (even if empty)
                # This ensures frontend can check for deltas and display summaries
                if spec_delta is not None:
                    message_metadata["spec_delta"] = spec_delta
                if world_model_delta:
                    message_metadata["world_model_delta"] = world_model_delta
                if touched_sections:
                    message_metadata["touched_sections"] = list(set(touched_sections))
                if suggested_actions:
                    message_metadata["suggested_actions"] = suggested_actions

                if guidance_type == "run_recommendation":
                    recommendation = guidance_service._build_run_recommendation(
                        project_id=session.project_id,
                        chat_session_id=chat_session_id,
                        mode=project_state.get("mode", "full_search") if isinstance(project_state, dict) else "full_search",
                    )
                    if recommendation:
                        message_metadata["recommended_run_config"] = recommendation.to_dict()
                        reminder = "Use the Run panel (Run button) to execute—I'm only recommending settings."
                        if reminder not in suggested_actions:
                            suggested_actions.append(reminder)
                            message_metadata["suggested_actions"] = suggested_actions
                
                # Note: tool_call_audits are added when using GuidanceService,
                # but streaming endpoint doesn't use GuidanceService directly.
                # Tool call audits would be available if we call guidance_service.provide_guidance()
                # before streaming. For now, streaming endpoint doesn't capture tool call audits.
                
                summary_text = build_update_summary(spec_delta, world_model_delta)
                if summary_text:
                    full_content += summary_text
                    yield f"data: {json.dumps({'type': 'chunk', 'content': summary_text})}\n\n"
                
                # Create and store the Architect message
                architect_message = repo_create_message(
                    db,
                    chat_session_id=chat_session_id,
                    role=MessageRole.AGENT,
                    content=full_content,
                    message_metadata=message_metadata
                )
                
                # Send completion event with message ID
                yield f"data: {json.dumps({'type': 'done', 'message_id': architect_message.id})}\n\n"
                
            except (ImportError, NotImplementedError, AttributeError) as e:
                # Fallback to non-streaming if streaming not available
                logger.warning(f"Streaming not available, falling back to non-streaming: {e}")
                response = llm_provider.generate(
                    prompt,
                    system=system_prompt,
                    temperature=0.8,
                    max_tokens=2048
                )
                full_content = response.content.strip()
                
                # Stream the full content as a single chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': full_content})}\n\n"
                
                # Do refinement and save message (reuse same logic as streaming path)
                spec_delta = None
                world_model_delta = None
                touched_sections = []
                guidance_type = guidance_service._determine_guidance_type(user_query, workflow_stage, project_state)
                
                # Refine ProblemSpec if needed
                allow_spec_refine = _should_refine_problem_spec(user_query, guidance_type, workflow_stage)
                if guidance_type in ["spec_refinement", "setup_guidance"] or (workflow_stage == "setup" and allow_spec_refine):
                    try:
                        from crucible.db.repositories import get_problem_spec
                        from datetime import datetime
                        current_spec = get_problem_spec(db, session.project_id)
                        should_refine = True
                        if current_spec and current_spec.updated_at:
                            time_since_update = (datetime.utcnow() - current_spec.updated_at.replace(tzinfo=None)).total_seconds()
                            if time_since_update < 2:
                                should_refine = False
                        if should_refine:
                            spec_service = ProblemSpecService(db)
                            spec_result = spec_service.refine_problem_spec(
                                project_id=session.project_id,
                                chat_session_id=chat_session_id,
                                message_limit=20
                            )
                            spec_delta = spec_result.get("spec_delta")
                        else:
                            spec_service = ProblemSpecService(db)
                            spec_result = spec_service.refine_problem_spec(
                                project_id=session.project_id,
                                chat_session_id=chat_session_id,
                                message_limit=20
                            )
                            spec_delta = spec_result.get("spec_delta")
                        if spec_delta and spec_delta.get("touched_sections"):
                            touched_sections.extend(spec_delta["touched_sections"])
                    except Exception as e:
                        logger.warning(f"Could not refine ProblemSpec: {e}")
                
                # Refine WorldModel if needed
                if guidance_type in ["world_model_guidance"]:
                    try:
                        from crucible.db.repositories import get_problem_spec
                        problem_spec = get_problem_spec(db, session.project_id)
                        if problem_spec:
                            world_model_service = WorldModelService(db)
                            world_model_result = world_model_service.generate_or_refine_world_model(
                                project_id=session.project_id,
                                chat_session_id=chat_session_id,
                                message_limit=20
                            )
                            world_model_delta = world_model_result.get("world_model_delta")
                            if world_model_delta and world_model_delta.get("touched_sections"):
                                touched_sections.extend(world_model_delta["touched_sections"])
                    except Exception as e:
                        logger.warning(f"Could not refine WorldModel: {e}")
                
                # Extract suggested actions
                import re
                numbered = re.findall(r'\d+\.\s+([^\n]+)', full_content)
                bullets = re.findall(r'[-•]\s+([^\n]+)', full_content)
                suggested_actions = [s.strip() for s in (numbered[:4] if numbered else bullets[:4])] if (numbered or bullets) else []
                
                # Build message metadata
                message_metadata = {
                    "agent_name": "Architect",
                    "workflow_stage": workflow_stage,
                    "guidance_type": guidance_type,
                }
                if spec_delta:
                    message_metadata["spec_delta"] = spec_delta
                if world_model_delta:
                    message_metadata["world_model_delta"] = world_model_delta
                if touched_sections:
                    message_metadata["touched_sections"] = list(set(touched_sections))
                if suggested_actions:
                    message_metadata["suggested_actions"] = suggested_actions

                if guidance_type == "run_recommendation":
                    recommendation = guidance_service._build_run_recommendation(
                        project_id=session.project_id,
                        chat_session_id=chat_session_id,
                        mode=project_state.get("mode", "full_search") if isinstance(project_state, dict) else "full_search",
                    )
                    if recommendation:
                        message_metadata["recommended_run_config"] = recommendation.to_dict()
                        reminder = "Use the Run panel (Run button) to execute—I'm only recommending settings."
                        if reminder not in suggested_actions:
                            suggested_actions.append(reminder)
                            message_metadata["suggested_actions"] = suggested_actions

                summary_text = build_update_summary(spec_delta, world_model_delta)
                if summary_text:
                    full_content += summary_text
                    yield f"data: {json.dumps({'type': 'chunk', 'content': summary_text})}\n\n"
                
                # Create and store the Architect message
                architect_message = repo_create_message(
                    db,
                    chat_session_id=chat_session_id,
                    role=MessageRole.AGENT,
                    content=full_content,
                    message_metadata=message_metadata
                )
                
                yield f"data: {json.dumps({'type': 'done', 'message_id': architect_message.id})}\n\n"
                
        except Exception as e:
            logger.error(f"Error in streaming Architect reply: {e}", exc_info=True)
            # Extract a user-friendly error message
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if isinstance(error_data, dict):
                        error_msg = error_data.get('error', {}).get('message', error_msg) if isinstance(error_data.get('error'), dict) else error_msg
                except:
                    pass
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.get("/projects/{project_id}/workflow-state", response_model=WorkflowStateResponse)
async def get_workflow_state(
    project_id: str,
    db: Session = Depends(get_db)
) -> WorkflowStateResponse:
    """
    Get the current workflow state for a project.
    
    This endpoint returns the current state of the project:
    - Whether it has a ProblemSpec
    - Whether it has a WorldModel
    - Whether it has runs
    - Run count and project metadata
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        Workflow state response
    """
    try:
        service = GuidanceService(db)
        state = service.get_workflow_state(project_id)
        
        return WorkflowStateResponse(**state)
        
    except Exception as e:
        logger.error(f"Error getting workflow state: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting workflow state: {str(e)}"
        )


@app.get("/projects/{project_id}/provenance", response_model=ProjectProvenanceResponse)
async def get_project_provenance(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectProvenanceResponse:
    """
    Aggregate provenance information for a project.
    """
    try:
        from crucible.db.repositories import (
            get_project as repo_get_project,
            get_problem_spec as repo_get_problem_spec,
            get_world_model as repo_get_world_model,
            list_candidates as repo_list_candidates,
        )

        project = repo_get_project(db, project_id)
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}",
            )

        problem_spec = repo_get_problem_spec(db, project_id)
        world_model = repo_get_world_model(db, project_id)
        candidates = repo_list_candidates(db, project_id=project_id)

        problem_spec_log = problem_spec.provenance_log if problem_spec and problem_spec.provenance_log else []
        world_model_log = []
        if world_model and isinstance(world_model.model_data, dict):
            world_model_log = world_model.model_data.get("provenance") or []

        candidate_logs = [
            {
                "candidate_id": candidate.id,
                "run_id": candidate.run_id,
                "parent_ids": candidate.parent_ids or [],
                "provenance_log": candidate.provenance_log or [],
            }
            for candidate in candidates
        ]

        return ProjectProvenanceResponse(
            project_id=project_id,
            problem_spec=problem_spec_log,
            world_model=world_model_log,
            candidates=candidate_logs,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project provenance for {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting project provenance: {str(e)}",
        )


# Pydantic models for Issue API
class IssueCreateRequest(BaseModel):
    """Request model for issue creation."""
    type: str  # IssueType enum value
    severity: str  # IssueSeverity enum value
    description: str
    run_id: Optional[str] = None
    candidate_id: Optional[str] = None


class IssueUpdateRequest(BaseModel):
    """Request model for issue update."""
    description: Optional[str] = None
    resolution_status: Optional[str] = None  # IssueResolutionStatus enum value


class IssueResolveRequest(BaseModel):
    """Request model for resolving an issue with remediation action."""
    remediation_action: str  # "patch_and_rescore", "partial_rerun", "full_rerun", "invalidate_candidates"
    remediation_metadata: Optional[Dict[str, Any]] = None  # Additional action-specific parameters


class IssueResponse(BaseModel):
    """Response model for Issue."""
    id: str
    project_id: str
    run_id: Optional[str] = None
    candidate_id: Optional[str] = None
    type: str
    severity: str
    description: str
    resolution_status: str
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None


# Issue API endpoints
@app.post("/projects/{project_id}/issues", response_model=IssueResponse)
async def create_issue(
    project_id: str,
    request: IssueCreateRequest,
    db: Session = Depends(get_db)
) -> IssueResponse:
    """
    Create a new issue for a project.
    
    Args:
        project_id: Project ID
        request: Issue creation request
        db: Database session
        
    Returns:
        Created issue
    """
    try:
        from crucible.db.repositories import (
            get_project as repo_get_project,
            create_issue as repo_create_issue,
        )
        from crucible.db.models import IssueType, IssueSeverity
        
        # Verify project exists
        project = repo_get_project(db, project_id)
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )
        
        # Validate enum values
        try:
            issue_type = IssueType(request.type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid issue type: {request.type}. Must be one of: {[e.value for e in IssueType]}"
            )
        
        try:
            severity = IssueSeverity(request.severity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {request.severity}. Must be one of: {[e.value for e in IssueSeverity]}"
            )
        
        # Create issue
        issue = repo_create_issue(
            session=db,
            project_id=project_id,
            type=issue_type.value,
            severity=severity.value,
            description=request.description,
            run_id=request.run_id,
            candidate_id=request.candidate_id
        )
        
        # Record provenance entry on project
        from crucible.core.provenance import build_provenance_entry
        from crucible.db.repositories import get_problem_spec as repo_get_problem_spec
        
        problem_spec = repo_get_problem_spec(db, project_id)
        if problem_spec:
            provenance_entry = build_provenance_entry(
                event_type="issue_created",
                actor="user",
                source=f"api:/projects/{project_id}/issues",
                description=f"Issue created: {issue_type.value} - {severity.value}",
                reference_ids=[issue.id, project_id],
                metadata={
                    "issue_type": issue_type.value,
                    "issue_severity": severity.value,
                    "run_id": request.run_id,
                    "candidate_id": request.candidate_id
                }
            )
            if problem_spec.provenance_log is None:
                problem_spec.provenance_log = []
            problem_spec.provenance_log.append(provenance_entry)
            db.commit()
        
        return IssueResponse(
            id=issue.id,
            project_id=issue.project_id,
            run_id=issue.run_id,
            candidate_id=issue.candidate_id,
            type=issue.type.value,
            severity=issue.severity.value,
            description=issue.description,
            resolution_status=issue.resolution_status.value,
            created_at=issue.created_at.isoformat() if issue.created_at else None,
            resolved_at=issue.resolved_at.isoformat() if issue.resolved_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating issue: {str(e)}"
        )


@app.get("/projects/{project_id}/issues", response_model=List[IssueResponse])
async def list_issues(
    project_id: str,
    run_id: Optional[str] = Query(None),
    candidate_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    resolution_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> List[IssueResponse]:
    """
    List issues for a project with optional filters.
    
    Args:
        project_id: Project ID
        run_id: Optional filter by run ID
        candidate_id: Optional filter by candidate ID
        type: Optional filter by issue type
        severity: Optional filter by severity
        resolution_status: Optional filter by resolution status
        db: Database session
        
    Returns:
        List of issues
    """
    try:
        from crucible.db.repositories import (
            get_project as repo_get_project,
            list_issues as repo_list_issues,
        )
        from crucible.db.models import Issue
        
        # Verify project exists
        project = repo_get_project(db, project_id)
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )
        
        # Get all issues for project
        issues = repo_list_issues(db, project_id=project_id, resolution_status=resolution_status)
        
        # Apply additional filters
        filtered_issues = []
        for issue in issues:
            if run_id is not None and issue.run_id != run_id:
                continue
            if candidate_id is not None and issue.candidate_id != candidate_id:
                continue
            if type is not None and issue.type.value != type:
                continue
            if severity is not None and issue.severity.value != severity:
                continue
            filtered_issues.append(issue)
        
        return [
            IssueResponse(
                id=issue.id,
                project_id=issue.project_id,
                run_id=issue.run_id,
                candidate_id=issue.candidate_id,
                type=issue.type.value,
                severity=issue.severity.value,
                description=issue.description,
                resolution_status=issue.resolution_status.value,
                created_at=issue.created_at.isoformat() if issue.created_at else None,
                resolved_at=issue.resolved_at.isoformat() if issue.resolved_at else None,
            )
            for issue in filtered_issues
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing issues: {str(e)}"
        )


@app.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: str,
    db: Session = Depends(get_db)
) -> IssueResponse:
    """
    Get an issue by ID.
    
    Args:
        issue_id: Issue ID
        db: Database session
        
    Returns:
        Issue data
    """
    try:
        from crucible.db.repositories import get_issue as repo_get_issue
        
        issue = repo_get_issue(db, issue_id)
        if issue is None:
            raise HTTPException(
                status_code=404,
                detail=f"Issue not found: {issue_id}"
            )
        
        return IssueResponse(
            id=issue.id,
            project_id=issue.project_id,
            run_id=issue.run_id,
            candidate_id=issue.candidate_id,
            type=issue.type.value,
            severity=issue.severity.value,
            description=issue.description,
            resolution_status=issue.resolution_status.value,
            created_at=issue.created_at.isoformat() if issue.created_at else None,
            resolved_at=issue.resolved_at.isoformat() if issue.resolved_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting issue: {str(e)}"
        )


@app.patch("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: str,
    request: IssueUpdateRequest,
    db: Session = Depends(get_db)
) -> IssueResponse:
    """
    Update an issue.
    
    Args:
        issue_id: Issue ID
        request: Issue update request
        db: Database session
        
    Returns:
        Updated issue
    """
    try:
        from crucible.db.repositories import (
            get_issue as repo_get_issue,
            update_issue as repo_update_issue,
        )
        from crucible.db.models import IssueResolutionStatus
        from datetime import datetime
        
        issue = repo_get_issue(db, issue_id)
        if issue is None:
            raise HTTPException(
                status_code=404,
                detail=f"Issue not found: {issue_id}"
            )
        
        # Update fields
        if request.description is not None:
            issue.description = request.description
        
        resolved_at = None
        if request.resolution_status is not None:
            try:
                resolution_status = IssueResolutionStatus(request.resolution_status)
                issue.resolution_status = resolution_status
                if resolution_status != IssueResolutionStatus.OPEN and issue.resolved_at is None:
                    resolved_at = datetime.utcnow()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid resolution status: {request.resolution_status}. Must be one of: {[e.value for e in IssueResolutionStatus]}"
                )
        
        # Update via repository
        updated_issue = repo_update_issue(
            session=db,
            issue_id=issue_id,
            resolution_status=request.resolution_status,
            resolved_at=resolved_at
        )
        
        if updated_issue is None:
            raise HTTPException(
                status_code=404,
                detail=f"Issue not found: {issue_id}"
            )
        
        return IssueResponse(
            id=updated_issue.id,
            project_id=updated_issue.project_id,
            run_id=updated_issue.run_id,
            candidate_id=updated_issue.candidate_id,
            type=updated_issue.type.value,
            severity=updated_issue.severity.value,
            description=updated_issue.description,
            resolution_status=updated_issue.resolution_status.value,
            created_at=updated_issue.created_at.isoformat() if updated_issue.created_at else None,
            resolved_at=updated_issue.resolved_at.isoformat() if updated_issue.resolved_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating issue: {str(e)}"
        )


@app.post("/issues/{issue_id}/feedback")
async def get_issue_feedback(
    issue_id: str,
    user_clarification: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get feedback and remediation proposal for an issue.
    
    Args:
        issue_id: Issue ID
        user_clarification: Optional user response to clarifying questions
        db: Database session
        
    Returns:
        Feedback response with questions and/or remediation proposal
    """
    try:
        from crucible.db.repositories import get_issue as repo_get_issue
        from crucible.services.feedback_service import FeedbackService
        
        issue = repo_get_issue(db, issue_id)
        if issue is None:
            raise HTTPException(
                status_code=404,
                detail=f"Issue not found: {issue_id}"
            )
        
        feedback_service = FeedbackService(db)
        result = feedback_service.propose_remediation(
            issue_id=issue_id,
            user_clarification=user_clarification,
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback for issue {issue_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting feedback: {str(e)}"
        )


@app.post("/issues/{issue_id}/resolve")
async def resolve_issue(
    issue_id: str,
    request: IssueResolveRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Resolve an issue with a remediation action.
    
    This endpoint triggers the appropriate remediation based on the action type.
    The actual remediation logic will be implemented in IssueService.
    
    Args:
        issue_id: Issue ID
        request: Remediation action request
        db: Database session
        
    Returns:
        Remediation result
    """
    try:
        from crucible.db.repositories import get_issue as repo_get_issue
        from crucible.db.models import IssueResolutionStatus
        from datetime import datetime
        
        issue = repo_get_issue(db, issue_id)
        if issue is None:
            raise HTTPException(
                status_code=404,
                detail=f"Issue not found: {issue_id}"
            )
        
        if issue.resolution_status != IssueResolutionStatus.OPEN:
            raise HTTPException(
                status_code=400,
                detail=f"Issue {issue_id} is already {issue.resolution_status.value}"
            )
        
        # Call IssueService to apply remediation
        from crucible.services.issue_service import IssueService
        
        issue_service = IssueService(db)
        
        # Get issue to determine context
        issue = repo_get_issue(db, issue_id)
        if issue is None:
            raise HTTPException(
                status_code=404,
                detail=f"Issue not found: {issue_id}"
            )
        
        # Apply remediation based on action type
        patch_data = request.remediation_metadata or {}
        run_config = patch_data.pop("run_config", None)
        
        try:
            if request.remediation_action == "patch_and_rescore":
                result = issue_service.apply_patch_and_rescore(
                    issue_id=issue_id,
                    patch_data=patch_data,
                )
            elif request.remediation_action == "partial_rerun":
                result = issue_service.apply_partial_rerun(
                    issue_id=issue_id,
                    patch_data=patch_data,
                )
            elif request.remediation_action == "full_rerun":
                result = issue_service.apply_full_rerun(
                    issue_id=issue_id,
                    patch_data=patch_data,
                    run_config=run_config,
                )
            elif request.remediation_action == "invalidate_candidates":
                candidate_ids = patch_data.get("candidate_ids", [])
                if not candidate_ids:
                    raise HTTPException(
                        status_code=400,
                        detail="candidate_ids required for invalidate_candidates action"
                    )
                result = issue_service.invalidate_candidates(
                    issue_id=issue_id,
                    candidate_ids=candidate_ids,
                    reason=patch_data.get("reason"),
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown remediation action: {request.remediation_action}. Must be one of: patch_and_rescore, partial_rerun, full_rerun, invalidate_candidates"
                )
            
            return {
                "status": "success",
                "message": f"Issue {issue_id} resolved with action '{request.remediation_action}'",
                "issue_id": issue_id,
                "remediation_action": request.remediation_action,
                "result": result,
            }
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error resolving issue: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "crucible.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )

