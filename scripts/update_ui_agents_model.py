#!/usr/bin/env python3
"""Update UI enhancement agents to use the fastest LLM (Groq)."""

import os
import httpx

# Configuration
AGENT_API_URL = "https://agent-prod.studio.lyzr.ai"
API_KEY = os.environ.get("LYZR_API_KEY")

if not API_KEY:
    print("Error: LYZR_API_KEY environment variable required")
    exit(1)

# Agent IDs to update
AGENT_IDS = [
    ("695d568328a3f341188df4da", "Witty Loader Agent"),
    ("695d568428a3f341188df4db", "Revision Suggest Agent"),
    ("695d568552ab53b7bf377073", "Statement Options Agent"),
]

# Fast model configuration - Groq Llama 3.1 8B Instant
FAST_MODEL_CONFIG = {
    "model": "groq/llama-3.1-8b-instant",
    "provider_id": "Groq",
    "llm_credential_id": "lyzr_groq",
}

# Fields to remove before PUT (read-only fields)
REMOVE_FIELDS = ["_id", "created_at", "updated_at", "api_key", "organization_id"]


def update_agent_model(agent_id: str, agent_name: str) -> bool:
    """Update agent to use fast model."""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30.0) as client:
        # 1. Fetch current agent data
        response = client.get(
            f"{AGENT_API_URL}/v3/agents/{agent_id}",
            headers=headers,
        )
        response.raise_for_status()
        agent_data = response.json()

        print(f"  Current model: {agent_data.get('model')}")

        # 2. Update model configuration
        agent_data.update(FAST_MODEL_CONFIG)

        # 3. Remove read-only fields
        for field in REMOVE_FIELDS:
            agent_data.pop(field, None)

        # 4. Ensure array fields are not None
        array_fields = [
            "managed_agents", "tool_configs", "features", "tools",
            "files", "artifacts", "personas", "messages", "a2a_tools"
        ]
        for field in array_fields:
            if agent_data.get(field) is None:
                agent_data[field] = []

        # 5. PUT updated agent
        response = client.put(
            f"{AGENT_API_URL}/v3/agents/{agent_id}",
            headers=headers,
            json=agent_data,
        )
        response.raise_for_status()

        print(f"  New model: {FAST_MODEL_CONFIG['model']}")
        return True


def main():
    """Update all UI agents to use fast model."""
    print("Updating UI Agents to Fast Model (Groq)")
    print("=" * 50)
    print(f"Target: {FAST_MODEL_CONFIG['model']}")
    print("=" * 50)

    for agent_id, agent_name in AGENT_IDS:
        print(f"\nUpdating {agent_name}...")
        try:
            update_agent_model(agent_id, agent_name)
            print(f"  Status: SUCCESS")
        except Exception as e:
            print(f"  Status: FAILED - {e}")

    print("\n" + "=" * 50)
    print("Update Complete!")


if __name__ == "__main__":
    main()
