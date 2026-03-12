"""Rich Table Formatters.

Provides formatted table output for CLI commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from sdk.models import Blueprint, ValidationReport

console = Console()


def format_blueprint_table(blueprint: "Blueprint") -> None:
    """Print a single blueprint in table format.

    Args:
        blueprint: Blueprint object to display
    """
    table = Table(title="Blueprint Details", show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("ID", blueprint.id)
    table.add_row("Name", blueprint.name)
    table.add_row("Description", blueprint.description or "-")
    table.add_row("Category", blueprint.category or "-")
    table.add_row("Visibility", blueprint.visibility or "-")
    table.add_row("Tags", ", ".join(blueprint.tags) if blueprint.tags else "-")
    table.add_row("Manager ID", blueprint.manager_id or "-")
    table.add_row(
        "Worker IDs",
        ", ".join(blueprint.worker_ids) if blueprint.worker_ids else "-",
    )
    table.add_row("Studio URL", blueprint.studio_url or "-")

    console.print(table)


def format_list_table(blueprints: list[dict[str, Any]]) -> None:
    """Print a list of blueprints in table format.

    Args:
        blueprints: List of blueprint dictionaries
    """
    if not blueprints:
        console.print("[yellow]No blueprints found.[/yellow]")
        return

    table = Table(title=f"Blueprints ({len(blueprints)} total)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Category")
    table.add_column("Visibility")
    table.add_column("Tags")

    for bp in blueprints:
        tags = bp.get("tags", [])
        tag_str = ", ".join(tags[:3])
        if len(tags) > 3:
            tag_str += f" (+{len(tags) - 3})"

        table.add_row(
            bp.get("_id", "-"),
            bp.get("name", "-"),
            bp.get("category", "-"),
            bp.get("visibility", "-"),
            tag_str or "-",
        )

    console.print(table)


def format_validation_report(report: "ValidationReport", verbose: bool = True) -> None:
    """Print a validation report.

    Args:
        report: ValidationReport object
        verbose: Whether to show all details
    """
    if report.valid:
        console.print(
            Panel(
                Text("Validation Passed", style="bold green"),
                title="Result",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                Text("Validation Failed", style="bold red"),
                title="Result",
                border_style="red",
            )
        )

    if report.errors:
        console.print("\n[red bold]Errors:[/red bold]")
        for i, error in enumerate(report.errors, 1):
            console.print(f"  {i}. {error}")

    if verbose and report.warnings:
        console.print("\n[yellow bold]Warnings:[/yellow bold]")
        for i, warning in enumerate(report.warnings, 1):
            console.print(f"  {i}. {warning}")

    # Summary
    console.print()
    if report.errors:
        console.print(f"[red]{len(report.errors)} error(s)[/red]", end="")
    else:
        console.print("[green]0 errors[/green]", end="")

    if report.warnings:
        console.print(f", [yellow]{len(report.warnings)} warning(s)[/yellow]")
    else:
        console.print(", [dim]0 warnings[/dim]")
