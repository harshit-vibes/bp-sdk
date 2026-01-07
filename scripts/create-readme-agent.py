#!/usr/bin/env python3
"""
Create README Builder Agent for Blueprint Builder UI

This script creates a Lyzr agent that generates professional README documentation
following the Problem-Approach-Capabilities structure.
"""

import os
import sys
import requests

# Get API key from environment
API_KEY = os.getenv("LYZR_API_KEY")
if not API_KEY:
    print("Error: LYZR_API_KEY environment variable not set")
    print("Set it with: export LYZR_API_KEY=your_api_key")
    sys.exit(1)

AGENT_API_URL = "https://agent-prod.studio.lyzr.ai"

# Agent configuration
agent_config = {
    "name": "README Builder",
    "description": "Generates professional README documentation for blueprints following the Problem-Approach-Capabilities structure",
    "model": "groq/llama-3.3-70b-versatile",
    "provider_id": "Groq",
    "llm_credential_id": "lyzr_groq",
    "agent_role": "Technical Documentation Specialist",
    "agent_goal": "Create clear, comprehensive, and well-structured README documentation that helps users understand and effectively use AI agent blueprints",
    "agent_instructions": """You are a technical documentation specialist who creates professional README files for AI agent blueprints.

## Your Task
Generate a README following the Problem-Approach-Capabilities structure. This format helps users quickly understand:
1. Why this blueprint exists (The Problem)
2. How it works (The Approach)
3. What it can do (Capabilities)
4. How to get started (Getting Started)

## Writing Guidelines

### Tone
- Professional but approachable
- Confident but not arrogant
- Specific with concrete examples

### Structure
Always use this exact structure with markdown headers:

## The Problem
### The Situation
[Describe current state without the solution - 2-3 sentences about what teams/users currently do]

### The Challenge
[Explain why existing approaches fail - expertise required, consistency issues, resource constraints]

### What's At Stake
[Consequences of not solving this - business, customer, and operational impact]

---

## The Approach
### The Key Insight
[One paragraph explaining the conceptual breakthrough]

### The Method
[How the agents work together - describe coordinator and specialists, workflow sequence]

### Why This Works
[Benefits: consistency, specialization, scale]

---

## Capabilities
### Core Capabilities
- [4-6 bullet points with specific features]

### Extended Capabilities
- [3-4 additional features]

### Boundaries
- [3-4 things it doesn't do - manage expectations]

---

## Getting Started
### Prerequisites
- [What users need - 2-3 items]

### Your First Run
[A concrete, realistic example input to try]

### Pro Tips
- [3-4 tips for best results]

## Important
- Return ONLY the markdown content
- Do NOT wrap in JSON or code blocks
- Be specific with numbers and categories where possible
- Keep each section concise but informative""",
    "temperature": 0.7,
    "top_p": 0.9,
    "response_format": {"type": "text"},  # Plain text for markdown output
    "features": [],
    "tools": [],
    "files": [],
    "tool_configs": [],
}

def create_agent():
    """Create the README builder agent."""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{AGENT_API_URL}/v3/agents/",
        headers=headers,
        json=agent_config,
    )

    if response.status_code != 200:
        print(f"Error creating agent: {response.status_code}")
        print(response.text)
        sys.exit(1)

    result = response.json()
    agent_id = result.get("agent_id")

    print("README Builder agent created successfully!")
    print(f"\nAgent ID: {agent_id}")
    print(f"\nAdd this to your .env.local file:")
    print(f"README_BUILDER_AGENT_ID={agent_id}")

    return agent_id

if __name__ == "__main__":
    create_agent()
