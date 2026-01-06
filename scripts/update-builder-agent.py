#!/usr/bin/env python3
"""Update the Blueprint Builder agent to use JSON output mode with memory."""

import os
from pathlib import Path
import httpx
import yaml

# Configuration
AGENT_ID = "695aad9ba45696ac999e18cf"
API_KEY = os.environ.get("LYZR_API_KEY", "sk-default-8YV7PJp8NNBoZpVfOz8jg6GN0dPkaIEn")
BASE_URL = "https://agent-prod.studio.lyzr.ai"

# Path to the YAML definition
YAML_PATH = Path(__file__).parent.parent.parent / "blueprints" / "local" / "agents" / "builder-manager.yaml"

# Memory configuration: SHORT_TERM_MEMORY with 20 messages
SHORT_TERM_MEMORY_CONFIG = {
    "type": "SHORT_TERM_MEMORY",
    "config": {"message_count": 20},
    "priority": 0
}

def load_system_prompt_from_yaml() -> str:
    """Load the system prompt from the YAML definition file."""
    if not YAML_PATH.exists():
        raise FileNotFoundError(f"YAML file not found: {YAML_PATH}")

    with open(YAML_PATH) as f:
        data = yaml.safe_load(f)

    instructions = data.get("spec", {}).get("instructions", "")
    if not instructions:
        raise ValueError("No instructions found in YAML file")

    return instructions


def get_current_agent():
    """Get current agent configuration."""
    response = httpx.get(
        f"{BASE_URL}/v3/agents/{AGENT_ID}",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def update_agent(payload):
    """Update agent configuration."""
    response = httpx.put(
        f"{BASE_URL}/v3/agents/{AGENT_ID}",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def ensure_short_term_memory(features: list) -> list:
    """Ensure SHORT_TERM_MEMORY is in features list, replacing any existing memory config."""
    # Remove any existing memory-related features
    features = [f for f in features if f.get("type") not in ("memory", "SHORT_TERM_MEMORY", "STRUCTURED_MEMORY")]

    # Add SHORT_TERM_MEMORY
    features.append(SHORT_TERM_MEMORY_CONFIG)

    return features


def main():
    print("=" * 60)
    print("Updating Blueprint Builder Agent")
    print("  - JSON Output Mode")
    print("  - SHORT_TERM_MEMORY (20 messages)")
    print("=" * 60)

    # Load system prompt from YAML
    print(f"\n1. Loading system prompt from YAML...")
    print(f"   Path: {YAML_PATH}")
    system_prompt = load_system_prompt_from_yaml()
    print(f"   Loaded {len(system_prompt)} characters")

    # Get current config
    print("\n2. Fetching current agent configuration...")
    current = get_current_agent()
    print(f"   Agent: {current['name']}")
    print(f"   Current response_format: {current.get('response_format')}")
    print(f"   Current features: {[f.get('type') for f in current.get('features', [])]}")

    # Prepare update payload
    # Remove read-only fields
    readonly_fields = ['_id', 'created_at', 'updated_at', 'api_key', 'version']
    payload = {k: v for k, v in current.items() if k not in readonly_fields}

    # Update with JSON output mode
    payload['response_format'] = {"type": "json_object"}

    # Update system prompt
    payload['agent_instructions'] = system_prompt

    # Update features with SHORT_TERM_MEMORY
    payload['features'] = ensure_short_term_memory(payload.get('features', []))

    print("\n3. Updating agent...")
    print(f"   response_format: {payload['response_format']}")
    print(f"   features: {[f.get('type') for f in payload['features']]}")

    # Update
    result = update_agent(payload)
    print("\n4. Update successful!")
    print(f"   Updated at: {result.get('updated_at', 'N/A')}")

    # Verify
    print("\n5. Verifying update...")
    updated = get_current_agent()
    print(f"   response_format: {updated.get('response_format')}")
    print(f"   features: {[f.get('type') for f in updated.get('features', [])]}")

    success = True

    if updated.get('response_format', {}).get('type') != 'json_object':
        print("\n❌ WARNING: response_format may not have updated correctly")
        success = False

    has_short_term_memory = any(
        f.get('type') == 'SHORT_TERM_MEMORY'
        for f in updated.get('features', [])
    )
    if not has_short_term_memory:
        print("\n❌ WARNING: SHORT_TERM_MEMORY feature may not have been added")
        success = False

    if success:
        print("\n✅ SUCCESS: Agent updated with JSON output mode and SHORT_TERM_MEMORY!")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
