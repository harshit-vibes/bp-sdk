"""Create command implementation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from sdk import BlueprintClient

from ..config import get_client_kwargs, load_config
from ..formatters import format_blueprint_table

console = Console()


def create(file: Path) -> None:
    """Create blueprint from YAML file.

    Args:
        file: Path to blueprint.yaml file
    """
    # Validate file exists
    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise SystemExit(1)

    if not file.is_file():
        console.print(f"[red]Error:[/red] Not a file: {file}")
        raise SystemExit(1)

    # Load config
    config = load_config()
    if not config.is_valid():
        missing = config.missing_fields()
        console.print("[red]Error:[/red] Missing required configuration:")
        for field in missing:
            console.print(f"  - {field}")
        console.print("\nSet environment variables or create ~/.bp/config.yaml")
        raise SystemExit(1)

    try:
        # Create client
        client = BlueprintClient(**get_client_kwargs(config))

        console.print(f"[dim]Creating blueprint from {file}...[/dim]")

        # Create from YAML
        blueprint = client.create_from_yaml(file)

        console.print("[green]Blueprint created successfully![/green]\n")
        format_blueprint_table(blueprint)

        console.print(f"\n[dim]IDs have been written back to {file}[/dim]")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
