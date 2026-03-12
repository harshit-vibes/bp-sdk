"""ID Manager for YAML Blueprints.

Manages platform-provided IDs in blueprint YAML files.
Uses ruamel.yaml for comment-preserving round-trips.
"""

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


class IDManager:
    """Read/write platform-provided IDs to YAML files.

    This class manages the `ids` section in blueprint YAML files,
    which stores platform-provided IDs after creation.

    Example blueprint.yaml with IDs:
    ```yaml
    apiVersion: lyzr.ai/v1
    kind: Blueprint

    metadata:
      name: "Daily News Agent"
      description: "Curates daily news"

    root_agents:
      - "agents/coordinator.yaml"

    ids:
      blueprint: "11938e83-5b25-41a8-ab89-0481ecfe3669"
      agents:
        "agents/coordinator.yaml": "69538cfd6363be71980ec157"
        "agents/researcher.yaml": "abc123def456"
    ```

    Features:
    - Comment-preserving YAML round-trips via ruamel.yaml
    - Safe file operations with atomic writes
    - Relative path normalization for agent IDs
    """

    def __init__(self, blueprint_path: Path) -> None:
        """Initialize the ID manager.

        Args:
            blueprint_path: Path to the blueprint YAML file
        """
        self.path = blueprint_path.resolve()
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.indent(mapping=2, sequence=4, offset=2)

    def get_blueprint_id(self) -> str | None:
        """Get the blueprint ID from YAML.

        Returns:
            Blueprint ID if present, None otherwise
        """
        data = self._load()
        if data is None:
            return None

        ids = data.get("ids")
        if ids is None:
            return None

        return ids.get("blueprint")

    def get_agent_id(self, agent_path: str) -> str | None:
        """Get agent ID for a given file path.

        Args:
            agent_path: Relative path to agent file (as written in YAML)

        Returns:
            Agent ID if present, None otherwise
        """
        data = self._load()
        if data is None:
            return None

        ids = data.get("ids")
        if ids is None:
            return None

        agents = ids.get("agents", {})
        return agents.get(agent_path)

    def get_all_agent_ids(self) -> dict[str, str]:
        """Get all agent IDs from YAML.

        Returns:
            Dictionary mapping agent file paths to their IDs
        """
        data = self._load()
        if data is None:
            return {}

        ids = data.get("ids")
        if ids is None:
            return {}

        return dict(ids.get("agents", {}))

    def has_ids(self) -> bool:
        """Check if the blueprint has any IDs stored.

        Returns:
            True if blueprint has IDs section with blueprint ID
        """
        return self.get_blueprint_id() is not None

    def save_ids(
        self,
        blueprint_id: str,
        agent_ids: dict[str, str],
    ) -> None:
        """Write IDs to YAML after successful creation.

        This method preserves existing YAML structure and comments
        while adding/updating the `ids` section.

        Args:
            blueprint_id: Platform-provided blueprint ID
            agent_ids: Mapping of agent file paths to their IDs
        """
        data = self._load()
        if data is None:
            raise FileNotFoundError(f"Blueprint file not found: {self.path}")

        # Create or update ids section
        if "ids" not in data:
            data["ids"] = {}

        data["ids"]["blueprint"] = blueprint_id
        data["ids"]["agents"] = dict(agent_ids)

        self._save(data)

    def clear_ids(self) -> None:
        """Remove IDs section from YAML.

        Use this when you want to create a new blueprint from the same YAML
        without the existing IDs.
        """
        data = self._load()
        if data is None:
            return

        if "ids" in data:
            del data["ids"]
            self._save(data)

    def update_blueprint_id(self, blueprint_id: str) -> None:
        """Update only the blueprint ID.

        Args:
            blueprint_id: New blueprint ID
        """
        data = self._load()
        if data is None:
            raise FileNotFoundError(f"Blueprint file not found: {self.path}")

        if "ids" not in data:
            data["ids"] = {}

        data["ids"]["blueprint"] = blueprint_id
        self._save(data)

    def update_agent_id(self, agent_path: str, agent_id: str) -> None:
        """Update or add a single agent ID.

        Args:
            agent_path: Relative path to agent file
            agent_id: Platform-provided agent ID
        """
        data = self._load()
        if data is None:
            raise FileNotFoundError(f"Blueprint file not found: {self.path}")

        if "ids" not in data:
            data["ids"] = {}
        if "agents" not in data["ids"]:
            data["ids"]["agents"] = {}

        data["ids"]["agents"][agent_path] = agent_id
        self._save(data)

    def remove_agent_id(self, agent_path: str) -> bool:
        """Remove a single agent ID.

        Args:
            agent_path: Relative path to agent file

        Returns:
            True if agent was found and removed, False otherwise
        """
        data = self._load()
        if data is None:
            return False

        ids = data.get("ids")
        if ids is None:
            return False

        agents = ids.get("agents", {})
        if agent_path not in agents:
            return False

        del agents[agent_path]
        self._save(data)
        return True

    def _load(self) -> dict[str, Any] | None:
        """Load YAML data from file.

        Returns:
            Parsed YAML data, or None if file doesn't exist
        """
        if not self.path.exists():
            return None

        with open(self.path) as f:
            return self._yaml.load(f)

    def _save(self, data: dict[str, Any]) -> None:
        """Save YAML data to file with atomic write.

        Uses a temporary file and rename for atomic writes
        to prevent data corruption on failure.

        Args:
            data: YAML data to save
        """
        # Write to temp file first, then rename (atomic on most filesystems)
        temp_path = self.path.with_suffix(".yaml.tmp")
        try:
            with open(temp_path, "w") as f:
                self._yaml.dump(data, f)
            temp_path.rename(self.path)
        except Exception:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise
