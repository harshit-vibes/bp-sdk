"""Tests for sdk.exceptions"""

import pytest

from sdk.exceptions import (
    BlueprintSDKError,
    APIError,
    NetworkError,
    TimeoutError,
    ConfigurationError,
    ValidationError,
    AgentCreationError,
    BlueprintCreationError,
    SyncError,
    RollbackError,
)


class TestBlueprintSDKError:
    """Tests for base BlueprintSDKError."""

    def test_base_exception(self):
        """Test base exception can be raised."""
        with pytest.raises(BlueprintSDKError):
            raise BlueprintSDKError("Base error")

    def test_inheritance(self):
        """Test all exceptions inherit from BlueprintSDKError."""
        assert issubclass(APIError, BlueprintSDKError)
        assert issubclass(NetworkError, BlueprintSDKError)
        assert issubclass(TimeoutError, BlueprintSDKError)
        assert issubclass(ConfigurationError, BlueprintSDKError)
        assert issubclass(ValidationError, BlueprintSDKError)
        assert issubclass(AgentCreationError, BlueprintSDKError)
        assert issubclass(BlueprintCreationError, BlueprintSDKError)
        assert issubclass(SyncError, BlueprintSDKError)
        assert issubclass(RollbackError, BlueprintSDKError)


class TestAPIError:
    """Tests for APIError exception."""

    def test_attributes(self):
        """Test APIError stores attributes correctly."""
        error = APIError(
            endpoint="create_blueprint",
            status_code=400,
            message="Invalid payload",
        )
        assert error.endpoint == "create_blueprint"
        assert error.status_code == 400
        assert error.message == "Invalid payload"

    def test_str_representation(self):
        """Test APIError string representation."""
        error = APIError("get_agent", 404, "Agent not found")
        assert "[404]" in str(error)
        assert "get_agent" in str(error)
        assert "Agent not found" in str(error)

    def test_catch_as_base(self):
        """Test APIError can be caught as BlueprintSDKError."""
        try:
            raise APIError("test", 500, "error")
        except BlueprintSDKError as e:
            assert isinstance(e, APIError)


class TestNetworkError:
    """Tests for NetworkError exception."""

    def test_attributes(self):
        """Test NetworkError stores attributes correctly."""
        error = NetworkError(
            operation="fetch_blueprint",
            reason="Connection refused",
        )
        assert error.operation == "fetch_blueprint"
        assert error.reason == "Connection refused"

    def test_str_representation(self):
        """Test NetworkError string representation."""
        error = NetworkError("create_agent", "DNS resolution failed")
        assert "create_agent" in str(error)
        assert "DNS resolution failed" in str(error)


class TestTimeoutError:
    """Tests for TimeoutError exception."""

    def test_attributes(self):
        """Test TimeoutError stores attributes correctly."""
        error = TimeoutError(
            operation="long_request",
            reason="Request exceeded 30s timeout",
        )
        assert error.operation == "long_request"
        assert error.reason == "Request exceeded 30s timeout"

    def test_str_representation(self):
        """Test TimeoutError string representation."""
        error = TimeoutError("update", "Timed out after 60s")
        assert "update" in str(error)
        assert "Timed out" in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_attributes(self):
        """Test ConfigurationError stores attributes correctly."""
        error = ConfigurationError(reason="Missing API key")
        assert error.reason == "Missing API key"

    def test_str_representation(self):
        """Test ConfigurationError string representation."""
        error = ConfigurationError("Invalid bearer token format")
        assert "Configuration error" in str(error)
        assert "Invalid bearer token format" in str(error)


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_single_error(self):
        """Test ValidationError with single error."""
        error = ValidationError(["Missing name field"])
        assert error.errors == ["Missing name field"]

    def test_multiple_errors(self):
        """Test ValidationError with multiple errors."""
        errors = ["Missing name", "Invalid temperature", "Role too short"]
        error = ValidationError(errors)
        assert len(error.errors) == 3
        assert "Missing name" in error.errors

    def test_str_representation(self):
        """Test ValidationError string representation."""
        error = ValidationError(["Error 1", "Error 2"])
        error_str = str(error)
        assert "Validation failed" in error_str
        assert "Error 1" in error_str
        assert "Error 2" in error_str


