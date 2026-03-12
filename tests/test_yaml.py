"""Tests for YAML module (models and loader)."""

import tempfile
from pathlib import Path

import pytest

from sdk.exceptions import ValidationError
from sdk.models import AgentConfig, BlueprintConfig, Visibility
from sdk.yaml import (
    AgentMetadata,
    AgentSpec,
    AgentYAML,
    BlueprintIDs,
    BlueprintLoader,
    BlueprintMetadata,
    BlueprintYAML,
    IDManager,
    YAMLWriter,
    api_response_to_yaml,
    config_to_yaml,
    load_and_convert,
    write_blueprint,
    yaml_to_config,
)
from sdk.yaml.loader import load_agent, load_blueprint


class TestAgentYAML:
    """Tests for AgentYAML model."""

    def test_minimal_agent(self):
        """Test creating agent with minimal fields."""
        agent = AgentYAML(
            metadata=AgentMetadata(
                name="Test Agent",
                description="A test agent",
            ),
            spec=AgentSpec(
                instructions="You are a helpful assistant.",
            ),
        )
        assert agent.metadata.name == "Test Agent"
        assert agent.spec.model == "gpt-4o"  # default
        assert agent.spec.temperature == 0.3  # default
        assert agent.is_worker  # no sub_agents

    def test_full_agent(self):
        """Test creating agent with all fields."""
        agent = AgentYAML(
            apiVersion="lyzr.ai/v1",
            kind="Agent",
            metadata=AgentMetadata(
                name="News Coordinator",
                description="Orchestrates news curation",
            ),
            spec=AgentSpec(
                model="gpt-4o-mini",
                temperature=0.5,
                top_p=0.9,
                response_format="json_object",
                store_messages=False,
                file_output=True,
                role="News Pipeline Orchestrator",
                goal="Coordinate agents to deliver accurate daily news updates",
                context="You work in a news organization.",
                output="JSON format with structured data",
                examples="User: Get news\nAssistant: Here are today's headlines...",
                instructions="You coordinate the news pipeline.",
                usage="Use to coordinate news gathering",
                features=["memory", "reflection"],
            ),
            sub_agents=["query-gen.yaml", "research.yaml"],
        )
        assert agent.metadata.name == "News Coordinator"
        assert agent.spec.model == "gpt-4o-mini"
        assert agent.spec.response_format == "json_object"
        assert agent.is_manager  # has sub_agents
        assert len(agent.sub_agents) == 2

    def test_agent_is_manager_property(self):
        """Test is_manager/is_worker properties."""
        worker = AgentYAML(
            metadata=AgentMetadata(name="Worker", description="A worker"),
            spec=AgentSpec(instructions="Do work"),
            sub_agents=[],
        )
        assert worker.is_worker
        assert not worker.is_manager

        manager = AgentYAML(
            metadata=AgentMetadata(name="Manager", description="A manager"),
            spec=AgentSpec(instructions="Manage"),
            sub_agents=["worker.yaml"],
        )
        assert manager.is_manager
        assert not manager.is_worker


class TestBlueprintYAML:
    """Tests for BlueprintYAML model."""

    def test_minimal_blueprint(self):
        """Test creating blueprint with minimal fields."""
        blueprint = BlueprintYAML(
            metadata=BlueprintMetadata(
                name="Test Blueprint",
                description="A test blueprint",
            ),
            root_agents=["agents/manager.yaml"],
        )
        assert blueprint.metadata.name == "Test Blueprint"
        assert blueprint.metadata.visibility == "private"  # default
        assert blueprint.ids is None

    def test_full_blueprint(self):
        """Test creating blueprint with all fields."""
        blueprint = BlueprintYAML(
            apiVersion="lyzr.ai/v1",
            kind="Blueprint",
            metadata=BlueprintMetadata(
                name="Daily News Agent",
                description="Curates daily news",
                category="marketing",
                tags=["news", "automation"],
                visibility="organization",
                is_template=True,
                shared_with_users=["user-123"],
                shared_with_organizations=["org-456"],
                readme="# Daily News Agent\n\nThis blueprint...",
            ),
            root_agents=["agents/coordinator.yaml"],
            ids=BlueprintIDs(
                blueprint="bp-123",
                agents={"agents/coordinator.yaml": "agent-456"},
            ),
        )
        assert blueprint.metadata.name == "Daily News Agent"
        assert blueprint.metadata.category == "marketing"
        assert blueprint.metadata.visibility == "organization"
        assert blueprint.metadata.is_template is True
        assert blueprint.ids.blueprint == "bp-123"

    def test_blueprint_requires_root_agents(self):
        """Test that root_agents is required."""
        with pytest.raises(Exception):  # Pydantic validation error
            BlueprintYAML(
                metadata=BlueprintMetadata(
                    name="Test",
                    description="Test",
                ),
                root_agents=[],  # Empty not allowed
            )


class TestBlueprintLoader:
    """Tests for BlueprintLoader."""

    def test_load_simple_blueprint(self, tmp_path: Path):
        """Test loading a simple blueprint with one agent."""
        # Create agent file
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()
        agent_file = agent_dir / "manager.yaml"
        agent_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Test Manager
  description: A test manager
spec:
  instructions: You are a test manager.
""")

        # Create blueprint file
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/manager.yaml
""")

        # Load blueprint
        loader = BlueprintLoader()
        blueprint, agents = loader.load(bp_file)

        assert blueprint.metadata.name == "Test Blueprint"
        assert len(agents) == 1
        assert "Test Manager" in str(agents)

    def test_load_blueprint_with_sub_agents(self, tmp_path: Path):
        """Test loading blueprint with nested sub-agents."""
        # Create worker agent
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        worker_file = agents_dir / "worker.yaml"
        worker_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Worker
  description: A worker agent
spec:
  instructions: You are a worker.
  usage: Use for specialized tasks
""")

        # Create manager agent with sub_agents
        manager_file = agents_dir / "manager.yaml"
        manager_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Manager
  description: A manager agent
spec:
  instructions: You coordinate workers.
sub_agents:
  - worker.yaml
""")

        # Create blueprint
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Nested Blueprint
  description: Blueprint with nested agents
root_agents:
  - agents/manager.yaml
""")

        # Load and verify
        loader = BlueprintLoader()
        blueprint, agents = loader.load(bp_file)

        assert len(agents) == 2  # manager + worker

        # Get the manager
        manager_path = str((agents_dir / "manager.yaml").resolve())
        manager = agents[manager_path]
        assert manager.is_manager
        assert len(manager.sub_agents) == 1

    def test_circular_dependency_detection(self, tmp_path: Path):
        """Test that circular dependencies are detected."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Agent A references B
        (agents_dir / "a.yaml").write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Agent A
  description: Agent A
spec:
  instructions: A
sub_agents:
  - b.yaml
""")

        # Agent B references A (circular!)
        (agents_dir / "b.yaml").write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Agent B
  description: Agent B
spec:
  instructions: B
sub_agents:
  - a.yaml
""")

        # Blueprint
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Circular Test
  description: Test circular deps
root_agents:
  - agents/a.yaml
""")

        loader = BlueprintLoader()
        with pytest.raises(ValidationError) as exc_info:
            loader.load(bp_file)
        assert "Circular dependency" in str(exc_info.value.errors)

    def test_missing_agent_file(self, tmp_path: Path):
        """Test error when agent file doesn't exist."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Missing Agent Test
  description: Test missing file
root_agents:
  - agents/nonexistent.yaml
""")

        loader = BlueprintLoader()
        with pytest.raises(ValidationError) as exc_info:
            loader.load(bp_file)
        assert "not found" in str(exc_info.value.errors)

    def test_missing_blueprint_file(self, tmp_path: Path):
        """Test error when blueprint file doesn't exist."""
        loader = BlueprintLoader()
        with pytest.raises(ValidationError) as exc_info:
            loader.load(tmp_path / "nonexistent.yaml")
        assert "not found" in str(exc_info.value.errors)

    def test_invalid_yaml(self, tmp_path: Path):
        """Test error on invalid YAML syntax."""
        bp_file = tmp_path / "invalid.yaml"
        bp_file.write_text("""
this is not valid yaml: [
  unclosed bracket
""")

        loader = BlueprintLoader()
        with pytest.raises(ValidationError) as exc_info:
            loader.load(bp_file)
        assert "Invalid YAML" in str(exc_info.value.errors)

    def test_wrong_kind(self, tmp_path: Path):
        """Test error when kind is wrong."""
        bp_file = tmp_path / "wrong_kind.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Wrong Kind
  description: This is not a blueprint
