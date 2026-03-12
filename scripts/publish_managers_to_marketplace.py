"""Publish manager agents to marketplace.

This script:
1. Reads local blueprint JSON files
2. Gets manager agent info from each blueprint
3. Publishes manager to marketplace
4. Returns marketplace URLs for the report
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from sdk.api.marketplace import MarketplaceAPI

# Configuration
BEARER_TOKEN = os.getenv("BLUEPRINT_BEARER_TOKEN")
USER_ID = os.getenv("LYZR_USER_ID")

# Initialize marketplace API
marketplace = MarketplaceAPI(
    bearer_token=BEARER_TOKEN,
    user_id=USER_ID,
)


def get_owned_blueprints() -> list[dict]:
    """Get all owned (public-owned) blueprints with their manager info."""
    blueprint_dir = Path(__file__).parent.parent / "blueprints" / "studio" / "public-owned"
    blueprints = []

    for json_file in sorted(blueprint_dir.glob("*.json")):
        with open(json_file) as f:
            try:
                bp = json.load(f)
            except json.JSONDecodeError:
                continue

        bp_data = bp.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id")
        agents = bp_data.get("agents", {})
        manager = agents.get(manager_id, {})

        blueprints.append({
            "id": bp.get("_id"),
            "name": bp.get("name"),
            "description": bp.get("description", ""),
            "category": bp.get("category", ""),
            "tags": bp.get("tags", []),
            "file": str(json_file),
            "manager_id": manager_id,
            "manager_name": manager.get("name", bp.get("name")),
            "manager_description": manager.get("description", bp.get("description", "")),
        })

    return blueprints


def check_existing_apps() -> dict[str, str]:
    """Check which agents are already published and return agent_id -> app_id mapping."""
    try:
        apps = marketplace.list_by_user()
        return {app.get("agent_id"): app.get("id") for app in apps if app.get("agent_id")}
    except Exception as e:
        print(f"Warning: Could not fetch existing apps: {e}")
        return {}


def publish_manager(bp: dict, existing_apps: dict) -> dict | None:
    """Publish a manager agent to marketplace.

    Returns app data if published, None if already exists.
    """
    manager_id = bp["manager_id"]

    # Check if already published
    if manager_id in existing_apps:
        app_id = existing_apps[manager_id]
        return {
            "app_id": app_id,
            "agent_id": manager_id,
            "status": "existing",
        }

    # Determine category/function tag from blueprint
    category = bp.get("category", "")
    function_tag = None
    if category:
        function_tag = category.title()  # e.g., "people" -> "People"

    try:
        app = marketplace.create(
            name=bp["manager_name"],
            agent_id=manager_id,
            description=bp["manager_description"],
            creator="Lyzr",  # Or use current user
            public=True,
            function=function_tag,
        )
        return {
            "app_id": app.get("id"),
            "agent_id": manager_id,
            "status": "created",
        }
    except Exception as e:
        return {
            "app_id": None,
            "agent_id": manager_id,
            "status": "error",
            "error": str(e),
        }


def main():
    print("=" * 60)
    print("PUBLISH MANAGER AGENTS TO MARKETPLACE")
    print("=" * 60)

    # Get blueprints
    blueprints = get_owned_blueprints()
    print(f"\nFound {len(blueprints)} owned blueprints")

    # Check existing apps
    print("\nChecking existing marketplace apps...")
    existing_apps = check_existing_apps()
    print(f"Found {len(existing_apps)} existing apps")

    # Publish each manager
    results = []
    created = 0
    existing = 0
    errors = 0

    for i, bp in enumerate(blueprints, 1):
        print(f"\n[{i}/{len(blueprints)}] {bp['name']}")
        print(f"  Manager ID: {bp['manager_id']}")

        result = publish_manager(bp, existing_apps)
        result["blueprint_id"] = bp["id"]
        result["blueprint_name"] = bp["name"]
        results.append(result)

        if result["status"] == "created":
            print(f"  ✓ Published -> app_id: {result['app_id']}")
            created += 1
        elif result["status"] == "existing":
            print(f"  • Already exists -> app_id: {result['app_id']}")
            existing += 1
        else:
            print(f"  ✗ Error: {result.get('error', 'Unknown')}")
            errors += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: {created} created, {existing} existing, {errors} errors")
    print("=" * 60)

    # Generate report
    print("\n\nMARKETPLACE URLS:")
    print("-" * 60)

    for r in results:
        if r.get("app_id"):
            marketplace_url = f"https://studio.lyzr.ai/agent/{r['app_id']}"
            blueprint_url = f"https://studio.lyzr.ai/lyzr-manager?blueprint={r['blueprint_id']}"
            print(f"\n{r['blueprint_name']}")
            print(f"  Blueprint: {blueprint_url}")
            print(f"  Marketplace: {marketplace_url}")
        else:
            print(f"\n{r['blueprint_name']}")
            print(f"  Error: {r.get('error', 'Failed to publish')}")

    return results


if __name__ == "__main__":
    main()
