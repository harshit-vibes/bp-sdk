"""Tests for sdk.builders (PayloadBuilder and TreeBuilder)."""

import pytest

from sdk.builders.payload import PayloadBuilder
from sdk.builders.tree import TreeBuilder
from sdk.models import AgentConfig, BlueprintConfig, Visibility


class TestPayloadBuilderAgentPayload:
    """Tests for PayloadBuilder.build_agent_payload()."""

    def test_minimal_worker_payload(self):
        """Test building minimal worker agent payload."""
        builder = PayloadBuilder()
        config = AgentConfig(
            name="Research Worker",
            description="Performs research tasks",
            instructions="You research topics thoroughly",
            usage_description="Use for research and analysis",
        )

        payload = builder.build_agent_payload(config, is_manager=False)

        assert payload["name"] == "Research Worker"
        assert payload["description"] == "Performs research tasks"
        assert payload["agent_instructions"] == "You research topics thoroughly"
        assert payload["tool_usage_description"] == "Use for research and analysis"
        assert payload["managed_agents"] == []

    def test_minimal_manager_payload(self):
        """Test building minimal manager agent payload."""
        builder = PayloadBuilder()
        config = AgentConfig(
            name="Team Manager",
            description="Manages the team",
            instructions="You coordinate team activities",
        )

        payload = builder.build_agent_payload(config, is_manager=True)

        assert payload["name"] == "Team Manager"
        assert payload["managed_agents"] == []

    def test_manager_with_managed_agents(self):
        """Test manager payload includes managed_agents."""
        builder = PayloadBuilder()
        config = AgentConfig(
            name="Manager",
            description="Manager",
            instructions="Manage workers",
        )
        managed = [
            {"id": "worker_1", "name": "Worker 1", "usage_description": "Does task 1"},
            {"id": "worker_2", "name": "Worker 2", "usage_description": "Does task 2"},
        ]

        payload = builder.build_agent_payload(
            config, is_manager=True, managed_agents=managed
        )

        assert payload["managed_agents"] == managed

    def test_full_agent_payload(self):
        """Test building agent payload with all optional fields."""
        builder = PayloadBuilder()
        config = AgentConfig(
            name="Full Agent",
            description="Fully configured agent",
            instructions="Complete instructions here",
            role="Senior Data Analyst Position",
            goal="Analyze complex datasets and provide actionable insights to stakeholders",
            context="Working in a data science team with access to various databases",
            output_format="Structured JSON with analysis results and recommendations",
            examples="Example: Given sales data, identify top performing regions",
            model="gpt-4o-mini",
            temperature=0.5,
            top_p=0.9,
            features=["memory"],
        )

        payload = builder.build_agent_payload(config, is_manager=False)

        assert payload["agent_role"] == "Senior Data Analyst Position"
        assert "Analyze complex datasets" in payload["agent_goal"]
        assert payload["agent_context"] == "Working in a data science team with access to various databases"
        assert "Structured JSON" in payload["agent_output"]
        assert "sales data" in payload["examples"]
        assert payload["model"] == "gpt-4o-mini"
        assert payload["temperature"] == 0.5
        assert payload["top_p"] == 0.9

    def test_default_model(self):
        """Test default model is set."""
        builder = PayloadBuilder()
        config = AgentConfig(
            name="Agent",
            description="Test",
            instructions="Test",
        )

        payload = builder.build_agent_payload(config, is_manager=False)

        assert payload["model"] == "gpt-4o"

    def test_temperature_default(self):
        """Test default temperature is set."""
        builder = PayloadBuilder()
        config = AgentConfig(
            name="Agent",
            description="Test",
            instructions="Test",
        )

        payload = builder.build_agent_payload(config, is_manager=False)

        assert payload["temperature"] == 0.3


class TestPayloadBuilderManagedAgentsList:
    """Tests for PayloadBuilder.build_managed_agents_list()."""

    def test_build_managed_agents_list(self):
        """Test building managed_agents list from workers."""
        builder = PayloadBuilder()
        workers = [
            AgentConfig(
                name="Worker 1",
                description="First worker",
                instructions="Do task 1",
                usage_description="Use for task 1",
            ),
            AgentConfig(
                name="Worker 2",
                description="Second worker",
                instructions="Do task 2",
                usage_description="Use for task 2",
            ),
        ]
        worker_ids = ["id_1", "id_2"]

        result = builder.build_managed_agents_list(workers, worker_ids)

        assert len(result) == 2
        assert result[0]["id"] == "id_1"
        assert result[0]["name"] == "Worker 1"
        assert result[0]["usage_description"] == "Use for task 1"
        assert result[1]["id"] == "id_2"
        assert result[1]["name"] == "Worker 2"

    def test_missing_usage_description(self):
        """Test default usage_description when not provided."""
        builder = PayloadBuilder()
        workers = [
            AgentConfig(
                name="Worker",
                description="A worker",
                instructions="Work",
            ),
        ]
        worker_ids = ["id_1"]

        result = builder.build_managed_agents_list(workers, worker_ids)

        assert "Use Worker for" in result[0]["usage_description"]


