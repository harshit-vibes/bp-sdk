"""Marketplace API Client

Client for Lyzr Agent Marketplace API.
Handles app publishing and management operations.

Uses httpx for HTTP requests with Bearer token authentication.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..exceptions import APIError, NetworkError, TimeoutError

logger = logging.getLogger(__name__)


class MarketplaceAPI:
    """Client for Lyzr Agent Marketplace API.

    Handles agent publishing to marketplace with proper error handling.
    Uses httpx for HTTP requests (aligned with other SDK APIs).

    Authentication:
        - Bearer token via Authorization header (Memberstack JWT)
        - Same token used for Blueprint API

    Example:
        >>> api = MarketplaceAPI(
        ...     bearer_token="your-memberstack-jwt",
        ...     user_id="mem_xxx"
        ... )
        >>> app = api.create(
        ...     name="My Agent App",
        ...     agent_id="agent-123",
        ...     description="Does amazing things"
        ... )
    """

    DEFAULT_BASE_URL = "https://marketplace-prod.studio.lyzr.ai"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        bearer_token: str,
        user_id: str,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Marketplace API client.

        Args:
            bearer_token: Bearer token for authentication (Memberstack JWT)
            user_id: User ID for app ownership
            base_url: API base URL (defaults to production)
            timeout: Request timeout in seconds
        """
        self.bearer_token = bearer_token
        self.user_id = user_id
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
        if response.status_code in (200, 201, 204):
            try:
                return response.json()
            except ValueError:
                return {"status": "success"}

        # Extract error message
        try:
            error_data = response.json()
            message = error_data.get("detail") or error_data.get("message") or str(error_data)
        except ValueError:
            message = response.text[:500] or f"HTTP {response.status_code}"

        raise APIError(
            endpoint=operation,
            status_code=response.status_code,
            message=message,
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

    def create(
        self,
        name: str,
        agent_id: str,
        description: str | None = None,
        creator: str | None = None,
        public: bool = True,
        organization_id: str | None = None,
        welcome_message: str | None = None,
        industry: str | None = None,
        function: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Publish an agent to the marketplace.

        Args:
            name: App name (must be unique)
            agent_id: ID of the agent to publish
            description: App description
            creator: Creator name (defaults to "SDK")
            public: Whether app is publicly visible (default True)
            organization_id: Organization ID for org-only visibility
            welcome_message: Welcome message shown to users
            industry: Industry tag (e.g., "Banking & Financial Services")
            function: Function tag (e.g., "Marketing", "Sales")
            category: Category tag (e.g., "Productivity & Cost Savings")

        Returns:
            Created app data with id, name, agent_id, etc.

        Raises:
            APIError: If creation fails (e.g., duplicate name)
        """
        # Build tags object (required by production API)
        tags: dict[str, str] = {
            "industry": industry or "",
            "function": function or "",
            "category": category or "",
        }

        payload: dict[str, Any] = {
            "name": name,
            "agent_id": agent_id,
            "user_id": self.user_id,
            "creator": creator or "SDK",
            "public": public,
            "categories": [],  # Legacy field
            "welcome_message": welcome_message or "",  # Required by production API
            "tags": tags,  # Required by production API
        }

        if description:
            payload["description"] = description
        if organization_id:
            payload["organization_id"] = organization_id

        return self._request(
            method="POST",
            path="/app/",
            operation="create_app",
            json_data=payload,
        )

    def get(self, app_id: str) -> dict[str, Any]:
        """Get app by ID or name.

        Args:
            app_id: App ID or name

        Returns:
            App data including id, name, agent_id, public, upvotes, etc.
        """
        return self._request(
            method="GET",
            path=f"/app/{app_id}",
            operation=f"get_app:{app_id}",
        )

    def update(
        self,
        app_id: str,
        name: str | None = None,
        description: str | None = None,
        public: bool | None = None,
        categories: list[str] | None = None,
        industry: str | None = None,
        function: str | None = None,
        category: str | None = None,
        organization_id: str | None = None,
        welcome_message: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing app.

        Args:
            app_id: App ID to update
            name: New name (optional)
            description: New description (optional)
            public: New visibility (optional)
            categories: New categories list (optional)
            industry: Industry tag (optional)
            function: Function tag (optional)
            category: Category tag (optional)
            organization_id: Organization ID (optional)
            welcome_message: Welcome message (optional)

        Returns:
            Updated app data
        """
        payload: dict[str, Any] = {}

        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if public is not None:
            payload["public"] = public
        if categories is not None:
            payload["categories"] = categories
        if organization_id is not None:
            payload["organization_id"] = organization_id
        if welcome_message is not None:
            payload["welcome_message"] = welcome_message

        # Add tags if any provided
        if industry is not None or function is not None or category is not None:
            payload["tags"] = {}
            if industry is not None:
                payload["tags"]["industry"] = industry
            if function is not None:
                payload["tags"]["function"] = function
            if category is not None:
                payload["tags"]["category"] = category

        return self._request(
            method="PUT",
            path=f"/app/{app_id}",
            operation=f"update_app:{app_id}",
            json_data=payload,
        )

    def delete(self, app_id: str) -> bool:
        """Delete an app.

        Args:
            app_id: App ID to delete

        Returns:
            True if deleted successfully
        """
        url = f"{self.base_url}/app/{app_id}"

        try:
            response = self._client.delete(url)
            return response.status_code in (200, 204)

        except httpx.TimeoutException as e:
            logger.error(f"Timeout deleting app {app_id}")
            raise TimeoutError(f"delete_app:{app_id}", "Request timed out") from e

        except httpx.RequestError as e:
            logger.error(f"Error deleting app {app_id}: {e}")
            raise NetworkError(f"delete_app:{app_id}", str(e)) from e

    def list_by_user(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List apps by user.

        Args:
            user_id: User ID (defaults to configured user_id)

        Returns:
            List of app data
        """
        uid = user_id or self.user_id
        data = self._request(
            method="GET",
            path=f"/apps/user/{uid}",
            operation=f"list_apps_by_user:{uid}",
        )
        return data if isinstance(data, list) else []

    def list_user_and_public(
        self,
        user_id: str | None = None,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List user's apps plus public apps.

        Args:
            user_id: User ID (defaults to configured user_id)
            skip: Number of items to skip (pagination)
            limit: Max items to return
            search: Search term for name/description

        Returns:
            Paginated response with total, skip, limit, data
        """
        uid = user_id or self.user_id
        params: dict[str, Any] = {
            "skip": skip,
            "limit": limit,
        }
        if search:
            params["search"] = search

        return self._request(
            method="GET",
            path=f"/apps/user/{uid}/with-public",
            operation=f"list_user_and_public:{uid}",
            params=params,
        )

    def list_by_organization(
        self,
        organization_id: str,
        user_id: str | None = None,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        industry_tag: str | None = None,
        function_tag: str | None = None,
        category_tag: str | None = None,
    ) -> dict[str, Any]:
        """List apps by organization.

        Args:
            organization_id: Organization ID
            user_id: User ID (defaults to configured user_id)
            skip: Number of items to skip (pagination)
            limit: Max items to return
            search: Search term for name/description
            industry_tag: Filter by industry
            function_tag: Filter by function
            category_tag: Filter by category

        Returns:
            Paginated response with total, skip, limit, data
        """
        uid = user_id or self.user_id
        params: dict[str, Any] = {
            "skip": skip,
            "limit": limit,
        }
        if search:
            params["search"] = search
        if industry_tag:
            params["industry_tag"] = industry_tag
        if function_tag:
            params["function_tag"] = function_tag
        if category_tag:
            params["category_tag"] = category_tag

        return self._request(
            method="GET",
            path=f"/apps/organization/{organization_id}/{uid}",
            operation=f"list_by_org:{organization_id}",
            params=params,
        )

    def list_public(self) -> list[dict[str, Any]]:
        """List all public apps.

        Returns:
            List of public app data
        """
        data = self._request(
            method="GET",
            path="/apps/public",
            operation="list_public_apps",
        )
        return data if isinstance(data, list) else []

    def get_random(self, limit: int = 6) -> list[dict[str, Any]]:
        """Get random public apps.

        Args:
            limit: Number of apps to return (default 6)

        Returns:
            List of random public app data
        """
        data = self._request(
            method="GET",
            path="/apps/random",
            operation="get_random_apps",
            params={"limit": limit},
        )
        return data if isinstance(data, list) else []

    def get_leaderboard(self) -> list[dict[str, Any]]:
        """Get top 10 apps by upvotes.

        Returns:
            List of top apps sorted by upvotes
        """
        data = self._request(
            method="GET",
            path="/apps/leaderboard",
            operation="get_leaderboard",
        )
        if isinstance(data, dict):
            return data.get("leaderboard", [])
        return data if isinstance(data, list) else []

    def upvote(self, app_id: str, user_email: str) -> dict[str, Any]:
        """Upvote an app.

        Args:
            app_id: App ID to upvote
            user_email: Email of the user upvoting

        Returns:
            Success message

        Raises:
            APIError: If user already upvoted or app not found
        """
        return self._request(
            method="POST",
            path=f"/app/{app_id}/upvote",
            operation=f"upvote_app:{app_id}",
            json_data={
                "app_id": app_id,
                "user_email": user_email,
            },
        )
