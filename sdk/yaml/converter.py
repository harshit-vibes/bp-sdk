"""YAML ↔ SDK Model Conversion.

Provides bidirectional conversion between YAML format and SDK models.
"""

from pathlib import Path
from typing import Any

from ..models import AgentConfig, BlueprintConfig, Visibility
from .loader import BlueprintLoader
from .models import (
    AgentMetadata,
    AgentSpec,
    AgentYAML,
    BlueprintIDs,
    BlueprintMetadata,
    BlueprintYAML,
)


def yaml_to_config(
    blueprint: BlueprintYAML,
    agents: dict[str, AgentYAML],
    loader: BlueprintLoader | None = None,
) -> BlueprintConfig:
    """Convert YAML models to SDK BlueprintConfig.

    Args:
        blueprint: BlueprintYAML model
        agents: Dictionary mapping file paths to AgentYAML models
        loader: Optional BlueprintLoader for resolving agent order

    Returns:
        BlueprintConfig ready for SDK create() method

    Raises:
        ValueError: If no root agents or manager not found
    """
    if not blueprint.root_agents:
        raise ValueError("Blueprint must have at least one root_agent")

    # Get the first root agent as manager
    root_agent_path = blueprint.root_agents[0]

    # Find the manager agent
    manager_yaml = _find_agent_by_path(agents, root_agent_path)
    if manager_yaml is None:
        raise ValueError(f"Manager agent not found: {root_agent_path}")

    # Convert manager with recursive sub_agents support
    manager = _agent_yaml_to_config(manager_yaml, is_worker=False, agents=agents)

    # Collect workers: either from manager's sub_agents or flat list
    workers = []

    # If manager has sub_agents, they are the workers (already in manager.sub_agents)
    if manager.sub_agents:
        workers = list(manager.sub_agents)
    else:
        # Fall back to flat worker collection for backward compatibility
        if loader:
            agent_order = loader.get_agent_order()
            worker_paths = [p for p in agent_order if not _path_matches(p, root_agent_path)]
        else:
            worker_paths = [p for p in agents.keys() if not _path_matches(p, root_agent_path)]

        for path in worker_paths:
            agent_yaml = agents.get(path)
            if agent_yaml:
                workers.append(_agent_yaml_to_config(agent_yaml, is_worker=True, agents=agents))

    # Note: Single-agent blueprints (no workers) are valid
    # Workers list can be empty for single_agent pattern

    # Convert visibility
    visibility = Visibility(blueprint.metadata.visibility)

    return BlueprintConfig(
        name=blueprint.metadata.name,
        description=blueprint.metadata.description,
        manager=manager,
        workers=workers,
        category=blueprint.metadata.category,
        tags=blueprint.metadata.tags,
        visibility=visibility,
        readme=blueprint.metadata.readme,
        is_template=blueprint.metadata.is_template,
        shared_with_users=blueprint.metadata.shared_with_users,
        shared_with_organizations=blueprint.metadata.shared_with_organizations,
    )


