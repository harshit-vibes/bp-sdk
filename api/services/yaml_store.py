"""YAML Store service for in-memory blueprint YAML management.

This service handles:
1. Converting AgentYAMLSpec to SDK-compatible YAML dict format
2. Building blueprint.yaml from saved agents
3. Preparing data for BlueprintClient.create()
"""

from __future__ import annotations

from typing import Any, Optional

from ..models.hitl import AgentYAMLSpec, BlueprintYAMLSpec
from ..models.session import CraftingState, Session


class YAMLStoreService:
    """Convert and manage YAML specifications for blueprint creation."""

    def agent_spec_to_yaml_dict(self, spec: AgentYAMLSpec) -> dict[str, Any]:
        """Convert AgentYAMLSpec to SDK-compatible YAML dict format.

        This produces the structure expected by the bp-sdk YAML loader.

        Args:
            spec: The agent specification from the agent

        Returns:
            Dict matching the agent YAML schema
        """
        yaml_dict = {
            "apiVersion": "lyzr.ai/v1",
            "kind": "Agent",
            "metadata": {
                "name": spec.name,
                "description": spec.description,
            },
            "spec": {
                "model": spec.model,
                "temperature": spec.temperature,
                "role": spec.role,
                "goal": spec.goal,
                "instructions": spec.instructions,
            },
        }

        # Add features if present
        if spec.features:
            yaml_dict["spec"]["features"] = spec.features

        # Add usage_description for workers
        if spec.usage_description and not spec.is_manager:
            yaml_dict["spec"]["usage_description"] = spec.usage_description

        # Add sub_agents for manager
        if spec.is_manager and spec.sub_agents:
            yaml_dict["sub_agents"] = spec.sub_agents

        return yaml_dict

    def blueprint_spec_to_yaml_dict(
        self,
        spec: BlueprintYAMLSpec,
        manager_filename: str,
    ) -> dict[str, Any]:
        """Convert BlueprintYAMLSpec to SDK-compatible YAML dict format.

        Args:
            spec: The blueprint specification
            manager_filename: Filename of the manager agent YAML

        Returns:
            Dict matching the blueprint YAML schema
        """
        yaml_dict = {
            "apiVersion": "lyzr.ai/v1",
            "kind": "Blueprint",
            "metadata": {
                "name": spec.name,
                "description": spec.description,
                "category": spec.category,
                "tags": spec.tags,
                "visibility": spec.visibility,
            },
            "root_agents": [f"../agents/{manager_filename}"],
        }

        # Add readme if present
        if spec.readme:
            yaml_dict["metadata"]["readme"] = spec.readme

        return yaml_dict

    def build_blueprint_config(self, session: Session) -> dict[str, Any]:
        """Build a BlueprintConfig-compatible dict from session state.

        This is used with BlueprintClient.create() for direct creation.

        Args:
            session: Session with saved agent YAMLs

        Returns:
            Dict compatible with BlueprintConfig
        """
        crafting = session.crafting
        blueprint_yaml = session.blueprint_yaml

        if not crafting.manager_yaml:
            raise ValueError("No manager YAML saved in session")

        if not blueprint_yaml:
            raise ValueError("No blueprint YAML spec in session")

        manager = crafting.manager_yaml

        # Build manager config
        manager_config = {
            "name": manager.name,
            "description": manager.description,
            "role": manager.role,
            "goal": manager.goal,
            "instructions": manager.instructions,
            "model": manager.model,
            "temperature": manager.temperature,
        }

        if manager.features:
            manager_config["features"] = manager.features

        # Build workers config
        workers = []
        for worker_yaml in crafting.worker_yamls:
            worker_config = {
                "name": worker_yaml.name,
                "description": worker_yaml.description,
                "role": worker_yaml.role,
                "goal": worker_yaml.goal,
                "instructions": worker_yaml.instructions,
                "usage_description": worker_yaml.usage_description or f"Use {worker_yaml.name} for its specialized tasks",
                "model": worker_yaml.model,
                "temperature": worker_yaml.temperature,
            }

            if worker_yaml.features:
                worker_config["features"] = worker_yaml.features

            workers.append(worker_config)

        # Build full config
        config = {
            "name": blueprint_yaml.name,
            "description": blueprint_yaml.description,
            "category": blueprint_yaml.category,
            "tags": blueprint_yaml.tags,
            "visibility": blueprint_yaml.visibility,
            "manager": manager_config,
            "workers": workers,
        }

        if blueprint_yaml.readme:
            config["readme"] = blueprint_yaml.readme

        return config

    def get_crafting_summary(self, crafting: CraftingState) -> dict[str, Any]:
        """Get a summary of the crafting state for display.

        Args:
            crafting: Current crafting state

        Returns:
            Summary dict for UI display
        """
        saved_count = 0
        if crafting.manager_yaml:
            saved_count += 1
        saved_count += len(crafting.worker_yamls)

        return {
            "total_agents": crafting.total_agents,
            "current_index": crafting.current_index,
            "saved_count": saved_count,
            "progress": f"{saved_count}/{crafting.total_agents}",
            "is_complete": crafting.all_agents_saved,
            "current_agent": crafting.current_agent,
            "is_crafting_manager": crafting.is_crafting_manager,
            "saved_agents": [
                {"name": a.name, "filename": a.filename, "is_manager": a.is_manager}
                for a in crafting.get_all_yamls()
            ],
        }

    def validate_agent_yaml(self, spec: AgentYAMLSpec) -> tuple[bool, list[str]]:
        """Validate an agent YAML specification.

        Args:
            spec: The agent specification to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check required fields
        if not spec.name:
            errors.append("Agent name is required")

        if not spec.description:
            errors.append("Agent description is required")

        # Check role length (15-80 chars)
        if len(spec.role) < 15:
            errors.append(f"Role too short ({len(spec.role)} chars, minimum 15)")
        elif len(spec.role) > 80:
            errors.append(f"Role too long ({len(spec.role)} chars, maximum 80)")

        # Check goal length (50-300 chars)
        if len(spec.goal) < 50:
            errors.append(f"Goal too short ({len(spec.goal)} chars, minimum 50)")
        elif len(spec.goal) > 300:
            errors.append(f"Goal too long ({len(spec.goal)} chars, maximum 300)")

        # Check instructions
        if not spec.instructions or len(spec.instructions) < 100:
            errors.append("Instructions too short (minimum 100 chars)")

        # Check workers have usage_description
        if not spec.is_manager and not spec.usage_description:
            errors.append("Workers must have usage_description")

        # Check manager has sub_agents
        if spec.is_manager and not spec.sub_agents:
            errors.append("Manager should have sub_agents list")

        return len(errors) == 0, errors

    def generate_worker_filenames(self, worker_names: list[str]) -> list[str]:
        """Generate safe filenames for workers.

        Args:
            worker_names: List of worker names

        Returns:
            List of safe filenames (e.g., "email-categorizer.yaml")
        """
        filenames = []
        for name in worker_names:
            # Convert to lowercase, replace spaces with hyphens
            safe_name = name.lower().replace(" ", "-").replace("_", "-")
            # Remove any non-alphanumeric characters except hyphens
            safe_name = "".join(c for c in safe_name if c.isalnum() or c == "-")
            # Remove consecutive hyphens
            while "--" in safe_name:
                safe_name = safe_name.replace("--", "-")
            # Remove leading/trailing hyphens
            safe_name = safe_name.strip("-")
            filenames.append(f"{safe_name}.yaml")
        return filenames
