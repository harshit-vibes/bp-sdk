"""Tests for sdk.utils.sanitize"""

import pytest

from sdk.utils.sanitize import (
    ITERABLE_FIELDS,
    sanitize_agent_data,
    sanitize_blueprint_data,
    sanitize_for_update,
)


class TestSanitizeAgentData:
    """Tests for sanitize_agent_data function."""

    def test_empty_data(self):
        """Test with empty dict."""
        assert sanitize_agent_data({}) == {}

    def test_none_data(self):
        """Test with None."""
        assert sanitize_agent_data(None) is None

    def test_converts_none_to_list(self):
        """Test that None values become empty lists."""
        data = {
            "name": "Agent",
            "managed_agents": None,
            "features": None,
            "tools": None,
        }
        result = sanitize_agent_data(data)
        assert result["managed_agents"] == []
        assert result["features"] == []
        assert result["tools"] == []
        assert result["name"] == "Agent"  # Non-iterable preserved

    def test_preserves_existing_lists(self):
        """Test that existing lists are preserved."""
        data = {
            "managed_agents": [{"id": "123", "name": "Worker"}],
            "features": [{"type": "MEMORY"}],
        }
        result = sanitize_agent_data(data)
        assert result["managed_agents"] == [{"id": "123", "name": "Worker"}]
        assert result["features"] == [{"type": "MEMORY"}]

    def test_adds_missing_fields(self):
        """Test that missing iterable fields are added."""
        data = {"name": "Agent"}
        result = sanitize_agent_data(data)
        for field in ITERABLE_FIELDS:
            assert result[field] == []


class TestSanitizeBlueprintData:
    """Tests for sanitize_blueprint_data function."""

    def test_sanitizes_nested_agents(self):
        """Test that agents dict is sanitized."""
        data = {
            "blueprint_data": {
                "agents": {
                    "agent1": {
                        "name": "Agent 1",
                        "managed_agents": None,
                    }
                }
            }
        }
        result = sanitize_blueprint_data(data)
        assert result["blueprint_data"]["agents"]["agent1"]["managed_agents"] == []

    def test_sanitizes_nodes(self):
        """Test that node data is sanitized."""
        data = {
            "blueprint_data": {
                "agents": {},
                "nodes": [
                    {
                        "id": "agent1",
                        "type": "agent",
                        "data": {
                            "managed_agents": None,
                        }
                    }
                ],
                "edges": [],
            }
        }
        result = sanitize_blueprint_data(data)
        assert result["blueprint_data"]["nodes"][0]["data"]["managed_agents"] == []


class TestSanitizeForUpdate:
    """Tests for sanitize_for_update function."""

    def test_preserves_managed_agents(self):
        """Test that managed_agents is preserved during update."""
        current = {
            "name": "Manager",
            "managed_agents": [{"id": "worker1", "name": "Worker"}],
        }
        updates = {
            "name": "Updated Manager",
        }
        result = sanitize_for_update(current, updates)
        assert result["name"] == "Updated Manager"
        assert result["managed_agents"] == [{"id": "worker1", "name": "Worker"}]

    def test_merges_updates(self):
        """Test that updates are applied."""
        current = {
            "name": "Old Name",
            "description": "Old description",
        }
        updates = {
            "name": "New Name",
            "description": None,  # None values should not overwrite
        }
        result = sanitize_for_update(current, updates)
        assert result["name"] == "New Name"
        assert result["description"] == "Old description"