class TestPayloadBuilderBlueprintPayload:
    """Tests for PayloadBuilder.build_blueprint_payload()."""

    def test_minimal_blueprint_payload(self):
        """Test building minimal blueprint payload."""
        builder = PayloadBuilder()
        config = BlueprintConfig(
            name="Test Blueprint",
            description="A test blueprint",
            manager=AgentConfig(
                name="Manager",
                description="Manages",
                instructions="Manage",
            ),
            workers=[
                AgentConfig(
                    name="Worker",
                    description="Works",
                    instructions="Work",
                    usage_description="Use for work",
                ),
            ],
        )
        tree_data = {
            "nodes": [],
            "edges": [],
            "agents": {},
            "tree_structure": {"children": []},
        }

        payload = builder.build_blueprint_payload(
            config=config,
            tree_data=tree_data,
            manager_id="mgr_123",
        )

        assert payload["name"] == "Test Blueprint"
        assert payload["description"] == "A test blueprint"
        assert payload["orchestration_type"] == "Manager Agent"
        assert payload["orchestration_name"] == "Test Blueprint"  # Uses blueprint name
        assert payload["share_type"] == "private"
        assert "blueprint_data" in payload

    def test_blueprint_with_category_and_tags(self):
        """Test blueprint payload with category and tags."""
        builder = PayloadBuilder()
        config = BlueprintConfig(
            name="Tagged Blueprint",
            description="Blueprint with tags",
            category="legal",
            tags=["contract", "compliance"],
            manager=AgentConfig(
                name="Manager",
                description="Manager",
                instructions="Manage",
            ),
            workers=[
                AgentConfig(
                    name="Worker",
                    description="Worker",
                    instructions="Work",
                ),
            ],
        )
        tree_data = {
            "nodes": [],
            "edges": [],
            "agents": {},
            "tree_structure": {"children": []},
        }

        payload = builder.build_blueprint_payload(
            config=config,
            tree_data=tree_data,
            manager_id="mgr_123",
        )

        assert payload["category"] == "legal"
        assert payload["tags"] == ["contract", "compliance"]

    def test_blueprint_visibility(self):
        """Test blueprint payload with custom visibility."""
        builder = PayloadBuilder()
        config = BlueprintConfig(
            name="Public Blueprint",
            description="A public blueprint",
            visibility=Visibility.PUBLIC,
            manager=AgentConfig(name="M", description="M", instructions="M"),
            workers=[AgentConfig(name="W", description="W", instructions="W")],
        )
        tree_data = {
            "nodes": [],
            "edges": [],
            "agents": {},
            "tree_structure": {},
        }

        payload = builder.build_blueprint_payload(config, tree_data, "mgr_123")

        assert payload["share_type"] == "public"


class TestPayloadBuilderUpdatePayload:
    """Tests for PayloadBuilder.build_update_payload()."""

    def test_update_with_new_tree(self):
        """Test update payload includes new tree data."""
        builder = PayloadBuilder()
        current = {
            "_id": "bp_123",
            "name": "Old Name",
            "blueprint_data": {
                "nodes": [],
                "edges": [],
                "agents": {},
                "tree_structure": {},
            },
        }
        new_tree = {
            "nodes": [{"id": "node_1"}],
            "edges": [],
            "agents": {"node_1": {}},
            "tree_structure": {},
        }

        payload = builder.build_update_payload(
            current_blueprint=current,
            new_tree_data=new_tree,
            updates={},
        )

        assert payload["blueprint_data"]["nodes"] == [{"id": "node_1"}]

    def test_update_with_field_changes(self):
        """Test update payload with field updates."""
        builder = PayloadBuilder()
        current = {
            "_id": "bp_123",
            "name": "Old Name",
            "description": "Old desc",
            "blueprint_data": {
                "nodes": [],
                "edges": [],
                "agents": {},
                "tree_structure": {},
            },
        }

        payload = builder.build_update_payload(
            current_blueprint=current,
            new_tree_data={
                "nodes": [],
                "edges": [],
                "agents": {},
                "tree_structure": {},
            },
            updates={"name": "New Name", "description": "New desc"},
        )

        assert payload["name"] == "New Name"
        assert payload["description"] == "New desc"


class TestTreeBuilder:
    """Tests for TreeBuilder."""

    def test_build_single_worker(self):
        """Test building tree with single worker."""
        builder = TreeBuilder()
        manager_data = {
            "_id": "mgr_123",
            "name": "Manager",
            "agent_type": "Manager",
            "agent_description": "Manager desc",
            "managed_agents": [],
        }
        worker_data = {
            "_id": "wkr_456",
            "name": "Worker",
            "agent_type": "Worker",
            "agent_description": "Worker desc",
        }

        result = builder.build(
            manager_data=manager_data,
            workers_data=[worker_data],
            manager_id="mgr_123",
            worker_ids=["wkr_456"],
        )

        # Check structure
        assert "nodes" in result
        assert "edges" in result
        assert "agents" in result

        # Check nodes
        assert len(result["nodes"]) == 2  # Manager + 1 worker
        manager_node = next(n for n in result["nodes"] if n["id"] == "mgr_123")
        worker_node = next(n for n in result["nodes"] if n["id"] == "wkr_456")

        assert manager_node["data"]["agent_role"] == "Manager"
        assert worker_node["data"]["agent_role"] == "Worker"

        # Check edges
        assert len(result["edges"]) == 1
        assert result["edges"][0]["source"] == "mgr_123"
        assert result["edges"][0]["target"] == "wkr_456"

    def test_build_multiple_workers(self):
        """Test building tree with multiple workers."""
        builder = TreeBuilder()
        manager_data = {"_id": "mgr", "name": "Manager", "agent_type": "Manager"}
        workers_data = [
            {"_id": "w1", "name": "Worker 1", "agent_type": "Worker"},
            {"_id": "w2", "name": "Worker 2", "agent_type": "Worker"},
            {"_id": "w3", "name": "Worker 3", "agent_type": "Worker"},
        ]

        result = builder.build(
            manager_data=manager_data,
            workers_data=workers_data,
            manager_id="mgr",
            worker_ids=["w1", "w2", "w3"],
        )

        assert len(result["nodes"]) == 4
        assert len(result["edges"]) == 3

        # All edges should originate from manager
        for edge in result["edges"]:
            assert edge["source"] == "mgr"

    def test_agents_dict_populated(self):
        """Test that agents dict is populated correctly."""
        builder = TreeBuilder()
        manager_data = {"_id": "mgr", "name": "Manager", "model": "gpt-4o"}
        worker_data = {"_id": "wkr", "name": "Worker", "model": "gpt-4o-mini"}

        result = builder.build(
            manager_data=manager_data,
            workers_data=[worker_data],
            manager_id="mgr",
            worker_ids=["wkr"],
        )

        assert "mgr" in result["agents"]
        assert "wkr" in result["agents"]
        assert result["agents"]["mgr"]["name"] == "Manager"
        assert result["agents"]["wkr"]["name"] == "Worker"

    def test_node_positions(self):
        """Test that nodes have position data."""
        builder = TreeBuilder()
        manager_data = {"_id": "mgr", "name": "Manager"}
        worker_data = {"_id": "wkr", "name": "Worker"}

        result = builder.build(
            manager_data=manager_data,
            workers_data=[worker_data],
            manager_id="mgr",
            worker_ids=["wkr"],
        )

        for node in result["nodes"]:
            assert "position" in node
            assert "x" in node["position"]
            assert "y" in node["position"]

    def test_manager_agent_id_set(self):
        """Test that manager_agent_id is set in result."""
        builder = TreeBuilder()
        manager_data = {"_id": "mgr", "name": "Manager"}

        result = builder.build(
            manager_data=manager_data,
            workers_data=[],
            manager_id="mgr",
            worker_ids=[],
        )

        assert result["manager_agent_id"] == "mgr"

    def test_empty_workers(self):
        """Test building tree with no workers (edge case)."""
        builder = TreeBuilder()
        manager_data = {"_id": "mgr", "name": "Solo Manager"}

        result = builder.build(
            manager_data=manager_data,
            workers_data=[],
            manager_id="mgr",
            worker_ids=[],
        )

        assert len(result["nodes"]) == 1
        assert len(result["edges"]) == 0
        assert result["nodes"][0]["id"] == "mgr"
