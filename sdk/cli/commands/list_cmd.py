"""List command implementation."""

from __future__ import annotations

import base64
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import load_config

console = Console()

# Default paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_ROADMAP_PATH = PROJECT_ROOT / "roadmap" / "tasks.csv"  # Legacy, kept for compatibility
DEFAULT_REPORT_PATH = PROJECT_ROOT / "roadmap" / "report.md"
DEFAULT_BLUEPRINT_MAP_PATH = PROJECT_ROOT / "roadmap" / "blueprint-map.yaml"

# Linear project ID for BP-LIB roadmap
BP_LIB_PROJECT_ID = "8b7c8685-baf9-496d-bff4-bcad19b4eecd"

# Studio URL base
STUDIO_URL_BASE = "https://studio.lyzr.ai/lyzr-manager?blueprint="


def list_blueprints(
    format: str = "table",
    limit: int = 50,
    visibility: Optional[str] = None,
    category: Optional[str] = None,
    mine: bool = False,
    summary: bool = False,
    report: bool = False,
    roadmap: Optional[Path] = None,
    output: Optional[Path] = None,
    csv_output: Optional[Path] = None,
) -> None:
    """List blueprints with filtering options.

    Args:
        format: Output format (table or json)
        limit: Maximum number of blueprints to return (0 = all)
        visibility: Filter by visibility (public, private, organization)
        category: Filter by category
        mine: Only show blueprints owned by current user
        summary: Show summary statistics instead of full list
        report: Show comprehensive roadmap comparison report (auto-syncs Linear)
        roadmap: Path to roadmap tasks.csv file
        output: Path to save report as markdown file
        csv_output: Path to save report as CSV file (includes all blueprint data)
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
        # Get user ID from token for --mine filter and display
        token = config.blueprint_bearer_token
        parts = token.split(".")
        payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        current_user_id = json.loads(decoded).get("id")

        console.print("[dim]Fetching blueprints...[/dim]")

        # For reports, fetch all blueprints (no limit)
        # Otherwise use the specified limit
        fetch_limit = 10000 if report else (limit if limit > 0 else 10000)

        # Fetch all blueprints with pagination
        all_blueprints = _fetch_all_blueprints(
            config=config,
            visibility=visibility,
            category=category,
            limit=fetch_limit,
        )

        console.print(f"[dim]Fetched {len(all_blueprints)} blueprints[/dim]\n")

        # Filter by owner if --mine flag
        if mine:
            all_blueprints = [
                bp for bp in all_blueprints if bp.get("owner_id") == current_user_id
            ]

        # Show report if requested (comprehensive roadmap comparison)
        if report or csv_output:
            roadmap_path = roadmap or DEFAULT_ROADMAP_PATH
            output_path = output or DEFAULT_REPORT_PATH
            _show_report(
                all_blueprints,
                config.organization_id,
                current_user_id,
                roadmap_path,
                output_path,
                csv_output=csv_output,
            )
            return

        # Show summary if requested
        if summary:
            _show_summary(all_blueprints, config.organization_id, current_user_id)
            return

        # Format output
        if format == "json":
            _format_json(all_blueprints)
        else:
            _format_table(all_blueprints, current_user_id)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


def _fetch_all_blueprints(
    config,
    visibility: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10000,
) -> list:
    """Fetch all blueprints with pagination.

    Uses page_size=1 to handle problematic blueprints that cause 500 errors.
    Skips individual blueprints that fail and continues fetching.
    """
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
    max_consecutive_errors = 5  # Stop after 5 consecutive failures

    with httpx.Client(timeout=60) as client:
        while len(all_blueprints) < limit:
            params = {
                "page_size": page_size,
                "page": page,
                "user_organization_id": config.organization_id,
            }

            if visibility:
                params["share_type"] = visibility
            if category:
                params["category"] = category

            response = client.get(url, headers=headers, params=params)

            if response.status_code != 200:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    console.print(
                        f"[dim]Stopped after {max_consecutive_errors} consecutive API errors[/dim]"
                    )
                    break
                page += 1
                continue

            consecutive_errors = 0
            data = response.json()
            blueprints = data.get("blueprints", [])
            all_blueprints.extend(blueprints)

            if not data.get("has_more", False):
                break
            page += 1

    return all_blueprints[:limit]


def _show_summary(blueprints: list, org_id: str, current_user_id: str) -> None:
    """Show summary statistics for blueprints."""
    total = len(blueprints)

    # By visibility
    visibility_counts = Counter(bp.get("share_type") for bp in blueprints)

    # By organization
    in_org = sum(1 for bp in blueprints if bp.get("organization_id") == org_id)
    other_orgs = total - in_org

    # By owner
    owned_by_me = sum(1 for bp in blueprints if bp.get("owner_id") == current_user_id)
    owned_by_others = total - owned_by_me

    # By category
    category_counts = Counter(bp.get("category") for bp in blueprints)

    console.print(f"[bold]Total blueprints:[/bold] {total}\n")

    # Visibility table
    table = Table(title="By Visibility", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right")

    for vis, count in visibility_counts.most_common():
        table.add_row(vis or "unknown", str(count))
    console.print(table)

    # Ownership breakdown
    console.print(f"\n[bold]By Owner:[/bold]")
    console.print(f"  Mine:   {owned_by_me}")
    console.print(f"  Others: {owned_by_others}")

    # Organization breakdown
    console.print(f"\n[bold]By Organization:[/bold]")
    console.print(f"  Current org: {in_org}")
    console.print(f"  Other orgs:  {other_orgs}")

    # Category table
    if category_counts:
        console.print()
        cat_table = Table(title="By Category (Top 10)", show_header=True)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count", justify="right")

        for cat, count in category_counts.most_common(10):
            cat_table.add_row(cat or "uncategorized", str(count))
        console.print(cat_table)


def _format_table(blueprints: list, current_user_id: str) -> None:
    """Print blueprints in table format with visibility and ownership markers."""
    if not blueprints:
        console.print("[yellow]No blueprints found.[/yellow]")
        return

    table = Table(title=f"Blueprints ({len(blueprints)} total)")
    table.add_column("ID", style="cyan", no_wrap=True, max_width=14)
    table.add_column("Name", style="green", max_width=35)
    table.add_column("Visibility", max_width=12)
    table.add_column("Owner", max_width=8)
    table.add_column("Category", max_width=15)

    for bp in blueprints:
        # Color visibility
        vis = bp.get("share_type", "-")
        if vis == "private":
            vis_display = "[yellow]private[/yellow]"
        elif vis == "public":
            vis_display = "[green]public[/green]"
        elif vis == "organization":
            vis_display = "[blue]org[/blue]"
        else:
            vis_display = vis or "-"

        # Owner marker
        owner_id = bp.get("owner_id", "")
        if owner_id == current_user_id:
            owner_display = "[bold cyan]ME[/bold cyan]"
        else:
            owner_display = owner_id[:8] if owner_id else "-"

        table.add_row(
            bp.get("_id", "-")[:14],
            bp.get("name", "-"),
            vis_display,
            owner_display,
            bp.get("category", "-"),
        )

    console.print(table)


def _format_json(blueprints: list) -> None:
    """Print blueprints as JSON."""
    import json as json_module

    output = [
        {
            "id": bp.get("_id"),
            "name": bp.get("name"),
            "description": bp.get("description"),
            "category": bp.get("category"),
            "visibility": bp.get("share_type"),
            "owner_id": bp.get("owner_id"),
            "organization_id": bp.get("organization_id"),
            "tags": bp.get("tags", []),
        }
        for bp in blueprints
    ]
    console.print_json(json_module.dumps(output, indent=2))


def _load_blueprint_map(map_path: Path = DEFAULT_BLUEPRINT_MAP_PATH) -> dict[str, str]:
    """Load linear_id → blueprint_id mappings from YAML.

    Returns dict mapping Linear issue ID to Lyzr blueprint ID.
    """
    if not map_path.exists():
        return {}

    import yaml
    with open(map_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("mappings", {}) if data else {}


def _fetch_linear_tasks() -> list[dict]:
    """Fetch roadmap tasks directly from Linear API.

    Returns list of tasks with: id, identifier, title, state, labels, blueprint_id
    """
    import os
    from .linear import LinearClient

    # Check for Linear credentials
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        console.print("[dim]LINEAR_API_KEY not set, skipping Linear fetch[/dim]")
        return []

    try:
        client = LinearClient(api_key)
        issues = client.get_project_issues(BP_LIB_PROJECT_ID)
    except Exception as e:
        console.print(f"[yellow]Could not fetch from Linear: {e}[/yellow]")
        return []

    # Load blueprint mappings
    mappings = _load_blueprint_map()

    # Convert Linear issues to task format
    tasks = []
    for issue in issues:
        linear_id = issue.get("id", "")
        identifier = issue.get("identifier", "")  # e.g., "LYZ-123"
        title = issue.get("title", "")
        state = issue.get("state", {})
        state_name = state.get("name", "").lower() if state else ""
        state_type = state.get("type", "") if state else ""
        labels = [l.get("name", "") for l in issue.get("labels", {}).get("nodes", [])]

        # Extract task ID from title (e.g., "[BP-038] Ticket Triage Agent" → "BP-038")
        task_id = ""
        if title.startswith("[") and "]" in title:
            task_id = title[1:title.index("]")]
            title = title[title.index("]") + 1:].strip()

        # Get blueprint_id from mapping
        blueprint_id = mappings.get(linear_id, "")

        # Determine week from labels
        week = ""
        for label in labels:
            if label.startswith("week-"):
                week = label
                break

        tasks.append({
            "id": task_id or identifier,
            "linear_id": linear_id,
            "identifier": identifier,
            "title": title,
            "state": "done" if state_type == "completed" or state_name == "done" else state_name,
            "labels": ",".join(labels),
            "week": week,
            "blueprint_id": blueprint_id,
            "priority": str(issue.get("priority", 0)),
        })

    return tasks


def _load_roadmap_tasks(roadmap_path: Path) -> list[dict]:
    """Load tasks from Linear API.

    Requires LINEAR_API_KEY environment variable.
    Returns empty list if Linear is not configured.
    """
    return _fetch_linear_tasks()


def _normalize_name(name: str) -> str:
    """Normalize blueprint name for matching."""
    return name.lower().replace("-", " ").replace("_", " ").strip()


def _match_blueprint_to_task(bp_name: str, tasks: list[dict]) -> Optional[dict]:
    """Find matching roadmap task for a blueprint name."""
    bp_normalized = _normalize_name(bp_name)

    for task in tasks:
        task_title = _normalize_name(task.get("title", ""))
        # Check for substring match in either direction
        if task_title in bp_normalized or bp_normalized in task_title:
            return task
        # Check for key words match
        task_words = set(task_title.split())
        bp_words = set(bp_normalized.split())
        if len(task_words & bp_words) >= 2:  # At least 2 words in common
            return task
    return None


def _classify_blueprints(
    blueprints: list,
    current_user_id: str,
    tasks: list,
    mapped_bp_ids: set[str] | None = None,
) -> dict:
    """Classify blueprints into structured categories.

    Uses blueprint_id column from tasks for mapping AND the blueprint-map.yaml
    as the source of truth for planned blueprints.

    Args:
        blueprints: All blueprints from the platform
        current_user_id: Current user's ID for ownership filtering
        tasks: Tasks from Linear API
        mapped_bp_ids: Set of blueprint IDs from blueprint-map.yaml (planned blueprints)

    Returns dict with:
    - unowned_public: Blueprints from other users
    - planned: Dict with public/organization/private lists (from roadmap)
    - adhoc: Dict with public/organization/private lists (not in roadmap)
    - showcase: Moonshot/Featured blueprints
    - bp_to_task: Mapping of blueprint ID to roadmap task
    - task_to_bp: Mapping of task ID to blueprint ID
    - matched_tasks: Set of matched task IDs
    - backlog: Roadmap tasks not yet completed
    - unmapped_tasks: Tasks with missing blueprint_id
    """
    # Load mapped blueprint IDs from mapping file if not provided
    if mapped_bp_ids is None:
        mappings = _load_blueprint_map()
        mapped_bp_ids = set(mappings.values())

    # Separate owned vs unowned
    owned = [bp for bp in blueprints if bp.get("owner_id") == current_user_id]
    unowned_public = [
        bp for bp in blueprints
        if bp.get("owner_id") != current_user_id and bp.get("share_type") == "public"
    ]

    # Build blueprint_id to task mapping from Linear tasks
    # Uses blueprint_id column (explicit mapping) instead of fuzzy name matching
    task_to_bp_id = {}  # task_id -> blueprint_id
    bp_id_to_task = {}  # blueprint_id -> task
    unmapped_tasks = []  # Tasks without blueprint_id

    for task in tasks:
        bp_id = task.get("blueprint_id", "").strip()
        if bp_id:
            task_to_bp_id[task["id"]] = bp_id
            bp_id_to_task[bp_id] = task
        else:
            # Task has no blueprint_id mapping - check state
            if task.get("state") != "done":
                unmapped_tasks.append(task)

    # Match blueprints to tasks using explicit mapping
    matched_tasks = set()
    bp_to_task = {}

    for bp in owned:
        bp_id = bp.get("_id")
        if bp_id in bp_id_to_task:
            task = bp_id_to_task[bp_id]
            matched_tasks.add(task["id"])
            bp_to_task[bp_id] = task

    # Identify showcase (moonshot/featured) blueprints from Linear tasks
    showcase_task_ids = {
        t["id"] for t in tasks
        if "[Moonshot]" in t.get("title", "") or "[Featured]" in t.get("title", "")
    }

    # Classify owned blueprints
    # A blueprint is "planned" if:
    #   1. It has a matching Linear task, OR
    #   2. Its ID is in the blueprint-map.yaml (the source of truth for planned BPs)
    planned = {"public": [], "organization": [], "private": []}
    adhoc = {"public": [], "organization": [], "private": []}
    showcase = []

    for bp in owned:
        bp_id = bp.get("_id")
        share_type = bp.get("share_type", "private")
        task = bp_to_task.get(bp_id)
        is_in_mapping = bp_id in mapped_bp_ids

        # Check if showcase (only if we have a Linear task with [Moonshot] or [Featured])
        if task and task["id"] in showcase_task_ids:
            showcase.append(bp)
            continue

        # Classify as planned or adhoc
        # Planned if: has a matching task OR is in the mapping file
        if task or is_in_mapping:
            planned[share_type].append(bp)
        else:
            adhoc[share_type].append(bp)

    # Get backlog (tasks with blueprint_id but blueprint not found in API)
    backlog = []
    missing_blueprints = []  # Tasks with blueprint_id but no matching blueprint

    for task in tasks:
        task_id = task["id"]
        bp_id = task.get("blueprint_id", "").strip()

        if task_id in matched_tasks:
            continue  # Already matched

        if task.get("state") == "done" and not bp_id:
            # Marked done but no blueprint_id - might be manually completed
            continue

        if bp_id:
            # Has blueprint_id but not found in API - might be deleted
            missing_blueprints.append(task)
        else:
            # No blueprint_id - backlog
            backlog.append(task)

    return {
        "unowned_public": unowned_public,
        "planned": planned,
        "adhoc": adhoc,
        "showcase": showcase,
        "bp_to_task": bp_to_task,
        "task_to_bp": task_to_bp_id,
        "matched_tasks": matched_tasks,
        "backlog": backlog,
        "unmapped_tasks": unmapped_tasks,
        "missing_blueprints": missing_blueprints,
        "total_owned": len(owned),
    }


def _sync_linear_tasks(classified: dict, roadmap_path: Path) -> dict:
    """Sync Linear task status based on blueprint share_type.

    Enforces the share_type → Linear status rule:
    - public → Done
    - organization → In Review
    - private → In Progress
    - backlog → stays in backlog (no blueprint yet)

    Runs silently unless there are actual updates or errors.

    Returns dict with sync results.
    """
    import os

    from .linear import _get_linear_client, _get_linear_team_id

    results = {"updated": [], "skipped": [], "errors": [], "already_synced": []}

    # Check for Linear credentials (silently skip if not configured)
    if not os.environ.get("LINEAR_API_KEY") or not os.environ.get("LINEAR_TEAM_ID"):
        return results

    try:
        client = _get_linear_client()
        team_id = _get_linear_team_id()
    except Exception:
        return results

    # Get workflow state IDs for all share types
    try:
        state_ids = client.get_workflow_state_ids(team_id)
        if not any(state_ids.values()):
            return results
    except Exception:
        return results

    # Build list of blueprints to sync with their expected Linear states
    # share_type → Linear status mapping:
    # - public → Done
    # - organization → In Review
    # - private → In Progress
    bp_to_task = classified["bp_to_task"]
    planned = classified["planned"]
    showcase = classified["showcase"]

    updates_needed = []  # [(linear_id, task_id, expected_state_id, share_type)]

    # Process planned blueprints by share_type
    for share_type in ["public", "organization", "private"]:
        expected_state_id = state_ids.get(share_type)
        if not expected_state_id:
            continue

        for bp in planned[share_type]:
            bp_id = bp.get("_id")
            task = bp_to_task.get(bp_id)
            if task:
                linear_id = task.get("linear_id", "").strip()
                if linear_id:
                    updates_needed.append((linear_id, task["id"], expected_state_id, share_type))

    # Process showcase blueprints (also by share_type)
    for bp in showcase:
        bp_id = bp.get("_id")
        share_type = bp.get("share_type", "private")
        expected_state_id = state_ids.get(share_type)
        if not expected_state_id:
            continue

        task = bp_to_task.get(bp_id)
        if task:
            linear_id = task.get("linear_id", "").strip()
            if linear_id:
                updates_needed.append((linear_id, task["id"], expected_state_id, share_type))

    if not updates_needed:
        return results

    # Update each task in Linear
    for linear_id, task_id, expected_state_id, share_type in updates_needed:
        state_name = {"public": "Done", "organization": "In Review", "private": "In Progress"}.get(share_type, share_type)

        try:
            success = client.update_issue_state(linear_id, expected_state_id)
            if success:
                results["updated"].append((task_id, share_type, state_name))
            else:
                results["errors"].append((task_id, "update failed"))
        except Exception as e:
            error_msg = str(e)
            if "Entity not found" in error_msg:
                results["errors"].append((task_id, "issue deleted in Linear"))
            else:
                results["errors"].append((task_id, error_msg[:50]))

    return results


def _update_tasks_csv_state(roadmap_path: Path, task_ids: list, new_state: str) -> None:
    """Update task state in local CSV."""
    tasks = []
    with open(roadmap_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["id"] in task_ids:
                row["state"] = new_state
            tasks.append(row)

    with open(roadmap_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)


def _show_report(
    blueprints: list,
    org_id: str,
    current_user_id: str,
    roadmap_path: Path,
    output: Optional[Path] = None,
    csv_output: Optional[Path] = None,
) -> None:
    """Show comprehensive roadmap comparison report.

    Automatically syncs Linear task status before generating report.
    """
    # Load roadmap tasks
    tasks = _load_roadmap_tasks(roadmap_path)

    # Classify blueprints
    classified = _classify_blueprints(blueprints, current_user_id, tasks)

    # Sync to Linear silently (only show output if there are updates/errors)
    sync_results = _sync_linear_tasks(classified, roadmap_path)

    updated_count = len(sync_results.get("updated", []))
    error_count = len(sync_results.get("errors", []))

    # Only show sync info if something changed or errored
    if updated_count > 0:
        console.print(f"[green]✓[/green] Synced {updated_count} tasks to Linear")
        # Reload tasks after sync
        tasks = _load_roadmap_tasks(roadmap_path)
        classified = _classify_blueprints(blueprints, current_user_id, tasks)
    if error_count > 0:
        console.print(f"[yellow]⚠[/yellow] {error_count} sync errors (see above)")

    # Extract for backward compatibility
    bp_to_task = classified["bp_to_task"]
    matched_tasks = classified["matched_tasks"]

    # Legacy variables for existing terminal display
    my_blueprints = [bp for bp in blueprints if bp.get("owner_id") == current_user_id]
    private_bps = [bp for bp in my_blueprints if bp.get("share_type") == "private"]
    public_bps = [bp for bp in my_blueprints if bp.get("share_type") == "public"]
    org_bps = [bp for bp in my_blueprints if bp.get("share_type") == "organization"]

    # Generate CSV if requested
    if csv_output:
        _generate_csv_report(classified, tasks, blueprints, current_user_id, csv_output)
        console.print(f"\n[green]✓[/green] CSV report saved to: {csv_output}")
        # Continue to also generate markdown report if output is specified

    # If output specified, generate markdown
    if output:
        md = _generate_markdown_report(
            classified, tasks, roadmap_path
        )

        # Show diff if previous report exists
        if output.exists():
            old_content = output.read_text(encoding="utf-8")
            _show_diff(old_content, md)

        output.write_text(md, encoding="utf-8")
        console.print(f"\n[green]✓[/green] Report saved to: {output}")

    # If only CSV was requested (no markdown output), return early
    if csv_output and not output:
        return

    # Otherwise show in terminal
    # Header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Blueprint Roadmap Report[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    # Overall Statistics
    console.print("[bold]📊 Overall Statistics[/bold]")
    console.print(f"  Total blueprints (mine): [cyan]{len(my_blueprints)}[/cyan]")
    console.print(f"  ├─ Public:       [green]{len(public_bps)}[/green]")
    console.print(f"  ├─ Private:      [yellow]{len(private_bps)}[/yellow]")
    console.print(f"  └─ Organization: [blue]{len(org_bps)}[/blue]")
    console.print()

    # Roadmap tracking
    if tasks:
        console.print(f"[bold]📋 Roadmap Tasks[/bold]: {len(tasks)} total")

        # Group tasks by week
        weeks: dict[str, list[dict]] = {}
        unscheduled: list[dict] = []

        for task in tasks:
            week = task.get("week", "").strip()
            if week:
                weeks.setdefault(week, []).append(task)
            else:
                unscheduled.append(task)

        # Week-by-week progress
        console.print()
        console.print("[bold]📅 Week-by-Week Progress[/bold]")

        week_table = Table(show_header=True, header_style="bold")
        week_table.add_column("Week", style="cyan", width=10)
        week_table.add_column("Tasks", justify="right", width=8)
        week_table.add_column("Done", justify="right", width=8)
        week_table.add_column("Progress", width=20)
        week_table.add_column("Status", width=10)

        for week_name in sorted(weeks.keys()):
            week_tasks = weeks[week_name]
            done_count = sum(1 for t in week_tasks if t["id"] in matched_tasks or t.get("state") == "done")
            total = len(week_tasks)
            pct = (done_count / total * 100) if total > 0 else 0

            # Progress bar
            bar_width = 15
            filled = int(pct / 100 * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            # Status
            if pct == 100:
                status = "[green]✓ Complete[/green]"
            elif pct > 0:
                status = "[yellow]In Progress[/yellow]"
            else:
                status = "[dim]Not Started[/dim]"

            week_table.add_row(
                week_name,
                str(total),
                str(done_count),
                f"[green]{bar}[/green] {pct:.0f}%",
                status
            )

        console.print(week_table)

        # Unscheduled tasks (Featured/Extra)
        if unscheduled:
            console.print()
            console.print(f"[bold]📦 Unscheduled/Featured Tasks[/bold]: {len(unscheduled)}")
            done_unscheduled = sum(1 for t in unscheduled if t["id"] in matched_tasks or t.get("state") == "done")
            console.print(f"  Completed: [green]{done_unscheduled}[/green] / {len(unscheduled)}")

        # Summary
        total_tasks = len(tasks)
        total_done = len(matched_tasks) + sum(1 for t in tasks if t.get("state") == "done" and t["id"] not in matched_tasks)
        overall_pct = (total_done / total_tasks * 100) if total_tasks > 0 else 0

        console.print()
        console.print(Panel(
            f"[bold]Overall Roadmap Progress: [green]{total_done}[/green] / {total_tasks} ({overall_pct:.0f}%)[/bold]",
            border_style="green" if overall_pct == 100 else "yellow"
        ))
    else:
        console.print(f"[dim]No roadmap file found at: {roadmap_path}[/dim]")

    # Private blueprints list
    console.print()
    console.print("[bold]🔒 Private Blueprints[/bold]")
    if private_bps:
        priv_table = Table(show_header=True, header_style="bold")
        priv_table.add_column("ID", style="dim", max_width=26)
        priv_table.add_column("Name", style="yellow", max_width=40)
        priv_table.add_column("Category", max_width=15)
        priv_table.add_column("Roadmap Task", max_width=20)

        for bp in private_bps:
            bp_id = bp.get("_id", "-")
            matched = bp_to_task.get(bp_id) if tasks else None
            roadmap_ref = matched["id"] if matched else "-"

            priv_table.add_row(
                bp_id,
                bp.get("name", "-"),
                bp.get("category", "-"),
                roadmap_ref
            )
        console.print(priv_table)
    else:
        console.print("  [dim]No private blueprints[/dim]")

    # Public blueprints list
    console.print()
    console.print("[bold]🌐 Public Blueprints[/bold]")
    if public_bps:
        pub_table = Table(show_header=True, header_style="bold")
        pub_table.add_column("ID", style="dim", max_width=26)
        pub_table.add_column("Name", style="green", max_width=40)
        pub_table.add_column("Category", max_width=15)
        pub_table.add_column("Roadmap Task", max_width=20)

        for bp in public_bps:
            bp_id = bp.get("_id", "-")
            matched = bp_to_task.get(bp_id) if tasks else None
            roadmap_ref = matched["id"] if matched else "-"

            pub_table.add_row(
                bp_id,
                bp.get("name", "-"),
                bp.get("category", "-"),
                roadmap_ref
            )
        console.print(pub_table)
    else:
        console.print("  [dim]No public blueprints[/dim]")

    # Missing from roadmap (blueprints without matching tasks)
    if tasks:
        unmatched_bps = [bp for bp in my_blueprints if bp.get("_id") not in bp_to_task]
        if unmatched_bps:
            console.print()
            console.print(f"[bold]❓ Blueprints Not in Roadmap[/bold]: {len(unmatched_bps)}")
            for bp in unmatched_bps[:10]:  # Show first 10
                vis = bp.get("share_type", "?")
                vis_color = "green" if vis == "public" else "yellow" if vis == "private" else "blue"
                console.print(f"  [{vis_color}]{vis:12}[/{vis_color}] {bp.get('name', '-')}")
            if len(unmatched_bps) > 10:
                console.print(f"  [dim]...and {len(unmatched_bps) - 10} more[/dim]")

        # Tasks without matching blueprints
        unmatched_tasks = [t for t in tasks if t["id"] not in matched_tasks and t.get("state") != "done"]
        if unmatched_tasks:
            console.print()
            console.print(f"[bold]⚠️  Roadmap Tasks Not Yet Completed[/bold]: {len(unmatched_tasks)}")
            for task in unmatched_tasks[:10]:
                week = task.get("week", "unscheduled")
                console.print(f"  [{task['id']}] {task.get('title', '-')} [dim]({week})[/dim]")
            if len(unmatched_tasks) > 10:
                console.print(f"  [dim]...and {len(unmatched_tasks) - 10} more[/dim]")

    console.print()


def _generate_csv_report(
    classified: dict,
    tasks: list,
    all_blueprints: list,
    current_user_id: str,
    output_path: Path,
) -> None:
    """Generate CSV report with all blueprint data.

    Columns:
    - blueprint_id: Platform blueprint ID
    - name: Blueprint name
    - category: Blueprint category
    - share_type: Visibility (public/organization/private)
    - classification: planned/adhoc/showcase/backlog/unowned
    - status: done/review/in_progress (based on share_type)
    - task_id: Roadmap task ID (e.g., BP-038)
    - linear_id: Linear issue UUID
    - week: Week label (week-1, week-2, etc.)
    - type: showcase/usecase
    - platform_url: Link to blueprint in Studio
    - linear_url: Link to Linear issue
    - owner: owner_id (mine or other)
    - description: Blueprint description
    """
    # Load mappings to identify planned blueprints
    mappings = _load_blueprint_map()
    mapped_bp_ids = set(mappings.values())

    # Build reverse lookup: blueprint_id -> linear_id
    bp_to_linear_id = {bp_id: lin_id for lin_id, bp_id in mappings.items()}

    # Build task lookup by blueprint_id
    bp_to_task = classified.get("bp_to_task", {})

    # Extract classified data
    planned = classified["planned"]
    adhoc = classified["adhoc"]
    showcase = classified["showcase"]
    unowned_public = classified["unowned_public"]
    backlog = classified["backlog"]

    # Status mapping based on share_type
    status_map = {
        "public": "done",
        "organization": "review",
        "private": "in_progress",
    }

    rows = []

    # Helper to create a row for a blueprint
    def make_row(bp: dict, classification: str, bp_type: str = "usecase") -> dict:
        bp_id = bp.get("_id", "")
        share_type = bp.get("share_type", "private")
        task = bp_to_task.get(bp_id, {})
        linear_id = task.get("linear_id", "") or bp_to_linear_id.get(bp_id, "")
        task_id = task.get("id", "")
        week = task.get("week", "")

        # Determine if this is showcase
        if "[Moonshot]" in task.get("title", "") or "[Featured]" in task.get("title", ""):
            bp_type = "showcase"

        return {
            "blueprint_id": bp_id,
            "name": bp.get("name", ""),
            "category": bp.get("category", ""),
            "share_type": share_type,
            "classification": classification,
            "status": status_map.get(share_type, "unknown"),
            "task_id": task_id,
            "linear_id": linear_id,
            "week": week,
            "type": bp_type,
            "platform_url": f"{STUDIO_URL_BASE}{bp_id}" if bp_id else "",
            "linear_url": f"https://linear.app/lyzr/issue/{linear_id}" if linear_id else "",
            "owner": "mine" if bp.get("owner_id") == current_user_id else "other",
            "description": (bp.get("description", "") or "")[:200],  # Truncate long descriptions
        }

    # Add showcase blueprints
    for bp in showcase:
        rows.append(make_row(bp, "showcase", "showcase"))

    # Add planned blueprints (by share_type)
    for share_type in ["public", "organization", "private"]:
        for bp in planned[share_type]:
            bp_id = bp.get("_id", "")
            task = bp_to_task.get(bp_id, {})
            bp_type = "showcase" if "[Moonshot]" in task.get("title", "") or "[Featured]" in task.get("title", "") else "usecase"
            rows.append(make_row(bp, "planned", bp_type))

    # Add adhoc blueprints (by share_type)
    for share_type in ["public", "organization", "private"]:
        for bp in adhoc[share_type]:
            rows.append(make_row(bp, "adhoc", "usecase"))

    # Add backlog tasks (no blueprint yet)
    for task in backlog:
        task_id = task.get("id", "")
        linear_id = task.get("linear_id", "")
        title = task.get("title", "")
        week = task.get("week", "")
        bp_type = "showcase" if "[Moonshot]" in title or "[Featured]" in title else "usecase"

        rows.append({
            "blueprint_id": "",
            "name": title,
            "category": "",
            "share_type": "",
            "classification": "backlog",
            "status": "backlog",
            "task_id": task_id,
            "linear_id": linear_id,
            "week": week,
            "type": bp_type,
            "platform_url": "",
            "linear_url": f"https://linear.app/lyzr/issue/{linear_id}" if linear_id else "",
            "owner": "mine",
            "description": "",
        })

    # Add unowned public blueprints
    for bp in unowned_public:
        rows.append(make_row(bp, "unowned", "usecase"))

    # Write CSV
    fieldnames = [
        "blueprint_id", "name", "category", "share_type", "classification",
        "status", "task_id", "linear_id", "week", "type",
        "platform_url", "linear_url", "owner", "description"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _generate_markdown_report(
    classified: dict,
    tasks: list,
    roadmap_path: Path,
) -> str:
    """Generate markdown report content with structured classification.

    Structure:
    1. Summary
    2. Unowned Public (discovery)
    3. Showcase (Moonshots/Featured)
    4. Planned (from roadmap):
       - Public (Reviewed)
       - Organization (Under Review)
       - Private (In Progress)
       - Backlog
    5. Ad-hoc (not in roadmap)
    """
    from datetime import datetime

    # Extract classified data
    unowned_public = classified["unowned_public"]
    planned = classified["planned"]
    adhoc = classified["adhoc"]
    showcase = classified["showcase"]
    bp_to_task = classified["bp_to_task"]
    matched_tasks = classified["matched_tasks"]
    backlog = classified["backlog"]
    total_owned = classified["total_owned"]

    lines = []
    lines.append("# Blueprint Library Report")
    lines.append("")
    lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # =========================================================================
    # Summary
    # =========================================================================
    lines.append("## 📊 Summary")
    lines.append("")

    # Calculate counts
    total_adhoc = len(adhoc["public"]) + len(adhoc["organization"]) + len(adhoc["private"])

    # Split showcase by share type
    showcase_public = [bp for bp in showcase if bp.get("share_type") == "public"]
    showcase_org = [bp for bp in showcase if bp.get("share_type") == "organization"]
    showcase_private = [bp for bp in showcase if bp.get("share_type") == "private"]

    # Count backlog by showcase vs usecase
    backlog_showcase = [t for t in backlog if "[Moonshot]" in t.get("title", "") or "[Featured]" in t.get("title", "")]
    backlog_usecase = [t for t in backlog if "[Moonshot]" not in t.get("title", "") and "[Featured]" not in t.get("title", "")]

    # Planned (Roadmap) Section
    if tasks:
        total_tasks = len(tasks)
        total_done = sum(1 for t in tasks if t["id"] in matched_tasks or t.get("state") == "done")
        total_roadmap_bps = len(showcase) + len(planned["public"]) + len(planned["organization"]) + len(planned["private"])

        lines.append(f"**Planned (Roadmap):** {total_roadmap_bps} BPs / {total_tasks} tasks")
        lines.append("")
        lines.append("| Status | Showcase | Usecase | Total |")
        lines.append("|--------|----------|---------|-------|")
        # Done (Public)
        lines.append(f"| ✅ Done (Public) | {len(showcase_public)} | {len(planned['public'])} | {len(showcase_public) + len(planned['public'])} |")
        # Review (Organization)
        lines.append(f"| 🔄 Review (Org) | {len(showcase_org)} | {len(planned['organization'])} | {len(showcase_org) + len(planned['organization'])} |")
        # In Progress (Private)
        lines.append(f"| 🔨 In Progress (Private) | {len(showcase_private)} | {len(planned['private'])} | {len(showcase_private) + len(planned['private'])} |")
        lines.append("")

    # Ad-hoc Section
    lines.append(f"**Ad-hoc Request BPs:** {total_adhoc}")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| ✅ Done (Public) | {len(adhoc['public'])} |")
    lines.append(f"| 🔄 Review (Org) | {len(adhoc['organization'])} |")
    lines.append(f"| 🔨 In Progress (Private) | {len(adhoc['private'])} |")
    lines.append("")

    # Backlog Section (at the end of summary)
    if tasks:
        lines.append(f"**Backlog:** {len(backlog)} tasks")
        lines.append("")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        lines.append(f"| Showcase | {len(backlog_showcase)} |")
        lines.append(f"| Usecase | {len(backlog_usecase)} |")
        lines.append("")

    # Unowned Public (at the very end of summary)
    lines.append(f"**Unowned Public BPs:** {len(unowned_public)}")
    lines.append("")

    # =========================================================================
    # 1. Planned (Roadmap) - organized by status
    # =========================================================================
    lines.append("## 📋 Planned (Roadmap)")
    lines.append("")

    # Linear base URL for roadmap links
    LINEAR_BASE_URL = "https://linear.app/lyzr/issue/"

    # Helper to render a standardized blueprint table
    # Format: Name | Category | Roadmap Link | Platform Link
    def _render_bp_table(bps: list, has_roadmap: bool = True) -> None:
        if not bps:
            lines.append("*None*")
            return
        lines.append("| Name | Category | Roadmap Link | Platform Link |")
        lines.append("|------|----------|--------------|---------------|")
        for bp in bps:
            bp_id = bp.get("_id", "-")
            task = bp_to_task.get(bp_id)
            platform_url = f"{STUDIO_URL_BASE}{bp_id}"
            if has_roadmap and task:
                linear_id = task.get("linear_id", "")
                task_id = task.get("id", "-")
                if linear_id:
                    roadmap_link = f"[{task_id}]({LINEAR_BASE_URL}{linear_id})"
                else:
                    roadmap_link = task_id
            else:
                roadmap_link = "-"
            lines.append(f"| {bp.get('name', '-')} | {bp.get('category', '-')} | {roadmap_link} | [Open]({platform_url}) |")

    # ✅ Done (Public)
    lines.append("### ✅ Done (Public)")
    lines.append("")
    if showcase_public or planned["public"]:
        if showcase_public:
            lines.append("**Showcase:**")
            lines.append("")
            _render_bp_table(showcase_public)
            lines.append("")
        if planned["public"]:
            lines.append("**Usecase:**")
            lines.append("")
            _render_bp_table(planned["public"])
            lines.append("")
    else:
        lines.append("*None*")
        lines.append("")

    # 🔄 Review (Organization)
    lines.append("### 🔄 Review (Organization)")
    lines.append("")
    if showcase_org or planned["organization"]:
        if showcase_org:
            lines.append("**Showcase:**")
            lines.append("")
            _render_bp_table(showcase_org)
            lines.append("")
        if planned["organization"]:
            lines.append("**Usecase:**")
            lines.append("")
            _render_bp_table(planned["organization"])
            lines.append("")
    else:
        lines.append("*None*")
        lines.append("")

    # 🔨 In Progress (Private)
    lines.append("### 🔨 In Progress (Private)")
    lines.append("")
    if showcase_private or planned["private"]:
        if showcase_private:
            lines.append("**Showcase:**")
            lines.append("")
            _render_bp_table(showcase_private)
            lines.append("")
        if planned["private"]:
            lines.append("**Usecase:**")
            lines.append("")
            _render_bp_table(planned["private"])
            lines.append("")
    else:
        lines.append("*None*")
        lines.append("")

    # =========================================================================
    # 3. Ad-hoc Request BPs (not in roadmap)
    # =========================================================================
    lines.append("## 🎯 Ad-hoc Request BPs")
    lines.append("")
    lines.append("> Blueprints created outside the roadmap")
    lines.append("")

    # Helper to render ad-hoc blueprint table (no roadmap link)
    def _render_adhoc_table(bps: list) -> None:
        if not bps:
            lines.append("*None*")
            return
        lines.append("| Name | Category | Roadmap Link | Platform Link |")
        lines.append("|------|----------|--------------|---------------|")
        for bp in bps:
            bp_id = bp.get("_id", "-")
            url = f"{STUDIO_URL_BASE}{bp_id}"
            lines.append(f"| {bp.get('name', '-')} | {bp.get('category', '-')} | - | [Open]({url}) |")

    # ✅ Done (Public)
    lines.append("### ✅ Done (Public)")
    lines.append("")
    _render_adhoc_table(adhoc["public"])
    lines.append("")

    # 🔄 Review (Organization)
    lines.append("### 🔄 Review (Organization)")
    lines.append("")
    _render_adhoc_table(adhoc["organization"])
    lines.append("")

    # 🔨 In Progress (Private)
    lines.append("### 🔨 In Progress (Private)")
    lines.append("")
    _render_adhoc_table(adhoc["private"])
    lines.append("")

    # =========================================================================
    # 4. Backlog (tasks without blueprints yet)
    # =========================================================================
    lines.append("## 📝 Backlog")
    lines.append("")
    lines.append("> Roadmap tasks not yet started")
    lines.append("")

    def _render_backlog_table(tasks_list: list) -> None:
        if not tasks_list:
            lines.append("*None*")
            return
        lines.append("| Name | Category | Roadmap Link | Platform Link |")
        lines.append("|------|----------|--------------|---------------|")
        for task in tasks_list:
            task_id = task.get("id", "-")
            title = task.get("title", "-")
            linear_id = task.get("linear_id", "")
            # Extract category from title or use default
            category = "-"
            if linear_id:
                roadmap_link = f"[{task_id}]({LINEAR_BASE_URL}{linear_id})"
            else:
                roadmap_link = task_id
            lines.append(f"| {title} | {category} | {roadmap_link} | - |")

    if backlog:
        if backlog_showcase:
            lines.append("### Showcase")
            lines.append("")
            _render_backlog_table(backlog_showcase)
            lines.append("")
        if backlog_usecase:
            lines.append("### Usecase")
            lines.append("")
            _render_backlog_table(backlog_usecase)
            lines.append("")
    else:
        lines.append("*No backlog items - roadmap complete!* 🎉")
        lines.append("")

    # =========================================================================
    # 5. Unowned Public (Discovery)
    # =========================================================================
    lines.append("## 🔍 Unowned Public BPs")
    lines.append("")
    lines.append("> Blueprints from other users available for discovery")
    lines.append("")
    if unowned_public:
        lines.append("| Name | Category | Roadmap Link | Platform Link |")
        lines.append("|------|----------|--------------|---------------|")
        for bp in unowned_public:
            bp_id = bp.get("_id", "-")
            url = f"{STUDIO_URL_BASE}{bp_id}"
            lines.append(f"| {bp.get('name', '-')} | {bp.get('category', '-')} | - | [Open]({url}) |")
    else:
        lines.append("*No unowned public blueprints*")
    lines.append("")

    lines.append("---")
    lines.append("*Generated by `bp list --report`*")

    return "\n".join(lines)


def _show_diff(old_content: str, new_content: str) -> None:
    """Show diff between old and new report."""
    import difflib

    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    # Skip the timestamp line for comparison
    old_compare = [l for l in old_lines if not l.startswith("> Generated:")]
    new_compare = [l for l in new_lines if not l.startswith("> Generated:")]

    if old_compare == new_compare:
        console.print("[dim]No changes since last report[/dim]")
        return

    console.print("\n[bold]📝 Changes since last report:[/bold]\n")

    # Get unified diff
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="previous",
        tofile="current",
        lineterm=""
    ))

    # Count changes
    added = 0
    removed = 0
    changes_shown = 0
    max_changes = 20  # Limit displayed changes

    for line in diff[2:]:  # Skip header lines
        if line.startswith("+") and not line.startswith("+++"):
            # Skip timestamp changes
            if "> Generated:" in line:
                continue
            added += 1
            if changes_shown < max_changes:
                console.print(f"[green]{line}[/green]")
                changes_shown += 1
        elif line.startswith("-") and not line.startswith("---"):
            # Skip timestamp changes
            if "> Generated:" in line:
                continue
            removed += 1
            if changes_shown < max_changes:
                console.print(f"[red]{line}[/red]")
                changes_shown += 1

    if changes_shown >= max_changes:
        remaining = (added + removed) - max_changes
        if remaining > 0:
            console.print(f"[dim]...and {remaining} more changes[/dim]")

    console.print(f"\n[dim]Summary: [green]+{added}[/green] [red]-{removed}[/red] lines[/dim]")