root_agents: []
""")

        loader = BlueprintLoader()
        with pytest.raises(ValidationError) as exc_info:
            loader.load(bp_file)
        assert "expected 'Blueprint'" in str(exc_info.value.errors)

    def test_get_agent_order(self, tmp_path: Path):
        """Test agent ordering (workers before managers)."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create deep nesting: root -> mid -> leaf
        (agents_dir / "leaf.yaml").write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Leaf
  description: Leaf agent
spec:
  instructions: Leaf
""")

        (agents_dir / "mid.yaml").write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Mid
  description: Mid-level agent
spec:
  instructions: Mid
sub_agents:
  - leaf.yaml
""")

        (agents_dir / "root.yaml").write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Root
  description: Root agent
spec:
  instructions: Root
sub_agents:
  - mid.yaml
""")

        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Order Test
  description: Test agent ordering
root_agents:
  - agents/root.yaml
""")

        loader = BlueprintLoader()
        blueprint, agents = loader.load(bp_file)
        order = loader.get_agent_order()

        # Should be: leaf, mid, root (workers first)
        assert len(order) == 3
        assert "leaf" in order[0]
        assert "root" in order[-1]


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_load_blueprint_function(self, tmp_path: Path):
        """Test load_blueprint convenience function."""
        agent_file = tmp_path / "agent.yaml"
        agent_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Simple Agent
  description: A simple agent
spec:
  instructions: Be helpful
""")

        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Simple Blueprint
  description: A simple blueprint
root_agents:
  - agent.yaml
""")

        blueprint, agents = load_blueprint(bp_file)
        assert blueprint.metadata.name == "Simple Blueprint"
        assert len(agents) == 1

    def test_load_agent_function(self, tmp_path: Path):
        """Test load_agent convenience function."""
        agent_file = tmp_path / "agent.yaml"
        agent_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Standalone Agent
  description: A standalone agent
spec:
  instructions: Work alone
""")

        agent = load_agent(agent_file)
        assert agent.metadata.name == "Standalone Agent"


class TestIDManager:
    """Tests for IDManager."""

    def test_save_and_get_ids(self, tmp_path: Path):
        """Test saving and retrieving IDs."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/manager.yaml
""")

        manager = IDManager(bp_file)

        # Initially no IDs
        assert manager.get_blueprint_id() is None
        assert manager.get_agent_id("agents/manager.yaml") is None
        assert not manager.has_ids()

        # Save IDs
        manager.save_ids(
            blueprint_id="bp-123",
            agent_ids={"agents/manager.yaml": "agent-456"},
        )

        # Verify IDs are saved
        assert manager.get_blueprint_id() == "bp-123"
        assert manager.get_agent_id("agents/manager.yaml") == "agent-456"
        assert manager.has_ids()

        # Verify all agent IDs
        all_ids = manager.get_all_agent_ids()
        assert all_ids == {"agents/manager.yaml": "agent-456"}

    def test_clear_ids(self, tmp_path: Path):
        """Test clearing IDs."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/manager.yaml
ids:
  blueprint: bp-123
  agents:
    agents/manager.yaml: agent-456
""")

        manager = IDManager(bp_file)

        # Initially has IDs
        assert manager.has_ids()
        assert manager.get_blueprint_id() == "bp-123"

        # Clear IDs
        manager.clear_ids()

        # Verify IDs are cleared
        assert not manager.has_ids()
        assert manager.get_blueprint_id() is None

    def test_update_individual_ids(self, tmp_path: Path):
        """Test updating individual IDs."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/manager.yaml
""")

        manager = IDManager(bp_file)

        # Update blueprint ID
        manager.update_blueprint_id("bp-new")
        assert manager.get_blueprint_id() == "bp-new"

        # Update agent ID
        manager.update_agent_id("agents/manager.yaml", "agent-new")
        assert manager.get_agent_id("agents/manager.yaml") == "agent-new"

        # Add another agent ID
        manager.update_agent_id("agents/worker.yaml", "agent-worker")
        assert manager.get_agent_id("agents/worker.yaml") == "agent-worker"

    def test_remove_agent_id(self, tmp_path: Path):
        """Test removing a single agent ID."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/manager.yaml
ids:
  blueprint: bp-123
  agents:
    agents/manager.yaml: agent-456
    agents/worker.yaml: agent-789
""")

        manager = IDManager(bp_file)

        # Remove worker ID
        removed = manager.remove_agent_id("agents/worker.yaml")
        assert removed is True
        assert manager.get_agent_id("agents/worker.yaml") is None
        assert manager.get_agent_id("agents/manager.yaml") == "agent-456"

        # Try to remove non-existent ID
        removed = manager.remove_agent_id("agents/nonexistent.yaml")
        assert removed is False

    def test_comment_preservation(self, tmp_path: Path):
        """Test that comments are preserved during round-trip."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""# Blueprint configuration
apiVersion: lyzr.ai/v1
kind: Blueprint

# Metadata section
metadata:
  name: Test Blueprint  # Blueprint name
  description: A test blueprint

root_agents:
  - agents/manager.yaml
""")

        manager = IDManager(bp_file)

        # Save IDs
        manager.save_ids(
            blueprint_id="bp-123",
            agent_ids={"agents/manager.yaml": "agent-456"},
        )

        # Read file and verify comments are preserved
        content = bp_file.read_text()
        assert "# Blueprint configuration" in content
        assert "# Metadata section" in content
        assert "# Blueprint name" in content

    def test_nonexistent_file(self, tmp_path: Path):
        """Test behavior with nonexistent file."""
        bp_file = tmp_path / "nonexistent.yaml"
        manager = IDManager(bp_file)

        # Should return None/empty for nonexistent file
        assert manager.get_blueprint_id() is None
        assert manager.get_agent_id("agents/manager.yaml") is None
        assert manager.get_all_agent_ids() == {}
        assert not manager.has_ids()

        # clear_ids should not raise on nonexistent file
        manager.clear_ids()

        # save_ids should raise on nonexistent file
        with pytest.raises(FileNotFoundError):
            manager.save_ids("bp-123", {})


class TestYAMLConverter:
    """Tests for YAML ↔ SDK conversion."""

    def test_yaml_to_config(self):
        """Test converting YAML models to BlueprintConfig."""
        # Create YAML models
        manager = AgentYAML(
            metadata=AgentMetadata(name="Manager", description="A manager agent"),
            spec=AgentSpec(
                model="gpt-4o-mini",
                temperature=0.5,
                instructions="You are the manager.",
                role="Pipeline Orchestrator",
                goal="Coordinate agents to deliver accurate results to users",
            ),
            sub_agents=["worker.yaml"],
        )

        worker = AgentYAML(
            metadata=AgentMetadata(name="Worker", description="A worker agent"),
            spec=AgentSpec(
                instructions="You are a worker.",
                usage="Use for specialized tasks",
            ),
        )

        blueprint = BlueprintYAML(
            metadata=BlueprintMetadata(
                name="Test Blueprint",
                description="A test blueprint",
                category="tech",
                tags=["test", "example"],
            ),
            root_agents=["agents/manager.yaml"],
        )

        agents = {
            "agents/manager.yaml": manager,
            "agents/worker.yaml": worker,
        }

        # Convert to config
        config = yaml_to_config(blueprint, agents)

        assert config.name == "Test Blueprint"
        assert config.description == "A test blueprint"
        assert config.category == "tech"
        assert config.tags == ["test", "example"]
        assert config.manager.name == "Manager"
        assert config.manager.model == "gpt-4o-mini"
        assert config.manager.temperature == 0.5
        assert len(config.workers) == 1
        assert config.workers[0].name == "Worker"
        assert config.workers[0].usage_description == "Use for specialized tasks"

    def test_config_to_yaml(self):
        """Test converting BlueprintConfig to YAML models."""
        config = BlueprintConfig(
            name="Test Blueprint",
            description="A test blueprint",
            category="people",
            tags=["hr", "automation"],
            visibility=Visibility.ORGANIZATION,
            manager=AgentConfig(
                name="HR Manager",
                description="Manages HR tasks",
                instructions="You coordinate HR processes.",
                model="gpt-4o",
                temperature=0.3,
            ),
            workers=[
                AgentConfig(
                    name="Recruiter",
                    description="Handles recruiting",
                    instructions="You find candidates.",
                    usage_description="Use for recruitment tasks",
                ),
            ],
        )

        blueprint, agents = config_to_yaml(config)

        assert blueprint.metadata.name == "Test Blueprint"
        assert blueprint.metadata.category == "people"
        assert blueprint.metadata.visibility == "organization"
        assert len(agents) == 2  # manager + 1 worker

        # Check manager has sub_agents
        manager_path = blueprint.root_agents[0]
        manager_yaml = agents[manager_path]
        assert manager_yaml.metadata.name == "HR Manager"
        assert len(manager_yaml.sub_agents) == 1

    def test_api_response_to_yaml(self):
        """Test converting API response to YAML format."""
        blueprint_data = {
            "_id": "bp-123",
            "name": "API Blueprint",
            "description": "From API",
            "category": "sales",
            "tags": ["api", "test"],
            "visibility": "private",
            "is_template": False,
            "blueprint_info": {
                "documentation_data": {
                    "readme_markdown": "# README\nTest blueprint."
                }
            },
        }

        agents = [
            {
                "agent_id": "agent-manager",
                "name": "Sales Manager",
                "description": "Manages sales",
                "template_type": "MANAGER",
                "model": "gpt-4o",
                "temperature": 0.3,
                "system_prompt": "You manage sales.",
                "response_format": {"type": "text"},
            },
            {
                "agent_id": "agent-worker",
                "name": "Sales Rep",
                "description": "Sells products",
                "template_type": "WORKER",
                "model": "gpt-4o-mini",
                "temperature": 0.5,
                "system_prompt": "You sell products.",
                "tool_usage_description": "Use for direct sales",
                "response_format": {"type": "json_object"},
            },
        ]

        blueprint, yaml_agents = api_response_to_yaml(blueprint_data, agents)

        assert blueprint.metadata.name == "API Blueprint"
        assert blueprint.metadata.readme == "# README\nTest blueprint."
        assert blueprint.ids is not None
        assert blueprint.ids.blueprint == "bp-123"
        assert len(yaml_agents) == 2

        # Check manager
        manager_path = blueprint.root_agents[0]
        manager_yaml = yaml_agents[manager_path]
        assert manager_yaml.metadata.name == "Sales Manager"
        assert len(manager_yaml.sub_agents) == 1

    def test_load_and_convert(self, tmp_path: Path):
        """Test load_and_convert convenience function."""
        # Create agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        worker_file = agents_dir / "worker.yaml"
        worker_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Worker
  description: A worker
spec:
  instructions: Do work
  usage: Use for tasks
""")

        manager_file = agents_dir / "manager.yaml"
        manager_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Manager
  description: A manager
