#!/usr/bin/env python3
"""Deploy or update meta-agents (Architect, Crafter) to Agent API.

These are standalone agents used by the Blueprint Builder API to create blueprints.
They are NOT part of a blueprint themselves.

Usage:
    python scripts/deploy_meta_agents.py          # Deploy/update agents
    python scripts/deploy_meta_agents.py --force  # Force create new (ignore existing IDs)

Environment variables:
    LYZR_API_KEY: Agent API key
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sdk.api.agent import AgentAPI
from sdk.builders.payload import get_provider_info
from sdk.utils.sanitize import sanitize_agent_data


def load_agent_yaml(yaml_path: Path) -> dict:
    """Load and parse agent YAML file."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def build_standalone_agent_payload(agent_data: dict) -> dict:
    """Build Agent API payload from YAML data.

    This is for standalone agents (not part of a blueprint).
    """
    metadata = agent_data.get("metadata", {})
    spec = agent_data.get("spec", {})

    model = spec.get("model", "gpt-4o")
    provider, credential_id = get_provider_info(model)

    # Build features
    features = []
    for i, feature_name in enumerate(spec.get("features", [])):
        if feature_name == "memory":
            features.append({
                "type": "MEMORY",
                "config": {
                    "provider": "lyzr",
                    "max_messages_context_count": 10,
                },
                "priority": i,
            })

    payload = {
        "name": metadata.get("name", "Unnamed Agent"),
        "description": metadata.get("description", ""),
        "agent_instructions": spec.get("instructions", ""),
        "provider_id": provider,
        "model": model,
        "llm_credential_id": credential_id,
        "temperature": spec.get("temperature", 0.7),
        "top_p": 1.0,
        "store_messages": False,
        "file_output": False,
        "template_type": "STANDARD",
        "features": features,
        "tool_configs": [],
        "managed_agents": [],
        "a2a_tools": [],
        "examples": None,
        "tools": [],
        "files": [],
        "artifacts": [],
        "personas": [],
        "messages": [],
    }

    # Add optional fields
    if spec.get("role"):
        payload["agent_role"] = spec["role"]
    if spec.get("goal"):
        payload["agent_goal"] = spec["goal"]

    # Handle response_format
    response_format = spec.get("response_format", {})
    if isinstance(response_format, dict):
        payload["response_format"] = response_format
    else:
        payload["response_format"] = {"type": "text"}

    return payload


def get_existing_agent_id(name: str) -> str | None:
    """Get existing agent ID from config.py."""
    config_path = project_root / "api" / "config.py"
    if not config_path.exists():
        return None

    content = config_path.read_text()

    # Map agent names to config keys
    key_map = {
        "architect": "architect_agent_id",
        "crafter": "crafter_agent_id",
    }

    key = key_map.get(name)
    if not key:
        return None

    # Parse the config file for the agent ID
    # Format: architect_agent_id: str = "695dd9c452ab53b7bf377603"
    for line in content.split("\n"):
        if f"{key}:" in line and '"' in line:
            # Extract ID between quotes
            start = line.find('"') + 1
            end = line.find('"', start)
            if end > start:
                return line[start:end]

    return None


def main():
    # Check for --force flag
    force_create = "--force" in sys.argv

    # Get API key
    api_key = os.getenv("LYZR_API_KEY")
    if not api_key:
        print("ERROR: LYZR_API_KEY environment variable not set")
        sys.exit(1)

    # Agent YAML files to deploy
    agents_dir = project_root / "blueprints" / "local" / "agents"

    agents_to_deploy = [
        ("architect", agents_dir / "architect.yaml"),
        ("crafter", agents_dir / "crafter.yaml"),
    ]

    # Create Agent API client
    agent_api = AgentAPI(api_key=api_key)

    print("Deploying meta-agents to Agent API...")
    if force_create:
        print("(--force: Creating new agents, ignoring existing IDs)")
    print("-" * 50)

    deployed_ids = {}
    updated_ids = {}

    for name, yaml_path in agents_to_deploy:
        if not yaml_path.exists():
            print(f"ERROR: {yaml_path} not found")
            continue

        print(f"\nProcessing {name}...")

        # Load and convert YAML
        agent_data = load_agent_yaml(yaml_path)
        payload = build_standalone_agent_payload(agent_data)

        # Check for existing agent ID
        existing_id = None if force_create else get_existing_agent_id(name)

        if existing_id:
            # UPDATE existing agent
            print(f"  Found existing ID: {existing_id}")
            print(f"  Updating agent...")

            try:
                # Fetch current agent data first
                current_data = agent_api.get(existing_id)

                # Sanitize and merge with new payload
                # Keep system fields, update our fields
                update_payload = sanitize_agent_data(current_data)

                # Update fields from YAML
                for key in ["name", "description", "agent_instructions", "agent_role",
                           "agent_goal", "model", "provider_id", "llm_credential_id",
                           "temperature", "response_format", "features"]:
                    if key in payload:
                        update_payload[key] = payload[key]

                # Remove read-only fields
                for field in ["_id", "created_at", "updated_at", "api_key"]:
                    update_payload.pop(field, None)

                # Update the agent
                agent_api.update(existing_id, update_payload)
                updated_ids[name] = existing_id
                print(f"  ✓ Updated: {existing_id}")

            except Exception as e:
                print(f"  ✗ Update failed: {e}")
                print(f"  Falling back to create...")
                # Fall through to create
                existing_id = None

        if not existing_id:
            # CREATE new agent
            print(f"  Creating new agent...")

            try:
                result = agent_api.create(payload)
                agent_id = result.get("_id") or result.get("agent_id")

                if agent_id:
                    deployed_ids[name] = agent_id
                    print(f"  ✓ Created: {agent_id}")
                else:
                    print(f"  ✗ Failed: No agent ID in response")
                    print(f"    Response: {result}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

    print("\n" + "=" * 50)
    print("DEPLOYMENT COMPLETE")
    print("=" * 50)

    if updated_ids:
        print("\n✓ UPDATED (existing agents):")
        for name, agent_id in updated_ids.items():
            print(f"  {name}: {agent_id}")

    if deployed_ids:
        print("\n⚠ CREATED (new agents - update config!):")
        for name, agent_id in deployed_ids.items():
            print(f"  {name}: {agent_id}")

        print("\nAdd these to your .env file:")
        print()
        for name, agent_id in deployed_ids.items():
            env_var = f"{name.upper()}_AGENT_ID"
            print(f"{env_var}={agent_id}")

        print("\nOr update api/config.py:")
        print()
        for name, agent_id in deployed_ids.items():
            print(f'{name}_agent_id: str = "{agent_id}"')

    if not updated_ids and not deployed_ids:
        print("\nNo agents were deployed or updated successfully.")


if __name__ == "__main__":
    main()
