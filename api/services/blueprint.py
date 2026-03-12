"""Blueprint service wrapping the BP-SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sdk import AgentConfig, BlueprintClient, BlueprintConfig


@dataclass
class CreatedBlueprint:
    """Result of blueprint creation."""

    id: str
    name: str
    studio_url: str
    manager_id: str
    worker_ids: list[str]


class BlueprintService:
    """Wrapper around BlueprintClient for creating blueprints."""

    def __init__(
        self,
        api_key: str,
        bearer_token: str,
        org_id: str,
    ) -> None:
        """Initialize blueprint service.

        Args:
            api_key: Lyzr API key
            bearer_token: Blueprint API bearer token
            org_id: Organization ID
        """
        self.client = BlueprintClient(
            agent_api_key=api_key,
            blueprint_bearer_token=bearer_token,
            organization_id=org_id,
        )

    def create(self, config: dict) -> CreatedBlueprint:
        """Create a blueprint from config dict.

        Args:
            config: Blueprint configuration dictionary with keys:
                - name: Blueprint name
                - description: Blueprint description
                - category: Category tag
                - tags: List of tags
                - manager: Manager agent config dict
                - workers: List of worker agent config dicts

        Returns:
            CreatedBlueprint with IDs and URLs
        """
        # Build manager AgentConfig
        manager_dict = config.get("manager", {})
        manager = AgentConfig(
            name=manager_dict.get("name", "Manager"),
            description=manager_dict.get("description", "Orchestrates the workflow"),
            role=manager_dict.get("role"),
            goal=manager_dict.get("goal"),
            instructions=manager_dict.get("instructions", "You are a manager."),
            model=manager_dict.get("model", "gpt-4o"),
            temperature=manager_dict.get("temperature", 0.3),
        )

        # Build worker AgentConfigs
        workers = []
        for worker_dict in config.get("workers", []):
            if not worker_dict:
                continue

            worker = AgentConfig(
                name=worker_dict.get("name", "Worker"),
                description=worker_dict.get("description", "Handles a specific task"),
                role=worker_dict.get("role"),
                goal=worker_dict.get("goal"),
                instructions=worker_dict.get("instructions", "You are a worker."),
                usage_description=worker_dict.get(
                    "usage_description", "Use this worker for specific tasks."
                ),
                model=worker_dict.get("model", "gpt-4o-mini"),
                temperature=worker_dict.get("temperature", 0.2),
            )
            workers.append(worker)

        # Build BlueprintConfig
        bp_config = BlueprintConfig(
            name=config.get("name", "New Blueprint"),
            description=config.get("description", "A blueprint created by the builder."),
            category=config.get("category", "general"),
            tags=config.get("tags", []),
            manager=manager,
            workers=workers,
        )

        # Create via SDK
        blueprint = self.client.create(bp_config)

        return CreatedBlueprint(
            id=blueprint.id,
            name=blueprint.name,
            studio_url=blueprint.studio_url or "",
            manager_id=blueprint.manager_id or "",
            worker_ids=blueprint.worker_ids or [],
        )

    def create_from_config(self, config: BlueprintConfig) -> CreatedBlueprint:
        """Create a blueprint from a BlueprintConfig object.

        Args:
            config: BlueprintConfig object with manager and workers

        Returns:
            CreatedBlueprint with IDs and URLs
        """
        # Create via SDK directly
        blueprint = self.client.create(config)

        return CreatedBlueprint(
            id=blueprint.id,
            name=blueprint.name,
            studio_url=blueprint.studio_url or "",
            manager_id=blueprint.manager_id or "",
            worker_ids=blueprint.worker_ids or [],
        )

    def validate(self, blueprint_id: str) -> dict:
        """Validate an existing blueprint.

        Args:
            blueprint_id: Blueprint ID to validate

        Returns:
            Validation report dictionary
        """
        report = self.client.doctor(blueprint_id)
        return {
            "valid": report.valid,
            "errors": report.errors,
            "warnings": report.warnings,
        }
