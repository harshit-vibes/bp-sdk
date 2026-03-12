"""YAML File Writer.

Exports blueprint and agent YAML files to disk.
"""

from pathlib import Path

from ruamel.yaml import YAML

from .models import AgentYAML, BlueprintYAML


class YAMLWriter:
    """Write blueprint and agent YAML files.

    Features:
    - Creates directory structure automatically
    - Uses ruamel.yaml for clean output formatting
    - Preserves field order for readability
    """

    def __init__(self) -> None:
        """Initialize the YAML writer."""
        self._yaml = YAML()
        self._yaml.default_flow_style = False
        self._yaml.indent(mapping=2, sequence=4, offset=2)
        self._yaml.preserve_quotes = True

    def write_blueprint(
        self,
        output_dir: Path,
        blueprint: BlueprintYAML,
        agents: dict[str, AgentYAML],
        blueprint_filename: str = "blueprint.yaml",
    ) -> Path:
        """Write blueprint and all agents to YAML files.

        Args:
            output_dir: Base output directory
            blueprint: BlueprintYAML model
            agents: Dictionary mapping file paths to AgentYAML models
            blueprint_filename: Name for the blueprint file

        Returns:
            Path to the created blueprint file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write agents first
        for agent_path, agent in agents.items():
            self._write_agent_file(output_dir, agent_path, agent)

        # Write blueprint
        blueprint_path = output_dir / blueprint_filename
        self._write_blueprint_file(blueprint_path, blueprint)

        return blueprint_path

    def write_agent(
        self,
        output_path: Path,
        agent: AgentYAML,
    ) -> Path:
        """Write a single agent to a YAML file.

        Args:
            output_path: Path for the agent file
            agent: AgentYAML model

        Returns:
            Path to the created agent file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = self._agent_to_dict(agent)

        with open(output_path, "w") as f:
            self._yaml.dump(data, f)

        return output_path

    def _write_blueprint_file(self, path: Path, blueprint: BlueprintYAML) -> None:
        """Write a blueprint YAML file."""
        data = self._blueprint_to_dict(blueprint)

        with open(path, "w") as f:
            self._yaml.dump(data, f)

    def _write_agent_file(
        self,
        output_dir: Path,
        agent_path: str,
        agent: AgentYAML,
    ) -> None:
        """Write an agent YAML file."""
        full_path = output_dir / agent_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        data = self._agent_to_dict(agent)

        with open(full_path, "w") as f:
            self._yaml.dump(data, f)

    def _blueprint_to_dict(self, blueprint: BlueprintYAML) -> dict:
        """Convert BlueprintYAML to ordered dictionary for YAML output."""
        # Build in desired field order
        data: dict = {}

        data["apiVersion"] = blueprint.apiVersion
        data["kind"] = blueprint.kind

        # Metadata section
        metadata: dict = {}
        metadata["name"] = blueprint.metadata.name
        metadata["description"] = blueprint.metadata.description

        if blueprint.metadata.category:
            metadata["category"] = blueprint.metadata.category
        if blueprint.metadata.tags:
            metadata["tags"] = blueprint.metadata.tags
        if blueprint.metadata.visibility != "private":
            metadata["visibility"] = blueprint.metadata.visibility
        if blueprint.metadata.is_template:
            metadata["is_template"] = blueprint.metadata.is_template
        if blueprint.metadata.shared_with_users:
            metadata["shared_with_users"] = blueprint.metadata.shared_with_users
        if blueprint.metadata.shared_with_organizations:
            metadata["shared_with_organizations"] = blueprint.metadata.shared_with_organizations
        if blueprint.metadata.readme:
            metadata["readme"] = blueprint.metadata.readme

        data["metadata"] = metadata

        # Root agents
        data["root_agents"] = blueprint.root_agents

        # IDs section (if present)
        if blueprint.ids and (blueprint.ids.blueprint or blueprint.ids.agents):
            ids: dict = {}
            if blueprint.ids.blueprint:
                ids["blueprint"] = blueprint.ids.blueprint
            if blueprint.ids.agents:
                ids["agents"] = dict(blueprint.ids.agents)
            data["ids"] = ids

        return data

    def _agent_to_dict(self, agent: AgentYAML) -> dict:
        """Convert AgentYAML to ordered dictionary for YAML output."""
        data: dict = {}

        data["apiVersion"] = agent.apiVersion
        data["kind"] = agent.kind

        # Metadata section
        data["metadata"] = {
            "name": agent.metadata.name,
            "description": agent.metadata.description,
        }

        # Spec section
        spec: dict = {}

        # LLM configuration (only non-default values)
        if agent.spec.model != "gpt-4o":
            spec["model"] = agent.spec.model
        if agent.spec.temperature != 0.3:
            spec["temperature"] = agent.spec.temperature
        if agent.spec.top_p != 1.0:
            spec["top_p"] = agent.spec.top_p
        if agent.spec.response_format != "text":
            spec["response_format"] = agent.spec.response_format
        if not agent.spec.store_messages:
            spec["store_messages"] = agent.spec.store_messages
        if agent.spec.file_output:
            spec["file_output"] = agent.spec.file_output

        # Persona fields (if present)
        if agent.spec.role:
            spec["role"] = agent.spec.role
        if agent.spec.goal:
            spec["goal"] = agent.spec.goal
        if agent.spec.context:
            spec["context"] = agent.spec.context
        if agent.spec.output:
            spec["output"] = agent.spec.output
        if agent.spec.examples:
            spec["examples"] = agent.spec.examples

        # Instructions (always present)
        spec["instructions"] = agent.spec.instructions

        # Worker-specific
        if agent.spec.usage:
            spec["usage"] = agent.spec.usage

        # Features
        if agent.spec.features:
            spec["features"] = agent.spec.features

        data["spec"] = spec

        # Sub-agents (if any)
        if agent.sub_agents:
            data["sub_agents"] = agent.sub_agents

        return data


def write_blueprint(
    output_dir: Path,
    blueprint: BlueprintYAML,
    agents: dict[str, AgentYAML],
    blueprint_filename: str = "blueprint.yaml",
) -> Path:
    """Convenience function to write blueprint and agents.

    Args:
        output_dir: Base output directory
        blueprint: BlueprintYAML model
        agents: Dictionary mapping file paths to AgentYAML models
        blueprint_filename: Name for the blueprint file

    Returns:
        Path to the created blueprint file
    """
    writer = YAMLWriter()
    return writer.write_blueprint(output_dir, blueprint, agents, blueprint_filename)


def write_agent(output_path: Path, agent: AgentYAML) -> Path:
    """Convenience function to write a single agent.

    Args:
        output_path: Path for the agent file
        agent: AgentYAML model

    Returns:
        Path to the created agent file
    """
    writer = YAMLWriter()
    return writer.write_agent(output_path, agent)
