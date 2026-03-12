"""bp-sdk: Blueprint SDK for Lyzr Studio

A Python SDK for JSON-based CRUD operations on Lyzr blueprints and agents.

Usage:
    from sdk import BlueprintClient, BlueprintConfig, AgentConfig

    # Initialize client
    client = BlueprintClient(api_key="...", bearer_token="...")

    # Create blueprint from config
    config = BlueprintConfig(
        name="My Blueprint",
        description="A helpful assistant blueprint",
        manager=AgentConfig(
            name="Manager",
            description="Coordinates tasks",
            instructions="You coordinate worker agents..."
        ),
        workers=[
            AgentConfig(
                name="Worker",
                description="Executes tasks",
                instructions="You execute assigned tasks...",
                usage_description="Use for general tasks"
            )
        ]
    )
    blueprint = client.create(config)

    # List, update, delete
    blueprints = client.get_all()
    client.update(blueprint.id, BlueprintUpdate(...))
    client.delete(blueprint.id)
"""

from .client import BlueprintClient
from .exceptions import (
    AgentCreationError,
    APIError,
    BlueprintCreationError,
    BlueprintSDKError,
    SyncError,
    ValidationError,
)
from .models import (
    AgentConfig,
    AgentUpdate,
    App,
    AppConfig,
    AppTags,
    Blueprint,
    BlueprintConfig,
    BlueprintUpdate,
    ListFilters,
    ValidationReport,
    Visibility,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "BlueprintClient",
    # Config models
    "AgentConfig",
    "AgentUpdate",
    "BlueprintConfig",
    "BlueprintUpdate",
    "ListFilters",
    # Response models
    "Blueprint",
    "ValidationReport",
    "Visibility",
    # Marketplace models
    "App",
    "AppConfig",
    "AppTags",
    # Exceptions
    "BlueprintSDKError",
    "APIError",
    "ValidationError",
    "AgentCreationError",
    "BlueprintCreationError",
    "SyncError",
]