spec:
  instructions: Manage work
sub_agents:
  - worker.yaml
""")

        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Full Test
  description: Test load and convert
root_agents:
  - agents/manager.yaml
""")

        # Load and convert
        config = load_and_convert(bp_file)

        assert config.name == "Full Test"
        assert config.manager.name == "Manager"
        assert len(config.workers) == 1
        assert config.workers[0].name == "Worker"


class TestYAMLWriter:
    """Tests for YAML file writer."""

    def test_write_blueprint(self, tmp_path: Path):
        """Test writing blueprint and agents to files."""
        manager = AgentYAML(
            metadata=AgentMetadata(name="Manager", description="A manager"),
            spec=AgentSpec(instructions="Manage"),
            sub_agents=["worker.yaml"],
        )

        worker = AgentYAML(
            metadata=AgentMetadata(name="Worker", description="A worker"),
            spec=AgentSpec(instructions="Work", usage="For tasks"),
        )

        blueprint = BlueprintYAML(
            metadata=BlueprintMetadata(
                name="Writer Test",
                description="Test the writer",
            ),
            root_agents=["agents/manager.yaml"],
        )

        agents = {
            "agents/manager.yaml": manager,
            "agents/worker.yaml": worker,
        }

        # Write files
        bp_path = write_blueprint(tmp_path, blueprint, agents)

        # Verify files exist
        assert bp_path.exists()
        assert (tmp_path / "agents" / "manager.yaml").exists()
        assert (tmp_path / "agents" / "worker.yaml").exists()

        # Verify content can be loaded back
        loader = BlueprintLoader()
        loaded_bp, loaded_agents = loader.load(bp_path)

        assert loaded_bp.metadata.name == "Writer Test"
        assert len(loaded_agents) == 2

    def test_write_agent_standalone(self, tmp_path: Path):
        """Test writing a single agent file."""
        from sdk.yaml import write_agent

        agent = AgentYAML(
            metadata=AgentMetadata(
                name="Standalone",
                description="A standalone agent",
            ),
            spec=AgentSpec(
                model="gpt-4o-mini",
                temperature=0.7,
                instructions="You are standalone.",
            ),
        )

        agent_path = tmp_path / "standalone.yaml"
        result_path = write_agent(agent_path, agent)

        assert result_path.exists()

        # Verify content
        loaded = load_agent(result_path)
        assert loaded.metadata.name == "Standalone"
        assert loaded.spec.model == "gpt-4o-mini"
        assert loaded.spec.temperature == 0.7

    def test_roundtrip_config_to_yaml_to_files(self, tmp_path: Path):
        """Test full roundtrip: Config -> YAML -> Files -> Config."""
        # Start with SDK config
        original_config = BlueprintConfig(
            name="Roundtrip Test",
            description="Test full roundtrip",
            category="data",
            tags=["test"],
            visibility=Visibility.PRIVATE,
            manager=AgentConfig(
                name="Data Manager",
                description="Manages data",
                instructions="You manage data pipelines.",
                model="gpt-4o",
            ),
            workers=[
                AgentConfig(
                    name="Data Analyst",
                    description="Analyzes data",
                    instructions="You analyze data.",
                    usage_description="Use for data analysis",
                    model="gpt-4o-mini",
                ),
            ],
        )

        # Convert to YAML
        blueprint, agents = config_to_yaml(original_config)

        # Write to files
        bp_path = write_blueprint(tmp_path, blueprint, agents)

        # Load back
        final_config = load_and_convert(bp_path)

        # Verify
        assert final_config.name == original_config.name
        assert final_config.description == original_config.description
        assert final_config.category == original_config.category
        assert final_config.manager.name == original_config.manager.name
        assert len(final_config.workers) == len(original_config.workers)
        assert final_config.workers[0].name == original_config.workers[0].name


