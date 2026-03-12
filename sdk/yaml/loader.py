"""Blueprint Loader for YAML Definitions.

Loads blueprint and agent YAML files with recursive sub-agent resolution.
Handles circular dependency detection and relative path resolution.
"""

from pathlib import Path
from typing import Any

import yaml

from ..exceptions import ValidationError
from .models import AgentYAML, BlueprintYAML


class BlueprintLoader:
    """Loads blueprint and all referenced agents from YAML files.

    Features:
    - Recursive sub-agent resolution
    - Circular dependency detection
    - Relative path resolution from file location
    - Validation of file existence

    Example:
    ```python
    loader = BlueprintLoader()
    blueprint, agents = loader.load(Path("blueprints/daily-news.yaml"))

    # blueprint: BlueprintYAML instance
    # agents: dict[str, AgentYAML] - keyed by resolved file path
    ```
    """

    def __init__(self) -> None:
        """Initialize the loader."""
        self._loaded_agents: dict[str, AgentYAML] = {}
        self._loading_stack: list[str] = []  # For circular dependency detection

    def load(
        self, blueprint_path: Path
    ) -> tuple[BlueprintYAML, dict[str, AgentYAML]]:
        """Load blueprint and all referenced agents.

        Args:
            blueprint_path: Path to the blueprint YAML file

        Returns:
            Tuple of (BlueprintYAML, dict of agent path -> AgentYAML)

        Raises:
            ValidationError: If file not found, invalid YAML, or circular dependency
        """
        # Reset state for fresh load
        self._loaded_agents = {}
        self._loading_stack = []

        # Resolve to absolute path
        blueprint_path = blueprint_path.resolve()

        if not blueprint_path.exists():
            raise ValidationError(
                errors=[f"Blueprint file not found: {blueprint_path}"],
            )

        # Parse blueprint YAML
        blueprint = self._parse_blueprint(blueprint_path)

        # Load all root agents and their sub-agents recursively
        for agent_ref in blueprint.root_agents:
            agent_path = self._resolve_path(blueprint_path.parent, agent_ref)
            self._load_agent_recursive(agent_path)

        return blueprint, self._loaded_agents

    def load_agent(self, agent_path: Path) -> AgentYAML:
        """Load a single agent file (for standalone use).

        Args:
            agent_path: Path to the agent YAML file

        Returns:
            AgentYAML instance

        Raises:
            ValidationError: If file not found or invalid YAML
        """
        agent_path = agent_path.resolve()

        if not agent_path.exists():
            raise ValidationError(
                errors=[f"Agent file not found: {agent_path}"],
            )

        return self._parse_agent(agent_path)

    def _parse_blueprint(self, path: Path) -> BlueprintYAML:
        """Parse a blueprint YAML file.

        Args:
            path: Resolved path to blueprint file

        Returns:
            BlueprintYAML instance
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ValidationError(
                    errors=[f"Empty blueprint file: {path}"],
                )

            # Validate kind
            if data.get("kind") != "Blueprint":
                raise ValidationError(
                    errors=[f"Invalid kind in {path}: expected 'Blueprint', got '{data.get('kind')}'"],
                )

            return BlueprintYAML(**data)

        except yaml.YAMLError as e:
            raise ValidationError(
                errors=[f"Invalid YAML in {path}: {e}"],
            )
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                errors=[f"Error parsing blueprint {path}: {e}"],
            )

    def _parse_agent(self, path: Path) -> AgentYAML:
        """Parse an agent YAML file.

        Args:
            path: Resolved path to agent file

        Returns:
            AgentYAML instance
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ValidationError(
                    errors=[f"Empty agent file: {path}"],
                )

            # Validate kind
            if data.get("kind") != "Agent":
                raise ValidationError(
                    errors=[f"Invalid kind in {path}: expected 'Agent', got '{data.get('kind')}'"],
                )

            return AgentYAML(**data)

        except yaml.YAMLError as e:
            raise ValidationError(
                errors=[f"Invalid YAML in {path}: {e}"],
            )
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                errors=[f"Error parsing agent {path}: {e}"],
            )

    def _load_agent_recursive(self, agent_path: Path) -> AgentYAML:
        """Load an agent and all its sub-agents recursively.

        Args:
            agent_path: Resolved absolute path to agent file

        Returns:
            AgentYAML instance

        Raises:
            ValidationError: If circular dependency detected
        """
        path_key = str(agent_path)

        # Check for circular dependency FIRST (before checking cache)
        # This detects A -> B -> A cycles even if A was already parsed
        if path_key in self._loading_stack:
            cycle = " -> ".join(self._loading_stack + [path_key])
            raise ValidationError(
                errors=[f"Circular dependency detected: {cycle}"],
            )

        # Check if already fully loaded (including sub-agents)
        if path_key in self._loaded_agents:
            return self._loaded_agents[path_key]

        # Add to loading stack to track current path
        self._loading_stack.append(path_key)

        try:
            # Check file exists
            if not agent_path.exists():
                raise ValidationError(
                    errors=[f"Agent file not found: {agent_path}"],
                )

            # Parse agent
            agent = self._parse_agent(agent_path)

            # Recursively load sub-agents BEFORE caching
            # This ensures circular deps are caught via loading_stack
            for sub_ref in agent.sub_agents:
                sub_path = self._resolve_path(agent_path.parent, sub_ref)
                self._load_agent_recursive(sub_path)

            # Only cache after all sub-agents are loaded
            self._loaded_agents[path_key] = agent

            return agent

        finally:
            # Remove from loading stack
            self._loading_stack.pop()

    def _resolve_path(self, base_dir: Path, ref: str) -> Path:
        """Resolve a relative path reference.

        Args:
            base_dir: Directory containing the referencing file
            ref: Relative path reference

        Returns:
            Resolved absolute path
        """
        ref_path = Path(ref)

        if ref_path.is_absolute():
            return ref_path.resolve()

        return (base_dir / ref_path).resolve()

    def get_agent_order(self) -> list[str]:
        """Get agents in dependency order (leaves first).

        Returns a list of agent paths sorted so that agents are listed
        before their parents. This is useful for creation order:
        workers/leaves should be created before managers/roots.

        Returns:
            List of agent paths in dependency order
        """
        # Build dependency graph: parent -> {children it depends on}
        deps: dict[str, set[str]] = {}
        for path_key, agent in self._loaded_agents.items():
            agent_dir = Path(path_key).parent
            deps[path_key] = set()
            for sub_ref in agent.sub_agents:
                sub_path = str(self._resolve_path(agent_dir, sub_ref))
                deps[path_key].add(sub_path)

        # Topological sort (Kahn's algorithm)
        # in_degree[node] = number of dependencies (children) the node has
        in_degree = {k: len(v) for k, v in deps.items()}

        # Start with nodes that have no dependencies (leaves)
        queue = [k for k, v in in_degree.items() if v == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Find all parents that depend on this node
            for parent, children in deps.items():
                if node in children:
                    in_degree[parent] -= 1
                    if in_degree[parent] == 0:
                        queue.append(parent)

        return result

    def validate_all_files_exist(self) -> list[str]:
        """Validate all referenced files exist.

        Returns:
            List of missing file paths (empty if all exist)
        """
        missing = []
        for path_key in self._loaded_agents:
            if not Path(path_key).exists():
                missing.append(path_key)
        return missing


def load_blueprint(path: str | Path) -> tuple[BlueprintYAML, dict[str, AgentYAML]]:
    """Convenience function to load a blueprint.

    Args:
        path: Path to blueprint YAML file

    Returns:
        Tuple of (BlueprintYAML, dict of agent path -> AgentYAML)
    """
    loader = BlueprintLoader()
    return loader.load(Path(path))


def load_agent(path: str | Path) -> AgentYAML:
    """Convenience function to load a single agent.

    Args:
        path: Path to agent YAML file

    Returns:
        AgentYAML instance
    """
    loader = BlueprintLoader()
    return loader.load_agent(Path(path))
