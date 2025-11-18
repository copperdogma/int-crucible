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


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "crucible.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )

