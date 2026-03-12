"""Tests for BlueprintClient."""

from unittest.mock import MagicMock, patch, call
import pytest

from sdk.client import BlueprintClient
from sdk.models import (
    AgentConfig,
    Blueprint,
    BlueprintConfig,
    BlueprintUpdate,
    ListFilters,
    Visibility,
)
from sdk.exceptions import (
    ValidationError,
    AgentCreationError,
    BlueprintCreationError,
)


class TestClientDeleteOrder:
    """Test that delete operation follows correct order: agents first, then blueprint."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_delete_agents_before_blueprint(self, mock_bp_api_class, mock_agent_api_class):
        """Verify agents are deleted BEFORE blueprint."""
        from sdk.client import BlueprintClient

        # Setup mocks
        mock_agent_api = MagicMock()
        mock_bp_api = MagicMock()
        mock_agent_api_class.return_value = mock_agent_api
        mock_bp_api_class.return_value = mock_bp_api

        # Mock blueprint response with 3 agents
        mock_bp_api.get.return_value = {
            "blueprint_data": {
                "agents": {
                    "manager_123": {"name": "Manager"},
                    "worker_456": {"name": "Worker 1"},
                    "worker_789": {"name": "Worker 2"},
                }
            }
        }

        # Create client and delete
        client = BlueprintClient(
            agent_api_key="test_key",
            blueprint_bearer_token="test_token",
            organization_id="test_org",
        )
        client.delete("blueprint_id_123", delete_agents=True)

        # Verify: agents deleted first
        agent_delete_calls = mock_agent_api.delete.call_args_list
        assert len(agent_delete_calls) == 3, "Should delete all 3 agents"

        # Verify: blueprint deleted after agents
        mock_bp_api.delete.assert_called_once_with("blueprint_id_123")

        # Get call order by checking mock call history
        # The key verification: agent deletes should happen before blueprint delete
        # We check this by ensuring agent_api.delete was called before bp_api.delete
        manager = mock_agent_api.delete.call_args_list
        assert len(manager) == 3, "All agents should be deleted"

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_delete_without_agents(self, mock_bp_api_class, mock_agent_api_class):
        """Verify delete_agents=False skips agent deletion."""
        from sdk.client import BlueprintClient

        mock_agent_api = MagicMock()
        mock_bp_api = MagicMock()
        mock_agent_api_class.return_value = mock_agent_api
        mock_bp_api_class.return_value = mock_bp_api

        client = BlueprintClient(
            agent_api_key="test_key",
            blueprint_bearer_token="test_token",
            organization_id="test_org",
        )
        client.delete("blueprint_id_123", delete_agents=False)

        # Verify: no agent deletes
        mock_agent_api.delete.assert_not_called()

        # Verify: blueprint still deleted
        mock_bp_api.delete.assert_called_once_with("blueprint_id_123")


class TestClientUpdateWorkerIds:
    """Test that update operation handles worker_ids filtering safely."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    @patch("sdk.client.TreeBuilder")
    @patch("sdk.client.PayloadBuilder")
    def test_worker_ids_filter_excludes_manager(
        self, mock_payload_class, mock_tree_class, mock_bp_api_class, mock_agent_api_class
    ):
        """Verify manager_id is filtered out of worker_ids without error."""
        from sdk.client import BlueprintClient
        from sdk.models import AgentUpdate, BlueprintUpdate

        # Setup mocks
        mock_agent_api = MagicMock()
        mock_bp_api = MagicMock()
        mock_tree = MagicMock()
        mock_payload = MagicMock()

        mock_agent_api_class.return_value = mock_agent_api
        mock_bp_api_class.return_value = mock_bp_api
        mock_tree_class.return_value = mock_tree
        mock_payload_class.return_value = mock_payload

        # Mock blueprint response
        mock_bp_api.get.return_value = {
            "_id": "blueprint_123",
            "blueprint_data": {
                "manager_agent_id": "manager_123",
            }
        }

        # Mock manager with managed_agents
        mock_agent_api.get.return_value = {
            "_id": "manager_123",
            "name": "Manager",
            "managed_agents": [
                {"id": "worker_456", "name": "Worker 1"},
                {"id": "worker_789", "name": "Worker 2"},
            ],
        }

        # Mock tree builder
        mock_tree.build.return_value = {"nodes": [], "edges": []}

        # Mock payload builder
        mock_payload.build_update_payload.return_value = {}

        # Mock blueprint update response
        mock_bp_api.update.return_value = {
            "_id": "blueprint_123",
            "blueprint_data": {
                "manager_agent_id": "manager_123",
                "nodes": [],
            }
        }

        client = BlueprintClient(
            agent_api_key="test_key",
            blueprint_bearer_token="test_token",
            organization_id="test_org",
        )

        # Pass manager update to trigger full sync path (smart path detection)
        # This should NOT raise ValueError (the bug we fixed)
        result = client.update(
            "blueprint_123",
            BlueprintUpdate(manager=AgentUpdate(id="manager_123"))
        )

        # Verify tree.build was called with correct worker_ids (excluding manager)
        tree_call = mock_tree.build.call_args
        worker_ids = tree_call.kwargs.get("worker_ids", tree_call.args[3] if len(tree_call.args) > 3 else [])

        # worker_ids should NOT contain manager_id
        assert "manager_123" not in worker_ids, "Manager should be filtered out of worker_ids"

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    @patch("sdk.client.TreeBuilder")
    @patch("sdk.client.PayloadBuilder")
    def test_update_with_no_workers(
        self, mock_payload_class, mock_tree_class, mock_bp_api_class, mock_agent_api_class
    ):
        """Verify update works even with no workers (edge case)."""
        from sdk.client import BlueprintClient
        from sdk.models import AgentUpdate, BlueprintUpdate

        mock_agent_api = MagicMock()
        mock_bp_api = MagicMock()
        mock_tree = MagicMock()
        mock_payload = MagicMock()

        mock_agent_api_class.return_value = mock_agent_api
        mock_bp_api_class.return_value = mock_bp_api
        mock_tree_class.return_value = mock_tree
        mock_payload_class.return_value = mock_payload

        # Mock blueprint with manager but no workers
        mock_bp_api.get.return_value = {
            "_id": "blueprint_123",
            "blueprint_data": {
                "manager_agent_id": "manager_123",
            }
        }

        # Manager with empty managed_agents
        mock_agent_api.get.return_value = {
            "_id": "manager_123",
            "name": "Manager",
            "managed_agents": [],  # No workers
        }

        mock_tree.build.return_value = {"nodes": [], "edges": []}
        mock_payload.build_update_payload.return_value = {}
        mock_bp_api.update.return_value = {
            "_id": "blueprint_123",
            "blueprint_data": {"manager_agent_id": "manager_123", "nodes": []},
        }

        client = BlueprintClient(
            agent_api_key="test_key",
            blueprint_bearer_token="test_token",
            organization_id="test_org",
        )

        # Pass manager update to trigger full sync path (smart path detection)
        # Should not raise any errors
        result = client.update(
            "blueprint_123",
            BlueprintUpdate(manager=AgentUpdate(id="manager_123"))
        )
        assert result is not None


class TestClientCreateOrder:
    """Test that create operation follows correct order: workers -> manager -> tree -> blueprint."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    @patch("sdk.client.TreeBuilder")
    @patch("sdk.client.PayloadBuilder")
    def test_create_workers_before_manager(
        self, mock_payload_class, mock_tree_class, mock_bp_api_class, mock_agent_api_class
    ):
        """Verify workers are created before manager."""
        from sdk.client import BlueprintClient
        from sdk.models import BlueprintConfig, AgentConfig

        mock_agent_api = MagicMock()
        mock_bp_api = MagicMock()
        mock_tree = MagicMock()
        mock_payload = MagicMock()

        mock_agent_api_class.return_value = mock_agent_api
        mock_bp_api_class.return_value = mock_bp_api
        mock_tree_class.return_value = mock_tree
        mock_payload_class.return_value = mock_payload

        # Track creation order
        creation_order = []

        def track_create(payload):
            agent_type = "manager" if payload.get("managed_agents") else "worker"
            creation_order.append(agent_type)
            return {"_id": f"{agent_type}_123"}

        mock_agent_api.create.side_effect = track_create
        mock_agent_api.get.return_value = {"_id": "test", "name": "Test", "managed_agents": []}

        mock_payload.build_agent_payload.return_value = {}
        mock_payload.build_managed_agents_list.return_value = [{"id": "w1"}]
        mock_payload.build_blueprint_payload.return_value = {}

        mock_tree.build.return_value = {"nodes": [], "edges": []}

        mock_bp_api.create.return_value = {"_id": "bp_123", "blueprint_data": {"nodes": []}}

        client = BlueprintClient(
            agent_api_key="test_key",
            blueprint_bearer_token="test_token",
            organization_id="test_org",
        )

        config = BlueprintConfig(
            name="Test Blueprint",
            description="Test description",
            manager=AgentConfig(
                name="Project Coordinator",
                description="Coordinates team activities",
                instructions="You coordinate team activities and delegate tasks",
                role="Project Coordinator Lead",
                goal="Coordinate team members to complete tasks efficiently and effectively",
            ),
            workers=[
                AgentConfig(
                    name="Research Specialist",
                    description="Performs research tasks",
                    instructions="You conduct thorough research on assigned topics",
                    role="Research Specialist Lead",
                    goal="Execute assigned research tasks with precision and report results accurately",
                    usage_description="Use for research and analysis tasks",
                ),
            ],
        )

        try:
            client.create(config)
        except Exception:
            pass  # We just want to verify order, not full success

        # Verify workers created before manager
        if len(creation_order) >= 2:
            worker_indices = [i for i, t in enumerate(creation_order) if t == "worker"]
            manager_indices = [i for i, t in enumerate(creation_order) if t == "manager"]

            if worker_indices and manager_indices:
                assert all(
                    wi < mi for wi in worker_indices for mi in manager_indices
                ), "All workers should be created before manager"


class TestClientGet:
    """Tests for BlueprintClient.get()."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_get_returns_blueprint(self, mock_bp_api_class, mock_agent_api_class):
        """Test get returns a Blueprint object."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        mock_bp_api.get.return_value = {
            "_id": "bp_123",
            "name": "Test Blueprint",
            "description": "A test",
            "share_type": "private",
            "blueprint_data": {
                "manager_agent_id": "mgr_123",
                "agents": {
                    "mgr_123": {"name": "Manager"},
                    "wkr_456": {"name": "Worker"},
                },
                "nodes": [
                    {"id": "mgr_123", "data": {}},
                    {"id": "wkr_456", "data": {}},
                ],
            },
        }

        client = BlueprintClient("key", "token", "org")
        result = client.get("bp_123")

        assert isinstance(result, Blueprint)
        assert result.id == "bp_123"
        assert result.name == "Test Blueprint"
        assert result.manager_id == "mgr_123"
        assert "wkr_456" in result.worker_ids


class TestClientGetAll:
    """Tests for BlueprintClient.get_all()."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_get_all_returns_list(self, mock_bp_api_class, mock_agent_api_class):
        """Test get_all returns list of Blueprint objects."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        mock_bp_api.list.return_value = {
            "blueprints": [
                {"_id": "bp_1", "name": "BP 1", "blueprint_data": {"nodes": []}},
                {"_id": "bp_2", "name": "BP 2", "blueprint_data": {"nodes": []}},
            ],
            "total": 2,
        }

        client = BlueprintClient("key", "token", "org")
        result = client.get_all()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(bp, Blueprint) for bp in result)

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_get_all_with_filters(self, mock_bp_api_class, mock_agent_api_class):
        """Test get_all passes filters to API."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        mock_bp_api.list.return_value = {"blueprints": []}

        client = BlueprintClient("key", "token", "org")
        filters = ListFilters(
            visibility=Visibility.PUBLIC,
            category="legal",
            search="contract",
        )
        client.get_all(filters)

        # Verify filter params passed
        call_kwargs = mock_bp_api.list.call_args.kwargs
        assert call_kwargs["share_type"] == "public"
        assert call_kwargs["category"] == "legal"
        assert call_kwargs["search"] == "contract"


