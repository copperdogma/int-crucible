"""
Profile command for performance analysis.

Displays profiling results with Rich formatting for easy analysis
of execution performance, memory usage, and bottlenecks.
"""

import typer
from typing import Optional
from pathlib import Path
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import profiling utilities
try:
    from kosmos.core.profiling import ProfileResult, format_profile_summary
    PROFILING_AVAILABLE = True
except ImportError:
    PROFILING_AVAILABLE = False

console = Console()


def profile_command(
    target: str = typer.Argument(
        ...,
        help="Target to profile: experiment, agent, workflow"
    ),
    experiment_id: Optional[str] = typer.Option(
        None,
        "--experiment", "-e",
        help="Experiment ID to profile"
    ),
    agent_type: Optional[str] = typer.Option(
        None,
        "--agent", "-a",
        help="Agent type to profile"
    ),
    mode: str = typer.Option(
        "standard",
        "--mode", "-m",
        help="Profiling mode: light, standard, full"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Save profile data to file (JSON)"
    ),
    compare: Optional[str] = typer.Option(
        None,
        "--compare", "-c",
        help="Compare with another profile ID"
    ),
    show_flamegraph: bool = typer.Option(
        False,
        "--flamegraph",
        help="Generate flamegraph visualization"
    ),
    top_n: int = typer.Option(
        20,
        "--top", "-n",
        help="Show top N functions by time"
    )
):
    """
    Profile Kosmos performance.

    Display detailed performance metrics including execution time,
    memory usage, function call statistics, and bottleneck analysis.

    Examples:

        # Profile an experiment
        kosmos profile experiment --experiment exp_123

        # Profile with full details
        kosmos profile experiment --experiment exp_123 --mode full

        # Compare two experiments
        kosmos profile experiment --experiment exp_123 --compare exp_456

        # Save profile data to JSON
        kosmos profile experiment --experiment exp_123 --output profile.json

        # Profile an agent workflow
        kosmos profile agent --agent HypothesisGenerator
    """
    if not PROFILING_AVAILABLE:
        console.print(
            "[red]Error:[/red] Profiling module not available",
            style="bold"
        )
        raise typer.Exit(1)

    # Validate target
    valid_targets = ["experiment", "agent", "workflow"]
    if target not in valid_targets:
        console.print(
            f"[red]Error:[/red] Invalid target '{target}'. "
            f"Must be one of: {', '.join(valid_targets)}",
            style="bold"
        )
        raise typer.Exit(1)

    # Route to appropriate handler
    if target == "experiment":
        if not experiment_id:
            console.print(
                "[red]Error:[/red] --experiment required for experiment profiling",
                style="bold"
            )
            raise typer.Exit(1)
        _profile_experiment(
            experiment_id=experiment_id,
            mode=mode,
            output=output,
            compare=compare,
            show_flamegraph=show_flamegraph,
            top_n=top_n
        )
    elif target == "agent":
        if not agent_type:
            console.print(
                "[red]Error:[/red] --agent required for agent profiling",
                style="bold"
            )
            raise typer.Exit(1)
        _profile_agent(
            agent_type=agent_type,
            mode=mode,
            output=output,
            top_n=top_n
        )
    elif target == "workflow":
        _profile_workflow(
            mode=mode,
            output=output,
            top_n=top_n
        )


def _profile_experiment(
    experiment_id: str,
    mode: str,
    output: Optional[Path],
    compare: Optional[str],
    show_flamegraph: bool,
    top_n: int
):
    """Profile an experiment."""
    console.print(
        f"\n[bold cyan]Profiling Experiment: {experiment_id}[/bold cyan]\n"
    )

    # Mock profile result for demonstration
    # In production, this would load from database
    profile_result = _load_profile_from_db(experiment_id, "experiment")

    if not profile_result:
        console.print(
            f"[yellow]Warning:[/yellow] No profiling data found for experiment {experiment_id}",
            style="bold"
        )
        console.print(
            "\nTo enable profiling, set ENABLE_PROFILING=true in your .env file",
            style="dim"
        )
        raise typer.Exit(0)

    # Display summary
    _display_profile_summary(profile_result)

    # Display bottlenecks
    if profile_result.bottlenecks:
        _display_bottlenecks(profile_result.bottlenecks, top_n)

    # Display function statistics
    if profile_result.function_times:
        _display_function_stats(profile_result.function_times, profile_result.function_calls, top_n)

    # Display memory timeline
    if profile_result.memory_snapshots:
        _display_memory_timeline(profile_result.memory_snapshots)

    # Comparison view
    if compare:
        console.print(f"\n[bold cyan]Comparison with {compare}[/bold cyan]\n")
        compare_profile = _load_profile_from_db(compare, "experiment")
        if compare_profile:
            _display_comparison(profile_result, compare_profile)
        else:
            console.print(
                f"[yellow]Warning:[/yellow] Profile {compare} not found",
                style="bold"
            )

    # Save output
    if output:
        _save_profile_output(profile_result, output)

    # Flamegraph
    if show_flamegraph:
        console.print(
            "\n[yellow]Note:[/yellow] Flamegraph generation not yet implemented",
            style="dim"
        )


