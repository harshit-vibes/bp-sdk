"""JSON Output Formatters.

Provides JSON formatted output for CLI commands.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.syntax import Syntax

if TYPE_CHECKING:
    from sdk.models import Blueprint

console = Console()


def format_blueprint_json(blueprint: "Blueprint", pretty: bool = True) -> None:
    """Print a single blueprint in JSON format.

    Args:
        blueprint: Blueprint object to display
        pretty: Whether to pretty-print with syntax highlighting
    """
    data = {
        "id": blueprint.id,
        "name": blueprint.name,
        "description": blueprint.description,
        "category": blueprint.category,
        "visibility": blueprint.visibility,
        "tags": blueprint.tags,
        "manager_id": blueprint.manager_id,
        "worker_ids": blueprint.worker_ids,
        "studio_url": blueprint.studio_url,
    }

    if pretty:
        json_str = json.dumps(data, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai")
        console.print(syntax)
    else:
        console.print(json.dumps(data))


def format_list_json(blueprints: list[dict[str, Any]], pretty: bool = True) -> None:
    """Print a list of blueprints in JSON format.

    Args:
        blueprints: List of blueprint dictionaries
        pretty: Whether to pretty-print with syntax highlighting
    """
    # Extract just the essential fields
    data = [
        {
            "id": bp.get("_id"),
            "name": bp.get("name"),
            "description": bp.get("description"),
            "category": bp.get("category"),
            "visibility": bp.get("visibility"),
            "tags": bp.get("tags", []),
        }
        for bp in blueprints
    ]

    if pretty:
        json_str = json.dumps(data, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai")
        console.print(syntax)
    else:
        console.print(json.dumps(data))