class TestClientYAMLMethods:
    """Tests for BlueprintClient YAML methods."""

    def test_validate_yaml_valid(self, tmp_path: Path):
        """Test validate_yaml with valid YAML."""
        from unittest.mock import MagicMock, patch

        # Create valid YAML files
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        worker_file = agents_dir / "worker.yaml"
        worker_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Worker Agent
  description: A worker that does tasks
spec:
  instructions: You are a helpful worker.
  usage: Use for specialized tasks
""")

        manager_file = agents_dir / "manager.yaml"
        manager_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Manager Agent
  description: A manager that coordinates
spec:
  instructions: You are the manager coordinating tasks.
sub_agents:
  - worker.yaml
""")

        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint for validation
root_agents:
  - agents/manager.yaml
""")

        # Create mock client
        with patch("sdk.client.AgentAPI"), patch("sdk.client.BlueprintAPI"):
            from sdk import BlueprintClient

            client = BlueprintClient(
                agent_api_key="test-key",
                blueprint_bearer_token="test-token",
                organization_id="test-org",
            )

            # Mock doctor_config to return valid report
            client.doctor_config = MagicMock(
                return_value=MagicMock(valid=True, errors=[], warnings=[])
            )

            report = client.validate_yaml(bp_file)

            assert report.valid is True
            assert len(report.errors) == 0

    def test_validate_yaml_missing_file(self, tmp_path: Path):
        """Test validate_yaml with missing agent file."""
        from unittest.mock import patch

        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/nonexistent.yaml
""")

        with patch("sdk.client.AgentAPI"), patch("sdk.client.BlueprintAPI"):
            from sdk import BlueprintClient

            client = BlueprintClient(
                agent_api_key="test-key",
                blueprint_bearer_token="test-token",
                organization_id="test-org",
            )

            report = client.validate_yaml(bp_file)

            assert report.valid is False
            assert any("not found" in err for err in report.errors)

    def test_validate_yaml_invalid_yaml(self, tmp_path: Path):
        """Test validate_yaml with invalid YAML syntax."""
        from unittest.mock import patch

        bp_file = tmp_path / "invalid.yaml"
        bp_file.write_text("""
this is not valid yaml: [
  unclosed bracket
""")

        with patch("sdk.client.AgentAPI"), patch("sdk.client.BlueprintAPI"):
            from sdk import BlueprintClient

            client = BlueprintClient(
                agent_api_key="test-key",
                blueprint_bearer_token="test-token",
                organization_id="test-org",
            )

            report = client.validate_yaml(bp_file)

            assert report.valid is False
            assert len(report.errors) > 0

    def test_export_to_yaml(self, tmp_path: Path):
        """Test export_to_yaml method."""
        from unittest.mock import MagicMock, patch

        with patch("sdk.client.AgentAPI") as mock_agent_api_class, patch(
            "sdk.client.BlueprintAPI"
        ) as mock_bp_api_class:
            mock_agent_api = MagicMock()
            mock_bp_api = MagicMock()
            mock_agent_api_class.return_value = mock_agent_api
            mock_bp_api_class.return_value = mock_bp_api

            # Mock blueprint data
            mock_bp_api.get.return_value = {
                "_id": "bp-123",
                "name": "Export Test",
                "description": "Test export functionality",
                "category": "tech",
                "tags": ["test"],
                "visibility": "private",
                "blueprint_data": {
                    "manager_agent_id": "agent-manager",
                    "nodes": [
                        {"id": "agent-manager", "data": {"agent_role": "Manager"}},
                        {"id": "agent-worker", "data": {"agent_role": "Worker"}},
                    ],
                    "edges": [
                        {"source": "agent-manager", "target": "agent-worker"}
                    ],
                },
            }

            # Mock agent data
            mock_agent_api.get.side_effect = [
                {
                    "agent_id": "agent-manager",
                    "name": "Manager",
                    "description": "Manages things",
                    "template_type": "MANAGER",
                    "model": "gpt-4o",
                    "temperature": 0.3,
                    "system_prompt": "You are the manager.",
                    "response_format": {"type": "text"},
                },
                {
                    "agent_id": "agent-worker",
                    "name": "Worker",
                    "description": "Does work",
                    "template_type": "WORKER",
                    "model": "gpt-4o-mini",
                    "temperature": 0.5,
                    "system_prompt": "You are a worker.",
                    "tool_usage_description": "Use for tasks",
                    "response_format": {"type": "text"},
                },
            ]

            from sdk import BlueprintClient

            client = BlueprintClient(
                agent_api_key="test-key",
                blueprint_bearer_token="test-token",
                organization_id="test-org",
            )

            output_dir = tmp_path / "exported"
            bp_path = client.export_to_yaml("bp-123", output_dir)

            # Verify files were created
            assert bp_path.exists()
            assert (output_dir / "agents").exists()

            # Verify content can be loaded
            loader = BlueprintLoader()
            loaded_bp, loaded_agents = loader.load(bp_path)

            assert loaded_bp.metadata.name == "Export Test"
            assert len(loaded_agents) == 2
            assert loaded_bp.ids is not None
            assert loaded_bp.ids.blueprint == "bp-123"