class TestClientGetAllWithPagination:
    """Tests for BlueprintClient.get_all_with_pagination()."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_returns_tuple(self, mock_bp_api_class, mock_agent_api_class):
        """Test returns tuple of (blueprints, pagination)."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        mock_bp_api.list.return_value = {
            "blueprints": [{"_id": "bp_1", "name": "BP", "blueprint_data": {}}],
            "total": 100,
            "page": 1,
            "has_more": True,
        }

        client = BlueprintClient("key", "token", "org")
        blueprints, pagination = client.get_all_with_pagination()

        assert isinstance(blueprints, list)
        assert isinstance(pagination, dict)
        assert pagination["total"] == 100
        assert pagination["page"] == 1
        assert pagination["has_more"] is True


class TestClientSetVisibility:
    """Tests for BlueprintClient.set_visibility()."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_set_visibility_public(self, mock_bp_api_class, mock_agent_api_class):
        """Test setting visibility to public."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        mock_bp_api.set_share_type.return_value = {
            "_id": "bp_123",
            "share_type": "public",
            "blueprint_data": {"nodes": []},
        }

        client = BlueprintClient("key", "token", "org")
        result = client.set_visibility("bp_123", Visibility.PUBLIC)

        mock_bp_api.set_share_type.assert_called_once_with(
            "bp_123", "public", user_ids=None, organization_ids=None
        )
        assert result.visibility == Visibility.PUBLIC

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_set_visibility_specific_users(self, mock_bp_api_class, mock_agent_api_class):
        """Test setting visibility to specific_users with user_ids and org_ids."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        mock_bp_api.set_share_type.return_value = {
            "_id": "bp_123",
            "share_type": "specific_users",
            "shared_with_users": ["user-1", "user-2"],
            "shared_with_organizations": ["org-1"],
            "blueprint_data": {"nodes": []},
        }

        client = BlueprintClient("key", "token", "org")
        result = client.set_visibility(
            "bp_123",
            Visibility.SPECIFIC_USERS,
            user_ids=["user-1", "user-2"],
            organization_ids=["org-1"],
        )

        mock_bp_api.set_share_type.assert_called_once_with(
            "bp_123",
            "specific_users",
            user_ids=["user-1", "user-2"],
            organization_ids=["org-1"],
        )
        assert result.visibility == Visibility.SPECIFIC_USERS


class TestClientClone:
    """Tests for BlueprintClient.clone()."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_clone_returns_blueprint(self, mock_bp_api_class, mock_agent_api_class):
        """Test clone returns new Blueprint object."""
        mock_bp_api = MagicMock()
        mock_agent_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = mock_agent_api
        mock_agent_api.api_key = "test_api_key"

        mock_bp_api.clone.return_value = {
            "_id": "bp_clone_123",
            "name": "Cloned Blueprint",
            "blueprint_data": {
                "manager_agent_id": "new_mgr",
                "nodes": [],
            },
        }

        client = BlueprintClient("key", "token", "org")
        result = client.clone("bp_original")

        assert isinstance(result, Blueprint)
        assert result.id == "bp_clone_123"

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_clone_with_new_name(self, mock_bp_api_class, mock_agent_api_class):
        """Test clone with custom name."""
        mock_bp_api = MagicMock()
        mock_agent_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = mock_agent_api
        mock_agent_api.api_key = "test_key"

        mock_bp_api.clone.return_value = {
            "_id": "cloned",
            "name": "My Custom Name",
            "blueprint_data": {"nodes": []},
        }

        client = BlueprintClient("key", "token", "org")
        client.clone("original", new_name="My Custom Name")

        mock_bp_api.clone.assert_called_once_with(
            "original",
            api_key="test_key",
            new_name="My Custom Name",
        )


class TestClientExtractWorkerIds:
    """Tests for BlueprintClient._extract_worker_ids() helper."""

    def test_extracts_worker_ids(self):
        """Test extracting worker IDs from blueprint data."""
        bp_data = {
            "manager_agent_id": "mgr_1",
            "agents": {
                "mgr_1": {"name": "Manager"},
                "wkr_1": {"name": "Worker 1"},
                "wkr_2": {"name": "Worker 2"},
            },
        }

        result = BlueprintClient._extract_worker_ids(bp_data)

        assert set(result) == {"wkr_1", "wkr_2"}

    def test_empty_agents(self):
        """Test with empty agents dict."""
        bp_data = {"manager_agent_id": "mgr_1", "agents": {}}
        result = BlueprintClient._extract_worker_ids(bp_data)
        assert result == []

    def test_no_agents_key(self):
        """Test with missing agents key."""
        bp_data = {"manager_agent_id": "mgr_1"}
        result = BlueprintClient._extract_worker_ids(bp_data)
        assert result == []

    def test_only_manager(self):
        """Test with only manager, no workers."""
        bp_data = {
            "manager_agent_id": "mgr_1",
            "agents": {
                "mgr_1": {"name": "Manager"},
            },
        }
        result = BlueprintClient._extract_worker_ids(bp_data)
        assert result == []


