"""Get command implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console

from sdk import BlueprintClient

from ..config import get_client_kwargs, load_config
from ..formatters import format_blueprint_json, format_blueprint_table

console = Console()


def get(
    blueprint_id: str,
    output: Optional[Path] = None,
    format: str = "table",
) -> None:
    """Fetch blueprint and optionally export to YAML.

    Args:
        blueprint_id: Blueprint ID to fetch
        output: Output directory for YAML export (optional)
        format: Output format (table, json, yaml)
    """
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

        # If output specified, export to YAML
        if output:
            console.print(f"[dim]Exporting blueprint {blueprint_id} to {output}...[/dim]")

            output.mkdir(parents=True, exist_ok=True)
            yaml_path = client.export_to_yaml(blueprint_id, output)

            console.print(f"[green]Exported to:[/green] {yaml_path}")
            console.print(f"\n[dim]Files created in {output}/[/dim]")

        else:
            # Just display the blueprint
            blueprint = client.get(blueprint_id)

            if format == "json":
                format_blueprint_json(blueprint)
            else:
                format_blueprint_table(blueprint)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
