"""Sync command implementation - syncs local Studio-BPs with remote blueprints."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import load_config

console = Console()

# Directory names for each category
DIRS = {
    "private": "private",
    "org-wide": "org-wide",
    "public-owned": "public-owned",
    "public-unowned": "public-unowned",
}


def slugify(name: str) -> str:
    """Convert name to safe filename."""
    if not name:
        return "unnamed"
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug[:50]


def get_current_user_id(token: str) -> str:
    """Extract user ID from JWT token."""
    parts = token.split(".")
    payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
    decoded = base64.urlsafe_b64decode(payload)
    return json.loads(decoded).get("id")


def fetch_blueprints_by_visibility(
    config,
    visibility: str,
    progress: Optional[Progress] = None,
    task_id: Optional[int] = None,
) -> list:
    """Fetch all blueprints for a specific visibility."""
    base_url = config.blueprint_api_url or "https://pagos-prod.studio.lyzr.ai"
    url = f"{base_url}/api/v1/blueprints/blueprints"

    headers = {
        "Authorization": f"Bearer {config.blueprint_bearer_token}",
        "Content-Type": "application/json",
    }

    all_blueprints = []
    page = 1
    page_size = 1  # Fetch one at a time to skip problematic blueprints
    consecutive_errors = 0
    max_consecutive_errors = 5

    with httpx.Client(timeout=60) as client:
        while True:
            params = {
                "page_size": page_size,
                "page": page,
                "user_organization_id": config.organization_id,
                "share_type": visibility,
            }

            response = client.get(url, headers=headers, params=params)

            if response.status_code != 200:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    break
                page += 1
                continue

            consecutive_errors = 0
            data = response.json()
            blueprints = data.get("blueprints", [])
            all_blueprints.extend(blueprints)

            if progress and task_id is not None:
                progress.update(
                    task_id,
                    description=f"[cyan]Fetching {visibility}... ({len(all_blueprints)} found)",
                )

            if not data.get("has_more", False):
                break
            page += 1

    return all_blueprints


def get_target_dir(visibility: str, is_owned: bool) -> str | None:
    """Get the target directory name based on visibility and ownership.

    Returns None if the blueprint should be skipped (e.g., org-shared but not owned).
    """
    if visibility == "private":
        return DIRS["private"]
    elif visibility == "organization":
        # Only sync org-shared blueprints that you own
        return DIRS["org-wide"] if is_owned else None
    elif visibility == "public":
        return DIRS["public-owned"] if is_owned else DIRS["public-unowned"]
    return DIRS["public-unowned"]


def save_blueprint(bp: dict, base_dir: Path, visibility: str, is_owned: bool) -> Path | None:
    """Save a blueprint to the appropriate directory.

    Returns None if the blueprint should be skipped.
    """
    target_dir_name = get_target_dir(visibility, is_owned)
    if target_dir_name is None:
        return None  # Skip this blueprint

    target_dir = base_dir / target_dir_name
    target_dir.mkdir(parents=True, exist_ok=True)

    name = bp.get("orchestration_name") or bp.get("name") or bp.get("_id")
    filename = f"{slugify(name)}.json"
    filepath = target_dir / filename

    with open(filepath, "w") as f:
        json.dump(bp, f, indent=2, default=str)

    return filepath


def sync_blueprints(
    directory: Path = Path("./blueprints/studio"),
    visibility: Optional[str] = None,
    clean: bool = False,
    dry_run: bool = False,
) -> None:
    """Sync local Studio-BPs directory with remote blueprints.

    Args:
        directory: Base directory for Studio-BPs
        visibility: Filter by visibility (public, private, organization, or None for all)
        clean: Remove local files not present in remote
        dry_run: Show what would be done without making changes
    """
    config = load_config()
    if not config.is_valid():
        missing = config.missing_fields()
        console.print("[red]Error:[/red] Missing required configuration:")
        for field in missing:
            console.print(f"  - {field}")
        raise SystemExit(1)

    # Get current user ID
    current_user_id = get_current_user_id(config.blueprint_bearer_token)

    # Determine which visibilities to sync
    if visibility:
        visibilities = [visibility]
    else:
        visibilities = ["public", "private", "organization"]

    console.print(f"\n[bold]Syncing blueprints to {directory}[/bold]")
    if dry_run:
        console.print("[yellow]DRY RUN - no changes will be made[/yellow]")

    # Create base directory
    if not dry_run:
        directory.mkdir(parents=True, exist_ok=True)

    stats = {"fetched": 0, "saved": 0, "skipped": 0, "cleaned": 0, "errors": 0}
    all_saved_files = set()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for vis in visibilities:
            task = progress.add_task(f"[cyan]Fetching {vis}...", total=None)

            # Fetch blueprints
            blueprints = fetch_blueprints_by_visibility(config, vis, progress, task)
            stats["fetched"] += len(blueprints)

            progress.update(task, description=f"[green]Fetched {len(blueprints)} {vis} blueprints")

            # Save each blueprint
            for bp in blueprints:
                owner_id = bp.get("owner_id", "")
                is_owned = owner_id == current_user_id
                name = bp.get("orchestration_name") or bp.get("name") or bp.get("_id")

                # Check if this blueprint should be skipped
                target_dir_name = get_target_dir(vis, is_owned)
                if target_dir_name is None:
                    stats["skipped"] += 1
                    if dry_run:
                        console.print(f"  [dim]Would skip (not owned): {name}[/dim]")
                    continue

                if dry_run:
                    console.print(f"  Would save: {target_dir_name}/{slugify(name)}.json")
                else:
                    try:
                        filepath = save_blueprint(bp, directory, vis, is_owned)
                        if filepath:
                            all_saved_files.add(filepath)
                            stats["saved"] += 1
                    except Exception as e:
                        console.print(f"[red]Error saving {bp.get('_id')}: {e}[/red]")
                        stats["errors"] += 1

            progress.remove_task(task)

    # Clean stale files if requested
    if clean and not dry_run:
        console.print("\n[dim]Cleaning stale files...[/dim]")
        for dir_name in DIRS.values():
            target_dir = directory / dir_name
            if target_dir.exists():
                for file in target_dir.glob("*.json"):
                    if file not in all_saved_files:
                        file.unlink()
                        stats["cleaned"] += 1
                        console.print(f"  [dim]Removed: {file.relative_to(directory)}[/dim]")

    # Summary
    console.print()
    table = Table(title="Sync Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Blueprints fetched", str(stats["fetched"]))
    if stats["skipped"]:
        table.add_row("Skipped (not owned)", f"[dim]{stats['skipped']}[/dim]")
    if not dry_run:
        table.add_row("Files saved", str(stats["saved"]))
        if clean:
            table.add_row("Files cleaned", str(stats["cleaned"]))
        if stats["errors"]:
            table.add_row("Errors", f"[red]{stats['errors']}[/red]")

    console.print(table)

    # Show directory structure
    if not dry_run and stats["saved"] > 0:
        console.print(f"\n[dim]Files saved to: {directory.absolute()}[/dim]")
        for dir_name in DIRS.values():
            target_dir = directory / dir_name
            if target_dir.exists():
                count = len(list(target_dir.glob("*.json")))
                if count > 0:
                    console.print(f"  {dir_name}/: {count} files")
