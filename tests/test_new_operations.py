"""Tests for new operations: update_metadata, add_worker, remove_worker, get_manager, get_workers."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from sdk import AgentConfig, BlueprintClient, Visibility
from sdk.exceptions import SyncError, ValidationError
from sdk.models import Blueprint


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_client():
    """Create a BlueprintClient with mocked APIs."""
    with patch("sdk.client.AgentAPI") as mock_agent_api, patch(
        "sdk.client.BlueprintAPI"
    ) as mock_blueprint_api:
        client = BlueprintClient(
            agent_api_key="test-key",
            blueprint_bearer_token="test-token",
            organization_id="test-org",
        )

        # Make mocks accessible
        client._agent_api = mock_agent_api.return_value
        client._blueprint_api = mock_blueprint_api.return_value

        yield client


@pytest.fixture
def sample_blueprint_data():
    """Sample blueprint data from API."""
    return {
        "_id": "bp-123",
        "name": "Test Blueprint",
        "description": "Test description",
        "category": "test",
        "tags": ["tag1"],
        "share_type": "private",
        "status": "active",
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "blueprint_data": {
            "manager_agent_id": "mgr-123",
            "nodes": [
                {
                    "id": "mgr-123",
                    "data": {"agent_role": "Manager", "name": "Manager"},
                },
                {
                    "id": "worker-1",
                    "data": {"agent_role": "Worker", "name": "Worker 1"},
                },
                {
                    "id": "worker-2",
                    "data": {"agent_role": "Worker", "name": "Worker 2"},
                },
            ],
            "edges": [],
            "agents": {
                "mgr-123": {
                    "name": "Manager",
                    "agent_role": "Manager",
                    "agent_instructions": "Manager instructions",
                    "managed_agents": [
                        {"id": "worker-1", "name": "Worker 1"},
                        {"id": "worker-2", "name": "Worker 2"},
                    ],
                },
                "worker-1": {
                    "name": "Worker 1",
                    "agent_role": "Worker",
                    "agent_instructions": "Worker 1 instructions",
                },
                "worker-2": {
                    "name": "Worker 2",
                    "agent_role": "Worker",
                    "agent_instructions": "Worker 2 instructions",
                },
            },
        },
    }


# =============================================================================
# Test update_metadata
# =============================================================================


class TestUpdateMetadata:
    """Tests for update_metadata fast path."""

    def test_updates_name_only(self, mock_client, sample_blueprint_data):
        """Should update only name without touching agents."""
        mock_client._blueprint_api.update.return_value = {
            **sample_blueprint_data,
            "name": "New Name",
        }

        result = mock_client.update_metadata("bp-123", name="New Name")

        # Should only call blueprint API, not agent API
        mock_client._blueprint_api.update.assert_called_once_with(
            "bp-123", {"name": "New Name"}
        )
        mock_client._agent_api.get.assert_not_called()
        mock_client._agent_api.update.assert_not_called()

    def test_updates_multiple_fields(self, mock_client, sample_blueprint_data):
        """Should update multiple metadata fields."""
        mock_client._blueprint_api.update.return_value = sample_blueprint_data

        result = mock_client.update_metadata(
            "bp-123",
            name="New Name",
            description="New description",
            tags=["new", "tags"],
            category="new-category",
        )

        call_args = mock_client._blueprint_api.update.call_args[0]
        payload = call_args[1]

        assert payload["name"] == "New Name"
        assert payload["description"] == "New description"
        assert payload["tags"] == ["new", "tags"]
        assert payload["category"] == "new-category"

    def test_updates_visibility(self, mock_client, sample_blueprint_data):
        """Should convert visibility enum to share_type."""
        mock_client._blueprint_api.update.return_value = sample_blueprint_data

        mock_client.update_metadata("bp-123", visibility=Visibility.PUBLIC)

        call_args = mock_client._blueprint_api.update.call_args[0]
        assert call_args[1]["share_type"] == "public"

    def test_no_updates_returns_current(self, mock_client, sample_blueprint_data):
        """Should return current blueprint if no updates provided."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data

        result = mock_client.update_metadata("bp-123")

        mock_client._blueprint_api.get.assert_called_once_with("bp-123")
        mock_client._blueprint_api.update.assert_not_called()


# =============================================================================
# Test add_worker
# =============================================================================