def config_to_yaml(
    config: BlueprintConfig,
    agents_dir: str = "agents",
) -> tuple[BlueprintYAML, dict[str, AgentYAML]]:
    """Convert SDK BlueprintConfig to YAML format.

    Supports recursive sub_agents for deep hierarchies.

    Args:
        config: BlueprintConfig from SDK
        agents_dir: Directory name for agent files (default: "agents")

    Returns:
        Tuple of (BlueprintYAML, dict of agent path -> AgentYAML)
    """
    agents: dict[str, AgentYAML] = {}
    used_filenames: set[str] = set()

    def get_unique_filename(name: str) -> str:
        """Generate a unique filename for an agent."""
        base = _sanitize_filename(name)
        filename = f"{base}.yaml"
        counter = 1
        while filename in used_filenames:
            filename = f"{base}_{counter}.yaml"
            counter += 1
        used_filenames.add(filename)
        return filename

    def process_agent_recursive(
        agent_config: AgentConfig,
        is_worker: bool,
        parent_dir: str,
    ) -> tuple[str, list[str]]:
        """Process an agent and its sub_agents recursively.

        Args:
            agent_config: Agent configuration
            is_worker: Whether this is a worker
            parent_dir: Directory for this agent's file

        Returns:
            Tuple of (agent_path, list of sub_agent relative paths)
        """
        filename = get_unique_filename(agent_config.name)
        agent_path = f"{parent_dir}/{filename}"

        sub_agent_refs: list[str] = []

        # Process sub_agents recursively
        if agent_config.sub_agents:
            for sub_agent in agent_config.sub_agents:
                sub_path, _ = process_agent_recursive(
                    sub_agent,
                    is_worker=True,
                    parent_dir=parent_dir,
                )
                # Store relative path from parent agent
                sub_filename = sub_path.split("/")[-1]
                sub_agent_refs.append(sub_filename)

        # Create YAML for this agent
        agents[agent_path] = _agent_config_to_yaml(
            agent_config,
            is_worker=is_worker,
            sub_agents=sub_agent_refs,
        )

        return agent_path, sub_agent_refs

    # Process manager
    manager_path, _ = process_agent_recursive(
        config.manager,
        is_worker=False,
        parent_dir=agents_dir,
    )

    # Process flat workers (for backward compatibility)
    # These are added as sub_agents of the manager
    worker_refs: list[str] = []
    for worker in config.workers:
        worker_path, _ = process_agent_recursive(
            worker,
            is_worker=True,
            parent_dir=agents_dir,
        )
        worker_filename = worker_path.split("/")[-1]
        worker_refs.append(worker_filename)

    # Update manager with worker refs if it doesn't have sub_agents
    if worker_refs and not config.manager.sub_agents:
        manager_yaml = agents[manager_path]
        agents[manager_path] = AgentYAML(
            apiVersion=manager_yaml.apiVersion,
            kind=manager_yaml.kind,
            metadata=manager_yaml.metadata,
            spec=manager_yaml.spec,
            sub_agents=worker_refs,
        )

    # Create blueprint YAML
    blueprint = BlueprintYAML(
        metadata=BlueprintMetadata(
            name=config.name,
            description=config.description,
            category=config.category,
            tags=config.tags,
            visibility=config.visibility.value,
            is_template=config.is_template,
            shared_with_users=config.shared_with_users,
            shared_with_organizations=config.shared_with_organizations,
            readme=config.readme,
        ),
        root_agents=[manager_path],
    )

    return blueprint, agents


def api_response_to_yaml(
    blueprint_data: dict[str, Any],
    agents: list[dict[str, Any]],
    agents_dir: str = "agents",
) -> tuple[BlueprintYAML, dict[str, AgentYAML]]:
    """Convert API response to YAML format.

    Used for exporting existing blueprints to YAML files.

    Args:
        blueprint_data: Blueprint API response
        agents: List of agent API responses
        agents_dir: Directory name for agent files

    Returns:
        Tuple of (BlueprintYAML, dict of agent path -> AgentYAML)
    """
    yaml_agents: dict[str, AgentYAML] = {}
    agent_id_to_path: dict[str, str] = {}

    # Find manager (template_type == "MANAGER")
    manager_data = None
    worker_data_list: list[dict[str, Any]] = []

    for agent in agents:
        if agent.get("template_type") == "MANAGER":
            manager_data = agent
        else:
            worker_data_list.append(agent)

    if not manager_data:
        raise ValueError("No manager agent found in agents list")

    # Convert manager
    manager_filename = _sanitize_filename(manager_data.get("name", "manager")) + ".yaml"
    manager_path = f"{agents_dir}/{manager_filename}"
    agent_id_to_path[manager_data.get("agent_id", "")] = manager_path

    # Convert workers first to get their paths
    worker_paths: list[str] = []
    for worker in worker_data_list:
        worker_filename = _sanitize_filename(worker.get("name", "worker")) + ".yaml"
        worker_path = f"{agents_dir}/{worker_filename}"
        worker_paths.append(worker_filename)  # Relative to manager
        agent_id_to_path[worker.get("agent_id", "")] = worker_path

        yaml_agents[worker_path] = _api_agent_to_yaml(worker, is_worker=True)

    # Convert manager with sub_agents
    yaml_agents[manager_path] = _api_agent_to_yaml(
        manager_data,
        is_worker=False,
        sub_agents=worker_paths,
    )

    # Extract blueprint metadata
    bp_info = blueprint_data.get("blueprint_info", {})
    doc_data = bp_info.get("documentation_data", {})

    # Get visibility
    visibility = blueprint_data.get("visibility", "private")
    if visibility not in ("private", "organization", "public"):
        visibility = "private"

    # Create blueprint YAML with IDs
    blueprint = BlueprintYAML(
        metadata=BlueprintMetadata(
            name=blueprint_data.get("name", "Untitled"),
            description=blueprint_data.get("description", ""),
            category=blueprint_data.get("category"),
            tags=blueprint_data.get("tags", []),
            visibility=visibility,
            is_template=blueprint_data.get("is_template", False),
            shared_with_users=blueprint_data.get("shared_with_users", []),
            shared_with_organizations=blueprint_data.get("shared_with_organizations", []),
            readme=doc_data.get("markdown"),
        ),
        root_agents=[manager_path],
        ids=BlueprintIDs(
            blueprint=blueprint_data.get("_id") or blueprint_data.get("id"),
            agents=agent_id_to_path,
        ),
    )

    return blueprint, yaml_agents


def load_and_convert(blueprint_path: Path) -> BlueprintConfig:
    """Load YAML files and convert to BlueprintConfig.

    Convenience function that combines loading and conversion.

    Args:
        blueprint_path: Path to blueprint YAML file

    Returns:
        BlueprintConfig ready for SDK create() method
    """
    loader = BlueprintLoader()
    blueprint_yaml, agents = loader.load(blueprint_path)
    return yaml_to_config(blueprint_yaml, agents, loader)


# --- Private Helper Functions ---


def _agent_yaml_to_config(
    agent: AgentYAML,
    is_worker: bool,
    agents: dict[str, AgentYAML] | None = None,
    visited: set[str] | None = None,
) -> AgentConfig:
    """Convert AgentYAML to AgentConfig with recursive sub_agents support.

    Args:
        agent: AgentYAML to convert
        is_worker: Whether this is a worker agent
        agents: All agents dict for resolving sub_agents references
        visited: Set of visited agent names for circular dependency detection

    Returns:
        AgentConfig with nested sub_agents
    """
    if visited is None:
        visited = set()

    # Circular dependency check
    agent_name = agent.metadata.name
    if agent_name in visited:
        raise ValueError(f"Circular dependency detected: {agent_name}")

    visited = visited | {agent_name}
    spec = agent.spec

    # Recursively convert sub_agents
    sub_agents_config: list[AgentConfig] | None = None
    if agent.sub_agents and agents:
        sub_agents_config = []
        for sub_ref in agent.sub_agents:
            sub_agent = _find_agent_by_path(agents, sub_ref)
            if sub_agent:
                sub_config = _agent_yaml_to_config(
                    sub_agent,
                    is_worker=True,  # Sub-agents are always workers
                    agents=agents,
                    visited=visited,
                )
                sub_agents_config.append(sub_config)

    return AgentConfig(
        name=agent.metadata.name,
        description=agent.metadata.description,
        instructions=spec.instructions,
        role=spec.role,
        goal=spec.goal,
        context=spec.context,
        output_format=spec.output,
        examples=spec.examples,
        model=spec.model,
        temperature=spec.temperature,
        top_p=spec.top_p,
        response_format=spec.response_format,
        store_messages=spec.store_messages,
        file_output=spec.file_output,
        features=spec.features,
        usage_description=spec.usage if is_worker else None,
        sub_agents=sub_agents_config,
    )


def _agent_config_to_yaml(
    config: AgentConfig,
    is_worker: bool,
    sub_agents: list[str] | None = None,
) -> AgentYAML:
    """Convert AgentConfig to AgentYAML."""
    return AgentYAML(
        metadata=AgentMetadata(
            name=config.name,
            description=config.description,
        ),
        spec=AgentSpec(
            model=config.model,
            temperature=config.temperature,
            top_p=config.top_p,
            response_format=config.response_format,
            store_messages=config.store_messages,
            file_output=config.file_output,
            role=config.role,
            goal=config.goal,
            context=config.context,
            output=config.output_format,
            examples=config.examples,
            instructions=config.instructions,
            usage=config.usage_description if is_worker else None,
            features=config.features,
        ),
        sub_agents=sub_agents or [],
    )


def _api_agent_to_yaml(
    agent_data: dict[str, Any],
    is_worker: bool,
    sub_agents: list[str] | None = None,
) -> AgentYAML:
    """Convert API agent response to AgentYAML."""
    # Handle response_format which can be dict or string
    response_format = agent_data.get("response_format", {"type": "text"})
    if isinstance(response_format, dict):
        response_format = response_format.get("type", "text")

    return AgentYAML(
        metadata=AgentMetadata(
            name=agent_data.get("name", "Untitled"),
            description=agent_data.get("description", ""),
        ),
        spec=AgentSpec(
            model=agent_data.get("model", "gpt-4o"),
            temperature=agent_data.get("temperature", 0.3),
            top_p=agent_data.get("top_p", 1.0),
            response_format=response_format,
            store_messages=agent_data.get("store_messages", True),
            file_output=agent_data.get("file_output", False),
            role=agent_data.get("agent_role"),
            goal=agent_data.get("agent_goal"),
            context=agent_data.get("agent_context"),
            output=agent_data.get("agent_output"),
            examples=agent_data.get("examples"),
            instructions=agent_data.get("system_prompt", ""),
            usage=agent_data.get("tool_usage_description") if is_worker else None,
            features=_extract_features(agent_data),
        ),
        sub_agents=sub_agents or [],
    )


def _extract_features(agent_data: dict[str, Any]) -> list[str]:
    """Extract feature flags from agent API data."""
    features = []

    # Check feature configs
    feature_configs = agent_data.get("features", [])
    if isinstance(feature_configs, list):
        for fc in feature_configs:
            if isinstance(fc, dict):
                feature_type = fc.get("feature_type", "")
                if feature_type:
                    features.append(feature_type.lower())

    return features


def _find_agent_by_path(
    agents: dict[str, AgentYAML],
    target_path: str,
) -> AgentYAML | None:
    """Find an agent by path (handles both absolute and relative paths)."""
    # Direct match
    if target_path in agents:
        return agents[target_path]

    # Try matching by filename
    target_name = Path(target_path).name
    for path, agent in agents.items():
        if Path(path).name == target_name:
            return agent

    # Try matching by resolved path
    for path, agent in agents.items():
        if path.endswith(target_path) or target_path.endswith(path):
            return agent

    return None


def _path_matches(path1: str, path2: str) -> bool:
    """Check if two paths refer to the same file."""
    if path1 == path2:
        return True

    # Compare by filename
    return Path(path1).name == Path(path2).name


def _sanitize_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    # Replace spaces and special chars with hyphens
    safe = name.lower()
    safe = "".join(c if c.isalnum() else "-" for c in safe)
    # Remove consecutive hyphens
    while "--" in safe:
        safe = safe.replace("--", "-")
    # Remove leading/trailing hyphens
    safe = safe.strip("-")
    return safe or "agent"
