"""CLI Configuration and Credential Management.

Handles environment variables and configuration for the CLI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Try to import yaml for config file support
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Try to import dotenv for .env file support
try:
    from dotenv import load_dotenv

    # Load .env file - try current directory first, then search parent directories
    load_dotenv(override=True)
except ImportError:
    pass


# Environment variable names
ENV_AGENT_API_KEY = "LYZR_API_KEY"
ENV_BLUEPRINT_TOKEN = "BLUEPRINT_BEARER_TOKEN"
ENV_ORG_ID = "LYZR_ORG_ID"
ENV_USER_ID = "LYZR_USER_ID"
ENV_AGENT_API_URL = "LYZR_AGENT_API_URL"
ENV_BLUEPRINT_API_URL = "LYZR_BLUEPRINT_API_URL"

# Default config file locations
CONFIG_PATHS = [
    Path.home() / ".bp" / "config.yaml",
    Path.home() / ".bp" / "config.yml",
    Path.cwd() / ".bp.yaml",
    Path.cwd() / ".bp.yml",
]


@dataclass
class CLIConfig:
    """CLI configuration container."""

    agent_api_key: str | None = None
    blueprint_bearer_token: str | None = None
    organization_id: str | None = None
    user_id: str | None = None
    agent_api_url: str | None = None
    blueprint_api_url: str | None = None

    def is_valid(self) -> bool:
        """Check if all required credentials are present."""
        return all(
            [
                self.agent_api_key,
                self.blueprint_bearer_token,
                self.organization_id,
            ]
        )

    def missing_fields(self) -> list[str]:
        """Get list of missing required fields."""
        missing = []
        if not self.agent_api_key:
            missing.append(ENV_AGENT_API_KEY)
        if not self.blueprint_bearer_token:
            missing.append(ENV_BLUEPRINT_TOKEN)
        if not self.organization_id:
            missing.append(ENV_ORG_ID)
        return missing

    def get_default_share_user_ids(self) -> list[str]:
        """Get default user IDs for sharing (self user)."""
        if self.user_id:
            return [self.user_id]
        return []

    def get_default_share_org_ids(self) -> list[str]:
        """Get default organization IDs for sharing (self org)."""
        if self.organization_id:
            return [self.organization_id]
        return []


def load_config_file(path: Path) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to config file

    Returns:
        Configuration dictionary
    """
    if not HAS_YAML:
        return {}

    if not path.exists():
        return {}

    with open(path) as f:
        data = yaml.safe_load(f)

    return data if isinstance(data, dict) else {}


def find_config_file() -> Path | None:
    """Find the first existing config file.

    Returns:
        Path to config file or None if not found
    """
    for path in CONFIG_PATHS:
        if path.exists():
            return path
    return None


def load_config() -> CLIConfig:
    """Load CLI configuration from environment and config files.

    Priority (highest to lowest):
    1. Environment variables
    2. Config file in current directory
    3. Config file in home directory

    Returns:
        CLIConfig with loaded values
    """
    config = CLIConfig()

    # Try to load from config file first
    config_file = find_config_file()
    if config_file:
        file_config = load_config_file(config_file)

        config.agent_api_key = file_config.get("agent_api_key")
        config.blueprint_bearer_token = file_config.get("blueprint_bearer_token")
        config.organization_id = file_config.get("organization_id")
        config.user_id = file_config.get("user_id")
        config.agent_api_url = file_config.get("agent_api_url")
        config.blueprint_api_url = file_config.get("blueprint_api_url")

    # Environment variables override config file
    if os.environ.get(ENV_AGENT_API_KEY):
        config.agent_api_key = os.environ[ENV_AGENT_API_KEY]

    if os.environ.get(ENV_BLUEPRINT_TOKEN):
        config.blueprint_bearer_token = os.environ[ENV_BLUEPRINT_TOKEN]

    if os.environ.get(ENV_ORG_ID):
        config.organization_id = os.environ[ENV_ORG_ID]

    if os.environ.get(ENV_USER_ID):
        config.user_id = os.environ[ENV_USER_ID]

    if os.environ.get(ENV_AGENT_API_URL):
        config.agent_api_url = os.environ[ENV_AGENT_API_URL]

    if os.environ.get(ENV_BLUEPRINT_API_URL):
        config.blueprint_api_url = os.environ[ENV_BLUEPRINT_API_URL]

    return config


def get_client_kwargs(config: CLIConfig) -> dict[str, Any]:
    """Get kwargs for BlueprintClient from config.

    Args:
        config: CLI configuration

    Returns:
        Dictionary of keyword arguments for BlueprintClient
    """
    kwargs: dict[str, Any] = {
        "agent_api_key": config.agent_api_key,
        "blueprint_bearer_token": config.blueprint_bearer_token,
        "organization_id": config.organization_id,
    }

    if config.user_id:
        kwargs["user_id"] = config.user_id

    if config.agent_api_url:
        kwargs["agent_api_base_url"] = config.agent_api_url

    if config.blueprint_api_url:
        kwargs["blueprint_api_base_url"] = config.blueprint_api_url

    return kwargs