def _profile_agent(agent_type: str, mode: str, output: Optional[Path], top_n: int):
    """Profile an agent."""
    console.print(
        f"\n[bold cyan]Profiling Agent: {agent_type}[/bold cyan]\n"
    )
    console.print(
        "[yellow]Note:[/yellow] Agent profiling not yet implemented",
        style="dim"
    )


def _profile_workflow(mode: str, output: Optional[Path], top_n: int):
    """Profile a workflow."""
    console.print(
        f"\n[bold cyan]Profiling Workflow[/bold cyan]\n"
    )
    console.print(
        "[yellow]Note:[/yellow] Workflow profiling not yet implemented",
        style="dim"
    )


def _display_profile_summary(profile: ProfileResult):
    """Display profile summary table."""
    table = Table(
        title="Profile Summary",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Status", justify="center")

    # Execution time
    exec_status = _get_performance_status(profile.execution_time, 5.0, 10.0)
    table.add_row(
        "Execution Time",
        f"{profile.execution_time:.3f}s",
        exec_status
    )

    # CPU time
    table.add_row(
        "CPU Time",
        f"{profile.cpu_time:.3f}s",
        ""
    )

    # Memory peak
    mem_status = _get_performance_status(profile.memory_peak_mb, 1000, 2000)
    table.add_row(
        "Peak Memory",
        f"{profile.memory_peak_mb:.1f} MB",
        mem_status
    )

    # Memory allocated
    table.add_row(
        "Memory Allocated",
        f"{profile.memory_allocated_mb:.1f} MB",
        ""
    )

    # Profiling mode
    table.add_row(
        "Profiling Mode",
        profile.profiling_mode.value,
        ""
    )

    # Overhead
    if profile.profiler_overhead_ms > 0:
        table.add_row(
            "Profiler Overhead",
            f"{profile.profiler_overhead_ms:.2f}ms",
            ""
        )

    # Timestamps
    if profile.started_at:
        table.add_row(
            "Started At",
            profile.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            ""
        )

    console.print(table)
    console.print()


def _display_bottlenecks(bottlenecks, max_display: int = 10):
    """Display performance bottlenecks."""
    console.print("[bold yellow]⚠ Performance Bottlenecks[/bold yellow]\n")

    for i, bottleneck in enumerate(bottlenecks[:max_display], 1):
        # Color by severity
        severity_colors = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "green"
        }
        color = severity_colors.get(bottleneck.severity, "white")

        panel_content = (
            f"[bold]Function:[/bold] {bottleneck.function_name}\n"
            f"[bold]Module:[/bold] {bottleneck.module_name}\n"
            f"[bold]Time:[/bold] {bottleneck.cumulative_time:.3f}s "
            f"({bottleneck.time_percent:.1f}% of total)\n"
            f"[bold]Calls:[/bold] {bottleneck.call_count:,}\n"
            f"[bold]Per Call:[/bold] {bottleneck.per_call_time:.2f}ms"
        )

        console.print(Panel(
            panel_content,
            title=f"[{color}]#{i} {bottleneck.severity.upper()}[/{color}]",
            border_style=color
        ))

    if len(bottlenecks) > max_display:
        console.print(
            f"\n[dim]... and {len(bottlenecks) - max_display} more[/dim]\n"
        )
    console.print()


