"""bp-sdk Exceptions

Custom exceptions for the Blueprint SDK with detailed error information.
"""


class BlueprintSDKError(Exception):
    """Base exception for all bp-sdk errors."""

    pass


class APIError(BlueprintSDKError):
    """Error from API call.

    Raised when the API returns a non-2xx status code.

    Attributes:
        endpoint: The API endpoint/operation that failed
        status_code: HTTP status code from the response
        message: Error message from the API
    """

    def __init__(self, endpoint: str, status_code: int, message: str):
        self.endpoint = endpoint
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error [{status_code}] {endpoint}: {message}")


class NetworkError(BlueprintSDKError):
    """Network connectivity error.

    Raised when there's a connection failure, DNS resolution error,
    or other network-level issues.

    Attributes:
        operation: The operation that was being attempted
        reason: Description of the network error
    """

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Network error during {operation}: {reason}")


class TimeoutError(BlueprintSDKError):
    """Request timeout error.

    Raised when an API request exceeds the configured timeout.

    Attributes:
        operation: The operation that timed out
        reason: Description of the timeout
    """

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Timeout during {operation}: {reason}")


class ConfigurationError(BlueprintSDKError):
    """Configuration error.

    Raised when credentials are missing, invalid, or configuration
    files cannot be read/written.

    Attributes:
        reason: Description of the configuration error
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Configuration error: {reason}")


class ValidationError(BlueprintSDKError):
    """Validation failed.

    Raised when blueprint or agent configuration fails validation.

    Attributes:
        errors: List of validation error messages
    """

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class AgentCreationError(BlueprintSDKError):
    """Agent creation failed.

    Raised when one or more agents fail to create during blueprint creation.

    Attributes:
        agent_name: Name of the agent that failed to create
        reason: Description of why creation failed
        created_ids: List of agent IDs that were created before failure
                     (useful for cleanup/rollback)
    """

    def __init__(self, agent_name: str, reason: str, created_ids: list[str] | None = None):
        self.agent_name = agent_name
        self.reason = reason
        self.created_ids = created_ids or []
        super().__init__(f"Failed to create agent '{agent_name}': {reason}")


class BlueprintCreationError(BlueprintSDKError):
    """Blueprint creation failed.

    Raised when the blueprint itself fails to create (after agents are created).

    Attributes:
        blueprint_name: Name of the blueprint that failed to create
        reason: Description of why creation failed
        created_agent_ids: List of agent IDs that were created and need cleanup
    """

    def __init__(
        self, blueprint_name: str, reason: str, created_agent_ids: list[str] | None = None
    ):
        self.blueprint_name = blueprint_name
        self.reason = reason
        self.created_agent_ids = created_agent_ids or []
        super().__init__(f"Failed to create blueprint '{blueprint_name}': {reason}")


class SyncError(BlueprintSDKError):
    """Synchronization between Agent API and Blueprint API failed.

    Raised when updating a blueprint fails to keep agent data in sync.

    Attributes:
        operation: The sync operation that failed
        reason: Description of why sync failed
    """

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Sync error during {operation}: {reason}")


class RollbackError(BlueprintSDKError):
    """Rollback operation failed.

    Raised when cleanup after a failed operation also fails.

    Attributes:
        operation: The original operation that failed
        failed_cleanups: List of (resource_id, error) tuples for failed cleanups
    """

    def __init__(self, operation: str, failed_cleanups: list[tuple[str, str]]):
        self.operation = operation
        self.failed_cleanups = failed_cleanups
        cleanup_msg = ", ".join(f"{rid}: {err}" for rid, err in failed_cleanups)
        super().__init__(f"Rollback failed during {operation}. Failed to cleanup: {cleanup_msg}")
