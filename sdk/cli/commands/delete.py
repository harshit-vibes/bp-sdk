"""Delete command implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

from sdk import BlueprintClient
from sdk.yaml import IDManager

from ..config import get_client_kwargs, load_config

console = Console()


def delete(
    blueprint_id: Optional[str] = None,
    file: Optional[Path] = None,
    force: bool = False,
) -> None:
    """Delete blueprint and its agents.

    Can specify either blueprint_id directly or a YAML file with IDs.

    Args:
        blueprint_id: Blueprint ID to delete
        file: Path to YAML file with IDs (alternative to blueprint_id)
        force: Skip confirmation prompt
    """
    # Must specify one of blueprint_id or file
    if not blueprint_id and not file:
        console.print("[red]Error:[/red] Must specify either --id or --file")
        raise SystemExit(1)

    if blueprint_id and file:
        console.print("[red]Error:[/red] Cannot specify both --id and --file")
        raise SystemExit(1)

    # If file specified, read ID from it
    if file:
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise SystemExit(1)

        id_manager = IDManager(file)
        blueprint_id = id_manager.get_blueprint_id()

        if not blueprint_id:
            console.print(f"[red]Error:[/red] No blueprint ID found in {file}")
            console.print("[dim]The file may not have been created with 'bp create' yet.[/dim]")
            raise SystemExit(1)

    # Load config
    config = load_config()
    if not config.is_valid():
        missing = config.missing_fields()
        console.print("[red]Error:[/red] Missing required configuration:")
        for field in missing:
            console.print(f"  - {field}")
        raise SystemExit(1)

    # Confirm deletion
    if not force:
        confirmed = Confirm.ask(
            f"[yellow]Delete blueprint {blueprint_id} and all its agents?[/yellow]"
        )
        if not confirmed:
            console.print("[dim]Cancelled.[/dim]")
            return

    try:
        # Create client
        client = BlueprintClient(**get_client_kwargs(config))

        console.print(f"[dim]Deleting blueprint {blueprint_id}...[/dim]")

        # Delete
        client.delete(blueprint_id)

        console.print("[green]Blueprint deleted successfully![/green]")

        # If file was specified, clear IDs from it
        if file:
            try:
                id_manager = IDManager(file)
                id_manager.clear_ids()
                console.print(f"[dim]IDs cleared from {file}[/dim]")
            except Exception:
                pass  # Non-critical, ignore

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