class TestAddWorker:
    """Tests for add_worker incremental operation."""

    def test_adds_worker_successfully(self, mock_client, sample_blueprint_data):
        """Should add a new worker to the blueprint."""
        # Setup mocks
        mock_client._blueprint_api.get.return_value = sample_blueprint_data
        mock_client._agent_api.create.return_value = {"agent_id": "worker-3"}
        mock_client._agent_api.get.side_effect = [
            # First call: get manager
            {
                "name": "Manager",
                "managed_agents": [
                    {"id": "worker-1", "name": "Worker 1"},
                    {"id": "worker-2", "name": "Worker 2"},
                ],
            },
            # Second call: get manager again after update
            {
                "name": "Manager",
                "managed_agents": [
                    {"id": "worker-1", "name": "Worker 1"},
                    {"id": "worker-2", "name": "Worker 2"},
                    {"id": "worker-3", "name": "New Worker"},
                ],
            },
            # Third call: get worker-1
            {"name": "Worker 1", "agent_role": "Worker"},
            # Fourth call: get worker-2
            {"name": "Worker 2", "agent_role": "Worker"},
            # Fifth call: get worker-3
            {"name": "New Worker", "agent_role": "Worker"},
        ]
        mock_client._blueprint_api.update.return_value = sample_blueprint_data

        new_worker = AgentConfig(
            name="New Worker",
            description="A new worker for testing",
            instructions="You are a new worker that helps with tasks.",
            usage_description="Use for new tasks",
        )

        result = mock_client.add_worker("bp-123", new_worker)

        # Verify worker was created
        mock_client._agent_api.create.assert_called_once()

        # Verify manager was updated with new managed_agents
        update_calls = mock_client._agent_api.update.call_args_list
        assert len(update_calls) >= 1

    def test_requires_usage_description(self, mock_client, sample_blueprint_data):
        """Should fail if worker has no usage_description."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data

        worker = AgentConfig(
            name="Bad Worker",
            description="A worker without usage_description",
            instructions="You are a worker.",
        )

        with pytest.raises(ValidationError) as excinfo:
            mock_client.add_worker("bp-123", worker)

        assert "usage_description" in str(excinfo.value)

    def test_rolls_back_on_failure(self, mock_client, sample_blueprint_data):
        """Should delete created worker if blueprint update fails."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data
        mock_client._agent_api.create.return_value = {"agent_id": "worker-3"}
        mock_client._agent_api.get.return_value = {
            "name": "Manager",
            "managed_agents": [],
        }
        mock_client._agent_api.update.side_effect = Exception("Update failed")

        worker = AgentConfig(
            name="New Worker",
            description="A new worker",
            instructions="You are a new worker.",
            usage_description="Use for tasks",
        )

        with pytest.raises(Exception):
            mock_client.add_worker("bp-123", worker)

        # Verify rollback was attempted
        mock_client._agent_api.delete.assert_called_with("worker-3")


# =============================================================================
# Test remove_worker
# =============================================================================


class TestRemoveWorker:
    """Tests for remove_worker incremental operation."""

    def test_removes_worker_successfully(self, mock_client, sample_blueprint_data):
        """Should remove a worker from the blueprint."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data
        mock_client._agent_api.get.side_effect = [
            # First call: get manager
            {
                "name": "Manager",
                "managed_agents": [
                    {"id": "worker-1", "name": "Worker 1"},
                    {"id": "worker-2", "name": "Worker 2"},
                ],
            },
            # Second call: get manager after update
            {
                "name": "Manager",
                "managed_agents": [{"id": "worker-2", "name": "Worker 2"}],
            },
            # Third call: get remaining worker
            {"name": "Worker 2", "agent_role": "Worker"},
        ]
        mock_client._blueprint_api.update.return_value = sample_blueprint_data

        result = mock_client.remove_worker("bp-123", "worker-1")

        # Verify worker was deleted
        mock_client._agent_api.delete.assert_called_with("worker-1")

    def test_cannot_remove_last_worker(self, mock_client):
        """Should fail when trying to remove the last worker."""
        single_worker_bp = {
            "_id": "bp-123",
            "name": "Test",
            "description": "Test",
            "status": "active",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "nodes": [
                    {"id": "mgr-123", "data": {"agent_role": "Manager"}},
                    {"id": "worker-1", "data": {"agent_role": "Worker"}},
                ],
                "edges": [],
                "agents": {},
            },
        }
        mock_client._blueprint_api.get.return_value = single_worker_bp

        with pytest.raises(ValidationError) as excinfo:
            mock_client.remove_worker("bp-123", "worker-1")

        assert "last worker" in str(excinfo.value)

    def test_worker_not_found(self, mock_client, sample_blueprint_data):
        """Should fail if worker ID not found in blueprint."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data

        with pytest.raises(ValidationError) as excinfo:
            mock_client.remove_worker("bp-123", "nonexistent-worker")

        assert "not found" in str(excinfo.value)


