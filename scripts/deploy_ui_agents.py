#!/usr/bin/env python3
"""Deploy UI enhancement agents (loader, suggest, options) to Lyzr Agent API."""

import os
import yaml
import httpx
from pathlib import Path

# Configuration
AGENT_API_URL = "https://agent-prod.studio.lyzr.ai"
API_KEY = os.environ.get("LYZR_API_KEY")
ORG_ID = os.environ.get("LYZR_ORG_ID")

if not API_KEY or not ORG_ID:
    print("Error: LYZR_API_KEY and LYZR_ORG_ID environment variables required")
    exit(1)

# Agent YAML files
AGENTS_DIR = Path(__file__).parent.parent / "blueprints" / "local" / "agents"
AGENT_FILES = [
    ("ui-loader-agent.yaml", "loader_agent_id"),
    ("ui-suggest-agent.yaml", "suggest_agent_id"),
    ("ui-options-agent.yaml", "options_agent_id"),
]


def load_agent_yaml(filepath: Path) -> dict:
    """Load and parse agent YAML file."""
    with open(filepath) as f:
        data = yaml.safe_load(f)

    metadata = data.get("metadata", {})
    spec = data.get("spec", {})

    return {
        "name": metadata.get("name"),
        "description": metadata.get("description"),
        "agent_role": spec.get("role"),
        "agent_goal": spec.get("goal"),
        "agent_instructions": spec.get("instructions"),
        "model": spec.get("model", "gpt-4o-mini"),
        "temperature": spec.get("temperature", 0.7),
    }


def create_agent(agent_data: dict) -> str:
    """Create agent via API and return agent ID."""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "name": agent_data["name"],
        "description": agent_data["description"],
        "agent_role": agent_data["agent_role"],
        "agent_goal": agent_data["agent_goal"],
        "agent_instructions": agent_data["agent_instructions"],
        "model": agent_data["model"],
        "temperature": agent_data["temperature"],
        "organization_id": ORG_ID,
        # Standard defaults
        "provider_id": "OpenAI",
        "llm_credential_id": "lyzr_openai",
        "top_p": 0.9,
        "max_tokens": 4096,
        "features": [],
        "tools": [],
        "tool_configs": [],
        "managed_agents": [],
    }

    with httpx.Client(timeout=30.0) as client:
        # Use template/single-task endpoint for agent creation
        response = client.post(
            f"{AGENT_API_URL}/v3/agents/template/single-task",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("agent_id") or data.get("_id")


def main():
    """Deploy all UI agents and print their IDs."""
    print("Deploying UI Enhancement Agents")
    print("=" * 50)

    results = {}

    for filename, config_key in AGENT_FILES:
        filepath = AGENTS_DIR / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found, skipping")
            continue

        print(f"\nDeploying {filename}...")
        agent_data = load_agent_yaml(filepath)
        print(f"  Name: {agent_data['name']}")

        try:
            agent_id = create_agent(agent_data)
            results[config_key] = agent_id
            print(f"  Agent ID: {agent_id}")
            print(f"  Status: SUCCESS")
        except Exception as e:
            print(f"  Status: FAILED - {e}")

    print("\n" + "=" * 50)
    print("Deployment Complete!")
    print("\nAdd these to your .env file:")
    print("-" * 50)
    for key, value in results.items():
        env_key = key.upper()
        print(f"{env_key}={value}")

    print("\nOr update api/config.py defaults:")
    print("-" * 50)
    for key, value in results.items():
        print(f'{key}: str = "{value}"')


if __name__ == "__main__":
    main()
