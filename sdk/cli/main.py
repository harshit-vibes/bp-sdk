"""Blueprint SDK CLI Entry Point.

Command-line interface for managing blueprints via YAML files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .commands import create as create_cmd
from .commands import delete as delete_cmd
from .commands import eval_agent as eval_cmd
from .commands import get as get_cmd
from .commands import linear_app
from .commands import list_blueprints as list_cmd
from .commands import sync as sync_cmd
from .commands import update as update_cmd
from .commands import validate as validate_cmd

app = typer.Typer(
    name="bp",
    help="Blueprint SDK CLI - Manage blueprints via YAML files",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

# Register subcommand groups
app.add_typer(linear_app, name="linear")


@app.command()
def create(
    file: Path = typer.Argument(
        ...,
        help="Path to blueprint.yaml file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Create a new blueprint from a YAML definition.

    The YAML file should contain a blueprint definition with root_agents
    pointing to agent YAML files. After creation, the blueprint and agent
    IDs will be written back to the YAML file.

    Example:
        bp create my-blueprint/blueprint.yaml
    """
    create_cmd(file)


@app.command()
def get(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID to fetch"),
    output: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output directory for YAML export",
    ),
    format: str = typer.Option(
        "table",
        "-f",
        "--format",
        help="Output format: table, json",
    ),
) -> None:
    """Fetch a blueprint and display or export it.

    Without --output, displays the blueprint details.
    With --output, exports to YAML files in the specified directory.

    Examples:
        bp get bp-123                    # Display blueprint
        bp get bp-123 -o ./exported      # Export to YAML
        bp get bp-123 -f json            # Display as JSON
    """
    get_cmd(blueprint_id, output, format)


@app.command("list")
def list_blueprints(
    format: str = typer.Option(
        "table",
        "-f",
        "--format",
        help="Output format: table, json",
    ),
    limit: int = typer.Option(
        50,
        "-l",
        "--limit",
        help="Maximum number of blueprints to return",
    ),
    visibility: Optional[str] = typer.Option(
        None,
        "-v",
        "--visibility",
        help="Filter by visibility: public, private, organization",
    ),
    category: Optional[str] = typer.Option(
        None,
        "-c",
        "--category",
        help="Filter by category",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Only show blueprints owned by current user",
    ),
    summary: bool = typer.Option(
        False,
        "--summary",
        "-s",
        help="Show summary statistics instead of list",
    ),
    report: bool = typer.Option(
        False,
        "--report",
        "-r",
        help="Show comprehensive roadmap comparison report",
    ),
    roadmap: Optional[Path] = typer.Option(
        None,
        "--roadmap",
        help="Path to roadmap tasks.csv file (default: ./roadmap/tasks.csv)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Custom output path for report (default: roadmap/report.md)",
    ),
    csv: Optional[Path] = typer.Option(
        None,
        "--csv",
        help="Export report as CSV file (includes all columns)",
    ),
) -> None:
    """List blueprints with filtering options.

    Examples:
        bp list                          # List all accessible blueprints
        bp list --mine                   # Only my blueprints
        bp list -v private               # Only private blueprints
        bp list -v public                # Only public blueprints
        bp list --summary                # Show statistics
        bp list --report                 # Generate roadmap report (syncs Linear first)
        bp list --report -o custom.md    # Save report to custom path
        bp list --csv report.csv         # Export as CSV (all blueprint data)
        bp list -c people                # Filter by category
        bp list -l 100                   # Get up to 100 blueprints
    """
    list_cmd(format, limit, visibility, category, mine, summary, report, roadmap, output, csv)


@app.command()
def update(
    file: Path = typer.Argument(
        ...,
        help="Path to blueprint.yaml file with IDs",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Update an existing blueprint from YAML.

    The YAML file must have an 'ids' section containing the blueprint
    and agent IDs. This is automatically added when you create a
    blueprint with 'bp create'.

    Example:
        bp update my-blueprint/blueprint.yaml
    """
    update_cmd(file)


@app.command()
def delete(
    blueprint_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Blueprint ID to delete",
    ),
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="YAML file with blueprint ID",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-y",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Delete a blueprint and all its agents.

    Specify either --id or --file to identify the blueprint.
    If using --file, the IDs will be cleared from the file after deletion.

    Examples:
        bp delete --id bp-123            # Delete by ID
        bp delete -f blueprint.yaml      # Delete by YAML file
        bp delete --id bp-123 -y         # Delete without confirmation
    """
    delete_cmd(blueprint_id, file, force)


@app.command()
def validate(
    file: Path = typer.Argument(
        ...,
        help="Path to blueprint.yaml file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    verbose: bool = typer.Option(
        True,
        "--verbose/--quiet",
        "-v/-q",
        help="Show detailed output including warnings",
    ),
) -> None:
    """Validate a YAML blueprint without making API calls.

    Checks that:
    - All referenced agent files exist
    - YAML syntax is valid
    - Blueprint and agent configurations are valid
    - No circular dependencies

    Examples:
        bp validate my-blueprint/blueprint.yaml
        bp validate my-blueprint/blueprint.yaml -q  # Quiet mode
    """
    validate_cmd(file, verbose)


@app.command()
def sync(
    directory: Path = typer.Option(
        Path("./blueprints/studio"),
        "-d",
        "--dir",
        help="Directory to sync blueprints to",
    ),
    visibility: Optional[str] = typer.Option(
        None,
        "-v",
        "--visibility",
        help="Filter by visibility: public, private, organization (default: all)",
    ),
    clean: bool = typer.Option(
        False,
        "--clean",
        help="Remove local files not present in remote",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be synced without making changes",
    ),
) -> None:
    """Sync blueprints from API to local directory.

    Fetches all accessible blueprints and saves them as individual JSON files,
    organized by visibility (private/org-wide/public-owned/public-unowned).

    Examples:
        bp sync                          # Sync all to ./blueprints/studio
        bp sync -d ./my-bps              # Custom directory
        bp sync -v public                # Only public blueprints
        bp sync --clean                  # Remove stale local files
        bp sync --dry-run                # Preview without changes
    """
    sync_cmd(directory, visibility, clean, dry_run)


@app.command("eval")
def eval_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to test"),
    query: str = typer.Argument(..., help="Query/message to send to the agent"),
    timeout: int = typer.Option(
        180,
        "-t",
        "--timeout",
        help="Request timeout in seconds",
    ),
    no_trace: bool = typer.Option(
        False,
        "--no-trace",
        help="Skip trace retrieval",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output result as JSON (includes response and trace)",
    ),
    session: Optional[str] = typer.Option(
        None,
        "-s",
        "--session",
        help="Session ID to continue a conversation",
    ),
) -> None:
    """Evaluate an agent by sending a query and displaying response + trace.

    Sends a query to the specified agent via streaming inference,
    then fetches and displays the execution trace showing the
    delegation sequence and agent interactions.

    Use --session to continue a multi-turn conversation.

    Examples:
        bp eval agent-123 "Hello, how are you?"
        bp eval agent-123 "Process this ticket" -t 300
        bp eval agent-123 "Quick test" --no-trace
        bp eval agent-123 "Test query" --json > result.json
        bp eval agent-123 "Continue conversation" --session abc-123
    """
    eval_cmd(agent_id, query, timeout, not no_trace, json_output, session)


@app.command()
def version() -> None:
    """Show bp-sdk version."""
    try:
        from sdk import __version__

        console.print(f"bp-sdk version {__version__}")
    except ImportError:
        console.print("bp-sdk version unknown")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
