"""Agent API Client

Client for Lyzr Agent API v3 operations.
"""

from .http import HTTPClient


class AgentAPI:
    """Client for Lyzr Agent API v3.

    Provides CRUD operations for agents:
    - create: Create new agent via template endpoint
    - get: Fetch agent by ID
    - update: Update agent configuration
    - delete: Remove agent
    - list: List all agents
    - chat: Send message to agent
    """

    # Production Agent API URL
    DEFAULT_BASE_URL = "https://agent-prod.studio.lyzr.ai"
    TIMEOUT = 30

    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = TIMEOUT):
        """Initialize Agent API client.

        Args:
            api_key: X-API-Key for authentication
            base_url: API base URL (defaults to production)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = float(timeout)

        # Create HTTP client
        self._client = HTTPClient(
            base_url=self.base_url,
            api_key=api_key,
            timeout=self.timeout,
        )

    def create(self, payload: dict) -> dict:
        """Create a new agent using template endpoint.

        Args:
            payload: Agent configuration payload

        Returns:
            Created agent data with _id
        """
        return self._client.post("/v3/agents/template/single-task", json=payload)

    def get(self, agent_id: str) -> dict:
        """Get agent by ID.

        Args:
            agent_id: Agent API ID

        Returns:
            Full agent data
        """
        return self._client.get(f"/v3/agents/{agent_id}")

    def update(self, agent_id: str, payload: dict) -> dict:
        """Update an existing agent.

        NOTE: This is PUT (full replacement), not PATCH.
        Always fetch current data first and merge changes to preserve fields.

        Args:
            agent_id: Agent API ID
            payload: Full agent configuration (replaces all fields)

        Returns:
            Updated agent data
        """
        return self._client.put(f"/v3/agents/{agent_id}", json=payload)

    def delete(self, agent_id: str) -> bool:
        """Delete an agent.

        Args:
            agent_id: Agent API ID

        Returns:
            True if deleted successfully
        """
        self._client.delete(f"/v3/agents/{agent_id}")
        return True

    def list(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all agents.

        Args:
            limit: Maximum number to return
            offset: Pagination offset

        Returns:
            List of agent data
        """
        response = self._client.get(
            "/v3/agents",
            params={"limit": limit, "offset": offset},
        )
        return response.get("agents", [])

    def chat(
        self, agent_id: str, message: str, session_id: str | None = None
    ) -> dict:
        """Send a chat message to an agent.

        Args:
            agent_id: Agent API ID
            message: User message
            session_id: Optional session ID for conversation continuity

        Returns:
            Agent response
        """
        payload = {"message": message}
        if session_id:
            payload["session_id"] = session_id

        return self._client.post(f"/v3/inference/chat/{agent_id}", json=payload)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