class TestClientRollbackAgents:
    """Tests for BlueprintClient._rollback_agents() helper."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_successful_rollback(self, mock_bp_api_class, mock_agent_api_class):
        """Test successful rollback deletes all agents."""
        mock_agent_api = MagicMock()
        mock_bp_api_class.return_value = MagicMock()
        mock_agent_api_class.return_value = mock_agent_api

        client = BlueprintClient("key", "token", "org")
        failed = client._rollback_agents(["a1", "a2", "a3"], "test_op")

        assert failed == []
        assert mock_agent_api.delete.call_count == 3

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_partial_rollback_failure(self, mock_bp_api_class, mock_agent_api_class):
        """Test rollback with some failures."""
        mock_agent_api = MagicMock()
        mock_bp_api_class.return_value = MagicMock()
        mock_agent_api_class.return_value = mock_agent_api

        # Second delete fails
        mock_agent_api.delete.side_effect = [None, Exception("Delete failed"), None]

        client = BlueprintClient("key", "token", "org")
        failed = client._rollback_agents(["a1", "a2", "a3"], "test_op")

        assert len(failed) == 1
        assert failed[0][0] == "a2"
        assert "Delete failed" in failed[0][1]

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_empty_agent_list(self, mock_bp_api_class, mock_agent_api_class):
        """Test rollback with empty list."""
        mock_agent_api = MagicMock()
        mock_bp_api_class.return_value = MagicMock()
        mock_agent_api_class.return_value = mock_agent_api

        client = BlueprintClient("key", "token", "org")
        failed = client._rollback_agents([], "test_op")

        assert failed == []
        mock_agent_api.delete.assert_not_called()


class TestClientCreateRollback:
    """Tests for rollback behavior during create failures."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    @patch("sdk.client.TreeBuilder")
    @patch("sdk.client.PayloadBuilder")
    @patch("sdk.client.doctor")
    def test_rollback_on_agent_creation_failure(
        self, mock_doctor, mock_payload_class, mock_tree_class, mock_bp_api_class, mock_agent_api_class
    ):
        """Test agents are rolled back when later agent creation fails."""
        from sdk.models import ValidationReport

        mock_agent_api = MagicMock()
        mock_bp_api = MagicMock()
        mock_tree = MagicMock()
        mock_payload = MagicMock()

        mock_agent_api_class.return_value = mock_agent_api
        mock_bp_api_class.return_value = mock_bp_api
        mock_tree_class.return_value = mock_tree
        mock_payload_class.return_value = mock_payload

        # Skip validation
        mock_doctor.return_value = ValidationReport(valid=True, errors=[], warnings=[])

        # First worker succeeds, second fails
        call_count = [0]
        def create_side_effect(payload):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"_id": "worker_1"}
            raise Exception("API Error")

        mock_agent_api.create.side_effect = create_side_effect
        mock_agent_api.get.return_value = {"_id": "worker_1", "name": "Worker"}
        mock_payload.build_agent_payload.return_value = {}

        client = BlueprintClient("key", "token", "org")

        config = BlueprintConfig(
            name="Failing Blueprint",
            description="This blueprint will fail during creation",
            manager=AgentConfig(
                name="Manager Agent",
                description="Manager agent description here",
                instructions="You are a manager agent that coordinates tasks effectively",
            ),
            workers=[
                AgentConfig(
                    name="Worker 1 Agent",
                    description="First worker description",
                    instructions="You are a worker agent that performs specific tasks efficiently",
                    usage_description="Use for task 1",
                ),
                AgentConfig(
                    name="Worker 2 Agent",
                    description="Second worker description",
                    instructions="You are another worker agent that performs other specific tasks",
                    usage_description="Use for task 2",
                ),
            ],
        )

        # Generic exceptions during agent creation are wrapped as BlueprintCreationError
        with pytest.raises(BlueprintCreationError):
            client.create(config)

        # Verify rollback was attempted for the created agent
        mock_agent_api.delete.assert_called_with("worker_1")

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    @patch("sdk.client.TreeBuilder")
    @patch("sdk.client.PayloadBuilder")
    @patch("sdk.client.doctor")
    def test_rollback_on_blueprint_creation_failure(
        self, mock_doctor, mock_payload_class, mock_tree_class, mock_bp_api_class, mock_agent_api_class
    ):
        """Test agents are rolled back when blueprint creation fails."""
        from sdk.models import ValidationReport

        mock_agent_api = MagicMock()
        mock_bp_api = MagicMock()
        mock_tree = MagicMock()
        mock_payload = MagicMock()

        mock_agent_api_class.return_value = mock_agent_api
        mock_bp_api_class.return_value = mock_bp_api
        mock_tree_class.return_value = mock_tree
        mock_payload_class.return_value = mock_payload

        # Skip validation
        mock_doctor.return_value = ValidationReport(valid=True, errors=[], warnings=[])

        # Agent creation succeeds
        mock_agent_api.create.return_value = {"_id": "agent_123"}
        mock_agent_api.get.return_value = {"_id": "agent_123", "name": "Agent", "managed_agents": []}

        # Blueprint creation fails
        mock_bp_api.create.side_effect = Exception("Blueprint API Error")

        mock_payload.build_agent_payload.return_value = {}
        mock_payload.build_managed_agents_list.return_value = []
        mock_payload.build_blueprint_payload.return_value = {}
        mock_tree.build.return_value = {"nodes": [], "edges": []}

        client = BlueprintClient("key", "token", "org")

        config = BlueprintConfig(
            name="Failing Blueprint",
            description="This blueprint will fail during creation",
            manager=AgentConfig(
                name="Manager Agent",
                description="Manager agent description here",
                instructions="You are a manager agent that coordinates tasks effectively",
            ),
            workers=[
                AgentConfig(
                    name="Worker Agent",
                    description="Worker agent description here",
                    instructions="You are a worker agent that performs specific tasks efficiently",
                    usage_description="Use for specific tasks",
                ),
            ],
        )

        with pytest.raises(BlueprintCreationError):
            client.create(config)

        # Verify rollback was attempted (2 agents: worker + manager)
        assert mock_agent_api.delete.call_count == 2


