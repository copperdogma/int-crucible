"""
Command-line interface for Int Crucible.

Provides CLI commands for interacting with the Int Crucible system,
including Kosmos integration testing.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, List
import time
import json
from datetime import datetime, timedelta

from crucible.config import get_config
from crucible.db.session import get_session
from crucible.services.run_service import RunService
from crucible.services.run_verification import (
    verify_run_completeness,
    verify_data_integrity,
    get_run_statistics
)
from crucible.db.repositories import (
    get_run,
    get_project,
    get_problem_spec,
    get_world_model,
    create_run,
    list_projects,
    get_snapshot,
    list_snapshots,
    create_snapshot,
    delete_snapshot,
)
from crucible.db.models import RunMode, Run, RunStatus
from crucible.services.snapshot_service import SnapshotService

app = typer.Typer(
    name="crucible",
    help="Int Crucible - A general multi-agent reasoning system",
    add_completion=False
)
console = Console()


@app.command()
def version():
    """Show version information."""
    console.print("[bold blue]Int Crucible[/bold blue] v0.1.0")
    console.print("A general multi-agent reasoning system")


@app.command()
def config():
    """Show current configuration."""
    config = get_config()
    
    table = Table(title="Int Crucible Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Database URL", config.database_url)
    table.add_row("Log Level", config.log_level)
    table.add_row("API Host", config.api_host)
    table.add_row("API Port", str(config.api_port))
    
    console.print(table)


@app.command()
def kosmos_agents():
    """
    List available Kosmos agents.
    
    This is a smoke test to verify Kosmos integration is working.
    """
    try:
        from kosmos.agents.registry import AgentRegistry
        
        console.print("[bold blue]Kosmos Agent Registry[/bold blue]")
        console.print("")
        
        registry = AgentRegistry()
        agents = registry.list_agents()
        
        if not agents:
            console.print("[yellow]No agents found in registry[/yellow]")
            return
        
        table = Table(title="Available Kosmos Agents")
        table.add_column("Agent Name", style="cyan")
        table.add_column("Type", style="green")
        
        for agent_name in agents:
            # Try to get agent class info
            try:
                agent_class = registry.get(agent_name)
                agent_type = agent_class.__name__ if agent_class else "Unknown"
            except:
                agent_type = "Unknown"
            
            table.add_row(agent_name, agent_type)
        
        console.print(table)
        console.print(f"\n[green]✓[/green] Found {len(agents)} agent(s)")
        
    except ImportError as e:
        console.print(f"[red]✗[/red] Failed to import Kosmos: {e}")
        console.print("\n[yellow]Hint:[/yellow] Install Kosmos with:")
        console.print("  [cyan]pip install -e vendor/kosmos[/cyan]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error accessing Kosmos agents: {e}")
        raise typer.Exit(1)


@app.command()
def kosmos_test():
    """
    Test Kosmos integration with a simple operation.
    
    Performs a minimal smoke test to verify Kosmos is properly integrated.
    """
    try:
        from kosmos.config import get_config as get_kosmos_config
        from kosmos.agents.registry import AgentRegistry
        
        console.print("[bold blue]Testing Kosmos Integration[/bold blue]")
        console.print("")
        
        # Test 1: Config access
        console.print("[cyan]1. Testing Kosmos configuration...[/cyan]")
        try:
            kosmos_config = get_kosmos_config()
            console.print("   [green]✓[/green] Kosmos config loaded")
            
            # Try to access LLM provider info
            if hasattr(kosmos_config, 'llm'):
                provider = kosmos_config.llm.provider if hasattr(kosmos_config.llm, 'provider') else "unknown"
                console.print(f"   [green]✓[/green] LLM Provider: {provider}")
        except Exception as e:
            console.print(f"   [red]✗[/red] Failed to load Kosmos config: {e}")
            raise typer.Exit(1)
        
        # Test 2: Database initialization
        console.print("[cyan]2. Testing database connection...[/cyan]")
        try:
            from kosmos.db import init_from_config
            init_from_config()
            console.print("   [green]✓[/green] Database initialized")
        except Exception as e:
            console.print(f"   [yellow]⚠[/yellow] Database initialization warning: {e}")
            console.print("   [yellow]   (This may be expected if database is not configured)[/yellow]")
        
        # Test 3: Agent registry
        console.print("[cyan]3. Testing agent registry...[/cyan]")
        try:
            registry = AgentRegistry()
            agents = registry.list_agents()
            console.print(f"   [green]✓[/green] Found {len(agents)} agent(s) in registry")
        except Exception as e:
            console.print(f"   [red]✗[/red] Failed to access agent registry: {e}")
            raise typer.Exit(1)
        
        console.print("")
        console.print("[bold green]✓ All tests passed! Kosmos integration is working.[/bold green]")
        
    except ImportError as e:
        console.print(f"[red]✗[/red] Failed to import Kosmos: {e}")
        console.print("\n[yellow]Hint:[/yellow] Install Kosmos with:")
        console.print("  [cyan]pip install -e vendor/kosmos[/cyan]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error testing Kosmos: {e}")
        raise typer.Exit(1)


@app.command()
def runs(
    project_id: str = typer.Option(..., "--project-id", "-p", help="Project ID to inspect"),
    status: Optional[List[str]] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by run status (repeatable: completed, failed, running, ...)",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of runs to display"),
    offset: int = typer.Option(0, "--offset", help="Pagination offset"),
    since_hours: Optional[int] = typer.Option(
        None,
        "--since-hours",
        help="Only include runs created within the last N hours",
    ),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table (default) or json",
    ),
):
    """
    List recent runs for a project with observability metrics.
    """
    fmt = output_format.lower()
    if fmt not in {"table", "json"}:
        raise typer.BadParameter("format must be either 'table' or 'json'")

    with get_session() as session:
        query = session.query(Run).filter(Run.project_id == project_id)

        if status:
            normalized_statuses = []
            for s in status:
                try:
                    normalized_statuses.append(RunStatus(s))
                except ValueError:
                    raise typer.BadParameter(f"Invalid status filter: {s}")
            if normalized_statuses:
                query = query.filter(Run.status.in_([st.value for st in normalized_statuses]))

        if since_hours:
            cutoff = datetime.utcnow() - timedelta(hours=since_hours)
            query = query.filter(Run.created_at >= cutoff)

        total = query.count()
        records = (
            query.order_by(Run.created_at.desc(), Run.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        def _run_to_dict(run: Run) -> dict:
            llm_total = None
            if run.llm_usage:
                llm_total = run.llm_usage.get("total") or {}
            return {
                "id": run.id,
                "project_id": run.project_id,
                "status": run.status.value if hasattr(run.status, "value") else str(run.status),
                "mode": run.mode.value if hasattr(run.mode, "value") else str(run.mode),
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "duration_seconds": run.duration_seconds,
                "candidate_count": run.candidate_count,
                "scenario_count": run.scenario_count,
                "evaluation_count": run.evaluation_count,
                "error_summary": run.error_summary,
                "llm_usage": run.llm_usage,
                "llm_calls": (llm_total or {}).get("call_count"),
                "llm_cost_usd": (llm_total or {}).get("cost_usd"),
            }

        if fmt == "json":
            payload = {
                "total": total,
                "offset": offset,
                "limit": limit,
                "runs": [_run_to_dict(run) for run in records],
            }
            console.print_json(data=json.dumps(payload, indent=2, default=str))
            return

        if not records:
            console.print(f"[yellow]No runs found for project {project_id}[/yellow]")
            return

        table = Table(title=f"Run History — Project {project_id}")
        table.add_column("Run ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Created", style="white")
        table.add_column("Duration (s)", justify="right")
        table.add_column("Counts (C/S/E)", justify="center")
        table.add_column("LLM Calls", justify="right")
        table.add_column("Cost ($)", justify="right")
        table.add_column("Error Summary", style="red")

        for run in records:
            run_dict = _run_to_dict(run)
            created_display = run.created_at.strftime("%Y-%m-%d %H:%M") if run.created_at else "-"
            duration_display = f"{run_dict['duration_seconds']:.1f}" if run_dict["duration_seconds"] else "-"
            counts_display = (
                f"{run_dict.get('candidate_count') or 0}/"
                f"{run_dict.get('scenario_count') or 0}/"
                f"{run_dict.get('evaluation_count') or 0}"
            )
            cost_display = "-"
            if run_dict.get("llm_cost_usd") is not None:
                cost_display = f"{run_dict['llm_cost_usd']:.4f}"
            error_display = "-"
            if run.error_summary:
                error_display = (run.error_summary[:60] + "…") if len(run.error_summary) > 60 else run.error_summary

            table.add_row(
                run.id,
                run_dict["status"],
                created_display,
                duration_display,
                counts_display,
                str(run_dict.get("llm_calls") or 0),
                cost_display,
                error_display or "-",
            )

        console.print(table)
        console.print(
            f"Showing {len(records)} of {total} runs (offset {offset}). "
            "Use --offset/--limit for pagination or --format json for automation."
        )


@app.command()
def test_run(
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="Project ID to test (creates test project if not provided)"),
    run_id: Optional[str] = typer.Option(None, "--run-id", "-r", help="Existing run ID to test (creates new run if not provided)"),
    num_candidates: int = typer.Option(5, "--candidates", "-c", help="Number of candidates to generate"),
    num_scenarios: int = typer.Option(8, "--scenarios", "-s", help="Number of scenarios to generate"),
    verify_only: bool = typer.Option(False, "--verify-only", help="Only verify existing run, don't execute pipeline"),
):
    """
    Test run execution with detailed progress reporting and verification.
    
    This command runs the full pipeline (Design → Scenarios → Evaluation → Ranking)
    with detailed instrumentation and verifies that all expected entities were created.
    
    Examples:
        # Test with existing project
        crucible test-run --project-id abc123
        
        # Test with existing run (verify only)
        crucible test-run --run-id xyz789 --verify-only
        
        # Test with custom parameters
        crucible test-run --project-id abc123 --candidates 10 --scenarios 12
    """
    try:
        with get_session() as session:
            # Determine project and run
            if run_id:
                # Verify existing run
                run = get_run(session, run_id)
                if run is None:
                    console.print(f"[red]✗[/red] Run not found: {run_id}")
                    raise typer.Exit(1)
                project_id = run.project_id
                console.print(f"[cyan]Using existing run: {run_id}[/cyan]")
            elif project_id:
                # Check if project exists and has prerequisites
                project = get_project(session, project_id)
                if project is None:
                    console.print(f"[red]✗[/red] Project not found: {project_id}")
                    raise typer.Exit(1)
                
                # Check prerequisites
                problem_spec = get_problem_spec(session, project_id)
                world_model = get_world_model(session, project_id)
                
                if not problem_spec:
                    console.print(f"[red]✗[/red] ProblemSpec not found for project {project_id}")
                    console.print("[yellow]Hint:[/yellow] Create a ProblemSpec first using the chat interface")
                    raise typer.Exit(1)
                
                if not world_model:
                    console.print(f"[red]✗[/red] WorldModel not found for project {project_id}")
                    console.print("[yellow]Hint:[/yellow] Create a WorldModel first using the chat interface")
                    raise typer.Exit(1)
                
                console.print(f"[green]✓[/green] Project {project_id} has ProblemSpec and WorldModel")
                
                if not verify_only:
                    # Create new run
                    run = create_run(
                        session,
                        project_id=project_id,
                        mode=RunMode.FULL_SEARCH.value,
                        config={"num_candidates": num_candidates, "num_scenarios": num_scenarios}
                    )
                    run_id = run.id
                    console.print(f"[cyan]Created new run: {run_id}[/cyan]")
            else:
                # List available projects
                projects = list_projects(session)
                if not projects:
                    console.print("[red]✗[/red] No projects found. Create a project first.")
                    raise typer.Exit(1)
                
                console.print("[yellow]Available projects:[/yellow]")
                for p in projects:
                    ps = get_problem_spec(session, p.id)
                    wm = get_world_model(session, p.id)
                    status = "✓" if (ps and wm) else "✗"
                    console.print(f"  {status} {p.id}: {p.title}")
                
                console.print("\n[yellow]Please specify a project ID with --project-id[/yellow]")
                raise typer.Exit(1)
            
            # Verify-only mode
            if verify_only:
                console.print(f"\n[bold blue]Verifying Run: {run_id}[/bold blue]\n")
                
                # Get statistics
                stats = get_run_statistics(session, run_id)
                if "error" in stats:
                    console.print(f"[red]✗[/red] {stats['error']}")
                    raise typer.Exit(1)
                
                # Display statistics
                stats_table = Table(title="Run Statistics", show_header=True, header_style="bold cyan")
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="green")
                
                stats_table.add_row("Run ID", stats["run_id"])
                stats_table.add_row("Project ID", stats["project_id"])
                stats_table.add_row("Status", stats["status"])
                stats_table.add_row("Candidates", str(stats["candidate_count"]))
                stats_table.add_row("Scenarios", str(stats["scenario_count"]))
                stats_table.add_row("Evaluations", str(stats["evaluation_count"]))
                stats_table.add_row("Has Rankings", "✓" if stats["has_rankings"] else "✗")
                if stats["duration_seconds"]:
                    stats_table.add_row("Duration", f"{stats['duration_seconds']:.2f}s")
                
                console.print(stats_table)
                
                # Verify completeness
                console.print("\n[cyan]Verifying completeness...[/cyan]")
                completeness = verify_run_completeness(session, run_id)
                
                if completeness["is_complete"]:
                    console.print("[green]✓ Run is complete[/green]")
                else:
                    console.print("[yellow]⚠ Run is incomplete[/yellow]")
                    if completeness.get("issues"):
                        for issue in completeness["issues"]:
                            console.print(f"  [yellow]•[/yellow] {issue}")
                
                # Verify integrity
                console.print("\n[cyan]Verifying data integrity...[/cyan]")
                integrity = verify_data_integrity(session, run_id)
                
                if integrity["is_valid"]:
                    console.print("[green]✓ Data integrity is valid[/green]")
                else:
                    console.print("[yellow]⚠ Data integrity issues found[/yellow]")
                    for issue in integrity["issues"]:
                        console.print(f"  [yellow]•[/yellow] {issue}")
                    for issue in integrity["candidate_issues"]:
                        console.print(f"  [yellow]•[/yellow] Candidate: {issue}")
                    for issue in integrity["evaluation_issues"]:
                        console.print(f"  [yellow]•[/yellow] Evaluation: {issue}")
                
                raise typer.Exit(0)
            
            # Execute pipeline
            console.print(f"\n[bold blue]Testing Run Execution: {run_id}[/bold blue]\n")
            console.print(f"[cyan]Configuration:[/cyan]")
            console.print(f"  Candidates: {num_candidates}")
            console.print(f"  Scenarios: {num_scenarios}")
            console.print("")
            
            service = RunService(session)
            
            # Execute with progress reporting
            start_time = time.time()
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("[cyan]Executing pipeline...", total=None)
                    
                    result = service.execute_full_pipeline(
                        run_id=run_id,
                        num_candidates=num_candidates,
                        num_scenarios=num_scenarios
                    )
                    
                    progress.update(task, completed=100)
                
                total_duration = time.time() - start_time
                
                # Display results
                console.print("\n[bold green]✓ Pipeline Execution Completed[/bold green]\n")
                
                results_table = Table(title="Execution Results", show_header=True, header_style="bold cyan")
                results_table.add_column("Phase", style="cyan")
                results_table.add_column("Result", style="green")
                
                results_table.add_row(
                    "Design",
                    f"{result['candidates']['count']} candidates generated"
                )
                results_table.add_row(
                    "Scenarios",
                    f"{result['scenarios']['count']} scenarios generated"
                )
                results_table.add_row(
                    "Evaluation",
                    f"{result['evaluations']['count']} evaluations created"
                )
                results_table.add_row(
                    "Ranking",
                    f"{result['rankings']['count']} candidates ranked"
                )
                
                if "timing" in result:
                    results_table.add_row(
                        "Total Duration",
                        f"{result['timing']['total']:.2f}s"
                    )
                    results_table.add_row(
                        "Phase 1 Duration",
                        f"{result['timing']['phase1']:.2f}s"
                    )
                    results_table.add_row(
                        "Phase 2 Duration",
                        f"{result['timing']['phase2']:.2f}s"
                    )
                
                console.print(results_table)
                
                # Verify completeness
                console.print("\n[cyan]Verifying run completeness...[/cyan]")
                completeness = verify_run_completeness(session, run_id)
                
                if completeness["is_complete"]:
                    console.print("[bold green]✓ Run verification passed![/bold green]")
                    console.print("  • All prerequisites present")
                    console.print(f"  • {completeness['candidate_count']} candidates created")
                    console.print(f"  • {completeness['scenario_count']} scenarios created")
                    console.print(f"  • {completeness['evaluation_count']} evaluations created")
                    console.print(f"  • Run status: {completeness['run_status']}")
                else:
                    console.print("[yellow]⚠ Run verification found issues:[/yellow]")
                    for issue in completeness.get("issues", []):
                        console.print(f"  [yellow]•[/yellow] {issue}")
                
                # Verify integrity
                console.print("\n[cyan]Verifying data integrity...[/cyan]")
                integrity = verify_data_integrity(session, run_id)
                
                if integrity["is_valid"]:
                    console.print("[green]✓ Data integrity verified[/green]")
                else:
                    console.print("[yellow]⚠ Data integrity issues:[/yellow]")
                    for issue in integrity.get("issues", []):
                        console.print(f"  [yellow]•[/yellow] {issue}")
                
                console.print(f"\n[bold green]✓ Test completed successfully![/bold green]")
                console.print(f"Run ID: {run_id}")
                
            except ValueError as e:
                console.print(f"\n[red]✗ Validation Error:[/red] {e}")
                raise typer.Exit(1)
            except Exception as e:
                console.print(f"\n[red]✗ Execution Error:[/red] {e}")
                console.print_exception()
                
                # Show run status
                run = get_run(session, run_id)
                if run:
                    console.print(f"\n[yellow]Run status: {run.status}[/yellow]")
                
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        console.print_exception()
        raise typer.Exit(1)


# Snapshot commands
snapshot_app = typer.Typer(help="Snapshot management commands")
app.add_typer(snapshot_app, name="snapshot")


@snapshot_app.command("create")
def snapshot_create(
    project_id: str = typer.Option(..., "--project-id", "-p", help="Project ID"),
    run_id: Optional[str] = typer.Option(None, "--run-id", "-r", help="Optional run ID to capture metrics from"),
    name: str = typer.Option(..., "--name", "-n", help="Snapshot name (must be unique)"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Snapshot description"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
    invariants_file: Optional[str] = typer.Option(None, "--invariants-file", help="Path to JSON file with invariants"),
):
    """
    Create a snapshot from a project (and optionally a run).
    
    Examples:
        crucible snapshot create --project-id abc123 --name "My Snapshot" --description "Test snapshot"
        crucible snapshot create --project-id abc123 --run-id xyz789 --name "Baseline" --tags "test,automated"
    """
    try:
        # Initialize database if needed
        try:
            from kosmos.db import init_from_config
            init_from_config()
        except Exception:
            pass  # May already be initialized
        
        with get_session() as session:
            # Parse tags
            tag_list = [t.strip() for t in tags.split(",")] if tags else None
            
            # Load invariants if file provided
            invariants = None
            if invariants_file:
                import json
                with open(invariants_file, 'r') as f:
                    invariants = json.load(f)
            
            # Create snapshot
            service = SnapshotService(session)
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Capturing snapshot data...", total=None)
                
                snapshot_data = service.capture_snapshot_data(
                    project_id=project_id,
                    run_id=run_id,
                    include_chat_context=False,  # Skip chat for CLI
                    max_chat_messages=0
                )
                
                reference_metrics = None
                if run_id:
                    progress.update(task, description="Capturing reference metrics...")
                    reference_metrics = service.capture_reference_metrics(run_id)
                
                progress.update(task, description="Creating snapshot record...")
                snapshot = create_snapshot(
                    session=session,
                    project_id=project_id,
                    run_id=run_id,
                    name=name,
                    description=description,
                    tags=tag_list,
                    invariants=invariants,
                    snapshot_data=snapshot_data,
                    reference_metrics=reference_metrics
                )
            
            console.print(f"\n[green]✓[/green] Created snapshot: {snapshot.id}")
            console.print(f"  Name: {snapshot.name}")
            console.print(f"  Version: {snapshot.version}")
            console.print(f"  Invariants: {len(snapshot.invariants or [])}")
            if snapshot.tags:
                console.print(f"  Tags: {', '.join(snapshot.tags)}")
            
    except ValueError as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error creating snapshot: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@snapshot_app.command("list")
def snapshot_list(
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="Filter by project ID"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Filter by tags (comma-separated)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter by name (partial match)"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table (default) or json"),
):
    """
    List snapshots with optional filters.
    
    Examples:
        crucible snapshot list
        crucible snapshot list --project-id abc123
        crucible snapshot list --tags test,automated
        crucible snapshot list --format json
    """
    try:
        # Initialize database if needed
        try:
            from kosmos.db import init_from_config
            init_from_config()
        except Exception:
            pass  # May already be initialized
        
        with get_session() as session:
            tag_list = [t.strip() for t in tags.split(",")] if tags else None
            
            snapshots = list_snapshots(
                session=session,
                project_id=project_id,
                tags=tag_list,
                name=name
            )
            
            if output_format.lower() == "json":
                import json
                result = [
                    {
                        "id": s.id,
                        "name": s.name,
                        "description": s.description,
                        "tags": s.tags or [],
                        "project_id": s.project_id,
                        "run_id": s.run_id,
                        "version": s.version,
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                    }
                    for s in snapshots
                ]
                console.print(json.dumps(result, indent=2))
            else:
                if not snapshots:
                    console.print("[yellow]No snapshots found[/yellow]")
                    return
                
                table = Table(title="Snapshots")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Project ID", style="blue")
                table.add_column("Tags", style="yellow")
                table.add_column("Created", style="dim")
                
                for s in snapshots:
                    tags_str = ", ".join(s.tags or []) if s.tags else "-"
                    created_str = s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "-"
                    table.add_row(
                        s.id[:8] + "...",
                        s.name[:40],
                        s.project_id[:8] + "...",
                        tags_str[:30],
                        created_str
                    )
                
                console.print(table)
                console.print(f"\nFound {len(snapshots)} snapshot(s)")
                
    except Exception as e:
        console.print(f"[red]✗[/red] Error listing snapshots: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@snapshot_app.command("show")
def snapshot_show(
    snapshot_id: str = typer.Argument(..., help="Snapshot ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Show details of a snapshot.
    
    Examples:
        crucible snapshot show abc123
        crucible snapshot show abc123 --json
    """
    try:
        # Initialize database if needed
        try:
            from kosmos.db import init_from_config
            init_from_config()
        except Exception:
            pass  # May already be initialized
        
        with get_session() as session:
            snapshot = get_snapshot(session, snapshot_id)
            if snapshot is None:
                console.print(f"[red]✗[/red] Snapshot not found: {snapshot_id}")
                raise typer.Exit(1)
            
            if json_output:
                import json
                console.print(json.dumps(snapshot.to_dict(), indent=2))
            else:
                console.print(f"\n[bold blue]Snapshot: {snapshot.name}[/bold blue]\n")
                console.print(f"ID: {snapshot.id}")
                console.print(f"Description: {snapshot.description or '(none)'}")
                console.print(f"Project ID: {snapshot.project_id}")
                console.print(f"Run ID: {snapshot.run_id or '(none)'}")
                console.print(f"Version: {snapshot.version}")
                console.print(f"Tags: {', '.join(snapshot.tags or [])}")
                console.print(f"Created: {snapshot.created_at}")
                console.print(f"Updated: {snapshot.updated_at}")
                
                invariants = snapshot.get_invariants()
                if invariants:
                    console.print(f"\n[bold]Invariants ({len(invariants)}):[/bold]")
                    for inv in invariants:
                        console.print(f"  - {inv.get('type')}: {inv.get('description', '')}")
                
                snapshot_data = snapshot.get_snapshot_data()
                console.print(f"\n[bold]Snapshot Data:[/bold]")
                console.print(f"  ProblemSpec: {'✓' if 'problem_spec' in snapshot_data else '✗'}")
                console.print(f"  WorldModel: {'✓' if 'world_model' in snapshot_data else '✗'}")
                console.print(f"  Run Config: {'✓' if 'run_config' in snapshot_data else '✗'}")
                console.print(f"  Chat Context: {'✓' if 'chat_context' in snapshot_data else '✗'}")
                
                if snapshot.reference_metrics:
                    console.print(f"\n[bold]Reference Metrics:[/bold]")
                    metrics = snapshot.reference_metrics
                    console.print(f"  Candidates: {metrics.get('candidate_count', 'N/A')}")
                    console.print(f"  Scenarios: {metrics.get('scenario_count', 'N/A')}")
                    console.print(f"  Status: {metrics.get('status', 'N/A')}")
                    if metrics.get('duration_seconds'):
                        console.print(f"  Duration: {metrics['duration_seconds']:.1f}s")
                
    except Exception as e:
        console.print(f"[red]✗[/red] Error showing snapshot: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@snapshot_app.command("delete")
def snapshot_delete(
    snapshot_id: str = typer.Argument(..., help="Snapshot ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """
    Delete a snapshot.
    
    Examples:
        crucible snapshot delete abc123
        crucible snapshot delete abc123 --confirm
    """
    try:
        # Initialize database if needed
        try:
            from kosmos.db import init_from_config
            init_from_config()
        except Exception:
            pass  # May already be initialized
        
        with get_session() as session:
            snapshot = get_snapshot(session, snapshot_id)
            if snapshot is None:
                console.print(f"[red]✗[/red] Snapshot not found: {snapshot_id}")
                raise typer.Exit(1)
            
            if not confirm:
                console.print(f"[yellow]Warning:[/yellow] This will delete snapshot: {snapshot.name}")
                response = typer.confirm("Are you sure?", default=False)
                if not response:
                    console.print("[yellow]Cancelled[/yellow]")
                    return
            
            success = delete_snapshot(session, snapshot_id)
            if success:
                console.print(f"[green]✓[/green] Deleted snapshot: {snapshot.name}")
            else:
                console.print(f"[red]✗[/red] Failed to delete snapshot")
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]✗[/red] Error deleting snapshot: {e}")
        raise typer.Exit(1)


@snapshot_app.command("replay")
def snapshot_replay(
    snapshot_id: str = typer.Argument(..., help="Snapshot ID to replay"),
    phases: str = typer.Option("full", "--phases", help="Phases to run: full, design, evaluate"),
    num_candidates: Optional[int] = typer.Option(None, "--num-candidates", "-c", help="Override number of candidates"),
    num_scenarios: Optional[int] = typer.Option(None, "--num-scenarios", "-s", help="Override number of scenarios"),
    reuse_project: bool = typer.Option(False, "--reuse-project", help="Reuse existing project instead of creating temp one"),
):
    """
    Replay a snapshot by creating a new run and executing the pipeline.
    
    Examples:
        crucible snapshot replay abc123
        crucible snapshot replay abc123 --phases design --num-candidates 3
        crucible snapshot replay abc123 --reuse-project
    """
    try:
        # Initialize database if needed
        try:
            from kosmos.db import init_from_config
            init_from_config()
        except Exception:
            pass  # May already be initialized
        
        with get_session() as session:
            service = SnapshotService(session)
            
            options = {
                "reuse_project": reuse_project,
                "phases": phases,
                "num_candidates": num_candidates,
                "num_scenarios": num_scenarios,
            }
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Replaying snapshot...", total=None)
                
                result = service.replay_snapshot(snapshot_id, options)
                progress.update(task, completed=True)
            
            console.print(f"\n[green]✓[/green] Snapshot replayed successfully")
            console.print(f"  Replay Run ID: {result['replay_run_id']}")
            console.print(f"  Project ID: {result['project_id']}")
            console.print(f"  Status: {result['status']}")
            
    except ValueError as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error replaying snapshot: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@snapshot_app.command("test")
def snapshot_test(
    snapshot_ids: Optional[str] = typer.Option(None, "--snapshot-ids", help="Comma-separated snapshot IDs (or use --all)"),
    all_snapshots: bool = typer.Option(False, "--all", help="Test all snapshots"),
    max_snapshots: Optional[int] = typer.Option(None, "--max-snapshots", help="Maximum number of snapshots to test"),
    stop_on_failure: bool = typer.Option(False, "--stop-on-failure", help="Stop on first failure"),
    cost_limit_usd: Optional[float] = typer.Option(None, "--cost-limit-usd", help="Maximum cost in USD"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table (default) or json"),
):
    """
    Run snapshot tests and validate invariants.
    
    Examples:
        crucible snapshot test --all
        crucible snapshot test --snapshot-ids abc123,xyz789
        crucible snapshot test --all --max-snapshots 5 --cost-limit-usd 10.0
        crucible snapshot test --all --format json
    """
    try:
        # Initialize database if needed
        try:
            from kosmos.db import init_from_config
            init_from_config()
        except Exception:
            pass  # May already be initialized
        
        with get_session() as session:
            service = SnapshotService(session)
            
            # Parse snapshot IDs
            snapshot_id_list = None
            if snapshot_ids:
                snapshot_id_list = [s.strip() for s in snapshot_ids.split(",")]
            elif not all_snapshots:
                console.print("[red]✗[/red] Must specify --snapshot-ids or --all")
                raise typer.Exit(1)
            
            options = {
                "max_snapshots": max_snapshots,
                "stop_on_first_failure": stop_on_failure,
                "cost_limit_usd": cost_limit_usd,
                "phases": "full",
            }
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Running snapshot tests...", total=None)
                
                result = service.run_snapshot_tests(snapshot_id_list, options)
                progress.update(task, completed=True)
            
            summary = result["summary"]
            results = result["results"]
            total_cost = result["total_cost_usd"]
            
            if output_format.lower() == "json":
                import json
                console.print(json.dumps(result, indent=2))
            else:
                # Summary table
                console.print(f"\n[bold blue]Test Summary[/bold blue]\n")
                console.print(f"Total: {summary['total']}")
                console.print(f"[green]Passed: {summary['passed']}[/green]")
                console.print(f"[red]Failed: {summary['failed']}[/red]")
                console.print(f"[yellow]Skipped: {summary['skipped']}[/yellow]")
                console.print(f"Total Cost: ${total_cost:.2f} USD")
                
                # Results table
                if results:
                    console.print(f"\n[bold blue]Test Results[/bold blue]\n")
                    table = Table()
                    table.add_column("Snapshot", style="cyan")
                    table.add_column("Status", style="green")
                    table.add_column("Run ID", style="blue")
                    table.add_column("Invariants", style="yellow")
                    table.add_column("Cost", style="dim")
                    
                    for r in results:
                        status_style = "green" if r["status"] == "passed" else "red" if r["status"] == "failed" else "yellow"
                        inv_results = r.get("invariants", [])
                        passed_inv = sum(1 for inv in inv_results if inv.get("status") == "passed")
                        total_inv = len(inv_results)
                        inv_str = f"{passed_inv}/{total_inv}" if total_inv > 0 else "-"
                        
                        table.add_row(
                            r.get("snapshot_name", "Unknown")[:30],
                            f"[{status_style}]{r['status']}[/{status_style}]",
                            r.get("replay_run_id", "-")[:8] + "..." if r.get("replay_run_id") else "-",
                            inv_str,
                            f"${r.get('cost_usd', 0):.2f}"
                        )
                    
                    console.print(table)
                    
                    # Show failed invariants
                    failed_snapshots = [r for r in results if r["status"] == "failed"]
                    if failed_snapshots:
                        console.print(f"\n[bold red]Failed Snapshots:[/bold red]\n")
                        for r in failed_snapshots:
                            console.print(f"[red]{r['snapshot_name']}[/red]")
                            failed_inv = [inv for inv in r.get("invariants", []) if inv.get("status") == "failed"]
                            for inv in failed_inv:
                                console.print(f"  ✗ {inv.get('type')}: {inv.get('message', '')}")
                
    except Exception as e:
        console.print(f"[red]✗[/red] Error running snapshot tests: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

