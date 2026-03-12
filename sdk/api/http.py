"""HTTP Client for Lyzr API communication.

A synchronous HTTP client for the bp-sdk, handling all communication
with the Lyzr Agent API.
"""

import logging
from typing import Any

import httpx

from ..exceptions import APIError, NetworkError, TimeoutError

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_TIMEOUT = 30.0


class HTTPClient:
    """Synchronous HTTP client for Lyzr APIs.

    Handles all HTTP communication including:
    - Request/response handling
    - Error translation to SDK exceptions
    - Header management (API key, content type)

    Usage:
        ```python
        client = HTTPClient(
            base_url="https://agent-prod.studio.lyzr.ai",
            api_key="your-api-key",
        )

        # Make requests
        agent = client.get("/v3/agents/agent-123")
        result = client.post("/v3/agents/template/single-task", json=payload)
        ```
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the HTTP client.

        Args:
            base_url: Base URL for API requests
            api_key: API key for X-API-Key header
            timeout: Request timeout in seconds
            headers: Additional headers to include
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._extra_headers = headers or {}

        # Create sync client
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            headers=self._get_headers(),
        )

    @property
    def api_key(self) -> str | None:
        """Get the API key."""
        return self._api_key

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        headers.update(self._extra_headers)
        return headers

    def _handle_response(self, response: httpx.Response, endpoint: str) -> dict[str, Any]:
        """Handle HTTP response and translate errors.

        Args:
            response: HTTP response object
            endpoint: Endpoint for error messages

        Returns:
            Response JSON data

        Raises:
            APIError: For HTTP errors
        """
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("message") or error_data.get("detail") or str(error_data)
            except Exception:
                message = response.text or f"HTTP {response.status_code}"

            raise APIError(
                endpoint=endpoint,
                status_code=response.status_code,
                message=message,
            )

        # Return JSON or empty dict
        if response.content:
            try:
                return response.json()
            except Exception:
                return {}
        return {}

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/v3/agents")
            json: JSON body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            APIError: For HTTP errors
            NetworkError: For connection failures
            TimeoutError: For request timeouts
        """
        try:
            response = self._client.request(
                method=method,
                url=endpoint,
                json=json,
                params=params,
            )
            return self._handle_response(response, endpoint)

        except httpx.TimeoutException as e:
            raise TimeoutError(
                operation=f"{method} {endpoint}",
                reason=str(e),
            ) from e

        except httpx.RequestError as e:
            raise NetworkError(
                operation=f"{method} {endpoint}",
                reason=str(e),
            ) from e

    def get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response data
        """
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: dict | None = None) -> dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint
            json: JSON body data

        Returns:
            Response data
        """
        return self.request("POST", endpoint, json=json)

    def put(self, endpoint: str, json: dict | None = None) -> dict[str, Any]:
        """Make a PUT request.

        Args:
            endpoint: API endpoint
            json: JSON body data

        Returns:
            Response data
        """
        return self.request("PUT", endpoint, json=json)

    def delete(self, endpoint: str) -> dict[str, Any]:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint

        Returns:
            Response data (usually empty)
        """
        return self.request("DELETE", endpoint)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "HTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
