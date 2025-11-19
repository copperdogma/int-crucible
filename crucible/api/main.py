"""
FastAPI application for Int Crucible backend.

Provides HTTP API endpoints for the Int Crucible system, integrating
with Kosmos for agent orchestration and infrastructure.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import Generator
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
from sqlalchemy.orm import Session

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


class RunResponse(BaseModel):
    """Response model for Run."""
    id: str
    project_id: str
    mode: str
    config: Optional[dict] = None
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class CandidateResponse(BaseModel):
    """Response model for Candidate."""
    id: str
    run_id: str
    project_id: str
    origin: str
    mechanism_description: str
    predicted_effects: Optional[dict] = None
    scores: Optional[dict] = None
    constraint_flags: Optional[List[str]] = None


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
    db: Session = Depends(get_db)
) -> List[RunResponse]:
    """
    List runs, optionally filtered by project.
    
    Args:
        project_id: Optional project ID filter
        db: Database session
        
    Returns:
        List of runs
    """
    try:
        from crucible.db.repositories import list_runs as repo_list_runs
        
        runs = repo_list_runs(db, project_id)
        return [
            RunResponse(
                id=r.id,
                project_id=r.project_id,
                mode=r.mode,
                config=r.config,
                status=r.status.value if hasattr(r.status, 'value') else str(r.status),
                created_at=r.created_at.isoformat() if r.created_at else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
            )
            for r in runs
        ]
    except Exception as e:
        logger.error(f"Error listing runs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing runs: {str(e)}"
        )


@app.get("/projects/{project_id}/runs", response_model=List[RunResponse])
async def list_project_runs(
    project_id: str,
    db: Session = Depends(get_db)
) -> List[RunResponse]:
    """
    List runs for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        List of runs
    """
    return await list_runs(project_id=project_id, db=db)


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
        from crucible.db.repositories import create_run as repo_create_run
        
        run = repo_create_run(
            db,
            project_id=request.project_id,
            mode=request.mode,
            config=request.config
        )
        
        return RunResponse(
            id=run.id,
            project_id=run.project_id,
            mode=run.mode,
            config=run.config,
            status=run.status.value if hasattr(run.status, 'value') else str(run.status),
            created_at=run.created_at.isoformat() if run.created_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )
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
        
        return RunResponse(
            id=run.id,
            project_id=run.project_id,
            mode=run.mode,
            config=run.config,
            status=run.status.value if hasattr(run.status, 'value') else str(run.status),
            created_at=run.created_at.isoformat() if run.created_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )
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
        
        # Get scores from evaluations if available
        ranker_service = RankerService(db)
        # Try to get ranked candidates (this will compute scores if not already computed)
        scores_map: dict[str, dict] = {}
        try:
            ranked_result = ranker_service.rank_candidates(run_id)
            # Create a map of candidate_id -> scores
            for ranked in ranked_result.get('ranked_candidates', []):
                candidate_id = ranked.get('id')
                if candidate_id:
                    scores_map[candidate_id] = {
                        'P': ranked.get('P'),
                        'R': ranked.get('R'),
                        'I': ranked.get('I'),
                    }
                    constraint_flags = ranked.get('constraint_flags', [])
                    if constraint_flags:
                        scores_map[candidate_id]['constraint_flags'] = constraint_flags
        except Exception as e:
            # If ranking fails, just return candidates without scores
            logger.warning(f"Could not get ranked candidates for run {run_id}: {e}")
        
        return [
            CandidateResponse(
                id=c.id,
                run_id=c.run_id,
                project_id=c.project_id,
                origin=c.origin,
                mechanism_description=c.mechanism_description,
                predicted_effects=c.predicted_effects,
                scores=scores_map.get(c.id) if c.id in scores_map else None,
                constraint_flags=scores_map.get(c.id, {}).get('constraint_flags') if c.id in scores_map else None,
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
        if guidance_type in ["spec_refinement", "setup_guidance"] or workflow_stage == "setup":
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
                    # Fallback: infer delta from user query
                    query_lower = user_query.lower()
                    constraint_names_in_query = []
                    
                    # Check for constraint-related keywords
                    if any(word in query_lower for word in ["constraint", "budget", "cost", "price", "size", "dimension", "maintain", "clean", "safety", "stimulation"]):
                        # Try to extract constraint names or infer from context
                        if "budget" in query_lower or "$" in query_lower or "cost" in query_lower or "price" in query_lower:
                            constraint_names_in_query.append("Budget")
                        if "size" in query_lower or "dimension" in query_lower or "x" in query_lower or "feet" in query_lower or "ft" in query_lower or "'" in query_lower:
                            constraint_names_in_query.append("Size")
                        if "maintain" in query_lower or "clean" in query_lower:
                            constraint_names_in_query.append("Maintenance")
                        if "safety" in query_lower:
                            constraint_names_in_query.append("Safety")
                        if "stimulation" in query_lower or "stimulate" in query_lower:
                            constraint_names_in_query.append("Stimulation")
                        
                        # If we found constraint mentions, create delta
                        if constraint_names_in_query:
                            logger.info(f"Creating fallback delta for constraints: {constraint_names_in_query}")
                            spec_delta = {
                                "touched_sections": ["constraints"],
                                "constraints": {
                                    "added": [],
                                    "updated": [{"name": name} for name in constraint_names_in_query],
                                    "removed": []
                                },
                                "goals": {"added": [], "updated": [], "removed": []},
                                "resolution_changed": False,
                                "mode_changed": False
                            }
                    
                    # Check for goal-related keywords
                    if "goal" in query_lower and not constraint_names_in_query:
                        logger.info("Creating fallback delta for goals")
                        spec_delta = {
                            "touched_sections": ["goals"],
                            "constraints": {"added": [], "updated": [], "removed": []},
                            "goals": {
                                "added": ["Updated goal"],
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
        
        # Add deltas to metadata if present
        if spec_delta:
            message_metadata["spec_delta"] = spec_delta
        if world_model_delta:
            message_metadata["world_model_delta"] = world_model_delta
        if touched_sections:
            # Remove duplicates and create aggregated summary
            message_metadata["touched_sections"] = list(set(touched_sections))
        
        # Add suggested actions to metadata if present
        if guidance_result.get("suggested_actions"):
            message_metadata["suggested_actions"] = guidance_result["suggested_actions"]
        
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


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "crucible.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )

