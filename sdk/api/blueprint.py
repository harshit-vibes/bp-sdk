"""Blueprint API Client

Client for Lyzr Blueprint (PAGOS) API.
Handles blueprint CRUD operations with proper error handling.

Uses httpx for HTTP requests (same as Agent API core).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..exceptions import APIError, NetworkError, TimeoutError

logger = logging.getLogger(__name__)


class BlueprintAPI:
    """Client for Lyzr Blueprint API (Pagos service).

    Handles all blueprint CRUD operations with proper error handling.
    Uses httpx for HTTP requests (aligned with Agent API).

    Authentication:
        - Bearer token via Authorization header
        - organization_id as query parameter (required for all operations)

    Example:
        >>> api = BlueprintAPI(
        ...     bearer_token="your-bearer-token",
        ...     organization_id="your-org-id"
        ... )
        >>> blueprints = api.list(page_size=10, share_type="public")
    """

    DEFAULT_BASE_URL = "https://pagos-prod.studio.lyzr.ai"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        bearer_token: str,
        organization_id: str,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Blueprint API client.

        Args:
            bearer_token: Bearer token for authentication (from Memberstack)
            organization_id: Organization ID for requests
            base_url: API base URL (defaults to production)
            timeout: Request timeout in seconds
        """
        self.bearer_token = bearer_token
        self.organization_id = organization_id
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

        # Create httpx client with default headers
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    def __del__(self):
        """Close httpx client on cleanup."""
        if hasattr(self, "_client"):
            self._client.close()

    def _handle_response(self, response: httpx.Response, operation: str) -> dict[str, Any]:
        """Handle API response, raise on error.

        Args:
            response: httpx Response object
            operation: Description of the operation (for error messages)

        Returns:
            Parsed JSON response

        Raises:
            APIError: If response status is not 2xx
        """
        if response.status_code in (200, 201):
            try:
                return response.json()
            except ValueError:
                return {"status": "success"}

        raise APIError(
            endpoint=operation,
            status_code=response.status_code,
            message=response.text[:500],
        )

    def _request(
        self,
        method: str,
        path: str,
        operation: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with standardized error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (appended to base_url)
            operation: Operation name for error messages
            params: Query parameters
            json_data: JSON body data

        Returns:
            Parsed JSON response

        Raises:
            NetworkError: Connection or network issues
            TimeoutError: Request timed out
            APIError: API returned error status
        """
        url = f"{self.base_url}{path}"

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            return self._handle_response(response, operation)

        except httpx.TimeoutException as e:
            logger.error(f"Timeout during {operation}: {e}")
            raise TimeoutError(operation, f"Request timed out after {self.timeout}s") from e

        except httpx.ConnectError as e:
            logger.error(f"Connection error during {operation}: {e}")
            raise NetworkError(operation, f"Failed to connect: {e}") from e

        except httpx.RequestError as e:
            logger.error(f"Request error during {operation}: {e}")
            raise NetworkError(operation, str(e)) from e

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new blueprint.

        Args:
            payload: Blueprint configuration payload containing:
                - name: Blueprint name (required)
                - orchestration_type: Type of orchestration (required)
                - orchestration_name: Name of orchestration (required)
                - description: Optional description
                - blueprint_data: Agent tree and configuration
                - share_type: Visibility (default: private)
                - tags: Optional list of tags

        Returns:
            Created blueprint data with _id

        Raises:
            APIError: If creation fails (e.g., duplicate name)
        """
        return self._request(
            method="POST",
            path="/api/v1/blueprints/blueprints",
            operation="create_blueprint",
            params={"organization_id": self.organization_id},
            json_data=payload,
        )

    def get(self, blueprint_id: str) -> dict[str, Any]:
        """Get blueprint by ID.

        Args:
            blueprint_id: Blueprint API ID

        Returns:
            Full blueprint data including blueprint_data, agents, tree_structure
        """
        return self._request(
            method="GET",
            path=f"/api/v1/blueprints/blueprints/{blueprint_id}",
            operation=f"get_blueprint:{blueprint_id}",
            params={"organization_id": self.organization_id},
        )

    def update(self, blueprint_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update an existing blueprint.

        Args:
            blueprint_id: Blueprint API ID
            payload: Blueprint update payload (only include changed fields)

        Returns:
            Updated blueprint data
        """
        return self._request(
            method="PUT",
            path=f"/api/v1/blueprints/blueprints/{blueprint_id}",
            operation=f"update_blueprint:{blueprint_id}",
            params={"organization_id": self.organization_id},
            json_data=payload,
        )

    def delete(self, blueprint_id: str) -> bool:
        """Delete a blueprint.

        Note: This does NOT delete the agents. Use BlueprintClient.delete()
        for full cleanup including agents.

        Args:
            blueprint_id: Blueprint API ID

        Returns:
            True if deleted successfully
        """
        url = f"{self.base_url}/api/v1/blueprints/blueprints/{blueprint_id}"
        params = {"organization_id": self.organization_id}

        try:
            response = self._client.delete(url, params=params)
            return response.status_code in (200, 204)

        except httpx.TimeoutException as e:
            logger.error(f"Timeout deleting blueprint {blueprint_id}")
            raise TimeoutError(f"delete_blueprint:{blueprint_id}", "Request timed out") from e

        except httpx.RequestError as e:
            logger.error(f"Error deleting blueprint {blueprint_id}: {e}")
            raise NetworkError(f"delete_blueprint:{blueprint_id}", str(e)) from e

    def list(
        self,
        page_size: int = 50,
        page: int = 1,
        share_type: str | None = None,
        category: str | None = None,
        search: str | None = None,
        orchestration_type: str | None = None,
        tags: list[str] | None = None,
        owner_id: str | None = None,
        is_template: bool | None = None,
        sort_by: str | None = None,
        include_private: bool = True,
    ) -> dict[str, Any]:
        """List blueprints with filtering and pagination.

        Args:
            page_size: Items per page (max 100, default 50)
            page: Page number (1-indexed, default 1)
            share_type: Filter by visibility (public, private, organization)
            category: Filter by category
            search: Search term (case-insensitive regex on name/description)
            orchestration_type: Filter by type (e.g., "Manager Agent", "Single Agent")
            tags: Filter by tags (matched with $in operator)
            owner_id: Filter by owner ID
            is_template: Filter by template status
            sort_by: Sort field (created_at, updated_at, name, usage_count)
            include_private: If True (default), authenticate to include private/org blueprints.
                             Set to False to only list public blueprints.

        Returns:
            Dict with blueprints list and pagination info:
            {"blueprints": [...], "total": int, "page": int, "has_more": bool}
        """
        params: dict[str, Any] = {
            "page_size": min(page_size, 100),
            "page": max(page, 1),
        }

        # Include user_organization_id for authentication
        # This enables access to private, organization, and shared blueprints
        if include_private and self.organization_id:
            params["user_organization_id"] = self.organization_id

        # Visibility filter
        if share_type:
            params["share_type"] = share_type

        # Content filters
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        if orchestration_type:
            params["orchestration_type"] = orchestration_type
        if tags:
            params["tags"] = ",".join(tags)
        if owner_id:
            params["owner_id"] = owner_id
        if is_template is not None:
            params["is_template"] = str(is_template).lower()
        if sort_by:
            params["sort_by"] = sort_by

        data = self._request(
            method="GET",
            path="/api/v1/blueprints/blueprints",
            operation="list_blueprints",
            params=params,
        )

        # Return full response with pagination info
        if isinstance(data, dict) and "blueprints" in data:
            return data
        # Fallback for unexpected response format
        return {"blueprints": data if isinstance(data, list) else [], "total": 0, "page": page}

    def set_share_type(
        self,
        blueprint_id: str,
        share_type: str,
        user_ids: list[str] | None = None,
        organization_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Set blueprint share type and sharing targets.

        Args:
            blueprint_id: Blueprint API ID
            share_type: One of "private", "organization", "public", "specific_users"
            user_ids: List of user IDs to share with (for specific_users)
            organization_ids: List of organization IDs to share with (for specific_users)

        Returns:
            Updated blueprint data

        Note:
            - PRIVATE/PUBLIC: user_ids and organization_ids are ignored
            - ORGANIZATION: Shares with all members of the owning organization
            - SPECIFIC_USERS: Requires at least one user_id or organization_id
        """
        payload: dict[str, Any] = {"share_type": share_type}

        if user_ids:
            payload["user_ids"] = user_ids
        if organization_ids:
            payload["organization_ids"] = organization_ids

        return self._request(
            method="POST",
            path=f"/api/v1/blueprints/blueprints/{blueprint_id}/share",
            operation=f"set_share_type:{blueprint_id}",
            params={"organization_id": self.organization_id},
            json_data=payload,
        )

    def clone(
        self,
        blueprint_id: str,
        api_key: str,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """Clone a blueprint.

        Creates a complete copy with new agent IDs. The cloned blueprint
        is always private. Requires a valid Agent API key for cloning agents.

        Args:
            blueprint_id: Blueprint API ID to clone
            api_key: Agent API key for creating cloned agents
            new_name: Optional new name for the clone (auto-generated if duplicate)

        Returns:
            Cloned blueprint data with new ID
        """
        payload: dict[str, Any] = {
            "blueprint_id": blueprint_id,
            "api_key": api_key,
        }
        if new_name:
            payload["blueprint_name"] = new_name

        return self._request(
            method="POST",
            path="/api/v1/blueprints/blueprints/clone",
            operation=f"clone_blueprint:{blueprint_id}",
            params={"organization_id": self.organization_id},
            json_data=payload,
        )

    def duplicate(
        self,
        blueprint_id: str,
        new_name: str,
        new_description: str | None = None,
        target_organization_id: str | None = None,
    ) -> dict[str, Any]:
        """Duplicate a blueprint within the same organization.

        Unlike clone, duplicate does not create new agents - it copies
        the blueprint metadata only.

        Args:
            blueprint_id: Blueprint API ID to duplicate
            new_name: Name for the duplicated blueprint (required)
            new_description: Optional new description
            target_organization_id: Optional target org (for cross-org copy)

        Returns:
            Duplicated blueprint data with new ID
        """
        payload: dict[str, Any] = {"new_name": new_name}
        if new_description:
            payload["new_description"] = new_description
        if target_organization_id:
            payload["target_organization_id"] = target_organization_id

        return self._request(
            method="POST",
            path=f"/api/v1/blueprints/blueprints/{blueprint_id}/duplicate",
            operation=f"duplicate_blueprint:{blueprint_id}",
            params={"organization_id": self.organization_id},
            json_data=payload,
        )

    def track_usage(self, blueprint_id: str, event_type: str = "executed") -> dict[str, Any]:
        """Track blueprint usage.

        Updates usage_count and last_used_at timestamp.

        Args:
            blueprint_id: Blueprint API ID
            event_type: Type of usage event (default: "executed")

        Returns:
            Confirmation message
        """
        return self._request(
            method="POST",
            path=f"/api/v1/blueprints/blueprints/{blueprint_id}/use",
            operation=f"track_usage:{blueprint_id}",
            params={"organization_id": self.organization_id, "event_type": event_type},
        )
