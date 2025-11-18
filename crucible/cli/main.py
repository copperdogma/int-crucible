"""
Command-line interface for Int Crucible.

Provides CLI commands for interacting with the Int Crucible system,
including Kosmos integration testing.
"""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional

from crucible.config import get_config

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


if __name__ == "__main__":
    app()

