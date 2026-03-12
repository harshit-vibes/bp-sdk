"""Tests for sdk.models"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from sdk.models import AgentConfig, BlueprintConfig, Visibility, ValidationReport


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_minimal_valid_config(self):
        """Test creating agent with minimal required fields."""
        config = AgentConfig(
            name="Test Agent",
            description="A test agent",
            instructions="You are a test agent",
        )
        assert config.name == "Test Agent"
        assert config.model == "gpt-4o"  # default
        assert config.temperature == 0.3  # default

    def test_full_config(self):
        """Test creating agent with all fields."""
        config = AgentConfig(
            name="Full Agent",
            description="A fully configured agent",
            instructions="Complete instructions for the agent",
            role="Senior Data Analyst",  # 19 chars, valid
            goal="Analyze data patterns and provide insights to stakeholders for decision making",  # 80 chars
            model="gpt-4o-mini",
            temperature=0.7,
            top_p=0.9,
            features=["memory", "reflection"],  # LLM features (tools moved to payload level)
            usage_description="Use for data analysis",
        )
        assert config.role == "Senior Data Analyst"
        assert config.features == ["memory", "reflection"]

    def test_role_too_short(self):
        """Test that role under 15 chars fails."""
        with pytest.raises(PydanticValidationError):
            AgentConfig(
                name="Agent",
                description="Description",
                instructions="Instructions",
                role="Analyst",  # 7 chars, too short
            )

    def test_role_generic_term(self):
        """Test that role with generic term fails."""
        with pytest.raises(PydanticValidationError):
            AgentConfig(
                name="Agent",
                description="Description",
                instructions="Instructions",
                role="Worker that does analysis",  # contains "worker"
            )

    def test_invalid_feature(self):
        """Test that invalid feature fails."""
        with pytest.raises(PydanticValidationError):
            AgentConfig(
                name="Agent",
                description="Description",
                instructions="Instructions",
                features=["invalid_feature"],  # Not in allowed list
            )

    def test_temperature_bounds(self):
        """Test temperature validation."""
        with pytest.raises(PydanticValidationError):
            AgentConfig(
                name="Agent",
                description="Description",
                instructions="Instructions",
                temperature=1.5,  # > 1.0
            )


class TestBlueprintConfig:
    """Tests for BlueprintConfig model."""

    def test_valid_config(self):
        """Test creating valid blueprint config."""
        config = BlueprintConfig(
            name="Test Blueprint",
            description="A test blueprint",
            manager=AgentConfig(
                name="Manager",
                description="Manager description",
                instructions="Manager instructions",
            ),
            workers=[
                AgentConfig(
                    name="Worker",
                    description="Worker description",
                    instructions="Worker instructions",
                    usage_description="Use for tasks",
                ),
            ],
        )
        assert config.name == "Test Blueprint"
        assert len(config.workers) == 1

    def test_no_workers_fails(self):
        """Test that blueprint without workers fails."""
        with pytest.raises(PydanticValidationError):
            BlueprintConfig(
                name="Test Blueprint",
                description="A test blueprint",
                manager=AgentConfig(
                    name="Manager",
                    description="Manager description",
                    instructions="Manager instructions",
                ),
                workers=[],  # Empty!
            )

    def test_too_many_tags(self):
        """Test that too many tags fails."""
        with pytest.raises(PydanticValidationError):
            BlueprintConfig(
                name="Test Blueprint",
                description="A test blueprint",
                manager=AgentConfig(
                    name="Manager",
                    description="Manager description",
                    instructions="Manager instructions",
                ),
                workers=[
                    AgentConfig(
                        name="Worker",
                        description="Worker description",
                        instructions="Worker instructions",
                    ),
                ],
                tags=["tag" + str(i) for i in range(25)],  # 25 tags > 20
            )


class TestValidationReport:
    """Tests for ValidationReport model."""

    def test_valid_report_bool(self):
        """Test that valid report is truthy."""
        report = ValidationReport(valid=True, errors=[], warnings=[])
        assert report
        assert bool(report) is True

    def test_invalid_report_bool(self):
        """Test that invalid report is falsy."""
        report = ValidationReport(valid=False, errors=["Error"], warnings=[])
        assert not report
        assert bool(report) is False

    def test_str_representation(self):
        """Test string representation."""
        report = ValidationReport(
            valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        s = str(report)
        assert "Error 1" in s
        assert "Warning 1" in s
