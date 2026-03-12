"""Payload Builder

Builds API payloads for agent and blueprint creation/updates.
Handles provider mapping, feature configuration, and field placement.
"""

from typing import Any

from ..models import AgentConfig, BlueprintConfig

# Provider mapping: model -> (provider_name, credential_id)
# Last verified: 2024-12-29
PROVIDER_MAP = {
    # OpenAI models
    "gpt-4o": ("OpenAI", "lyzr_openai"),
    "gpt-4o-mini": ("OpenAI", "lyzr_openai"),
    "o3": ("OpenAI", "lyzr_openai"),
    "o3-mini": ("OpenAI", "lyzr_openai"),
    "o4-mini": ("OpenAI", "lyzr_openai"),
    "o1-preview": ("OpenAI", "lyzr_openai"),
    "o1-mini": ("OpenAI", "lyzr_openai"),
    # Anthropic models
    "claude-sonnet-4-0": ("Anthropic", "lyzr_anthropic"),
    "claude-opus-4-0": ("Anthropic", "lyzr_anthropic"),
    "claude-3-5-sonnet-latest": ("Anthropic", "lyzr_anthropic"),
    # Google models
    "gemini-2.0-flash": ("Google", "lyzr_google"),
    "gemini-2.0-flash-exp": ("Google", "lyzr_google"),
    "gemini-1.5-pro": ("Google", "lyzr_google"),
    "gemini-1.5-flash": ("Google", "lyzr_google"),
    # Groq models
    "llama-3.3-70b-versatile": ("Groq", "lyzr_groq"),
    "llama-3.1-8b-instant": ("Groq", "lyzr_groq"),
    "mixtral-8x7b-32768": ("Groq", "lyzr_groq"),
    # Perplexity models (online search)
    "sonar-pro": ("Perplexity", "lyzr_perplexity"),
    "sonar": ("Perplexity", "lyzr_perplexity"),
    "sonar-reasoning-pro": ("Perplexity", "lyzr_perplexity"),
    "sonar-reasoning": ("Perplexity", "lyzr_perplexity"),
    # DeepSeek models
    "deepseek-reasoner": ("DeepSeek", "lyzr_deepseek"),
}


def get_provider_info(model: str) -> tuple[str, str]:
    """Get provider name and credential ID for a model.

    Args:
        model: Model name (e.g., "gpt-4o", "claude-sonnet-4-0")

    Returns:
        Tuple of (provider_name, credential_id)
    """
    # Check exact match first
    if model in PROVIDER_MAP:
        return PROVIDER_MAP[model]

    # Check prefixed models (legacy support)
    if model.startswith("anthropic/"):
        return ("Anthropic", "lyzr_anthropic")
    elif model.startswith("gemini/"):
        return ("Google", "lyzr_google")
    elif model.startswith("groq/"):
        return ("Groq", "lyzr_groq")
    elif model.startswith("bedrock/"):
        return ("Aws-Bedrock", "lyzr_aws-bedrock")
    elif model.startswith("perplexity/"):
        return ("Perplexity", "lyzr_perplexity")
    elif model.startswith("deepseek/"):
        return ("DeepSeek", "lyzr_deepseek")

    # Default to OpenAI
    return ("OpenAI", "lyzr_openai")


def build_features(features: list[str]) -> list[dict]:
    """Build features list from feature names.

    Args:
        features: List of feature names (e.g., 'memory', 'voice')

    Returns:
        Features list for Agent API
    """
    result = []
    priority = 0

    for feature in features:
        if feature == "memory":
            result.append({
                "type": "MEMORY",
                "config": {
                    "provider": "lyzr",
                    "max_messages_context_count": 10,
                },
                "priority": priority,
            })
            priority += 1

        elif feature == "voice":
            result.append({
                "type": "VOICE",
                "config": {},
                "priority": priority,
            })
            priority += 1

        elif feature == "context":
            result.append({
                "type": "CONTEXT",
                "config": {
                    "context_id": "",
                    "context_name": "",
                },
                "priority": priority,
            })
            priority += 1

        elif feature == "file_output":
            result.append({
                "type": "FILEASOUTPUT",
                "config": {},
                "priority": priority,
            })
            priority += 1

        elif feature == "image_output":
            result.append({
                "type": "IMAGEASOUTPUT",
                "config": {
                    "provider": "openai",
                    "model": "dall-e-3",
                },
                "priority": priority,
            })
            priority += 1

        elif feature == "reflection":
            result.append({
                "type": "REFLECTION",
                "config": {},
                "priority": priority,
            })
            priority += 1

        elif feature == "groundedness":
            result.append({
                "type": "GROUNDEDNESS",
                "config": {
                    "provider": "lyzr",
                },
                "priority": priority,
            })
            priority += 1

        elif feature == "fairness":
            result.append({
                "type": "FAIRNESS",
                "config": {},
                "priority": priority,
            })
            priority += 1

        elif feature == "rai":
            result.append({
                "type": "RAI",
                "config": {
                    "policy_id": "",  # Will need policy_id when connected to actual policy
                },
                "priority": priority,
            })
            priority += 1

        elif feature == "llm_judge":
            result.append({
                "type": "UQLM_LLM_JUDGE",
                "config": {},
                "priority": priority,
            })
            priority += 1

    return result


