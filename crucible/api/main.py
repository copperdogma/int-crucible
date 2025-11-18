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
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from crucible.config import get_config
from crucible.db.session import get_session
from crucible.services.problemspec_service import ProblemSpecService
from crucible.services.worldmodel_service import WorldModelService
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


class WorldModelUpdateRequest(BaseModel):
    """Request model for manual WorldModel update."""
    model_data: dict
    source: str = "manual_edit"


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


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "crucible.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )

