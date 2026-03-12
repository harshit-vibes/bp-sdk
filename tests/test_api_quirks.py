"""Tests for API quirks and schema validation.

The Lyzr API has several quirks that the SDK must handle:
1. NoneType fields that MUST be arrays (clone fails otherwise)
2. String fields that MUST NOT be arrays (examples is a string!)
3. managed_agents must be preserved during updates
4. ReactFlow nodes need specific fields (label, template_type, tool)
5. Field name mappings (role → agent_role, etc.)
6. Blueprint-level iterable fields
"""

import pytest

from sdk.utils.sanitize import (
    BLUEPRINT_ITERABLE_FIELDS,
    ITERABLE_FIELDS,
    STRING_FIELDS,
    sanitize_agent_data,
    sanitize_blueprint_data,
    sanitize_for_update,
    sanitize_node_data,
)
from sdk.utils.validation import (
    GENERIC_ROLE_TERMS,
    MIN_DESCRIPTION_LENGTH,
    MIN_INSTRUCTIONS_LENGTH,
    MIN_INSTRUCTIONS_WORDS,
    doctor,
    validate_agent,
    validate_blueprint,
    validate_blueprint_data,
    validate_content_quality,
)
from sdk.models import AgentConfig, BlueprintConfig


# =============================================================================
# Sanitization: NoneType → Empty List
# =============================================================================


class TestIterableFieldsSanitization:
    """Tests for converting None to empty lists for iterable fields."""

    def test_all_iterable_fields_defined(self):
        """Verify all expected iterable fields are in the list."""
        expected = {
            "managed_agents",
            "a2a_tools",
            "tool_configs",
            "features",
            "tools",
            "files",
            "artifacts",
            "personas",
            "messages",
            "tags",
            "shared_with_users",
            "shared_with_organizations",
            "user_ids",
            "organization_ids",
            "permissions",
            "assets",
        }
        assert set(ITERABLE_FIELDS) == expected

    def test_sanitize_converts_none_to_empty_list(self):
        """None values in iterable fields must become empty lists."""
        data = {
            "name": "Test Agent",
            "managed_agents": None,
            "tool_configs": None,
            "features": None,
        }

        result = sanitize_agent_data(data)

        assert result["managed_agents"] == []
        assert result["tool_configs"] == []
        assert result["features"] == []

    def test_sanitize_preserves_existing_lists(self):
        """Existing lists should not be modified."""
        data = {
            "name": "Test Agent",
            "managed_agents": [{"id": "w1"}],
            "tool_configs": [{"tool": "web_search"}],
            "features": ["memory"],
        }

        result = sanitize_agent_data(data)

        assert result["managed_agents"] == [{"id": "w1"}]
        assert result["tool_configs"] == [{"tool": "web_search"}]
        assert result["features"] == ["memory"]

    def test_sanitize_adds_missing_iterable_fields(self):
        """Missing iterable fields should be added as empty lists."""
        data = {"name": "Test Agent"}

        result = sanitize_agent_data(data)

        for field in ITERABLE_FIELDS:
            assert field in result
            assert result[field] == []

    def test_sanitize_handles_empty_dict(self):
        """Empty dict should return empty dict."""
        assert sanitize_agent_data({}) == {}

    def test_sanitize_handles_none_input(self):
        """None input should return None."""
        assert sanitize_agent_data(None) is None


# =============================================================================
# Sanitization: String Fields
# =============================================================================


class TestStringFieldsSanitization:
    """Tests for ensuring string fields remain strings."""

    def test_all_string_fields_defined(self):
        """Verify all expected string fields are in the list."""
        expected = {
            "examples",
            "agent_role",
            "agent_goal",
            "agent_context",
            "agent_output",
            "tool_usage_description",
        }
        assert set(STRING_FIELDS) == expected

    def test_examples_is_string_not_array(self):
        """examples field MUST be a string, not an array."""
        # This is a common mistake - examples looks like it should be a list
        data = {
            "name": "Test",
            "examples": ["example 1", "example 2"],  # Wrong!
        }

        result = sanitize_agent_data(data)

        # Should be converted to empty string (arrays not allowed)
        assert result["examples"] == ""

    def test_string_fields_preserve_strings(self):
        """String values in string fields should be preserved."""
        data = {
            "name": "Test",
            "examples": "Example 1:\nInput: ...\nOutput: ...",
            "agent_role": "HR Specialist",
            "agent_goal": "Assist with HR tasks",
        }

        result = sanitize_agent_data(data)

        assert result["examples"] == "Example 1:\nInput: ...\nOutput: ..."
        assert result["agent_role"] == "HR Specialist"
        assert result["agent_goal"] == "Assist with HR tasks"

    def test_string_fields_convert_none_to_empty(self):
        """None values in string fields should become empty strings."""
        data = {
            "name": "Test",
            "examples": None,
            "agent_role": None,
        }

        result = sanitize_agent_data(data)

        assert result["examples"] == ""
        assert result["agent_role"] == ""


# =============================================================================
# Sanitization: managed_agents Preservation
# =============================================================================


class TestManagedAgentsPreservation:
    """Tests for preserving managed_agents during updates."""

    def test_managed_agents_preserved_on_update(self):
        """managed_agents must be preserved when updating agent."""
        current = {
            "name": "Manager",
            "managed_agents": [
                {"id": "w1", "name": "Worker 1"},
                {"id": "w2", "name": "Worker 2"},
            ],
        }
        updates = {"name": "Updated Manager"}

        result = sanitize_for_update(current, updates)

        assert result["managed_agents"] == current["managed_agents"]

    def test_managed_agents_not_lost_when_none_in_current(self):
        """managed_agents should be empty list if None in current."""
        current = {
            "name": "Manager",
            "managed_agents": None,
        }
        updates = {"name": "Updated Manager"}

        result = sanitize_for_update(current, updates)

        assert result["managed_agents"] == []

    def test_managed_agents_from_current_overrides_updates(self):
        """If updates doesn't have managed_agents, use current."""
        current = {
            "name": "Manager",
            "managed_agents": [{"id": "w1"}],
        }
        updates = {"name": "New Name"}  # No managed_agents

        result = sanitize_for_update(current, updates)

        # Should have current managed_agents
        assert result["managed_agents"] == [{"id": "w1"}]


# =============================================================================
# Blueprint Data Sanitization
# =============================================================================


class TestBlueprintDataSanitization:
    """Tests for blueprint-level sanitization."""

    def test_blueprint_iterable_fields_defined(self):
        """Verify blueprint-level iterable fields."""
        expected = {
            "tags",
            "shared_with_users",
            "shared_with_organizations",
            "user_ids",
            "organization_ids",
            "permissions",
            "assets",
        }
        assert set(BLUEPRINT_ITERABLE_FIELDS) == expected

    def test_sanitizes_root_level_fields(self):
        """Root-level iterable fields should be sanitized."""
        data = {
            "name": "Test Blueprint",
            "tags": None,
            "shared_with_users": None,
            "permissions": None,
        }

        result = sanitize_blueprint_data(data)

        assert result["tags"] == []
        assert result["shared_with_users"] == []
        assert result["permissions"] == []

    def test_sanitizes_nested_agents(self):
        """Agents within blueprint_data should be sanitized."""
        data = {
            "name": "Test Blueprint",
            "blueprint_data": {
                "agents": {
                    "agent-1": {
                        "name": "Agent",
                        "features": None,
                        "tool_configs": None,
                    }
                },
                "nodes": [],
                "edges": [],
            },
        }

        result = sanitize_blueprint_data(data)

        agent = result["blueprint_data"]["agents"]["agent-1"]
        assert agent["features"] == []
        assert agent["tool_configs"] == []

    def test_sanitizes_node_data(self):
        """Node data should be sanitized."""
        data = {
            "name": "Test Blueprint",
            "blueprint_data": {
                "agents": {},
                "nodes": [
                    {
                        "id": "node-1",
                        "data": {
                            "features": None,
                            "tool_configs": None,
                        },
                    }
                ],
                "edges": [],
            },
        }

        result = sanitize_blueprint_data(data)

        node_data = result["blueprint_data"]["nodes"][0]["data"]
        assert node_data["features"] == []
        assert node_data["tool_configs"] == []


# =============================================================================
# ReactFlow Node Validation
# =============================================================================


class TestReactFlowNodeValidation:
    """Tests for ReactFlow node structure validation."""

    def test_validates_required_node_fields(self):
        """Nodes must have label, template_type, and tool fields."""
        bp_data = {
            "manager_agent_id": "mgr-1",
            "agents": {"mgr-1": {}},
            "nodes": [
                {
                    "id": "mgr-1",
                    "data": {
                        # Missing required fields
                    },
                }
            ],
            "edges": [],
        }

        errors = validate_blueprint_data(bp_data)

        assert any("label" in err for err in errors)
        assert any("template_type" in err for err in errors)
        assert any("tool" in err for err in errors)

    def test_passes_with_all_required_fields(self):
        """Nodes with all required fields should pass validation."""
        bp_data = {
            "manager_agent_id": "mgr-1",
            "agents": {"mgr-1": {"managed_agents": []}},
            "nodes": [
                {
                    "id": "mgr-1",
                    "data": {
                        "label": "Manager",
                        "template_type": "manager",
                        "tool": "orchestrator",
                    },
                }
            ],
            "edges": [],
        }

        errors = validate_blueprint_data(bp_data)

        # Should have no node-related errors
        node_errors = [e for e in errors if "Node" in e]
        assert len(node_errors) == 0

    def test_validates_manager_agent_id_exists(self):
        """manager_agent_id must exist in agents dict."""
        bp_data = {
            "manager_agent_id": "missing-id",
            "agents": {"other-id": {}},
            "nodes": [],
            "edges": [],
        }

        errors = validate_blueprint_data(bp_data)

        assert any("manager_agent_id" in err and "not in agents" in err for err in errors)

    def test_validates_managed_agents_exist(self):
        """All managed_agents must exist in agents dict."""
        bp_data = {
            "manager_agent_id": "mgr-1",
            "agents": {
                "mgr-1": {
                    "managed_agents": [
                        {"id": "worker-1"},  # Exists
                        {"id": "missing-worker"},  # Missing
                    ]
                },
                "worker-1": {},
            },
            "nodes": [],
            "edges": [],
        }

        errors = validate_blueprint_data(bp_data)

        assert any("missing-worker" in err for err in errors)


# =============================================================================
# Field Name Mapping Validation
# =============================================================================


class TestFieldNameMapping:
    """Tests for correct API field names."""

    def test_role_validation_uses_correct_length(self):
        """Role field has specific length requirements (15-80 chars)."""
        from pydantic import ValidationError as PydanticValidationError

        # Too short - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                role="Short role",  # < 15 chars
            )
        assert "15 characters" in str(excinfo.value)

        # Too long - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                role="A" * 81,  # > 80 chars
            )
        assert "80 characters" in str(excinfo.value)

    def test_goal_validation_uses_correct_length(self):
        """Goal field has specific length requirements (50-300 chars)."""
        from pydantic import ValidationError as PydanticValidationError

        # Too short - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                goal="Short goal here",  # < 50 chars
            )
        assert "50 characters" in str(excinfo.value)

        # Too long - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                goal="A" * 301,  # > 300 chars
            )
        assert "300 characters" in str(excinfo.value)

    def test_generic_role_terms_rejected(self):
        """Role should not contain generic terms (validated by Pydantic validator)."""
        from pydantic import ValidationError as PydanticValidationError

        for term in GENERIC_ROLE_TERMS:
            # Need at least 15 chars for role
            padded_role = f"The {term} for this specific task"
            if len(padded_role) < 15:
                padded_role = padded_role + " more text"

            with pytest.raises(PydanticValidationError) as excinfo:
                AgentConfig(
                    name="Test",
                    description="A valid description for testing.",
                    instructions="Valid instructions that are long enough for validation.",
                    role=padded_role,
                )
            assert term in str(excinfo.value).lower(), f"Term '{term}' should be rejected"


# =============================================================================
# Content Quality Validation
# =============================================================================


class TestContentQualityValidation:
    """Tests for README-style content quality validation."""

    def test_description_minimum_length(self):
        """Description must be at least MIN_DESCRIPTION_LENGTH chars."""
        short_desc = AgentConfig(
            name="Test",
            description="Short",  # < 20 chars
            instructions="Valid instructions that are long enough for validation.",
        )

        report = validate_agent(short_desc)
        assert any(f"≥{MIN_DESCRIPTION_LENGTH}" in err for err in report.errors)

    def test_instructions_minimum_length(self):
        """Instructions must be at least MIN_INSTRUCTIONS_LENGTH chars."""
        short_inst = AgentConfig(
            name="Test",
            description="A valid description for testing.",
            instructions="Too short",  # < 50 chars
        )

        report = validate_agent(short_inst)
        assert any(f"≥{MIN_INSTRUCTIONS_LENGTH}" in err for err in report.errors)

    def test_instructions_minimum_words(self):
        """Instructions should have minimum word count."""
        few_words = AgentConfig(
            name="Test",
            description="A valid description for testing.",
            instructions="A" * 60,  # 60 chars but only 1 "word"
        )

        report = validate_agent(few_words)
        assert any(f"≥{MIN_INSTRUCTIONS_WORDS}" in warn for warn in report.warnings)

    def test_placeholder_detection(self):
        """Placeholder text should be detected."""
        placeholders = [
            "TODO: Add real description",
            "FIXME: Update this later",
            "This is a [placeholder] description",
            "Contains {placeholder} text",
            "lorem ipsum dolor sit amet",
        ]

        for placeholder in placeholders:
            errors, _ = validate_content_quality(
                "Test field", placeholder, check_placeholders=True
            )
            assert len(errors) > 0, f"Should detect placeholder: {placeholder}"

    def test_weak_instructions_detection(self):
        """Weak/generic instructions should generate warnings."""
        agent = AgentConfig(
            name="Test",
            description="A valid description for testing.",
            instructions="You are an AI assistant. Be helpful to the user and answer questions.",
        )

        report = validate_agent(agent)
        assert any("generic" in warn.lower() for warn in report.warnings)


# =============================================================================
# Worker-Specific Validation
# =============================================================================


class TestWorkerValidation:
    """Tests for worker-specific validation rules."""

    def test_worker_warns_missing_usage_description(self):
        """Workers should have usage_description for orchestration."""
        worker = AgentConfig(
            name="Test Worker",
            description="A valid description for testing.",
            instructions="Valid instructions that are long enough for validation.",
            # No usage_description
        )

        report = validate_agent(worker, is_worker=True)
        assert any("usage_description" in warn for warn in report.warnings)

    def test_worker_validates_usage_description_content(self):
        """Usage description should not contain placeholders."""
        worker = AgentConfig(
            name="Test Worker",
            description="A valid description for testing.",
            instructions="Valid instructions that are long enough for validation.",
            usage_description="TODO: Add usage description",
        )

        report = validate_agent(worker, is_worker=True)
        assert any("placeholder" in err.lower() for err in report.errors)


# =============================================================================
# Blueprint-Level Validation
# =============================================================================


class TestBlueprintValidation:
    """Tests for blueprint-level validation."""

    def test_single_agent_blueprint_is_valid(self):
        """Blueprint with no workers (single-agent) is now valid."""
        # Single-agent blueprints are supported - no workers required
        config = BlueprintConfig(
            name="Test Blueprint",
            description="A valid description for testing.",
            manager=AgentConfig(
                name="Manager",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
            ),
            workers=[],  # No workers - valid for single_agent pattern
        )

        # Should create successfully
        assert config.name == "Test Blueprint"
        assert len(config.workers) == 0

    def test_validates_tag_count(self):
        """Blueprint cannot have more than 20 tags - validated by Pydantic."""
        from pydantic import ValidationError as PydanticValidationError

        # Pydantic enforces max_length=20 on tags
        with pytest.raises(PydanticValidationError) as exc_info:
            BlueprintConfig(
                name="Test Blueprint",
                description="A valid description for testing.",
                manager=AgentConfig(
                    name="Manager",
                    description="A valid description for testing.",
                    instructions="Valid instructions that are long enough for validation.",
                ),
                workers=[
                    AgentConfig(
                        name="Worker",
                        description="A valid description for testing.",
                        instructions="Valid instructions that are long enough for validation.",
                    )
                ],
                tags=[f"tag-{i}" for i in range(21)],  # 21 tags - Pydantic will reject
            )

        # Should mention tags or length constraint
        assert "tags" in str(exc_info.value).lower() or "20" in str(exc_info.value)

    def test_validates_manager_and_workers(self):
        """Both manager and workers should be validated."""
        config = BlueprintConfig(
            name="Test Blueprint",
            description="A valid description for testing.",
            manager=AgentConfig(
                name="Bad Manager",
                description="Short",  # Invalid
                instructions="Short",  # Invalid
            ),
            workers=[
                AgentConfig(
                    name="Bad Worker",
                    description="Short",  # Invalid
                    instructions="Short",  # Invalid
                )
            ],
        )

        report = doctor(config)

        # Should have errors for both manager and worker
        assert any("Manager:" in err for err in report.errors)
        assert any("Worker" in err for err in report.errors)


# =============================================================================
# Tree Structure Validation
# =============================================================================


class TestTreeStructureValidation:
    """Tests for tree_structure consistency validation."""

    def test_tree_structure_must_match_nodes(self):
        """tree_structure.nodes must match blueprint_data.nodes."""
        bp_data = {
            "manager_agent_id": "mgr-1",
            "agents": {"mgr-1": {"managed_agents": []}},
            "nodes": [{"id": "node-1", "data": {"label": "A", "template_type": "t", "tool": "x"}}],
            "edges": [],
            "tree_structure": {
                "nodes": [{"id": "different-node"}],  # Doesn't match!
                "edges": [],
            },
        }

        errors = validate_blueprint_data(bp_data)

        assert any("tree_structure.nodes" in err for err in errors)

    def test_tree_structure_must_match_edges(self):
        """tree_structure.edges must match blueprint_data.edges."""
        bp_data = {
            "manager_agent_id": "mgr-1",
            "agents": {"mgr-1": {"managed_agents": []}},
            "nodes": [{"id": "mgr-1", "data": {"label": "A", "template_type": "t", "tool": "x"}}],
            "edges": [{"id": "edge-1", "source": "a", "target": "b"}],
            "tree_structure": {
                "nodes": [{"id": "mgr-1", "data": {"label": "A", "template_type": "t", "tool": "x"}}],
                "edges": [{"id": "different-edge"}],  # Doesn't match!
            },
        }

        errors = validate_blueprint_data(bp_data)

        assert any("tree_structure.edges" in err for err in errors)


# =============================================================================
# Feature Validation
# =============================================================================


class TestFeatureValidation:
    """Tests for agent feature validation."""

    def test_valid_features_accepted(self):
        """Valid features should be accepted."""
        valid_features = [
            "memory",
            "voice",
            "context",
            "file_output",
            "image_output",
            "reflection",
            "groundedness",
            "fairness",
            "rai",
            "llm_judge",
        ]

        for feature in valid_features:
            agent = AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                features=[feature],
            )

            report = validate_agent(agent)
            feature_errors = [e for e in report.errors if "feature" in e.lower()]
            assert len(feature_errors) == 0, f"Feature '{feature}' should be valid"

    def test_invalid_features_rejected_by_pydantic(self):
        """Invalid features should be rejected by Pydantic literal validation."""
        from pydantic import ValidationError as PydanticValidationError

        # Pydantic validates features against Literal enum
        with pytest.raises(PydanticValidationError) as exc_info:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                features=["invalid_feature"],  # Not in allowed features
            )

        # Should mention features or the invalid value
        assert "invalid_feature" in str(exc_info.value) or "features" in str(exc_info.value).lower()


# =============================================================================
# Temperature and Top-p Validation
# =============================================================================


class TestParameterValidation:
    """Tests for model parameter validation."""

    def test_temperature_bounds(self):
        """Temperature must be 0.0-1.0 - validated by Pydantic."""
        from pydantic import ValidationError as PydanticValidationError

        # Below minimum - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                temperature=-0.1,
            )
        assert "temperature" in str(excinfo.value).lower()

        # Above maximum - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                temperature=1.5,
            )
        assert "temperature" in str(excinfo.value).lower()

    def test_top_p_bounds(self):
        """Top_p must be 0.0-1.0 - validated by Pydantic."""
        from pydantic import ValidationError as PydanticValidationError

        # Below minimum - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                top_p=-0.1,
            )
        assert "top_p" in str(excinfo.value).lower()

        # Above maximum - Pydantic validates at model creation time
        with pytest.raises(PydanticValidationError) as excinfo:
            AgentConfig(
                name="Test",
                description="A valid description for testing.",
                instructions="Valid instructions that are long enough for validation.",
                top_p=1.5,
            )
        assert "top_p" in str(excinfo.value).lower()