class TestAgentCreationError:
    """Tests for AgentCreationError exception."""

    def test_attributes_minimal(self):
        """Test AgentCreationError with minimal attributes."""
        error = AgentCreationError(
            agent_name="Worker 1",
            reason="API returned 500",
        )
        assert error.agent_name == "Worker 1"
        assert error.reason == "API returned 500"
        assert error.created_ids == []

    def test_attributes_with_created_ids(self):
        """Test AgentCreationError with created_ids for rollback."""
        error = AgentCreationError(
            agent_name="Worker 3",
            reason="Duplicate name",
            created_ids=["agent_1", "agent_2"],
        )
        assert error.created_ids == ["agent_1", "agent_2"]

    def test_str_representation(self):
        """Test AgentCreationError string representation."""
        error = AgentCreationError("Research Agent", "Invalid config")
        assert "Research Agent" in str(error)
        assert "Invalid config" in str(error)


class TestBlueprintCreationError:
    """Tests for BlueprintCreationError exception."""

    def test_attributes_minimal(self):
        """Test BlueprintCreationError with minimal attributes."""
        error = BlueprintCreationError(
            blueprint_name="HR Blueprint",
            reason="Duplicate name exists",
        )
        assert error.blueprint_name == "HR Blueprint"
        assert error.reason == "Duplicate name exists"
        assert error.created_agent_ids == []

    def test_attributes_with_agent_ids(self):
        """Test BlueprintCreationError with agent IDs for cleanup."""
        error = BlueprintCreationError(
            blueprint_name="Failed Blueprint",
            reason="Tree validation failed",
            created_agent_ids=["manager_1", "worker_1", "worker_2"],
        )
        assert len(error.created_agent_ids) == 3

    def test_str_representation(self):
        """Test BlueprintCreationError string representation."""
        error = BlueprintCreationError("My Blueprint", "API error")
        assert "My Blueprint" in str(error)
        assert "API error" in str(error)


class TestSyncError:
    """Tests for SyncError exception."""

    def test_attributes(self):
        """Test SyncError stores attributes correctly."""
        error = SyncError(
            operation="update_tree",
            reason="Agent API returned stale data",
        )
        assert error.operation == "update_tree"
        assert error.reason == "Agent API returned stale data"

    def test_str_representation(self):
        """Test SyncError string representation."""
        error = SyncError("refresh", "Mismatched agent IDs")
        assert "Sync error" in str(error)
        assert "refresh" in str(error)
        assert "Mismatched agent IDs" in str(error)


class TestRollbackError:
    """Tests for RollbackError exception."""

    def test_attributes(self):
        """Test RollbackError stores attributes correctly."""
        failed_cleanups = [
            ("agent_1", "Not found"),
            ("agent_2", "Permission denied"),
        ]
        error = RollbackError(
            operation="create_blueprint",
            failed_cleanups=failed_cleanups,
        )
        assert error.operation == "create_blueprint"
        assert len(error.failed_cleanups) == 2

    def test_empty_cleanups(self):
        """Test RollbackError with empty failed cleanups."""
        error = RollbackError("delete", [])
        assert error.failed_cleanups == []

    def test_str_representation(self):
        """Test RollbackError string representation."""
        error = RollbackError(
            "update",
            [("id_1", "timeout"), ("id_2", "404")],
        )
        error_str = str(error)
        assert "Rollback failed" in error_str
        assert "update" in error_str
        assert "id_1" in error_str
        assert "timeout" in error_str

    def test_single_failure(self):
        """Test RollbackError with single cleanup failure."""
        error = RollbackError("create", [("orphan_agent", "delete failed")])
        assert "orphan_agent" in str(error)


class TestExceptionChaining:
    """Tests for proper exception chaining."""

    def test_catch_specific_then_general(self):
        """Test catching specific exception before general."""
        def raise_api_error():
            raise APIError("test", 400, "Bad request")

        # Should catch as APIError first
        with pytest.raises(APIError):
            raise_api_error()

        # Should also catch as BlueprintSDKError
        try:
            raise_api_error()
        except BlueprintSDKError:
            pass  # Should reach here

    def test_exception_context_preserved(self):
        """Test that exception context is preserved when re-raising."""
        original = ValueError("Original error")

        try:
            try:
                raise original
            except ValueError as e:
                raise NetworkError("test", "wrapped") from e
        except NetworkError as e:
            assert e.__cause__ is original
