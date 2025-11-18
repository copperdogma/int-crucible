CLI Modules
===========

The command-line interface provides a beautiful, user-friendly way to interact with Kosmos
using Typer and Rich for modern terminal UI.

Main CLI Application
--------------------

The main Typer application and entry point.

.. automodule:: kosmos.cli.main
   :members:
   :undoc-members:
   :show-inheritance:

Interactive Mode
----------------

Interactive research configuration with guided prompts.

.. automodule:: kosmos.cli.interactive
   :members:
   :undoc-members:
   :show-inheritance:

CLI Utilities
-------------

Shared utilities for formatting, printing, and database access.

.. automodule:: kosmos.cli.utils
   :members:
   :undoc-members:
   :show-inheritance:

CLI Themes
----------

Rich theme configuration for consistent styling.

.. automodule:: kosmos.cli.themes
   :members:
   :undoc-members:
   :show-inheritance:

CLI Commands
------------

Run Command
^^^^^^^^^^^

Execute research with live progress visualization.

.. automodule:: kosmos.cli.commands.run
   :members:
   :undoc-members:
   :show-inheritance:

Status Command
^^^^^^^^^^^^^^

Show research status with optional live watch mode.

.. automodule:: kosmos.cli.commands.status
   :members:
   :undoc-members:
   :show-inheritance:

History Command
^^^^^^^^^^^^^^^

Browse past research runs with filtering.

.. automodule:: kosmos.cli.commands.history
   :members:
   :undoc-members:
   :show-inheritance:

Cache Command
^^^^^^^^^^^^^

Manage caching system with statistics and optimization.

.. automodule:: kosmos.cli.commands.cache
   :members:
   :undoc-members:
   :show-inheritance:

Config Command
^^^^^^^^^^^^^^

View and validate configuration.

.. automodule:: kosmos.cli.commands.config
   :members:
   :undoc-members:
   :show-inheritance:

Results Viewer
--------------

Beautiful visualization of research results.

.. automodule:: kosmos.cli.views.results_viewer
   :members:
   :undoc-members:
   :show-inheritance:

CLI Architecture
----------------

The CLI is built with:

**Typer**
   - Type-safe command definitions
   - Automatic help generation
   - Rich integration

**Rich Library**
   - Tables for structured data
   - Panels for important messages
   - Progress bars for long operations
   - Syntax highlighting for code
   - Trees for hierarchical data

**Interactive Prompts**
   - Domain selection
   - Research question input
   - Configuration parameters
   - Confirmations

Usage Examples
--------------

**Running research interactively**::

   $ kosmos run --interactive

   # Provides guided prompts for:
   # - Domain selection
   # - Research question
   # - Max iterations
   # - Budget settings
   # - Cache configuration
   # - Model selection

**Running research with command-line arguments**::

   $ kosmos run "What causes neurodegeneration?" \\
       --domain neuroscience \\
       --max-iterations 10 \\
       --budget 50 \\
       --no-cache

**Monitoring research status**::

   $ kosmos status run_12345

   # Shows:
   # - Research overview
   # - Progress bar
   # - Workflow state
   # - Metrics summary

**Watch mode for live updates**::

   $ kosmos status run_12345 --watch

   # Refreshes every 5 seconds
   # Updates progress in real-time
   # Exits when research completes

**Browsing research history**::

   $ kosmos history --limit 20 --domain biology

   # Shows compact table with:
   # - Run ID
   # - Question
   # - Domain
   # - State
   # - Created date

**Detailed history view**::

   $ kosmos history --details

   # Shows expanded view for each run
   # Offers to view specific run

**Managing cache**::

   $ kosmos cache --stats

   # Shows:
   # - Overall cache performance
   # - Per-cache statistics
   # - Cost savings estimate

**Optimizing cache**::

   $ kosmos cache --optimize

   # Cleans up expired entries
   # Shows number of entries removed

**Viewing configuration**::

   $ kosmos config --show

   # Displays:
   # - Claude configuration
   # - Research settings
   # - Database URL

**Validating configuration**::

   $ kosmos config --validate

   # Checks:
   # - API key configured
   # - Model valid
   # - Database accessible

**System diagnostics**::

   $ kosmos doctor

   # Checks:
   # - Python version
   # - Required packages
   # - API key
   # - Cache directory
   # - Database connection

Customizing CLI Output
----------------------

The CLI uses a theme system for consistent styling:

.. code-block:: python

   from kosmos.cli.themes import KOSMOS_THEME, get_domain_color

   # Get color for domain
   color = get_domain_color("biology")  # Returns "green"

   # Use in Rich components
   from rich.panel import Panel

   panel = Panel(
       "Biology research results",
       border_style=color
   )

Custom formatting functions:

