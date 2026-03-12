"""Linear Sync CLI Commands.

Sync blueprint roadmap tasks with Linear for project tracking.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Load environment variables
load_dotenv()

console = Console()
app = typer.Typer(
    name="linear",
    help="Sync blueprint roadmap tasks with Linear",
    no_args_is_help=True,
)

LINEAR_API_URL = "https://api.linear.app/graphql"
LINEAR_INITIATIVE_ID = "091ba015-09c1-4a28-8a71-bbc31e9599c4"  # Blueprints initiative

# Priority mapping (Linear: 0=none, 1=urgent, 2=high, 3=medium, 4=low)
PRIORITY_MAP = {
    "urgent": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "none": 0,
}


def _get_config() -> tuple[str, str, Path]:
    """Get Linear configuration from environment."""
    api_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("LINEAR_TEAM_ID")

    if not api_key:
        console.print("[red]Error:[/red] LINEAR_API_KEY not set in environment")
        raise typer.Exit(1)
    if not team_id:
        console.print("[red]Error:[/red] LINEAR_TEAM_ID not set in environment")
        raise typer.Exit(1)

    # Default roadmap directory
    roadmap_dir = Path(__file__).parent.parent.parent.parent / "roadmap"

    return api_key, team_id, roadmap_dir


@dataclass
class Project:
    id: str
    name: str
    initiative: str
    team: str
    description: str
    state: str
    linear_id: Optional[str] = None


@dataclass
class Task:
    id: str
    title: str
    project_id: str
    description: str
    priority: str
    state: str
    labels: str
    linear_id: Optional[str] = None
    week: Optional[str] = None


class LinearClient:
    """Client for Linear GraphQL API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }

    def _query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            LINEAR_API_URL,
            json=payload,
            headers=self.headers,
            timeout=30,
        )

        result = response.json()

        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get("data", {})

    def get_team_states(self, team_id: str) -> List[Dict]:
        """Get workflow states for a team."""
        query = """
        query GetTeamStates($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                    }
                }
            }
        }
        """
        data = self._query(query, {"teamId": team_id})
        return data.get("team", {}).get("states", {}).get("nodes", [])

    def list_projects(self) -> List[Dict]:
        """List all projects."""
        query = """
        query ListProjects {
            projects(first: 100) {
                nodes {
                    id
                    name
                    description
                    state
                }
            }
        }
        """
        data = self._query(query)
        return data.get("projects", {}).get("nodes", [])

    def create_project(
        self, name: str, team_ids: List[str], description: str = "", initiative_id: Optional[str] = None
    ) -> Dict:
        """Create a new project linked to an initiative."""
        query = """
        mutation CreateProject($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project {
                    id
                    name
                    url
                }
            }
        }
        """
        variables = {
            "input": {
                "name": name,
                "teamIds": team_ids,
                "description": description,
            }
        }
        if initiative_id:
            variables["input"]["initiativeIds"] = [initiative_id]
        data = self._query(query, variables)
        result = data.get("projectCreate", {})
        if result.get("success"):
            return result.get("project")
        raise Exception(f"Failed to create project: {name}")

    def get_or_create_label(self, team_id: str, name: str) -> str:
        """Get or create a label by name."""
        query = """
        query GetTeamLabels($teamId: String!) {
            team(id: $teamId) {
                labels {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        data = self._query(query, {"teamId": team_id})
        for label in data.get("team", {}).get("labels", {}).get("nodes", []):
            if label["name"].lower() == name.lower():
                return label["id"]

        mutation = """
        mutation CreateLabel($teamId: String!, $name: String!) {
            issueLabelCreate(input: { teamId: $teamId, name: $name }) {
                issueLabel {
                    id
                    name
                }
            }
        }
        """
        data = self._query(mutation, {"teamId": team_id, "name": name})
        return data.get("issueLabelCreate", {}).get("issueLabel", {}).get("id")

    def get_project_issues(self, project_id: str) -> List[Dict]:
        """Get all issues in a project with full details."""
        query = """
        query GetProjectIssues($projectId: String!) {
            project(id: $projectId) {
                issues {
                    nodes {
                        id
                        identifier
                        title
                        description
                        priority
                        state {
                            name
                            type
                        }
                        labels {
                            nodes {
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        data = self._query(query, {"projectId": project_id})
        return data.get("project", {}).get("issues", {}).get("nodes", [])

    def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue by ID."""
        mutation = """
        mutation DeleteIssue($id: String!) {
            issueDelete(id: $id) {
                success
            }
        }
        """
        data = self._query(mutation, {"id": issue_id})
        return data.get("issueDelete", {}).get("success", False)

    def create_issue(
        self,
        title: str,
        team_id: str,
        project_id: Optional[str] = None,
        description: str = "",
        priority: int = 0,
        state_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
    ) -> Dict:
        """Create a new issue."""
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        input_data = {
            "title": title,
            "teamId": team_id,
            "description": description,
            "priority": priority,
        }
        if project_id:
            input_data["projectId"] = project_id
        if state_id:
            input_data["stateId"] = state_id
        if label_ids:
            input_data["labelIds"] = label_ids

        data = self._query(query, {"input": input_data})
        result = data.get("issueCreate", {})
        if result.get("success"):
            return result.get("issue")
        raise Exception(f"Failed to create issue: {title}")

    def update_initiative(self, initiative_id: str, description: str) -> bool:
        """Update initiative description."""
        query = """
        mutation UpdateInitiative($id: String!, $input: InitiativeUpdateInput!) {
            initiativeUpdate(id: $id, input: $input) {
                success
                initiative {
                    id
                    name
                }
            }
        }
        """
        variables = {
            "id": initiative_id,
            "input": {"description": description},
        }
        data = self._query(query, variables)
        return data.get("initiativeUpdate", {}).get("success", False)

    def update_issue_state(self, issue_id: str, state_id: str) -> bool:
        """Update issue state by ID."""
        mutation = """
        mutation UpdateIssue($id: String!, $stateId: String!) {
            issueUpdate(id: $id, input: { stateId: $stateId }) {
                success
                issue {
                    id
                    title
                    state { name }
                }
            }
        }
        """
        data = self._query(mutation, {"id": issue_id, "stateId": state_id})
        return data.get("issueUpdate", {}).get("success", False)

    def get_done_state_id(self, team_id: str) -> Optional[str]:
        """Get the 'Done' workflow state ID for a team."""
        states = self.get_team_states(team_id)
        for state in states:
            if state["name"].lower() == "done" or state["type"] == "completed":
                return state["id"]
        return None

    def get_in_review_state_id(self, team_id: str) -> Optional[str]:
        """Get the 'In Review' workflow state ID for a team."""
        states = self.get_team_states(team_id)
        for state in states:
            if state["name"].lower() == "in review":
                return state["id"]
        return None

    def get_in_progress_state_id(self, team_id: str) -> Optional[str]:
        """Get the 'In Progress' workflow state ID for a team."""
        states = self.get_team_states(team_id)
        for state in states:
            if state["name"].lower() == "in progress":
                return state["id"]
        return None

    def get_workflow_state_ids(self, team_id: str) -> Dict[str, Optional[str]]:
        """Get all relevant workflow state IDs for share_type sync.

        Returns mapping of share_type to Linear state ID:
        - public → Done
        - organization → In Review
        - private → In Progress
        """
        states = self.get_team_states(team_id)
        result = {
            "public": None,       # Done
            "organization": None,  # In Review
            "private": None,       # In Progress
        }
        for state in states:
            name_lower = state["name"].lower()
            if name_lower == "done" or state["type"] == "completed":
                result["public"] = state["id"]
            elif name_lower == "in review":
                result["organization"] = state["id"]
            elif name_lower == "in progress":
                result["private"] = state["id"]
        return result


def _get_linear_client() -> LinearClient:
    """Get a configured LinearClient instance."""
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        raise ValueError("LINEAR_API_KEY not set in environment")
    return LinearClient(api_key)


def _get_linear_team_id() -> str:
    """Get Linear team ID from environment."""
    team_id = os.getenv("LINEAR_TEAM_ID")
    if not team_id:
        raise ValueError("LINEAR_TEAM_ID not set in environment")
    return team_id


class SyncManager:
    """Manages sync between CSV and Linear."""

    def __init__(self, csv_dir: Path, api_key: str, team_id: str):
        self.csv_dir = csv_dir
        self.projects_file = csv_dir / "projects.csv"
        self.tasks_file = csv_dir / "tasks.csv"
        self.client = LinearClient(api_key)
        self.team_id = team_id
        self._state_cache: Dict[str, str] = {}

    def _load_projects(self) -> List[Project]:
        """Load projects from CSV."""
        projects = []
        if not self.projects_file.exists():
            return projects
        with open(self.projects_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                projects.append(
                    Project(
                        id=row["id"],
                        name=row["name"],
                        initiative=row["initiative"],
                        team=row["team"],
                        description=row["description"],
                        state=row["state"],
                        linear_id=row.get("linear_id") or None,
                    )
                )
        return projects

    def _load_tasks(self) -> List[Task]:
        """Load tasks from CSV."""
        tasks = []
        if not self.tasks_file.exists():
            return tasks
        with open(self.tasks_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tasks.append(
                    Task(
                        id=row["id"],
                        title=row["title"],
                        project_id=row["project_id"],
                        description=row["description"],
                        priority=row["priority"],
                        state=row["state"],
                        labels=row["labels"],
                        linear_id=row.get("linear_id") or None,
                        week=row.get("week") or None,
                    )
                )
        return tasks

    def _save_projects(self, projects: List[Project]) -> None:
        """Save projects to CSV."""
        with open(self.projects_file, "w", newline="") as f:
            fieldnames = ["id", "name", "initiative", "team", "description", "state", "linear_id"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in projects:
                writer.writerow({
                    "id": p.id,
                    "name": p.name,
                    "initiative": p.initiative,
                    "team": p.team,
                    "description": p.description,
                    "state": p.state,
                    "linear_id": p.linear_id or "",
                })

    def _save_tasks(self, tasks: List[Task]) -> None:
        """Save tasks to CSV."""
        with open(self.tasks_file, "w", newline="") as f:
            fieldnames = ["id", "title", "project_id", "description", "priority", "state", "labels", "linear_id", "week"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in tasks:
                writer.writerow({
                    "id": t.id,
                    "title": t.title,
                    "project_id": t.project_id,
                    "description": t.description,
                    "priority": t.priority,
                    "state": t.state,
                    "labels": t.labels,
                    "linear_id": t.linear_id or "",
                    "week": t.week or "",
                })

    def _get_backlog_state_id(self) -> Optional[str]:
        """Get the Backlog state ID for the team."""
        if not self._state_cache:
            states = self.client.get_team_states(self.team_id)
            for s in states:
                self._state_cache[s["name"].lower()] = s["id"]
        return self._state_cache.get("backlog")

    def sync_projects(self, dry_run: bool = False) -> int:
        """Sync projects to Linear. Returns count of synced projects."""
        projects = self._load_projects()
        existing = {p["name"]: p for p in self.client.list_projects()}

        synced = 0
        for project in projects:
            if project.linear_id:
                console.print(f"  [green]✓[/green] {project.name} (already synced)")
                continue

            if project.name in existing:
                project.linear_id = existing[project.name]["id"]
                console.print(f"  [yellow]→[/yellow] {project.name} (found existing)")
                synced += 1
            else:
                if dry_run:
                    console.print(f"  [blue]+[/blue] {project.name} (would create)")
                else:
                    try:
                        result = self.client.create_project(
                            name=project.name,
                            team_ids=[self.team_id],
                            description=project.description,
                            initiative_id=LINEAR_INITIATIVE_ID,
                        )
                        project.linear_id = result["id"]
                        console.print(f"  [green]+[/green] {project.name} (created)")
                        synced += 1
                    except Exception as e:
                        console.print(f"  [red]✗[/red] {project.name} ({e})")

        if not dry_run:
            self._save_projects(projects)

        return synced

    def sync_tasks(self, dry_run: bool = False, limit: Optional[int] = None) -> int:
        """Sync tasks to Linear. Returns count of synced tasks."""
        projects = self._load_projects()
        tasks = self._load_tasks()

        project_map = {p.id: p.linear_id for p in projects if p.linear_id}
        backlog_state_id = self._get_backlog_state_id()

        # Pre-create week labels
        week_label_cache: Dict[str, str] = {}
        if not dry_run:
            for week in ["week-1", "week-2", "week-3", "week-4", "week-5", "week-6", "week-7"]:
                week_label_cache[week] = self.client.get_or_create_label(self.team_id, week)

        # Filter tasks with valid weeks
        active_tasks = [t for t in tasks if t.week and t.week.startswith("week-")]
        task_count = len(active_tasks) if limit is None else min(limit, len(active_tasks))

        synced = 0
        for task in active_tasks:
            if limit and synced >= limit:
                break

            if task.linear_id:
                console.print(f"  [green]✓[/green] {task.id}: {task.title[:40]}...")
                continue

            linear_project_id = project_map.get(task.project_id)
            if not linear_project_id:
                console.print(f"  [red]✗[/red] {task.id}: {task.title[:40]}... (project not synced)")
                continue

            if dry_run:
                console.print(f"  [blue]+[/blue] {task.id}: {task.title[:40]}... [{task.week}]")
                synced += 1
            else:
                try:
                    label_ids = []
                    if task.week and task.week in week_label_cache:
                        label_ids.append(week_label_cache[task.week])

                    result = self.client.create_issue(
                        title=f"[{task.id}] {task.title}",
                        team_id=self.team_id,
                        project_id=linear_project_id,
                        description=task.description,
                        priority=PRIORITY_MAP.get(task.priority, 0),
                        state_id=backlog_state_id,
                        label_ids=label_ids if label_ids else None,
                    )
                    task.linear_id = result["id"]
                    console.print(f"  [green]+[/green] {task.id}: {task.title[:40]}... ({result['identifier']})")
                    synced += 1
                except Exception as e:
                    console.print(f"  [red]✗[/red] {task.id}: {task.title[:40]}... ({e})")

        if not dry_run:
            self._save_tasks(tasks)

        return synced

    def delete_project_issues(self, project_id: str, dry_run: bool = False) -> int:
        """Delete all issues in a project."""
        projects = self._load_projects()
        project = next((p for p in projects if p.id == project_id), None)
        if not project or not project.linear_id:
            console.print(f"[red]Project {project_id} not found or not synced[/red]")
            return 0

        issues = self.client.get_project_issues(project.linear_id)
        console.print(f"{'[DRY RUN] ' if dry_run else ''}Deleting {len(issues)} issues from {project.name}...")

        deleted = 0
        for issue in issues:
            if dry_run:
                console.print(f"  [blue]-[/blue] {issue['identifier']}: {issue['title'][:40]}...")
            else:
                if self.client.delete_issue(issue["id"]):
                    console.print(f"  [red]-[/red] {issue['identifier']}: {issue['title'][:40]}...")
                    deleted += 1
                else:
                    console.print(f"  [red]✗[/red] Failed to delete {issue['identifier']}")

        if not dry_run:
            tasks = self._load_tasks()
            for task in tasks:
                if task.project_id == project_id:
                    task.linear_id = None
            self._save_tasks(tasks)

        return deleted

    def get_status(self) -> tuple[List[Project], List[Task]]:
        """Get sync status."""
        return self._load_projects(), self._load_tasks()

    def pull_updates(self) -> int:
        """Pull updates from Linear. Returns count of updated IDs."""
        projects = self._load_projects()
        existing_projects = {p["name"]: p for p in self.client.list_projects()}

        updated = 0
        for project in projects:
            if not project.linear_id and project.name in existing_projects:
                project.linear_id = existing_projects[project.name]["id"]
                updated += 1

        self._save_projects(projects)
        return updated


# CLI Commands

@app.command("push")
def push_cmd(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview changes without syncing"),
    projects_only: bool = typer.Option(False, "--projects", "-p", help="Sync only projects"),
    tasks_only: bool = typer.Option(False, "--tasks", "-t", help="Sync only tasks"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of tasks to sync"),
) -> None:
    """Push roadmap tasks to Linear.

    Syncs projects and tasks from CSV files to Linear issues.
    Tasks are tagged with week labels for sprint planning.

    Examples:
        bp linear push                    # Sync all
        bp linear push --dry-run          # Preview changes
        bp linear push --projects         # Only sync projects
        bp linear push --tasks -l 10      # Sync up to 10 tasks
    """
    api_key, team_id, roadmap_dir = _get_config()
    manager = SyncManager(roadmap_dir, api_key, team_id)

    if dry_run:
        console.print(Panel("[yellow]DRY RUN[/yellow] - No changes will be made", style="yellow"))

    if not tasks_only:
        console.print("\n[bold]Syncing Projects...[/bold]")
        project_count = manager.sync_projects(dry_run=dry_run)
        console.print(f"  → {project_count} projects synced")

    if not projects_only:
        console.print("\n[bold]Syncing Tasks...[/bold]")
        task_count = manager.sync_tasks(dry_run=dry_run, limit=limit)
        console.print(f"  → {task_count} tasks synced")

    console.print("\n[green]✓[/green] Push complete!")


@app.command("pull")
def pull_cmd() -> None:
    """Pull Linear project IDs to local CSV.

    Updates local CSV files with Linear project IDs for projects
    that exist in Linear but don't have IDs locally.

    Example:
        bp linear pull
    """
    api_key, team_id, roadmap_dir = _get_config()
    manager = SyncManager(roadmap_dir, api_key, team_id)

    console.print("[bold]Pulling from Linear...[/bold]")
    updated = manager.pull_updates()
    console.print(f"  → Updated {updated} project IDs")
    console.print("[green]✓[/green] Pull complete!")


@app.command("status")
def status_cmd() -> None:
    """Show sync status of projects and tasks.

    Displays how many projects and tasks are synced with Linear.

    Example:
        bp linear status
    """
    api_key, team_id, roadmap_dir = _get_config()
    manager = SyncManager(roadmap_dir, api_key, team_id)

    projects, tasks = manager.get_status()

    synced_projects = sum(1 for p in projects if p.linear_id)
    synced_tasks = sum(1 for t in tasks if t.linear_id)

    # Summary
    console.print(Panel.fit(
        f"[bold]Projects:[/bold] {synced_projects}/{len(projects)} synced\n"
        f"[bold]Tasks:[/bold] {synced_tasks}/{len(tasks)} synced",
        title="Sync Status"
    ))

    # Projects table
    table = Table(title="Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("State")
    table.add_column("Synced", justify="center")

    for p in projects:
        status = "[green]✓[/green]" if p.linear_id else "[dim]○[/dim]"
        table.add_row(p.id, p.name, p.state, status)

    console.print(table)

    # Tasks by project
    console.print("\n[bold]Tasks by Project:[/bold]")
    for p in projects:
        project_tasks = [t for t in tasks if t.project_id == p.id]
        synced = sum(1 for t in project_tasks if t.linear_id)
        pct = (synced / len(project_tasks) * 100) if project_tasks else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        console.print(f"  {p.name}: {bar} {synced}/{len(project_tasks)}")


@app.command("delete-issues")
def delete_issues_cmd(
    project_id: str = typer.Argument(..., help="Project ID (e.g., BP-LIB)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview what would be deleted"),
    force: bool = typer.Option(False, "--force", "-y", help="Skip confirmation"),
) -> None:
    """Delete all Linear issues in a project.

    Removes all issues from the specified project in Linear
    and clears the linear_ids in the local tasks CSV.

    Examples:
        bp linear delete-issues BP-LIB
        bp linear delete-issues BP-LIB --dry-run
        bp linear delete-issues BP-LIB --force
    """
    api_key, team_id, roadmap_dir = _get_config()
    manager = SyncManager(roadmap_dir, api_key, team_id)

    if not dry_run and not force:
        confirm = typer.confirm(f"Delete all issues in project {project_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    deleted = manager.delete_project_issues(project_id, dry_run=dry_run)
    console.print(f"\n{'Would delete' if dry_run else 'Deleted'} {deleted} issues")


@app.command("update-initiative")
def update_initiative_cmd(
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Markdown file for initiative description",
        exists=True,
    ),
) -> None:
    """Update Blueprints initiative description from markdown.

    Updates the Linear initiative description with contents
    from a markdown file. Defaults to ~/Documents/lyzr/kb/README.md.

    Examples:
        bp linear update-initiative
        bp linear update-initiative -f ./INITIATIVE.md
    """
    api_key, team_id, _ = _get_config()
    client = LinearClient(api_key)

    # Default path
    if file is None:
        file = Path.home() / "Documents" / "Work" / "Lyzr" / "kb" / "README.md"
        if not file.exists():
            console.print(f"[red]Default file not found:[/red] {file}")
            raise typer.Exit(1)

    content = file.read_text()

    console.print(f"[bold]Updating initiative from:[/bold] {file}")
    try:
        if client.update_initiative(LINEAR_INITIATIVE_ID, content):
            console.print("[green]✓[/green] Initiative updated")
        else:
            console.print("[red]✗[/red] Failed to update initiative")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
