"""
Command-line interface for Int Crucible.

Provides CLI commands for interacting with the Int Crucible system,
including Kosmos integration testing.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
import time

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
)
from crucible.db.models import RunMode

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


if __name__ == "__main__":
    app()