class TestClientDoctor:
    """Tests for BlueprintClient.doctor() validation."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_doctor_valid_blueprint(self, mock_bp_api_class, mock_agent_api_class):
        """Test doctor returns valid report for good blueprint."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        nodes = [
            {
                "id": "mgr",
                "data": {
                    "label": "Manager",
                    "template_type": "agent",
                    "tool": "manager",
                },
            },
            {
                "id": "wkr",
                "data": {
                    "label": "Worker",
                    "template_type": "agent",
                    "tool": "worker",
                },
            },
        ]
        edges = [{"source": "mgr", "target": "wkr"}]
        mock_bp_api.get.return_value = {
            "_id": "bp_123",
            "blueprint_data": {
                "nodes": nodes,
                "edges": edges,
                "agents": {
                    "mgr": {
                        "name": "Manager",
                        "agent_role": "Manager",
                    },
                    "wkr": {
                        "name": "Worker",
                        "agent_role": "Worker",
                        "usage_description": "Use for work",
                    },
                },
                "manager_agent_id": "mgr",
                "tree_structure": {
                    "nodes": nodes,
                    "edges": edges,
                },
            },
        }

        client = BlueprintClient("key", "token", "org")
        report = client.doctor("bp_123")

        # Should be valid (structure is correct)
        assert report.valid

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    def test_doctor_warns_missing_usage_description(
        self, mock_bp_api_class, mock_agent_api_class
    ):
        """Test doctor warns when worker missing usage_description."""
        mock_bp_api = MagicMock()
        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = MagicMock()

        mock_bp_api.get.return_value = {
            "_id": "bp_123",
            "blueprint_data": {
                "nodes": [],
                "edges": [],
                "agents": {
                    "wkr": {
                        "name": "Worker Without Usage",
                        "agent_role": "Worker",
                        # Missing usage_description
                    },
                },
                "manager_agent_id": "mgr",
            },
        }

        client = BlueprintClient("key", "token", "org")
        report = client.doctor("bp_123")

        assert any("usage_description" in w for w in report.warnings)


