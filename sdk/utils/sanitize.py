"""Sanitization Utilities

Functions to sanitize agent and blueprint data before API calls.
Handles the NoneType iterable fields that cause clone errors.
"""

# Fields that MUST be arrays, never None
# Setting these to None breaks clone operations with "NoneType is not iterable"
ITERABLE_FIELDS = [
    # Agent API fields
    "managed_agents",  # List of managed worker agents
    "a2a_tools",  # Agent-to-agent tools
    "tool_configs",  # Tool configurations
    "features",  # Enabled features (memory, KB, etc.)
    # NOTE: "examples" is a STRING field, not array! Do not include here.
    "tools",  # Simple tool list
    "files",  # Attached files
    "artifacts",  # Generated artifacts
    "personas",  # Agent personas
    "messages",  # Message history
    # Blueprint API fields
    "tags",  # Catalog tags
    "shared_with_users",  # User IDs for sharing
    "shared_with_organizations",  # Org IDs for sharing
    # Blueprint permission/sharing fields (PAGOS iterates these)
    "user_ids",  # User IDs with access
    "organization_ids",  # Org IDs with access
    "permissions",  # Permission entries
    "assets",  # Associated assets
]

# Fields that should be strings (or None), not arrays
STRING_FIELDS = [
    "examples",  # Few-shot examples as multiline string
    "agent_role",
    "agent_goal",
    "agent_context",
    "agent_output",
    "tool_usage_description",
]

# Blueprint-level iterable fields (at root of blueprint, not in agents)
BLUEPRINT_ITERABLE_FIELDS = [
    "tags",
    "shared_with_users",
    "shared_with_organizations",
    "user_ids",
    "organization_ids",
    "permissions",
    "assets",
]


def sanitize_agent_data(data: dict) -> dict:
    """Sanitize agent data by converting None iterables to empty lists.

    This is CRITICAL for preventing clone errors. The Agent API sometimes
    returns None for iterable fields, but the clone operation iterates
    over them causing "NoneType is not iterable" errors.

    Also ensures string fields remain strings (not arrays).

    Args:
        data: Raw agent data from API

    Returns:
        Sanitized agent data with all iterable fields as lists
    """
    if not data:
        return data

    result = data.copy()

    # Ensure iterable fields are lists
    for field in ITERABLE_FIELDS:
        if field not in result or result[field] is None:
            result[field] = []

    # Ensure string fields remain strings (not arrays)
    for field in STRING_FIELDS:
        if field in result:
            val = result[field]
            # Convert empty arrays to empty string
            if isinstance(val, list):
                result[field] = ""
            # Keep None as-is or convert to empty string
            elif val is None:
                result[field] = ""

    return result


def sanitize_node_data(data: dict) -> dict:
    """Sanitize node data (both agent and non-agent nodes).

    Non-agent nodes (tool nodes, etc.) may also have iterable fields
    that PAGOS iterates over during serialization.

    Args:
        data: Node data dict

    Returns:
        Sanitized node data
    """
    if not data:
        return data

    result = data.copy()

    # Sanitize all known iterable fields in node data
    for field in ITERABLE_FIELDS:
        if field in result and result[field] is None:
            result[field] = []

    return result


def sanitize_blueprint_data(data: dict) -> dict:
    """Sanitize blueprint data, including nested agents.

    Args:
        data: Raw blueprint data from API

    Returns:
        Sanitized blueprint data
    """
    if not data:
        return data

    result = data.copy()

    # Sanitize ALL root-level iterable fields (not just 3)
    for field in BLUEPRINT_ITERABLE_FIELDS:
        if field not in result or result[field] is None:
            result[field] = []

    # Sanitize blueprint_data if present
    if "blueprint_data" in result and result["blueprint_data"]:
        bp_data = result["blueprint_data"].copy()

        # Sanitize agents dict
        if "agents" in bp_data and bp_data["agents"]:
            bp_data["agents"] = {
                agent_id: sanitize_agent_data(agent_data)
                for agent_id, agent_data in bp_data["agents"].items()
            }

        # Sanitize ALL nodes (both agent and non-agent types)
        # Non-agent nodes (tool nodes) may have iterable fields too
        if "nodes" in bp_data and bp_data["nodes"]:
            bp_data["nodes"] = [
                {
                    **node,
                    "data": sanitize_node_data(node.get("data", {})),
                }
                for node in bp_data["nodes"]
            ]

        # Sync tree_structure with sanitized nodes
        if "tree_structure" in bp_data:
            bp_data["tree_structure"] = {
                "nodes": bp_data.get("nodes", []),
                "edges": bp_data.get("edges", []),
            }

        result["blueprint_data"] = bp_data

    return result


def sanitize_for_update(current: dict, updates: dict) -> dict:
    """Merge updates into current data while preserving critical fields.

    IMPORTANT: This preserves `managed_agents` which only exists in API
    responses and must not be lost during updates.

    Args:
        current: Current agent data from API
        updates: Fields to update

    Returns:
        Merged data ready for PUT request
    """
    result = sanitize_agent_data(current)

    # Apply updates
    for key, value in updates.items():
        if value is not None:
            result[key] = value

    # Ensure managed_agents is preserved (critical!)
    if "managed_agents" not in result or result["managed_agents"] is None:
        result["managed_agents"] = current.get("managed_agents", []) or []

    return result
