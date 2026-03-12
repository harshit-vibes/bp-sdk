"""Recreate deleted agents from blueprint embedded data.

This script:
1. Identifies blueprints with deleted agents
2. Recreates agents from embedded data
3. Updates blueprints with new agent IDs
4. Syncs blueprints to rebuild tree structure
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import requests

from sdk import BlueprintClient
from sdk.builders import TreeBuilder
from sdk.utils.sanitize import sanitize_agent_data

# Configuration
AGENT_API_URL = "https://agent-prod.studio.lyzr.ai"
API_KEY = os.getenv("LYZR_API_KEY")
BEARER_TOKEN = os.getenv("BLUEPRINT_BEARER_TOKEN")
ORG_ID = os.getenv("LYZR_ORG_ID")


def get_existing_agent_ids() -> set[str]:
    """Get all agent IDs that currently exist."""
    r = requests.get(
        f"{AGENT_API_URL}/v3/agents/",
        headers={"X-API-Key": API_KEY},
    )
    r.raise_for_status()
    return {a.get("_id") for a in r.json()}


def create_agent(agent_data: dict) -> str:
    """Create an agent and return its new ID."""
    # Prepare payload - remove fields that shouldn't be sent
    payload = sanitize_agent_data(agent_data.copy())

    # Remove read-only and system fields
    fields_to_remove = [
        "_id", "agent_id", "api_key", "created_at", "updated_at",
        "is_active", "sessions", "artifacts", "messages",
        "a2a_tools",  # Will be rebuilt from managed_agents
    ]
    for field in fields_to_remove:
        payload.pop(field, None)

    # Ensure required fields
    if not payload.get("llm_credential_id"):
        # Map provider to credential
        provider = payload.get("provider_id", "OpenAI")
        credential_map = {
            "OpenAI": "lyzr_openai",
            "Anthropic": "lyzr_anthropic",
            "Google": "lyzr_google",
            "Groq": "lyzr_groq",
        }
        payload["llm_credential_id"] = credential_map.get(provider, "lyzr_openai")

    # Ensure top_p and temperature are set (required by API)
    if payload.get("top_p") is None:
        payload["top_p"] = 0.9
    if payload.get("temperature") is None:
        payload["temperature"] = 0.7

    # Clear managed_agents for now - will be set after workers are created
    original_managed = payload.pop("managed_agents", [])

    # NOTE: Endpoint requires trailing slash
    r = requests.post(
        f"{AGENT_API_URL}/v3/agents/",
        headers={"X-API-Key": API_KEY},
        json=payload,
    )

    if r.status_code != 200:
        print(f"    Error creating agent: {r.status_code} - {r.text[:200]}")
        raise Exception(f"Failed to create agent: {r.text}")

    result = r.json()
    return result.get("agent_id") or result.get("_id")


def update_agent_managed_agents(agent_id: str, managed_agents: list[dict]) -> None:
    """Update an agent's managed_agents list."""
    # First get current agent data
    r = requests.get(
        f"{AGENT_API_URL}/v3/agents/{agent_id}",
        headers={"X-API-Key": API_KEY},
    )
    r.raise_for_status()

    current = r.json()
    payload = sanitize_agent_data(current.copy())

    # Remove read-only fields
    for field in ["_id", "agent_id", "api_key", "created_at", "updated_at"]:
        payload.pop(field, None)

    # Set managed_agents
    payload["managed_agents"] = managed_agents

    r = requests.put(
        f"{AGENT_API_URL}/v3/agents/{agent_id}",
        headers={"X-API-Key": API_KEY},
        json=payload,
    )

    if r.status_code != 200:
        print(f"    Error updating managed_agents: {r.status_code} - {r.text[:200]}")


def recreate_blueprint_agents(bp_data: dict, blueprint_id: str, blueprint_name: str) -> dict:
    """Recreate all deleted agents for a blueprint.

    Returns:
        Dict mapping old_agent_id -> new_agent_id
    """
    existing_ids = get_existing_agent_ids()
    agents = bp_data.get("agents", {})
    manager_id = bp_data.get("manager_agent_id")

    id_mapping = {}  # old_id -> new_id

    # Separate manager and workers
    manager_data = agents.get(manager_id)
    worker_data = {k: v for k, v in agents.items() if k != manager_id}

    # 1. Create workers first
    print(f"  Creating {len(worker_data)} workers...")
    for old_worker_id, worker in worker_data.items():
        if old_worker_id in existing_ids:
            print(f"    {worker.get('name')}: already exists")
            id_mapping[old_worker_id] = old_worker_id
        else:
            try:
                new_id = create_agent(worker)
                id_mapping[old_worker_id] = new_id
                print(f"    {worker.get('name')}: created -> {new_id}")
            except Exception as e:
                print(f"    {worker.get('name')}: FAILED - {e}")
                raise

    # 2. Create manager
    print(f"  Creating manager...")
    if manager_id in existing_ids:
        print(f"    {manager_data.get('name')}: already exists")
        id_mapping[manager_id] = manager_id
    else:
        try:
            new_manager_id = create_agent(manager_data)
            id_mapping[manager_id] = new_manager_id
            print(f"    {manager_data.get('name')}: created -> {new_manager_id}")
        except Exception as e:
            print(f"    {manager_data.get('name')}: FAILED - {e}")
            raise

    # 3. Link workers to manager via managed_agents
    print(f"  Linking workers to manager...")
    new_manager_id = id_mapping[manager_id]
    managed_agents = []

    for old_worker_id, worker in worker_data.items():
        new_worker_id = id_mapping[old_worker_id]
        managed_agents.append({
            "id": new_worker_id,
            "name": worker.get("name"),
            "description": worker.get("tool_usage_description") or worker.get("description"),
        })

    update_agent_managed_agents(new_manager_id, managed_agents)
    print(f"    Linked {len(managed_agents)} workers")

    return id_mapping