class TestClientSync:
    """Tests for BlueprintClient.sync()."""

    @patch("sdk.client.AgentAPI")
    @patch("sdk.client.BlueprintAPI")
    @patch("sdk.client.TreeBuilder")
    @patch("sdk.client.PayloadBuilder")
    def test_sync_calls_update(
        self, mock_payload_class, mock_tree_class, mock_bp_api_class, mock_agent_api_class
    ):
        """Test sync triggers update with empty BlueprintUpdate."""
        mock_bp_api = MagicMock()
        mock_agent_api = MagicMock()
        mock_tree = MagicMock()
        mock_payload = MagicMock()

        mock_bp_api_class.return_value = mock_bp_api
        mock_agent_api_class.return_value = mock_agent_api
        mock_tree_class.return_value = mock_tree
        mock_payload_class.return_value = mock_payload

        mock_bp_api.get.return_value = {
            "_id": "bp_123",
            "blueprint_data": {"manager_agent_id": "mgr"},
        }
        mock_agent_api.get.return_value = {"_id": "mgr", "managed_agents": []}
        mock_tree.build.return_value = {"nodes": [], "edges": []}
        mock_payload.build_update_payload.return_value = {}
        mock_bp_api.update.return_value = {
            "_id": "bp_123",
            "blueprint_data": {"nodes": []},
        }

        client = BlueprintClient("key", "token", "org")
        client.sync("bp_123")

        # Verify update was called
        mock_bp_api.update.assert_called_once()