def _display_function_stats(function_times: dict, function_calls: dict, top_n: int):
    """Display function call statistics."""
    table = Table(
        title=f"Top {top_n} Functions by Time",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Function", style="cyan")
    table.add_column("Calls", justify="right", style="yellow")
    table.add_column("Total Time", justify="right", style="green")
    table.add_column("Per Call", justify="right", style="blue")

    # Sort by cumulative time
    sorted_funcs = sorted(
        function_times.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    for i, (func_name, cum_time) in enumerate(sorted_funcs, 1):
        calls = function_calls.get(func_name, 0)
        per_call = (cum_time / calls * 1000) if calls > 0 else 0

        table.add_row(
            str(i),
            func_name[:60] + "..." if len(func_name) > 60 else func_name,
            f"{calls:,}",
            f"{cum_time:.3f}s",
            f"{per_call:.2f}ms"
        )

    console.print(table)
    console.print()


def _display_memory_timeline(snapshots):
    """Display memory usage timeline."""
    console.print("[bold cyan]Memory Usage Timeline[/bold cyan]\n")

    if not snapshots:
        console.print("[dim]No memory snapshots available[/dim]\n")
        return

    # Simple text-based visualization
    for i, snapshot in enumerate(snapshots[:10]):
        bar_length = int(snapshot.current_mb / 10)
        bar = "█" * bar_length
        console.print(
            f"{i:2d}. [{snapshot.timestamp:6.2f}s] {bar} "
            f"{snapshot.current_mb:.1f} MB"
        )

    if len(snapshots) > 10:
        console.print(f"\n[dim]... and {len(snapshots) - 10} more snapshots[/dim]")
    console.print()


def _display_comparison(profile1: ProfileResult, profile2: ProfileResult):
    """Display comparison between two profiles."""
    table = Table(
        title="Profile Comparison",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Profile 1", justify="right", style="white")
    table.add_column("Profile 2", justify="right", style="white")
    table.add_column("Difference", justify="right")

    # Compare execution time
    exec_diff = profile2.execution_time - profile1.execution_time
    exec_diff_pct = (exec_diff / profile1.execution_time * 100) if profile1.execution_time > 0 else 0
    exec_diff_str = _format_diff(exec_diff, exec_diff_pct, "s", lower_is_better=True)

    table.add_row(
        "Execution Time",
        f"{profile1.execution_time:.3f}s",
        f"{profile2.execution_time:.3f}s",
        exec_diff_str
    )

    # Compare memory
    mem_diff = profile2.memory_peak_mb - profile1.memory_peak_mb
    mem_diff_pct = (mem_diff / profile1.memory_peak_mb * 100) if profile1.memory_peak_mb > 0 else 0
    mem_diff_str = _format_diff(mem_diff, mem_diff_pct, "MB", lower_is_better=True)

    table.add_row(
        "Peak Memory",
        f"{profile1.memory_peak_mb:.1f} MB",
        f"{profile2.memory_peak_mb:.1f} MB",
        mem_diff_str
    )

    console.print(table)
    console.print()


def _format_diff(diff: float, diff_pct: float, unit: str, lower_is_better: bool = True) -> str:
    """Format difference with color."""
    is_improvement = (diff < 0) if lower_is_better else (diff > 0)

    if abs(diff_pct) < 1:
        return f"[dim]{diff:+.2f}{unit} (~0%)[/dim]"

    color = "green" if is_improvement else "red"
    symbol = "↓" if diff < 0 else "↑"

    return f"[{color}]{symbol} {abs(diff):.2f}{unit} ({abs(diff_pct):.1f}%)[/{color}]"


def _get_performance_status(value: float, warning_threshold: float, critical_threshold: float) -> str:
    """Get performance status indicator."""
    if value < warning_threshold:
        return "[green]✓[/green]"
    elif value < critical_threshold:
        return "[yellow]⚠[/yellow]"
    else:
        return "[red]✗[/red]"


def _load_profile_from_db(profile_id: str, profile_type: str) -> Optional[ProfileResult]:
    """Load profile from database."""
    # This would query the execution_profiles table
    # For now, return None to indicate no profiling data
    # In production, implement database query here
    return None


def _save_profile_output(profile: ProfileResult, output_path: Path):
    """Save profile data to file."""
    try:
        with open(output_path, 'w') as f:
            json.dump(profile.model_dump(), f, indent=2, default=str)
        console.print(
            f"\n[green]✓[/green] Profile data saved to {output_path}",
            style="bold"
        )
    except Exception as e:
        console.print(
            f"\n[red]Error:[/red] Failed to save profile data: {e}",
            style="bold"
        )
