"""Tests for CRUD operation sequences.

Ensures operations happen in the correct order:
- CREATE: workers → manager (with managed_agents) → tree → blueprint
- UPDATE: fetch current → update agents → fetch fresh → rebuild tree → update blueprint
- DELETE: agents FIRST → blueprint

These tests verify the SDK handles the multi-API coordination correctly.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from sdk import AgentConfig, BlueprintClient, BlueprintConfig
from sdk.exceptions import AgentCreationError, BlueprintCreationError


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_agent_api():
    """Mock AgentAPI."""
    with patch("sdk.client.AgentAPI") as mock_cls:
        mock_api = MagicMock()
        mock_cls.return_value = mock_api
        yield mock_api


@pytest.fixture
def mock_blueprint_api():
    """Mock BlueprintAPI."""
    with patch("sdk.client.BlueprintAPI") as mock_cls:
        mock_api = MagicMock()
        mock_cls.return_value = mock_api
        yield mock_api


@pytest.fixture
def valid_config():
    """Create a valid blueprint configuration for testing."""
    return BlueprintConfig(
        name="Test Blueprint",
        description="A test blueprint for unit testing purposes.",
        manager=AgentConfig(
            name="Test Manager",
            description="Manager agent for testing purposes.",
            instructions="You are a test manager agent. Orchestrate workers effectively.",
        ),
        workers=[
            AgentConfig(
                name="Worker Alpha",
                description="First worker agent for testing.",
                instructions="You are worker Alpha. Complete assigned tasks efficiently.",
                usage_description="Use Worker Alpha for task type A operations.",
            ),
            AgentConfig(
                name="Worker Beta",
                description="Second worker agent for testing.",
                instructions="You are worker Beta. Handle specialized operations.",
                usage_description="Use Worker Beta for task type B operations.",
            ),
        ],
    )


@pytest.fixture
def client(mock_agent_api, mock_blueprint_api):
    """Create a BlueprintClient with mocked APIs."""
    return BlueprintClient(
        agent_api_key="test-agent-key",
        blueprint_bearer_token="test-blueprint-token",
        organization_id="org-123",
    )


# =============================================================================
# CREATE Operation Sequence Tests
# =============================================================================


class TestCreateOperationSequence:
    """Tests for the CREATE operation sequence."""

    def test_workers_created_before_manager(self, client, mock_agent_api, mock_blueprint_api, valid_config):
        """Workers MUST be created before manager to get their IDs."""
        # Track creation order
        creation_order = []

        def track_create(payload):
            name = payload.get("name", "unknown")
            creation_order.append(name)
            return {"agent_id": f"id-{len(creation_order)}"}

        mock_agent_api.create.side_effect = track_create
        mock_agent_api.get.return_value = {
            "name": "Test",
            "managed_agents": [],
            "tool_configs": [],
            "features": [],
        }
        mock_blueprint_api.create.return_value = {"_id": "bp-123"}

        client.create(valid_config)

        # Verify order: workers first, then manager
        assert creation_order == ["Worker Alpha", "Worker Beta", "Test Manager"]

    def test_manager_receives_managed_agents_list(self, client, mock_agent_api, mock_blueprint_api, valid_config):
        """Manager must be created with managed_agents containing worker IDs."""
        worker_ids = []

        def create_agent(payload):
            agent_id = f"agent-{len(worker_ids) + 1}"
            if "managed_agents" not in payload or not payload.get("managed_agents"):
                # This is a worker
                worker_ids.append(agent_id)
            return {"agent_id": agent_id}

        mock_agent_api.create.side_effect = create_agent
        mock_agent_api.get.return_value = {
            "name": "Test",
            "managed_agents": [],
            "tool_configs": [],
            "features": [],
        }
        mock_blueprint_api.create.return_value = {"_id": "bp-123"}

        client.create(valid_config)

        # Get the manager creation call (last one)
        calls = mock_agent_api.create.call_args_list
        manager_payload = calls[-1][0][0]

        # Verify managed_agents contains worker IDs
        managed_agents = manager_payload.get("managed_agents", [])
        assert len(managed_agents) == 2
        assert all(ma["id"] in worker_ids for ma in managed_agents)

    def test_blueprint_created_after_all_agents(self, client, mock_agent_api, mock_blueprint_api, valid_config):
        """Blueprint creation must happen AFTER all agents are created."""
        agent_creation_complete = []

        def track_agent_create(payload):
            agent_id = f"agent-{len(agent_creation_complete) + 1}"
            agent_creation_complete.append(agent_id)
            return {"agent_id": agent_id}

        mock_agent_api.create.side_effect = track_agent_create
        mock_agent_api.get.return_value = {
            "name": "Test",
            "managed_agents": [],
            "tool_configs": [],
            "features": [],
        }

        blueprint_call_agent_count = []

        def track_blueprint_create(payload):
            # Record how many agents existed when blueprint was created
            blueprint_call_agent_count.append(len(agent_creation_complete))
            return {"_id": "bp-123"}

        mock_blueprint_api.create.side_effect = track_blueprint_create

        client.create(valid_config)

        # Blueprint was created after all 3 agents
        assert blueprint_call_agent_count[0] == 3

    def test_tree_data_includes_all_agent_ids(self, client, mock_agent_api, mock_blueprint_api, valid_config):
        """Tree data sent to Blueprint API must include all agent IDs."""
        agent_ids = []

        def create_agent(payload):
            agent_id = f"agent-{len(agent_ids) + 1}"
            agent_ids.append(agent_id)
            return {"agent_id": agent_id}

        mock_agent_api.create.side_effect = create_agent
        mock_agent_api.get.return_value = {
            "name": "Test",
            "managed_agents": [],
            "tool_configs": [],
            "features": [],
        }
        mock_blueprint_api.create.return_value = {"_id": "bp-123"}

        client.create(valid_config)

        # Get the blueprint create payload
        bp_payload = mock_blueprint_api.create.call_args[0][0]
        bp_data = bp_payload.get("blueprint_data", {})

        # All agent IDs should be in the agents dict
        agents_dict = bp_data.get("agents", {})
        for agent_id in agent_ids:
            assert agent_id in agents_dict

    def test_manager_agent_id_set_in_blueprint(self, client, mock_agent_api, mock_blueprint_api, valid_config):
        """Blueprint must have manager_agent_id set correctly."""
        agent_ids = []

        def create_agent(payload):
            agent_id = f"agent-{len(agent_ids) + 1}"
            agent_ids.append(agent_id)
            return {"agent_id": agent_id}

        mock_agent_api.create.side_effect = create_agent
        mock_agent_api.get.return_value = {
            "name": "Test",
            "managed_agents": [],
            "tool_configs": [],
            "features": [],
        }
        mock_blueprint_api.create.return_value = {"_id": "bp-123"}

        client.create(valid_config)

        bp_payload = mock_blueprint_api.create.call_args[0][0]
        bp_data = bp_payload.get("blueprint_data", {})

        # Manager is created last (agent-3)
        assert bp_data.get("manager_agent_id") == "agent-3"


class TestCreateRollbackSequence:
    """Tests for rollback behavior during failed CREATE operations."""

    @patch("sdk.client.doctor")
    def test_rollback_deletes_workers_on_manager_failure(
        self, mock_doctor, client, mock_agent_api, mock_blueprint_api, valid_config
    ):
        """If manager creation fails, previously created workers must be deleted."""
        mock_doctor.return_value = MagicMock(valid=True, errors=[], warnings=[])

        created_agents = []
        deleted_agents = []

        def create_agent(payload):
            if len(created_agents) == 2:  # Fail on manager (3rd agent)
                raise Exception("Manager creation failed")
            agent_id = f"agent-{len(created_agents) + 1}"
            created_agents.append(agent_id)
            return {"agent_id": agent_id}

        mock_agent_api.create.side_effect = create_agent
        mock_agent_api.get.return_value = {"name": "Test", "managed_agents": []}
        mock_agent_api.delete.side_effect = lambda aid: deleted_agents.append(aid)

        with pytest.raises(BlueprintCreationError):
            client.create(valid_config)

        # Both workers should have been deleted (rollback)
        assert set(deleted_agents) == {"agent-1", "agent-2"}

    @patch("sdk.client.doctor")
    def test_rollback_deletes_all_agents_on_blueprint_failure(
        self, mock_doctor, client, mock_agent_api, mock_blueprint_api, valid_config
    ):
        """If blueprint creation fails, ALL agents must be deleted."""
        mock_doctor.return_value = MagicMock(valid=True, errors=[], warnings=[])

        created_agents = []
        deleted_agents = []

        def create_agent(payload):
            agent_id = f"agent-{len(created_agents) + 1}"
            created_agents.append(agent_id)
            return {"agent_id": agent_id}

        mock_agent_api.create.side_effect = create_agent
        mock_agent_api.get.return_value = {"name": "Test", "managed_agents": []}
        mock_agent_api.delete.side_effect = lambda aid: deleted_agents.append(aid)

        mock_blueprint_api.create.side_effect = Exception("Blueprint creation failed")

        with pytest.raises(BlueprintCreationError):
            client.create(valid_config)

        # All 3 agents should have been deleted
        assert len(deleted_agents) == 3

    @patch("sdk.client.doctor")
    def test_rollback_order_is_reverse_creation(
        self, mock_doctor, client, mock_agent_api, mock_blueprint_api, valid_config
    ):
        """Rollback should attempt to delete agents (order doesn't matter, but all must be attempted)."""
        mock_doctor.return_value = MagicMock(valid=True, errors=[], warnings=[])

        created_agents = []
        deleted_agents = []

        def create_agent(payload):
            agent_id = f"agent-{len(created_agents) + 1}"
            created_agents.append(agent_id)
            return {"agent_id": agent_id}

        mock_agent_api.create.side_effect = create_agent
        mock_agent_api.get.return_value = {"name": "Test", "managed_agents": []}
        mock_agent_api.delete.side_effect = lambda aid: deleted_agents.append(aid)

        mock_blueprint_api.create.side_effect = Exception("Blueprint creation failed")

        with pytest.raises(BlueprintCreationError):
            client.create(valid_config)

        # All created agents must be in deleted list
        assert set(created_agents) == set(deleted_agents)


# =============================================================================
# UPDATE Operation Sequence Tests
# =============================================================================


class TestUpdateOperationSequence:
    """Tests for the UPDATE operation sequence."""

    def test_fetches_current_blueprint_first(self, client, mock_agent_api, mock_blueprint_api):
        """Update must fetch current blueprint to get manager_id when doing agent updates."""
        mock_blueprint_api.get.return_value = {
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "agents": {},
                "nodes": [],
                "edges": [],
            }
        }
        mock_agent_api.get.return_value = {
            "name": "Manager",
            "managed_agents": [],
            "tool_configs": [],
            "features": [],
        }
        mock_blueprint_api.update.return_value = {
            "_id": "bp-123",
            "blueprint_data": {"manager_agent_id": "mgr-123"},
        }

        from sdk.models import AgentUpdate, BlueprintUpdate

        # Pass manager update to trigger full sync path (smart path detection)
        client.update("bp-123", BlueprintUpdate(manager=AgentUpdate(id="mgr-123")))

        # First call should be to get the current blueprint
        mock_blueprint_api.get.assert_called_once_with("bp-123")

    def test_fetches_fresh_agent_data_for_tree_rebuild(self, client, mock_agent_api, mock_blueprint_api):
        """Update must fetch fresh agent data to rebuild tree when doing agent updates."""
        mock_blueprint_api.get.return_value = {
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "agents": {"mgr-123": {}, "worker-1": {}},
                "nodes": [],
                "edges": [],
            }
        }
        mock_agent_api.get.return_value = {
            "name": "Agent",
            "managed_agents": [{"id": "worker-1", "name": "Worker"}],
            "tool_configs": [],
            "features": [],
        }
        mock_blueprint_api.update.return_value = {
            "_id": "bp-123",
            "blueprint_data": {"manager_agent_id": "mgr-123"},
        }

        from sdk.models import AgentUpdate, BlueprintUpdate

        # Pass manager update to trigger full sync path (smart path detection)
        client.update("bp-123", BlueprintUpdate(manager=AgentUpdate(id="mgr-123")))

        # Should fetch manager and worker data
        get_calls = [call[0][0] for call in mock_agent_api.get.call_args_list]
        assert "mgr-123" in get_calls

    def test_updates_agents_before_blueprint(self, client, mock_agent_api, mock_blueprint_api):
        """Agent updates must happen before blueprint update."""
        operation_order = []

        def track_agent_update(agent_id, payload):
            operation_order.append(f"agent_update:{agent_id}")
            return {"agent_id": agent_id}

        def track_blueprint_update(bp_id, payload):
            operation_order.append(f"blueprint_update:{bp_id}")
            return {"_id": bp_id, "blueprint_data": {"manager_agent_id": "mgr-123"}}

        mock_blueprint_api.get.return_value = {
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "agents": {},
                "nodes": [],
                "edges": [],
            }
        }
        mock_agent_api.get.return_value = {
            "name": "Manager",
            "managed_agents": [],
            "tool_configs": [],
            "features": [],
        }
        mock_agent_api.update.side_effect = track_agent_update
        mock_blueprint_api.update.side_effect = track_blueprint_update

        from sdk.models import AgentUpdate, BlueprintUpdate

        client.update(
            "bp-123",
            BlueprintUpdate(
                manager=AgentUpdate(id="mgr-123", name="Updated Manager"),
            ),
        )

        # Agent update should come before blueprint update
        agent_idx = next(i for i, op in enumerate(operation_order) if op.startswith("agent_update"))
        bp_idx = next(i for i, op in enumerate(operation_order) if op.startswith("blueprint_update"))
        assert agent_idx < bp_idx

    def test_preserves_managed_agents_during_update(self, client, mock_agent_api, mock_blueprint_api):
        """managed_agents MUST be preserved during agent updates."""
        mock_blueprint_api.get.return_value = {
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "agents": {},
                "nodes": [],
                "edges": [],
            }
        }

        # Return managed_agents in get response
        mock_agent_api.get.return_value = {
            "name": "Manager",
            "managed_agents": [
                {"id": "worker-1", "name": "Worker 1"},
                {"id": "worker-2", "name": "Worker 2"},
            ],
            "tool_configs": [],
            "features": [],
        }
        mock_agent_api.update.return_value = {"agent_id": "mgr-123"}
        mock_blueprint_api.update.return_value = {
            "_id": "bp-123",
            "blueprint_data": {"manager_agent_id": "mgr-123"},
        }

        from sdk.models import AgentUpdate, BlueprintUpdate

        client.update(
            "bp-123",
            BlueprintUpdate(manager=AgentUpdate(id="mgr-123", name="Updated Name")),
        )

        # Check that update payload preserves managed_agents
        update_payload = mock_agent_api.update.call_args[0][1]
        assert "managed_agents" in update_payload
        assert len(update_payload["managed_agents"]) == 2


# =============================================================================
# DELETE Operation Sequence Tests
# =============================================================================


class TestDeleteOperationSequence:
    """Tests for the DELETE operation sequence."""

    def test_agents_deleted_before_blueprint(self, client, mock_agent_api, mock_blueprint_api):
        """Agents MUST be deleted BEFORE blueprint."""
        operation_order = []

        def track_agent_delete(agent_id):
            operation_order.append(f"delete_agent:{agent_id}")

        def track_blueprint_delete(bp_id):
            operation_order.append(f"delete_blueprint:{bp_id}")
            return True

        mock_blueprint_api.get.return_value = {
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "agents": {
                    "mgr-123": {"name": "Manager"},
                    "worker-1": {"name": "Worker 1"},
                    "worker-2": {"name": "Worker 2"},
                },
                "nodes": [],
                "edges": [],
            }
        }
        mock_agent_api.delete.side_effect = track_agent_delete
        mock_blueprint_api.delete.side_effect = track_blueprint_delete

        client.delete("bp-123")

        # Find indices
        agent_deletes = [i for i, op in enumerate(operation_order) if op.startswith("delete_agent")]
        bp_delete = next(i for i, op in enumerate(operation_order) if op.startswith("delete_blueprint"))

        # All agent deletes must come before blueprint delete
        assert all(ad < bp_delete for ad in agent_deletes)

    def test_all_agents_deleted(self, client, mock_agent_api, mock_blueprint_api):
        """All agents (manager + workers) must be deleted."""
        deleted_agents = []

        mock_blueprint_api.get.return_value = {
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "agents": {
                    "mgr-123": {"name": "Manager"},
                    "worker-1": {"name": "Worker 1"},
                    "worker-2": {"name": "Worker 2"},
                },
                "nodes": [],
                "edges": [],
            }
        }
        mock_agent_api.delete.side_effect = lambda aid: deleted_agents.append(aid)
        mock_blueprint_api.delete.return_value = True

        client.delete("bp-123")

        # All 3 agents should be deleted
        assert set(deleted_agents) == {"mgr-123", "worker-1", "worker-2"}

    def test_delete_without_agents_option(self, client, mock_agent_api, mock_blueprint_api):
        """delete_agents=False should skip agent deletion."""
        mock_blueprint_api.delete.return_value = True

        client.delete("bp-123", delete_agents=False)

        # Agent API should NOT be called at all
        mock_agent_api.delete.assert_not_called()
        mock_blueprint_api.delete.assert_called_once_with("bp-123")

    def test_continues_blueprint_delete_if_agent_delete_fails(self, client, mock_agent_api, mock_blueprint_api):
        """Blueprint should still be deleted even if some agent deletes fail."""
        mock_blueprint_api.get.return_value = {
            "blueprint_data": {
                "manager_agent_id": "mgr-123",
                "agents": {
                    "mgr-123": {"name": "Manager"},
                    "worker-1": {"name": "Worker 1"},
                },
                "nodes": [],
                "edges": [],
            }
        }

        # First agent delete fails
        mock_agent_api.delete.side_effect = [Exception("Failed"), None]
        mock_blueprint_api.delete.return_value = True

        result = client.delete("bp-123")

        # Blueprint should still be deleted
        assert result is True
        mock_blueprint_api.delete.assert_called_once_with("bp-123")


# =============================================================================
# Agent ID Extraction Tests
# =============================================================================


class TestAgentIdExtraction:
    """Tests for extracting agent IDs from blueprint data."""

    def test_extracts_worker_ids_from_nodes(self, client):
        """Worker IDs should be extracted from nodes with agent_role=Worker."""
        bp_data = {
            "nodes": [
                {"id": "mgr-123", "data": {"agent_role": "Manager"}},
                {"id": "worker-1", "data": {"agent_role": "Worker"}},
                {"id": "worker-2", "data": {"agent_role": "Worker"}},
            ]
        }

        worker_ids = client._extract_worker_ids(bp_data)

        assert set(worker_ids) == {"worker-1", "worker-2"}
        assert "mgr-123" not in worker_ids

    def test_extracts_empty_list_when_no_workers(self, client):
        """Should return empty list if no workers in nodes."""
        bp_data = {
            "nodes": [
                {"id": "mgr-123", "data": {"agent_role": "Manager"}},
            ]
        }

        worker_ids = client._extract_worker_ids(bp_data)

        assert worker_ids == []

    def test_handles_missing_nodes_key(self, client):
        """Should handle blueprint data without nodes key."""
        bp_data = {}

        worker_ids = client._extract_worker_ids(bp_data)

        assert worker_ids == []

    def test_handles_missing_data_in_nodes(self, client):
        """Should handle nodes without data field."""
        bp_data = {
            "nodes": [
                {"id": "node-1"},  # No data field
                {"id": "worker-1", "data": {"agent_role": "Worker"}},
            ]
        }

        worker_ids = client._extract_worker_ids(bp_data)

        assert worker_ids == ["worker-1"]
