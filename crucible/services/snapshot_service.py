"""
Snapshot Service.

Service layer for snapshot management, replay, and invariant validation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from crucible.db.repositories import (
    create_snapshot,
    get_snapshot,
    list_snapshots,
    get_problem_spec,
    get_world_model,
    get_run,
    create_project,
    create_problem_spec,
    create_world_model,
    create_run,
    list_chat_sessions,
    list_messages,
    get_project,
)
from crucible.db.models import ChatSessionMode
from crucible.services.run_service import RunService
from crucible.services.run_verification import (
    verify_run_completeness,
    get_run_statistics,
)
from crucible.utils.llm_usage import aggregate_usage

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for snapshot management and replay."""

    def __init__(self, session: Session):
        """
        Initialize Snapshot service.

        Args:
            session: Database session
        """
        self.session = session
        self.run_service = RunService(session)

    def capture_snapshot_data(
        self,
        project_id: str,
        run_id: Optional[str] = None,
        include_chat_context: bool = True,
        max_chat_messages: int = 10
    ) -> Dict[str, Any]:
        """
        Capture snapshot data from a project (and optionally a run).

        Args:
            project_id: Project ID to capture
            run_id: Optional run ID to capture metrics from
            include_chat_context: Whether to include chat messages
            max_chat_messages: Maximum number of chat messages to include

        Returns:
            dict with snapshot_data structure:
                - version: str
                - problem_spec: dict (full ProblemSpec data)
                - world_model: dict (full WorldModel data)
                - run_config: dict (run configuration if run_id provided)
                - chat_context: list (optional chat messages)
        """
        # Get ProblemSpec (using raw SQL to avoid SQLAlchemy metadata caching issues)
        from sqlalchemy import text, inspect
        from sqlalchemy.engine import reflection
        
        # Check what columns actually exist
        inspector = inspect(self.session.bind)
        columns = {col['name'] for col in inspector.get_columns('crucible_problem_specs')}
        
        # Build SELECT query based on available columns
        select_cols = ['constraints', 'goals', 'resolution', 'mode']
        if 'provenance_log' in columns:
            select_cols.append('provenance_log')
        
        query = f"SELECT {', '.join(select_cols)} FROM crucible_problem_specs WHERE project_id = :project_id"
        result = self.session.execute(text(query), {"project_id": project_id}).fetchone()
        
        if not result:
            raise ValueError(f"ProblemSpec not found for project {project_id}")
        
        # Create a simple dict-like object
        class SimpleProblemSpec:
            def __init__(self, row, cols):
                import json
                self.constraints = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or [])
                self.goals = json.loads(row[1]) if isinstance(row[1], str) else (row[1] or [])
                self.resolution = row[2]
                self.mode = row[3]
                if 'provenance_log' in cols:
                    self.provenance_log = json.loads(row[4]) if isinstance(row[4], str) else (row[4] or [])
                else:
                    self.provenance_log = []
        
        problem_spec = SimpleProblemSpec(result, columns)

        if problem_spec is None:
            raise ValueError(f"ProblemSpec not found for project {project_id}")

        # Get WorldModel (using raw SQL)
        result = self.session.execute(
            text("SELECT model_data FROM crucible_world_models WHERE project_id = :project_id"),
            {"project_id": project_id}
        ).fetchone()
        
        if not result:
            raise ValueError(f"WorldModel not found for project {project_id}")
        
        # Create a simple dict-like object
        import json
        model_data = result[0]
        if isinstance(model_data, str):
            model_data = json.loads(model_data)
        
        class SimpleWorldModel:
            def __init__(self, data):
                self.model_data = data or {}
        
        world_model = SimpleWorldModel(model_data)

        if world_model is None:
            raise ValueError(f"WorldModel not found for project {project_id}")

        # Handle resolution and mode (may be strings from raw SQL or enum objects)
        resolution = problem_spec.resolution
        if hasattr(resolution, 'value'):
            resolution = resolution.value
        
        mode = problem_spec.mode
        if hasattr(mode, 'value'):
            mode = mode.value
        
        snapshot_data = {
            "version": "1.0",
            "problem_spec": {
                "constraints": problem_spec.constraints or [],
                "goals": problem_spec.goals or [],
                "resolution": resolution,
                "mode": mode,
                "provenance_log": problem_spec.provenance_log or [],
            },
            "world_model": {
                "model_data": world_model.model_data or {},
            },
        }

        # Add run config if run_id provided
        if run_id:
            run = get_run(self.session, run_id)
            if run:
                snapshot_data["run_config"] = {
                    "mode": run.mode.value if run.mode else None,
                    "config": run.config or {},
                }

        # Optionally add chat context
        if include_chat_context:
            chat_sessions = list_chat_sessions(self.session, project_id=project_id)
            # Get setup chat sessions (most recent first)
            setup_sessions = [
                cs for cs in chat_sessions
                if cs.mode == ChatSessionMode.SETUP
            ]
            if setup_sessions:
                # Get last N messages from most recent setup session
                latest_session = setup_sessions[0]
                messages = list_messages(self.session, latest_session.id)
                # Take last N messages
                recent_messages = messages[-max_chat_messages:] if len(messages) > max_chat_messages else messages
                snapshot_data["chat_context"] = [
                    {
                        "id": m.id,
                        "role": m.role.value,
                        "content": m.content,
                        "message_metadata": m.message_metadata,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in recent_messages
                ]

        return snapshot_data

    def capture_reference_metrics(self, run_id: str) -> Dict[str, Any]:
        """
        Capture reference metrics from a run.

        Args:
            run_id: Run ID to capture metrics from

        Returns:
            dict with reference metrics
        """
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        # Get run statistics
        stats = get_run_statistics(self.session, run_id)
        
        # Get top candidate I-score if available
        top_i_score = None
        if stats.get("candidates"):
            candidates = stats["candidates"]
            if candidates:
                # Sort by I-score (descending)
                sorted_candidates = sorted(
                    candidates,
                    key=lambda c: c.get("scores", {}).get("I", 0) or 0,
                    reverse=True
                )
                if sorted_candidates:
                    top_i_score = sorted_candidates[0].get("scores", {}).get("I")

        return {
            "candidate_count": run.candidate_count or 0,
            "scenario_count": run.scenario_count or 0,
            "evaluation_count": run.evaluation_count or 0,
            "status": run.status.value if run.status else None,
            "duration_seconds": run.duration_seconds,
            "llm_usage": run.llm_usage,
            "error_summary": run.error_summary,
            "top_i_score": top_i_score,
            "metrics": run.metrics,
        }

    def restore_snapshot_data(
        self,
        project_id: str,
        snapshot_data: Dict[str, Any]
    ) -> None:
        """
        Restore snapshot data into a project.

        Args:
            project_id: Project ID to restore into
            snapshot_data: Snapshot data dict
        """
        version = snapshot_data.get("version", "1.0")
        
        # Handle version compatibility (for future migrations)
        if version == "1.0":
            # Restore ProblemSpec using raw SQL to avoid schema issues
            from sqlalchemy import text, inspect
            import json
            import uuid
            
            problem_spec_data = snapshot_data.get("problem_spec", {})
            
            # Check if ProblemSpec exists
            existing = self.session.execute(
                text("SELECT id FROM crucible_problem_specs WHERE project_id = :project_id"),
                {"project_id": project_id}
            ).fetchone()
            
            constraints_json = json.dumps(problem_spec_data.get("constraints", []))
            goals_json = json.dumps(problem_spec_data.get("goals", []))
            resolution = problem_spec_data.get("resolution")
            mode = problem_spec_data.get("mode")
            provenance_log_json = json.dumps(problem_spec_data.get("provenance_log", []))
            
            if existing:
                # Update existing using raw SQL
                spec_id = existing[0]
                # Check if provenance_log column exists
                inspector = inspect(self.session.bind)
                columns = {col['name'] for col in inspector.get_columns('crucible_problem_specs')}
                
                if 'provenance_log' in columns:
                    self.session.execute(
                        text("""
                            UPDATE crucible_problem_specs 
                            SET constraints = :constraints,
                                goals = :goals,
                                resolution = :resolution,
                                mode = :mode,
                                provenance_log = :provenance_log,
                                updated_at = :updated_at
                            WHERE id = :spec_id
                        """),
                        {
                            "spec_id": spec_id,
                            "constraints": constraints_json,
                            "goals": goals_json,
                            "resolution": resolution,
                            "mode": mode,
                            "provenance_log": provenance_log_json,
                            "updated_at": datetime.utcnow()
                        }
                    )
                else:
                    self.session.execute(
                        text("""
                            UPDATE crucible_problem_specs 
                            SET constraints = :constraints,
                                goals = :goals,
                                resolution = :resolution,
                                mode = :mode,
                                updated_at = :updated_at
                            WHERE id = :spec_id
                        """),
                        {
                            "spec_id": spec_id,
                            "constraints": constraints_json,
                            "goals": goals_json,
                            "resolution": resolution,
                            "mode": mode,
                            "updated_at": datetime.utcnow()
                        }
                    )
                self.session.commit()
            else:
                # Create new using raw SQL
                spec_id = str(uuid.uuid4())
                inspector = inspect(self.session.bind)
                columns = {col['name'] for col in inspector.get_columns('crucible_problem_specs')}
                
                if 'provenance_log' in columns:
                    self.session.execute(
                        text("""
                            INSERT INTO crucible_problem_specs 
                            (id, project_id, constraints, goals, resolution, mode, provenance_log, created_at, updated_at)
                            VALUES (:id, :project_id, :constraints, :goals, :resolution, :mode, :provenance_log, :created_at, :updated_at)
                        """),
                        {
                            "id": spec_id,
                            "project_id": project_id,
                            "constraints": constraints_json,
                            "goals": goals_json,
                            "resolution": resolution,
                            "mode": mode,
                            "provenance_log": provenance_log_json,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    )
                else:
                    self.session.execute(
                        text("""
                            INSERT INTO crucible_problem_specs 
                            (id, project_id, constraints, goals, resolution, mode, created_at, updated_at)
                            VALUES (:id, :project_id, :constraints, :goals, :resolution, :mode, :created_at, :updated_at)
                        """),
                        {
                            "id": spec_id,
                            "project_id": project_id,
                            "constraints": constraints_json,
                            "goals": goals_json,
                            "resolution": resolution,
                            "mode": mode,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    )
                self.session.commit()

            # Restore WorldModel using raw SQL
            world_model_data = snapshot_data.get("world_model", {})
            model_data_json = json.dumps(world_model_data.get("model_data", {}))
            
            existing_model = self.session.execute(
                text("SELECT id FROM crucible_world_models WHERE project_id = :project_id"),
                {"project_id": project_id}
            ).fetchone()
            
            if existing_model:
                # Update existing
                model_id = existing_model[0]
                self.session.execute(
                    text("""
                        UPDATE crucible_world_models 
                        SET model_data = :model_data,
                            updated_at = :updated_at
                        WHERE id = :model_id
                    """),
                    {
                        "model_id": model_id,
                        "model_data": model_data_json,
                        "updated_at": datetime.utcnow()
                    }
                )
                self.session.commit()
            else:
                # Create new
                model_id = str(uuid.uuid4())
                self.session.execute(
                    text("""
                        INSERT INTO crucible_world_models 
                        (id, project_id, model_data, created_at, updated_at)
                        VALUES (:id, :project_id, :model_data, :created_at, :updated_at)
                    """),
                    {
                        "id": model_id,
                        "project_id": project_id,
                        "model_data": model_data_json,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                )
                self.session.commit()
        else:
            raise ValueError(f"Unsupported snapshot version: {version}")

    def replay_snapshot(
        self,
        snapshot_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Replay a snapshot by creating a new run and executing the pipeline.

        Args:
            snapshot_id: Snapshot ID to replay
            options: Replay options:
                - reuse_project: bool (default False, creates temp project)
                - phases: str (default "full", can be "design", "evaluate", "full")
                - num_candidates: int (override snapshot config)
                - num_scenarios: int (override snapshot config)

        Returns:
            dict with:
                - replay_run_id: str
                - project_id: str
                - status: str
                - results: dict (pipeline execution results)
        """
        options = options or {}
        reuse_project = options.get("reuse_project", False)
        phases = options.get("phases", "full")
        num_candidates = options.get("num_candidates")
        num_scenarios = options.get("num_scenarios")

        # Get snapshot
        snapshot = get_snapshot(self.session, snapshot_id)
        if snapshot is None:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        snapshot_data = snapshot.get_snapshot_data()
        run_config = snapshot_data.get("run_config", {})

        # Create or reuse project
        if reuse_project:
            project_id = snapshot.project_id
            project = get_project(self.session, project_id)
            if project is None:
                raise ValueError(f"Project not found: {project_id}")
        else:
            # Create temporary project
            project_id = str(uuid.uuid4())
            project = create_project(
                self.session,
                title=f"Snapshot Replay: {snapshot.name}",
                description=f"Temporary project for replaying snapshot {snapshot.name}",
                project_id=project_id
            )

        # Restore snapshot data
        self.restore_snapshot_data(project_id, snapshot_data)

        # Create new run
        from crucible.db.models import RunMode, RunStatus
        run_mode = RunMode(run_config.get("mode", "full_search"))
        run_config_dict = run_config.get("config", {})
        
        # Override with options if provided
        if num_candidates is not None:
            run_config_dict["num_candidates"] = num_candidates
        if num_scenarios is not None:
            run_config_dict["num_scenarios"] = num_scenarios

        run = create_run(
            self.session,
            project_id=project_id,
            mode=run_mode.value,
            config=run_config_dict
        )

        # Execute pipeline based on phases
        try:
            if phases == "full":
                result = self.run_service.execute_full_pipeline(
                    run_id=run.id,
                    num_candidates=run_config_dict.get("num_candidates", 5),
                    num_scenarios=run_config_dict.get("num_scenarios", 8)
                )
            elif phases == "design":
                result = self.run_service.execute_design_and_scenario_phase(
                    run_id=run.id,
                    num_candidates=run_config_dict.get("num_candidates", 5),
                    num_scenarios=run_config_dict.get("num_scenarios", 8)
                )
            elif phases == "evaluate":
                result = self.run_service.execute_evaluate_and_rank_phase(
                    run_id=run.id
                )
            else:
                raise ValueError(f"Invalid phases option: {phases}")

            return {
                "replay_run_id": run.id,
                "project_id": project_id,
                "status": "completed",
                "results": result,
            }
        except Exception as e:
            logger.error(f"Error replaying snapshot {snapshot_id}: {e}", exc_info=True)
            # Update run status to failed
            from crucible.db.repositories import update_run_status
            from crucible.db.models import RunStatus
            update_run_status(self.session, run.id, RunStatus.FAILED.value)
            raise

    def validate_invariants(
        self,
        run_id: str,
        invariants: List[Dict[str, Any]],
        reference_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate invariants against a run.

        Args:
            run_id: Run ID to validate
            invariants: List of invariant definitions
            reference_metrics: Optional reference metrics for comparison

        Returns:
            dict with:
                - all_passed: bool
                - results: list of invariant validation results
        """
        # Get run statistics
        stats = get_run_statistics(self.session, run_id)
        completeness = verify_run_completeness(self.session, run_id)
        
        run = get_run(self.session, run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        results = []
        all_passed = True

        for invariant in invariants:
            inv_type = invariant.get("type")
            expected_value = invariant.get("value")
            description = invariant.get("description", "")

            result = {
                "type": inv_type,
                "description": description,
                "expected": expected_value,
                "status": "unknown",
                "actual": None,
                "message": "",
            }

            try:
                if inv_type == "min_candidates":
                    actual = stats.get("candidate_count", 0)
                    result["actual"] = actual
                    if actual >= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected at least {expected_value} candidates, got {actual}"
                        all_passed = False

                elif inv_type == "max_candidates":
                    actual = stats.get("candidate_count", 0)
                    result["actual"] = actual
                    if actual <= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected at most {expected_value} candidates, got {actual}"
                        all_passed = False

                elif inv_type == "min_scenarios":
                    actual = stats.get("scenario_count", 0)
                    result["actual"] = actual
                    if actual >= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected at least {expected_value} scenarios, got {actual}"
                        all_passed = False

                elif inv_type == "max_scenarios":
                    actual = stats.get("scenario_count", 0)
                    result["actual"] = actual
                    if actual <= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected at most {expected_value} scenarios, got {actual}"
                        all_passed = False

                elif inv_type == "run_status":
                    actual = run.status.value if run.status else None
                    result["actual"] = actual
                    if actual == expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected status {expected_value}, got {actual}"
                        all_passed = False

                elif inv_type == "min_top_i_score":
                    # Get top candidate I-score
                    top_i_score = None
                    if stats.get("candidates"):
                        candidates = stats["candidates"]
                        if candidates:
                            sorted_candidates = sorted(
                                candidates,
                                key=lambda c: c.get("scores", {}).get("I", 0) or 0,
                                reverse=True
                            )
                            if sorted_candidates:
                                top_i_score = sorted_candidates[0].get("scores", {}).get("I")
                    
                    result["actual"] = top_i_score
                    if top_i_score is not None and top_i_score >= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected top I-score >= {expected_value}, got {top_i_score}"
                        all_passed = False

                elif inv_type == "max_top_i_score":
                    # Get top candidate I-score
                    top_i_score = None
                    if stats.get("candidates"):
                        candidates = stats["candidates"]
                        if candidates:
                            sorted_candidates = sorted(
                                candidates,
                                key=lambda c: c.get("scores", {}).get("I", 0) or 0,
                                reverse=True
                            )
                            if sorted_candidates:
                                top_i_score = sorted_candidates[0].get("scores", {}).get("I")
                    
                    result["actual"] = top_i_score
                    if top_i_score is not None and top_i_score <= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected top I-score <= {expected_value}, got {top_i_score}"
                        all_passed = False

                elif inv_type == "no_hard_constraint_violations":
                    # Check if any candidates violate hard constraints (weight=100)
                    violations = []
                    if stats.get("candidates"):
                        candidates = stats["candidates"]
                        for candidate in candidates:
                            constraint_satisfaction = candidate.get("scores", {}).get("constraint_satisfaction", {})
                            if isinstance(constraint_satisfaction, dict):
                                for constraint_name, satisfied in constraint_satisfaction.items():
                                    if satisfied is False:
                                        # Check if this is a hard constraint
                                        # We'd need ProblemSpec to check weights, but for MVP we'll assume
                                        # any False constraint_satisfaction is a violation
                                        violations.append(f"{candidate.get('id')}: {constraint_name}")
                    
                    result["actual"] = len(violations) == 0
                    if len(violations) == 0:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Found {len(violations)} hard constraint violations: {', '.join(violations[:5])}"
                        all_passed = False

                elif inv_type == "max_duration_seconds":
                    actual = run.duration_seconds
                    result["actual"] = actual
                    if actual is not None and actual <= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected duration <= {expected_value}s, got {actual}s"
                        all_passed = False

                elif inv_type == "min_evaluation_coverage":
                    candidate_count = stats.get("candidate_count", 0)
                    scenario_count = stats.get("scenario_count", 0)
                    evaluation_count = stats.get("evaluation_count", 0)
                    expected_evaluations = candidate_count * scenario_count
                    
                    if expected_evaluations == 0:
                        coverage = 1.0  # No candidates/scenarios means 100% coverage
                    else:
                        coverage = evaluation_count / expected_evaluations
                    
                    result["actual"] = coverage
                    if coverage >= expected_value:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["message"] = f"Expected evaluation coverage >= {expected_value}, got {coverage:.2f}"
                        all_passed = False

                else:
                    result["status"] = "error"
                    result["message"] = f"Unknown invariant type: {inv_type}"
                    all_passed = False

            except Exception as e:
                logger.error(f"Error validating invariant {inv_type}: {e}", exc_info=True)
                result["status"] = "error"
                result["message"] = f"Error validating invariant: {str(e)}"
                all_passed = False

            results.append(result)

        return {
            "all_passed": all_passed,
            "results": results,
        }

    def run_snapshot_tests(
        self,
        snapshot_ids: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run tests for one or more snapshots.

        Args:
            snapshot_ids: List of snapshot IDs to test (None = all snapshots)
            options: Test options:
                - max_snapshots: int (max number to test)
                - phases: str (default "full")
                - num_candidates: int (override)
                - num_scenarios: int (override)
                - stop_on_first_failure: bool (default False)
                - cost_limit_usd: float (default None, no limit)

        Returns:
            dict with test results summary and details
        """
        options = options or {}
        max_snapshots = options.get("max_snapshots")
        stop_on_first_failure = options.get("stop_on_first_failure", False)
        cost_limit_usd = options.get("cost_limit_usd")
        
        # Get snapshots to test
        if snapshot_ids is None:
            all_snapshots = list_snapshots(self.session)
            snapshot_ids = [s.id for s in all_snapshots]
        
        if max_snapshots:
            snapshot_ids = snapshot_ids[:max_snapshots]

        results = []
        total_cost_usd = 0.0
        passed_count = 0
        failed_count = 0
        skipped_count = 0

        for snapshot_id in snapshot_ids:
            snapshot = get_snapshot(self.session, snapshot_id)
            if snapshot is None:
                skipped_count += 1
                results.append({
                    "snapshot_id": snapshot_id,
                    "snapshot_name": "Unknown",
                    "status": "skipped",
                    "message": "Snapshot not found",
                })
                continue

            # Check cost limit
            if cost_limit_usd is not None and total_cost_usd >= cost_limit_usd:
                skipped_count += 1
                results.append({
                    "snapshot_id": snapshot_id,
                    "snapshot_name": snapshot.name,
                    "status": "skipped",
                    "message": f"Cost limit ({cost_limit_usd}) exceeded",
                })
                continue

            try:
                # Replay snapshot
                replay_result = self.replay_snapshot(snapshot_id, options)
                replay_run_id = replay_result["replay_run_id"]

                # Get replay run metrics
                replay_run = get_run(self.session, replay_run_id)
                replay_cost = 0.0
                if replay_run and replay_run.llm_usage:
                    # Extract cost from llm_usage
                    total_usage = replay_run.llm_usage.get("total", {})
                    replay_cost = total_usage.get("cost_usd", 0.0) or 0.0
                
                total_cost_usd += replay_cost

                # Validate invariants
                invariants = snapshot.get_invariants()
                reference_metrics = snapshot.reference_metrics
                
                validation_result = self.validate_invariants(
                    replay_run_id,
                    invariants,
                    reference_metrics
                )

                # Compare metrics
                metrics_delta = {}
                if reference_metrics:
                    metrics_delta = {
                        "candidate_count": {
                            "baseline": reference_metrics.get("candidate_count", 0),
                            "replay": replay_run.candidate_count or 0,
                            "delta": (replay_run.candidate_count or 0) - reference_metrics.get("candidate_count", 0),
                        },
                        "scenario_count": {
                            "baseline": reference_metrics.get("scenario_count", 0),
                            "replay": replay_run.scenario_count or 0,
                            "delta": (replay_run.scenario_count or 0) - reference_metrics.get("scenario_count", 0),
                        },
                        "duration_seconds": {
                            "baseline": reference_metrics.get("duration_seconds"),
                            "replay": replay_run.duration_seconds,
                            "delta": (replay_run.duration_seconds or 0) - (reference_metrics.get("duration_seconds") or 0),
                        },
                    }

                status = "passed" if validation_result["all_passed"] else "failed"
                if status == "passed":
                    passed_count += 1
                else:
                    failed_count += 1

                results.append({
                    "snapshot_id": snapshot_id,
                    "snapshot_name": snapshot.name,
                    "status": status,
                    "replay_run_id": replay_run_id,
                    "invariants": validation_result["results"],
                    "metrics_delta": metrics_delta,
                    "cost_usd": replay_cost,
                })

                # Stop on first failure if requested
                if stop_on_first_failure and status == "failed":
                    break

            except Exception as e:
                logger.error(f"Error testing snapshot {snapshot_id}: {e}", exc_info=True)
                failed_count += 1
                results.append({
                    "snapshot_id": snapshot_id,
                    "snapshot_name": snapshot.name if snapshot else "Unknown",
                    "status": "failed",
                    "message": f"Error during replay: {str(e)}",
                })
                if stop_on_first_failure:
                    break

        return {
            "summary": {
                "total": len(snapshot_ids),
                "passed": passed_count,
                "failed": failed_count,
                "skipped": skipped_count,
            },
            "results": results,
            "total_cost_usd": total_cost_usd,
        }