class PayloadBuilder:
    """Builds API payloads for agents and blueprints."""

    def build_agent_payload(
        self,
        config: AgentConfig,
        is_manager: bool = False,
        managed_agents: list[dict] | None = None,
    ) -> dict:
        """Build Agent API payload from config.

        Args:
            config: Agent configuration
            is_manager: Whether this is the manager agent
            managed_agents: List of managed agent dicts for manager

        Returns:
            Payload dict for Agent API POST
        """
        provider, credential_id = get_provider_info(config.model)

        payload: dict[str, Any] = {
            "name": config.name,
            "description": config.description,
            "agent_instructions": config.instructions,
            "provider_id": provider,
            "model": config.model,
            "llm_credential_id": credential_id,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "response_format": {"type": config.response_format},
            "store_messages": config.store_messages,
            "file_output": config.file_output,
            "template_type": "MANAGER" if is_manager else "STANDARD",
            "features": build_features(config.features),
            "tool_configs": [],  # Always empty - tools removed from SDK
            # Required fields (prevent NoneType errors)
            "managed_agents": managed_agents or [],
            "a2a_tools": [],
            "examples": None,
            "tools": [],
            "files": [],
            "artifacts": [],
            "personas": [],
            "messages": [],
        }

        # Add optional persona fields (using correct API field names)
        if config.role:
            payload["agent_role"] = config.role
        if config.goal:
            payload["agent_goal"] = config.goal
        if config.context:
            payload["agent_context"] = config.context
        if config.output_format:
            payload["agent_output"] = config.output_format
        if config.examples:
            payload["examples"] = config.examples

        # Add usage_description for workers (correct API field name)
        if not is_manager and config.usage_description:
            payload["tool_usage_description"] = config.usage_description

        return payload

    def build_managed_agents_list(
        self,
        workers: list[AgentConfig],
        worker_ids: list[str],
    ) -> list[dict]:
        """Build managed_agents list for manager.

        Args:
            workers: Worker configurations
            worker_ids: Worker API IDs (in same order as workers)

        Returns:
            List of managed agent dicts
        """
        return [
            {
                "id": worker_id,
                "name": worker.name,
                "usage_description": worker.usage_description
                or f"Use {worker.name} for specialized tasks",
            }
            for worker, worker_id in zip(workers, worker_ids)
        ]

    def build_blueprint_payload(
        self,
        config: BlueprintConfig,
        tree_data: dict,
        manager_id: str,
    ) -> dict:
        """Build Blueprint API payload.

        IMPORTANT: Fields like category, tags, share_type go at ROOT level,
        NOT inside blueprint_data.

        Args:
            config: Blueprint configuration
            tree_data: Tree structure from TreeBuilder
            manager_id: Manager agent API ID

        Returns:
            Payload dict for Blueprint API POST
        """
        # Build blueprint_data (internal structure)
        blueprint_data = {
            "name": config.name,
            "orchestration_type": "Manager Agent",
            "manager_agent_id": manager_id,
            "agents": tree_data["agents"],
            "nodes": tree_data["nodes"],
            "edges": tree_data["edges"],
            "tree_structure": tree_data["tree_structure"],
        }

        # Build root payload
        # CRITICAL: category, tags, share_type, is_template, sharing lists must be at root level!
        payload = {
            "name": config.name,
            "description": config.description,
            "orchestration_type": "Manager Agent",
            "orchestration_name": config.name,
            "blueprint_data": blueprint_data,
            # Root-level fields (NOT in blueprint_data!)
            "share_type": config.visibility.value,
            "tags": config.tags,
            "is_template": config.is_template,
            "shared_with_users": config.shared_with_users,
            "shared_with_organizations": config.shared_with_organizations,
        }

        if config.category:
            payload["category"] = config.category

        # Add README documentation if provided
        if config.readme:
            payload["blueprint_info"] = {
                "documentation_data": {
                    "markdown": config.readme,
                },
                "type": "markdown",
            }

        return payload

    def build_update_payload(
        self,
        current_blueprint: dict,
        new_tree_data: dict,
        updates: dict | None = None,
    ) -> dict:
        """Build Blueprint API update payload.

        Args:
            current_blueprint: Current blueprint from API
            new_tree_data: Fresh tree structure
            updates: Optional field updates (name, description, readme, etc.)

        Returns:
            Payload dict for Blueprint API PUT
        """
        # Start with current data
        payload = {
            "name": current_blueprint.get("name"),
            "description": current_blueprint.get("description"),
            "orchestration_type": current_blueprint.get("orchestration_type", "Manager Agent"),
            "orchestration_name": current_blueprint.get("orchestration_name"),
            "share_type": current_blueprint.get("share_type", "private"),
            "category": current_blueprint.get("category"),
            "tags": current_blueprint.get("tags", []),
        }

        # Preserve existing blueprint_info
        current_bp_info = current_blueprint.get("blueprint_info", {})

        # Apply updates
        if updates:
            for key, value in updates.items():
                if value is not None and key in payload:
                    payload[key] = value

            # Handle readme update separately
            if "readme" in updates and updates["readme"] is not None:
                current_bp_info = {
                    "documentation_data": {
                        "markdown": updates["readme"],
                    },
                    "type": "markdown",
                }

        # Include blueprint_info if it has content
        if current_bp_info:
            payload["blueprint_info"] = current_bp_info

        # Update blueprint_data with fresh tree
        current_bp_data = current_blueprint.get("blueprint_data", {})
        payload["blueprint_data"] = {
            "name": payload["name"],
            "orchestration_type": payload["orchestration_type"],
            "manager_agent_id": current_bp_data.get("manager_agent_id"),
            "agents": new_tree_data["agents"],
            "nodes": new_tree_data["nodes"],
            "edges": new_tree_data["edges"],
            "tree_structure": new_tree_data["tree_structure"],
        }

        return payload