# =============================================================================
# Test get_manager
# =============================================================================


class TestGetManager:
    """Tests for get_manager inspection method."""

    def test_always_fetches_from_agent_api(self, mock_client, sample_blueprint_data):
        """Should always fetch from Agent API (blueprint_data.agents may be stale)."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data
        mock_client._agent_api.get.return_value = {"name": "Fresh Manager", "agent_role": "Manager"}

        result = mock_client.get_manager("bp-123")

        # Should always call Agent API for fresh data
        mock_client._agent_api.get.assert_called_once_with("mgr-123")
        assert result["name"] == "Fresh Manager"

    def test_returns_fresh_data(self, mock_client, sample_blueprint_data):
        """Should return fresh data from Agent API."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data
        mock_client._agent_api.get.return_value = {
            "name": "Updated Manager",
            "agent_role": "Manager",
            "agent_instructions": "Updated instructions",
        }

        result = mock_client.get_manager("bp-123")

        assert result["name"] == "Updated Manager"
        assert result["agent_instructions"] == "Updated instructions"

    def test_raises_if_no_manager(self, mock_client):
        """Should raise SyncError if no manager_agent_id."""
        bp_data = {
            "_id": "bp-123",
            "name": "Test",
            "description": "Test",
            "status": "active",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "blueprint_data": {
                "nodes": [],
                "edges": [],
                "agents": {},
            },
        }
        mock_client._blueprint_api.get.return_value = bp_data

        with pytest.raises(SyncError):
            mock_client.get_manager("bp-123")


# =============================================================================
# Test get_workers
# =============================================================================


class TestGetWorkers:
    """Tests for get_workers inspection method."""

    def test_always_fetches_from_agent_api(self, mock_client, sample_blueprint_data):
        """Should always fetch from Agent API (blueprint_data.agents may be stale)."""
        mock_client._blueprint_api.get.return_value = sample_blueprint_data
        mock_client._agent_api.get.side_effect = [
            {"name": "Fresh Worker 1", "agent_role": "Worker"},
            {"name": "Fresh Worker 2", "agent_role": "Worker"},
        ]

        result = mock_client.get_workers("bp-123")

        # Should call Agent API for each worker
        assert mock_client._agent_api.get.call_count == 2
        assert result[0]["name"] == "Fresh Worker 1"
        assert result[1]["name"] == "Fresh Worker 2"

    def test_returns_empty_list_if_no_workers(self, mock_client):
        """Should return empty list if no workers."""
        bp_data = {
            "_id": "bp-123",
            "name": "Test",
            "description": "Test",
            "status": "active",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "nodes": [{"id": "mgr-123", "data": {"agent_role": "Manager"}}],
                "edges": [],
                "agents": {},
            },
        }
        mock_client._blueprint_api.get.return_value = bp_data

        result = mock_client.get_workers("bp-123")

        assert result == []
        mock_client._agent_api.get.assert_not_called()

    def test_returns_fresh_data_for_each_worker(self, mock_client):
        """Should return fresh data from Agent API for each worker."""
        bp_data = {
            "_id": "bp-123",
            "name": "Test",
            "description": "Test",
            "status": "active",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "nodes": [
                    {"id": "mgr-123", "data": {"agent_role": "Manager"}},
                    {"id": "worker-1", "data": {"agent_role": "Worker"}},
                ],
                "edges": [],
                "agents": {},
            },
        }
        mock_client._blueprint_api.get.return_value = bp_data
        mock_client._agent_api.get.return_value = {
            "name": "Updated Worker",
            "agent_role": "Worker",
            "agent_instructions": "Updated instructions",
        }

        result = mock_client.get_workers("bp-123")

        mock_client._agent_api.get.assert_called_once_with("worker-1")
        assert len(result) == 1
        assert result[0]["name"] == "Updated Worker"
