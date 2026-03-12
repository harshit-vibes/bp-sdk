"""Validate command implementation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from sdk import BlueprintClient

from ..config import get_client_kwargs, load_config
from ..formatters import format_validation_report

console = Console()


def validate(file: Path, verbose: bool = True) -> None:
    """Validate YAML blueprint without making API calls.

    Args:
        file: Path to blueprint.yaml file
        verbose: Show detailed output including warnings
    """
    # Validate file exists
    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise SystemExit(1)

    if not file.is_file():
        console.print(f"[red]Error:[/red] Not a file: {file}")
        raise SystemExit(1)

    # Load config (only for client instantiation, not for API calls)
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

        console.print(f"[dim]Validating {file}...[/dim]\n")

        # Validate
        report = client.validate_yaml(file)

        # Format output
        format_validation_report(report, verbose=verbose)

        # Exit with error code if invalid
        if not report.valid:
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
