"""Update command implementation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from sdk import BlueprintClient

from ..config import get_client_kwargs, load_config
from ..formatters import format_blueprint_table

console = Console()


def update(file: Path) -> None:
    """Update blueprint from YAML file.

    The YAML file must have IDs section with existing blueprint and agent IDs.

    Args:
        file: Path to blueprint.yaml file with IDs
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
        raise SystemExit(1)

    try:
        # Create client
        client = BlueprintClient(**get_client_kwargs(config))

        console.print(f"[dim]Updating blueprint from {file}...[/dim]")

        # Update from YAML
        blueprint = client.update_from_yaml(file)

        console.print("[green]Blueprint updated successfully![/green]\n")
        format_blueprint_table(blueprint)

    except ValueError as e:
        # Likely missing IDs
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[dim]Hint: Run 'bp create' first to create the blueprint and write IDs.[/dim]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
