"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sdk.cli.main import app

runner = CliRunner()


class TestCLIHelp:
    """Tests for CLI help commands."""

    def test_main_help(self):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Blueprint SDK CLI" in result.output
        assert "create" in result.output
        assert "get" in result.output
        assert "list" in result.output
        assert "update" in result.output
        assert "delete" in result.output
        assert "validate" in result.output

    def test_create_help(self):
        """Test create command help."""
        result = runner.invoke(app, ["create", "--help"])
        assert result.exit_code == 0
        assert "Create a new blueprint" in result.output

    def test_get_help(self):
        """Test get command help."""
        result = runner.invoke(app, ["get", "--help"])
        assert result.exit_code == 0
        assert "Fetch a blueprint" in result.output

    def test_list_help(self):
        """Test list command help."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "List all blueprints" in result.output

    def test_update_help(self):
        """Test update command help."""
        result = runner.invoke(app, ["update", "--help"])
        assert result.exit_code == 0
        assert "Update an existing blueprint" in result.output

    def test_delete_help(self):
        """Test delete command help."""
        result = runner.invoke(app, ["delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a blueprint" in result.output

    def test_validate_help(self):
        """Test validate command help."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate a YAML blueprint" in result.output

    def test_version(self):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "bp-sdk version" in result.output


class TestCLIValidate:
    """Tests for validate command."""

    def test_validate_missing_file(self, tmp_path: Path):
        """Test validate with missing file."""
        result = runner.invoke(app, ["validate", str(tmp_path / "nonexistent.yaml")])
        assert result.exit_code == 2  # Typer returns 2 for invalid path

    def test_validate_valid_yaml(self, tmp_path: Path):
        """Test validate with valid YAML."""
        # Create agent file
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        manager_file = agents_dir / "manager.yaml"
        manager_file.write_text(
            """
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Manager Agent
  description: A manager that coordinates tasks
spec:
  instructions: You are the manager coordinating tasks.
"""
        )

        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text(
            """
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/manager.yaml
"""
        )

        # Mock the config and client
        with patch("sdk.cli.commands.validate.load_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.is_valid.return_value = True
            mock_cfg.agent_api_key = "test-key"
            mock_cfg.blueprint_bearer_token = "test-token"
            mock_cfg.organization_id = "test-org"
            mock_cfg.agent_api_url = None
            mock_cfg.blueprint_api_url = None
            mock_config.return_value = mock_cfg

            with patch("sdk.cli.commands.validate.BlueprintClient") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                # Return valid report
                mock_report = MagicMock()
                mock_report.valid = True
                mock_report.errors = []
                mock_report.warnings = []
                mock_instance.validate_yaml.return_value = mock_report

                result = runner.invoke(app, ["validate", str(bp_file)])
                assert result.exit_code == 0
                assert "Validation Passed" in result.output

    def test_validate_invalid_yaml(self, tmp_path: Path):
        """Test validate with invalid YAML structure."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text(
            """
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/nonexistent.yaml
"""
        )

        with patch("sdk.cli.commands.validate.load_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.is_valid.return_value = True
            mock_cfg.agent_api_key = "test-key"
            mock_cfg.blueprint_bearer_token = "test-token"
            mock_cfg.organization_id = "test-org"
            mock_cfg.agent_api_url = None
            mock_cfg.blueprint_api_url = None
            mock_config.return_value = mock_cfg

            with patch("sdk.cli.commands.validate.BlueprintClient") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                # Return invalid report
                mock_report = MagicMock()
                mock_report.valid = False
                mock_report.errors = ["Agent file not found: agents/nonexistent.yaml"]
                mock_report.warnings = []
                mock_instance.validate_yaml.return_value = mock_report

                result = runner.invoke(app, ["validate", str(bp_file)])
                assert result.exit_code == 1
                assert "Validation Failed" in result.output


class TestCLIConfig:
    """Tests for CLI configuration."""

    def test_missing_config(self, tmp_path: Path):
        """Test command with missing configuration."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text(
            """
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Test Blueprint
  description: A test blueprint
root_agents:
  - agents/manager.yaml
"""
        )

        with patch("sdk.cli.commands.validate.load_config") as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.is_valid.return_value = False
            mock_cfg.missing_fields.return_value = ["LYZR_API_KEY", "BLUEPRINT_BEARER_TOKEN"]
            mock_config.return_value = mock_cfg

            result = runner.invoke(app, ["validate", str(bp_file)])
            assert result.exit_code == 1
            assert "Missing required configuration" in result.output


class TestCLIDelete:
    """Tests for delete command."""

    def test_delete_requires_id_or_file(self):
        """Test delete requires either --id or --file."""
        result = runner.invoke(app, ["delete"])
        assert result.exit_code == 1
        assert "Must specify either --id or --file" in result.output

    def test_delete_not_both_id_and_file(self, tmp_path: Path):
        """Test delete rejects both --id and --file."""
        bp_file = tmp_path / "blueprint.yaml"
        bp_file.write_text("dummy")

        result = runner.invoke(app, ["delete", "--id", "bp-123", "--file", str(bp_file)])
        assert result.exit_code == 1
        assert "Cannot specify both" in result.output