.. code-block:: python

   from kosmos.cli.utils import (
       format_timestamp,
       format_duration,
       format_size,
       format_percentage
   )

   # Format timestamp
   formatted = format_timestamp(datetime.utcnow())
   # Returns: "just now" or "5m ago" or "2h ago"

   # Format duration
   duration = format_duration(seconds=3665)
   # Returns: "1h 1m 5s"

   # Format file size
   size = format_size(bytes=1024*1024*5.3)
   # Returns: "5.3 MB"

   # Format percentage
   pct = format_percentage(0.873)
   # Returns: "87.3%"

CLI Error Handling
------------------

The CLI provides user-friendly error messages:

.. code-block:: python

   from kosmos.cli.utils import print_error, print_warning

   try:
       result = execute_research(question)
   except ValueError as e:
       print_error(f"Invalid input: {e}")
       raise typer.Exit(1)
   except Exception as e:
       print_warning(f"Unexpected error: {e}")
       print_info("Run with --debug for full traceback")
       raise typer.Exit(1)

Progress Visualization
----------------------

Show progress for long-running operations:

.. code-block:: python

   from rich.progress import Progress, SpinnerColumn, TimeRemainingColumn
   from kosmos.cli.utils import console

   progress = Progress(
       SpinnerColumn(),
       TextColumn("[progress.description]{task.description}"),
       BarColumn(),
       TaskProgressColumn(),
       TimeRemainingColumn(),
       console=console
   )

   with progress:
       task = progress.add_task("Processing...", total=100)

       for i in range(100):
           # Do work
           process_item(i)
           progress.update(task, completed=i+1)

Results Export
--------------

Export results in multiple formats:

.. code-block:: python

   from kosmos.cli.views.results_viewer import ResultsViewer

   viewer = ResultsViewer()

   # Export to JSON
   viewer.export_to_json(
       data=research_results,
       output_path=Path("results.json")
   )

   # Export to Markdown
   viewer.export_to_markdown(
       data=research_results,
       output_path=Path("results.md")
   )

Interactive Prompts
-------------------

Use Rich prompts for user input:

.. code-block:: python

   from rich.prompt import Prompt, Confirm, IntPrompt
   from kosmos.cli.utils import console

   # Text input
   name = Prompt.ask("Enter your name")

   # Confirmation
   confirmed = Confirm.ask("Are you sure?", default=False)

   # Integer input
   count = IntPrompt.ask("How many iterations?", default=10)

   # Choice selection
   domain = Prompt.ask(
       "Select domain",
       choices=["biology", "neuroscience", "materials"],
       default="biology"
   )

Creating Custom CLI Commands
-----------------------------

Add custom commands to the CLI:

.. code-block:: python

   import typer
   from kosmos.cli.main import app
   from kosmos.cli.utils import console, print_success

   @app.command()
   def my_command(
       arg: str = typer.Argument(..., help="Required argument"),
       option: bool = typer.Option(False, "--flag", "-f", help="Optional flag")
   ):
       \"\"\"Custom command description.\"\"\"
       console.print(f"Processing {arg}...")

       # Command logic here
       result = process(arg, option)

       print_success(f"Completed: {result}")

Then register the command in `kosmos/cli/main.py`:

.. code-block:: python

   from kosmos.cli.commands import my_module

   app.command(name="mycommand")(my_module.my_command)

CLI Testing
-----------

Test CLI commands with Typer's test client:

.. code-block:: python

   from typer.testing import CliRunner
   from kosmos.cli.main import app

   runner = CliRunner()

   def test_version_command():
       result = runner.invoke(app, ["version"])
       assert result.exit_code == 0
       assert "Kosmos AI Scientist" in result.stdout

   def test_run_interactive():
       # Provide inputs for interactive prompts
       result = runner.invoke(
           app,
           ["run", "--interactive"],
           input="6\\nTest question\\nn\\n"  # Domain, question, cancel
       )
       assert result.exit_code in [0, 1]  # 0 for success, 1 for cancel

Global Options
--------------

All commands support global options:

**--verbose, -v**
   Enable verbose output

**--debug**
   Enable debug mode with full tracebacks

**--quiet, -q**
   Suppress non-essential output

Example::

   $ kosmos --debug run "question" --verbose

Context Management
------------------

Commands share context through Typer's context object:

.. code-block:: python

   @app.callback()
   def main(
       ctx: typer.Context,
       verbose: bool = typer.Option(False, "--verbose", "-v"),
       debug: bool = typer.Option(False, "--debug")
   ):
       # Store in context
       ctx.ensure_object(dict)
       ctx.obj["verbose"] = verbose
       ctx.obj["debug"] = debug

   @app.command()
   def my_command(ctx: typer.Context):
       # Access from context
       if ctx.obj.get("verbose"):
           console.print("[info]Verbose mode enabled[/info]")