def update_blueprint_with_new_ids(
    client: BlueprintClient,
    blueprint_id: str,
    id_mapping: dict,
) -> None:
    """Update blueprint with new agent IDs and rebuild tree."""

    # Get current blueprint
    bp = client._blueprint_api.get(blueprint_id)
    bp_data = bp.get("blueprint_data", {})
    old_manager_id = bp_data.get("manager_agent_id")
    new_manager_id = id_mapping.get(old_manager_id, old_manager_id)

    # Get fresh agent data from API
    fresh_agents = {}

    # Fetch new manager
    manager_data = sanitize_agent_data(client._agent_api.get(new_manager_id))
    fresh_agents[new_manager_id] = manager_data

    # Fetch new workers
    worker_ids = []
    for ma in manager_data.get("managed_agents", []):
        wid = ma.get("id")
        if wid:
            fresh_agents[wid] = sanitize_agent_data(client._agent_api.get(wid))
            worker_ids.append(wid)

    # Build fresh tree
    workers_data = [fresh_agents[wid] for wid in worker_ids]
    tree_builder = TreeBuilder()
    tree_data = tree_builder.build(
        manager_data=manager_data,
        workers_data=workers_data,
        manager_id=new_manager_id,
        worker_ids=worker_ids,
    )

    # Update blueprint
    update_payload = {
        "blueprint_data": {
            **bp_data,
            "manager_agent_id": new_manager_id,
            "agents": tree_data["agents"],
            "nodes": tree_data["nodes"],
            "edges": tree_data["edges"],
            "tree_structure": tree_data["tree_structure"],
        }
    }

    client._blueprint_api.update(blueprint_id, update_payload)


def find_affected_blueprints() -> list[dict]:
    """Find all blueprints with deleted agents."""
    existing_ids = get_existing_agent_ids()
    blueprint_dir = Path(__file__).parent.parent / "blueprints" / "studio"
    affected = []

    for json_file in blueprint_dir.rglob("*.json"):
        with open(json_file) as f:
            try:
                bp = json.load(f)
            except:
                continue

        bp_data = bp.get("blueprint_data", {})
        agents = bp_data.get("agents", {})

        if not agents:
            continue

        deleted = [aid for aid in agents.keys() if aid not in existing_ids]

        if deleted:
            affected.append({
                "id": bp.get("_id"),
                "name": bp.get("name"),
                "file": str(json_file),
                "bp_data": bp_data,
                "deleted_count": len(deleted),
                "total_agents": len(agents),
            })

    return sorted(affected, key=lambda x: x["deleted_count"], reverse=True)


def main():
    print("=" * 60)
    print("RECREATE DELETED AGENTS")
    print("=" * 60)

    # Initialize client
    client = BlueprintClient(
        agent_api_key=API_KEY,
        blueprint_bearer_token=BEARER_TOKEN,
        organization_id=ORG_ID,
    )

    # Find affected blueprints
    print("\nFinding affected blueprints...")
    affected = find_affected_blueprints()
    print(f"Found {len(affected)} blueprints with deleted agents")
    print()

    # Process each blueprint
    success = 0
    failed = 0

    for i, bp_info in enumerate(affected, 1):
        print(f"[{i}/{len(affected)}] {bp_info['name']}")
        print(f"  ID: {bp_info['id']}")
        print(f"  Deleted agents: {bp_info['deleted_count']}/{bp_info['total_agents']}")

        try:
            # Recreate agents
            id_mapping = recreate_blueprint_agents(
                bp_info["bp_data"],
                bp_info["id"],
                bp_info["name"],
            )

            # Update blueprint
            print(f"  Updating blueprint...")
            update_blueprint_with_new_ids(client, bp_info["id"], id_mapping)
            print(f"  Done!")
            success += 1

        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

        print()

    print("=" * 60)
    print(f"COMPLETE: {success} succeeded, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