class TestEnhancedOrchestration:
    """Tests for enhanced orchestration features (Phase 6.6)."""

    def test_deep_nesting_yaml_to_config(self, tmp_path: Path):
        """Test converting YAML with deep nesting to config."""
        # Create agent files with 3-level hierarchy: manager -> team_lead -> worker
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        worker_file = agents_dir / "worker.yaml"
        worker_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Worker
  description: Leaf worker
spec:
  instructions: I do the actual work.
  usage: Use for specific tasks
""")

        team_lead_file = agents_dir / "team_lead.yaml"
        team_lead_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Team Lead
  description: Manages workers
spec:
  instructions: I coordinate my team.
  usage: Use for team coordination
sub_agents:
  - worker.yaml
""")

        manager_file = agents_dir / "manager.yaml"
        manager_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Manager
  description: Top-level manager
spec:
  instructions: I oversee everything.
sub_agents:
  - team_lead.yaml
""")

        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("""
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Deep Hierarchy Blueprint
  description: Tests 3-level nesting
root_agents:
  - agents/manager.yaml
""")

        # Load and convert
        from sdk.yaml import load_and_convert

        config = load_and_convert(bp_file)

        assert config.name == "Deep Hierarchy Blueprint"
        assert config.manager.name == "Manager"
        assert config.manager.sub_agents is not None
        assert len(config.manager.sub_agents) == 1

        # Check team lead
        team_lead = config.manager.sub_agents[0]
        assert team_lead.name == "Team Lead"
        assert team_lead.sub_agents is not None
        assert len(team_lead.sub_agents) == 1

        # Check worker
        worker = team_lead.sub_agents[0]
        assert worker.name == "Worker"

    def test_config_with_nested_sub_agents_to_yaml(self, tmp_path: Path):
        """Test converting config with nested sub_agents to YAML."""
        from sdk.models import AgentConfig, BlueprintConfig
        from sdk.yaml import config_to_yaml, write_blueprint

        # Create config with nested sub_agents
        worker = AgentConfig(
            name="Deep Worker",
            description="A deeply nested worker",
            instructions="I work at the bottom.",
            usage_description="Use for deep tasks",
        )

        team_lead = AgentConfig(
            name="Team Lead",
            description="Coordinates a team",
            instructions="I manage the team.",
            usage_description="Use for team management",
            sub_agents=[worker],
        )

        manager = AgentConfig(
            name="Top Manager",
            description="Top-level manager",
            instructions="I oversee all teams.",
            sub_agents=[team_lead],
        )

        config = BlueprintConfig(
            name="Nested Blueprint",
            description="Tests nested sub_agents",
            manager=manager,
            workers=[],  # No flat workers, using sub_agents
        )

        # Convert to YAML
        blueprint, agents = config_to_yaml(config)

        # Verify structure
        assert blueprint.metadata.name == "Nested Blueprint"
        assert len(blueprint.root_agents) == 1

        # Should have 3 agents (manager, team_lead, worker)
        assert len(agents) == 3

        # Write and reload
        bp_path = write_blueprint(tmp_path, blueprint, agents)

        from sdk.yaml import load_and_convert

        reloaded = load_and_convert(bp_path)

        assert reloaded.name == "Nested Blueprint"
        assert reloaded.manager.name == "Top Manager"
        assert reloaded.manager.sub_agents is not None
        assert len(reloaded.manager.sub_agents) == 1
        assert reloaded.manager.sub_agents[0].name == "Team Lead"

    def test_tree_builder_recursive(self):
        """Test TreeBuilder.build_recursive for deep hierarchies."""
        from sdk.builders.tree import TreeBuilder

        builder = TreeBuilder()

        # Build hierarchy: root -> [child1, child2] where child1 -> [grandchild]
        root_data = {"name": "Root", "tool_usage_description": None}
        child1_data = {"name": "Child 1", "tool_usage_description": "Child 1 tasks"}
        child2_data = {"name": "Child 2", "tool_usage_description": "Child 2 tasks"}
        grandchild_data = {"name": "Grandchild", "tool_usage_description": "Deep tasks"}

        root_agents = [("root-id", root_data)]
        hierarchy = {
            "root-id": [("child1-id", child1_data), ("child2-id", child2_data)],
            "child1-id": [("grandchild-id", grandchild_data)],
        }

        result = builder.build_recursive(root_agents, hierarchy)

        # Verify structure
        assert result["manager_agent_id"] == "root-id"
        assert len(result["nodes"]) == 4  # root, child1, child2, grandchild
        assert len(result["edges"]) == 3  # root->child1, root->child2, child1->grandchild
        assert len(result["agents"]) == 4

        # Verify nodes at correct levels
        nodes_by_id = {n["id"]: n for n in result["nodes"]}
        assert nodes_by_id["root-id"]["position"]["y"] == 0  # Level 0
        assert nodes_by_id["child1-id"]["position"]["y"] == 300  # Level 1
        assert nodes_by_id["child2-id"]["position"]["y"] == 300  # Level 1
        assert nodes_by_id["grandchild-id"]["position"]["y"] == 600  # Level 2

    def test_tree_builder_circular_dependency_detection(self):
        """Test that TreeBuilder detects circular dependencies."""
        from sdk.builders.tree import TreeBuilder

        builder = TreeBuilder()

        # Create circular: A -> B -> C -> A
        a_data = {"name": "A"}
        b_data = {"name": "B"}
        c_data = {"name": "C"}

        root_agents = [("a-id", a_data)]
        hierarchy = {
            "a-id": [("b-id", b_data)],
            "b-id": [("c-id", c_data)],
            "c-id": [("a-id", a_data)],  # Circular reference back to A
        }

        import pytest

        with pytest.raises(ValueError, match="Circular dependency"):
            builder.build_recursive(root_agents, hierarchy)

    def test_agent_config_with_sub_agents(self):
        """Test AgentConfig model with sub_agents field."""
        from sdk.models import AgentConfig

        # Create nested structure
        leaf = AgentConfig(
            name="Leaf Agent",
            description="A leaf worker",
            instructions="I am a leaf.",
            usage_description="Use for leaf tasks",
        )

        parent = AgentConfig(
            name="Parent Agent",
            description="Has children",
            instructions="I coordinate children.",
            sub_agents=[leaf],
        )

        assert parent.sub_agents is not None
        assert len(parent.sub_agents) == 1
        assert parent.sub_agents[0].name == "Leaf Agent"

        # Can be serialized
        data = parent.model_dump()
        assert "sub_agents" in data
        assert len(data["sub_agents"]) == 1

        # Can be deserialized
        reconstructed = AgentConfig.model_validate(data)
        assert reconstructed.sub_agents is not None
        assert reconstructed.sub_agents[0].name == "Leaf Agent"
