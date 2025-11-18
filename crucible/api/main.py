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
from crucible.services.designer_service import DesignerService
from crucible.services.scenario_service import ScenarioService
from crucible.services.evaluator_service import EvaluatorService
from crucible.services.ranker_service import RankerService
from crucible.services.run_service import RunService
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


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "crucible.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )

