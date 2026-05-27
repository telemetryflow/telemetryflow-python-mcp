"""Unit tests for CLI commands."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from tfo_mcp import __version__
from tfo_mcp.main import cli, info, init_config, validate


class TestCLIBasics:
    """Test basic CLI functionality."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test CLI help output."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "TelemetryFlow Python MCP Server" in result.output
        assert "serve" in result.output
        assert "validate" in result.output
        assert "info" in result.output
        assert "init-config" in result.output

    def test_cli_version(self, runner: CliRunner) -> None:
        """Test CLI version output."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output


class TestInfoCommand:
    """Test info command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_info_output(self, runner: CliRunner) -> None:
        """Test info command output."""
        result = runner.invoke(info)

        assert result.exit_code == 0
        assert "TelemetryFlow Python MCP Server" in result.output
        assert __version__ in result.output

    def test_info_shows_builtin_tools(self, runner: CliRunner) -> None:
        """Test info shows built-in tools."""
        result = runner.invoke(info)

        assert result.exit_code == 0
        assert "Built-in Tools:" in result.output
        assert "echo" in result.output
        assert "read_file" in result.output
        assert "write_file" in result.output

    def test_info_shows_builtin_prompts(self, runner: CliRunner) -> None:
        """Test info shows built-in prompts."""
        result = runner.invoke(info)

        assert result.exit_code == 0
        assert "Built-in Prompts:" in result.output
        assert "code_review" in result.output

    def test_info_shows_builtin_resources(self, runner: CliRunner) -> None:
        """Test info shows built-in resources."""
        result = runner.invoke(info)

        assert result.exit_code == 0
        assert "Built-in Resources:" in result.output
        assert "config://server" in result.output


class TestValidateCommand:
    """Test validate command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_validate_default_config(self, runner: CliRunner) -> None:
        """Test validating default configuration."""
        result = runner.invoke(validate)

        assert result.exit_code == 0
        assert "Configuration is valid!" in result.output

    def test_validate_custom_config(self, runner: CliRunner) -> None:
        """Test validating custom configuration file."""
        yaml_content = """
server:
  name: "Custom-MCP"
  version: "2.0.0"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                result = runner.invoke(validate, ["-c", f.name])

                assert result.exit_code == 0
                assert "Configuration is valid!" in result.output
                assert "Custom-MCP" in result.output
            finally:
                Path(f.name).unlink()

    def test_validate_shows_config_details(self, runner: CliRunner) -> None:
        """Test validate shows configuration details."""
        result = runner.invoke(validate)

        assert result.exit_code == 0
        assert "Server:" in result.output
        assert "Transport:" in result.output
        assert "MCP Protocol:" in result.output
        assert "Tools:" in result.output
        assert "Resources:" in result.output
        assert "Prompts:" in result.output

    def test_validate_nonexistent_file(self, runner: CliRunner) -> None:
        """Test validating non-existent config file."""
        result = runner.invoke(validate, ["-c", "/nonexistent/config.yaml"])

        # Should error because file doesn't exist
        assert result.exit_code != 0


class TestInitConfigCommand:
    """Test init-config command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner with isolated filesystem."""
        return CliRunner()

    def test_init_config_creates_file(self, runner: CliRunner) -> None:
        """Test init-config creates configuration file."""
        with runner.isolated_filesystem():
            result = runner.invoke(init_config)

            assert result.exit_code == 0
            assert "Created configuration file" in result.output

            # Verify file was created
            config_path = Path("tfo-mcp.yaml")
            assert config_path.exists()

    def test_init_config_file_contents(self, runner: CliRunner) -> None:
        """Test init-config creates valid configuration."""
        with runner.isolated_filesystem():
            runner.invoke(init_config)

            config_path = Path("tfo-mcp.yaml")
            content = config_path.read_text()

            assert "server:" in content
            assert "claude:" in content
            assert "mcp:" in content
            assert "logging:" in content
            assert "telemetry:" in content

    def test_init_config_wont_overwrite(self, runner: CliRunner) -> None:
        """Test init-config won't overwrite existing file."""
        with runner.isolated_filesystem():
            # Create file first
            Path("tfo-mcp.yaml").write_text("existing content")

            result = runner.invoke(init_config)

            assert result.exit_code == 1
            assert "already exists" in result.output

            # Original content should be preserved
            assert Path("tfo-mcp.yaml").read_text() == "existing content"


class TestServeCommand:
    """Test serve command (without actually running server)."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_serve_help(self, runner: CliRunner) -> None:
        """Test serve command help."""
        result = runner.invoke(cli, ["serve", "--help"])

        assert result.exit_code == 0
        assert "--config" in result.output
        assert "--debug" in result.output

    @mock.patch("tfo_mcp.main.asyncio.run")
    def test_serve_default(self, mock_run: mock.MagicMock, runner: CliRunner) -> None:
        """Test serve with default options."""
        # Mock asyncio.run to prevent actual server start
        mock_run.side_effect = KeyboardInterrupt()

        runner.invoke(cli, ["serve"])

        # Should have been called (even if interrupted)
        mock_run.assert_called_once()

    @mock.patch("tfo_mcp.main.asyncio.run")
    def test_serve_with_debug(self, mock_run: mock.MagicMock, runner: CliRunner) -> None:
        """Test serve with debug flag."""
        mock_run.side_effect = KeyboardInterrupt()

        runner.invoke(cli, ["serve", "--debug"])

        mock_run.assert_called_once()

    @mock.patch("tfo_mcp.main.asyncio.run")
    def test_serve_with_config(self, mock_run: mock.MagicMock, runner: CliRunner) -> None:
        """Test serve with custom config file."""
        yaml_content = """
server:
  name: "Custom-Server"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                mock_run.side_effect = KeyboardInterrupt()

                runner.invoke(cli, ["serve", "-c", f.name])

                mock_run.assert_called_once()
            finally:
                Path(f.name).unlink()


class TestCLIErrorHandling:
    """Test CLI error handling."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_unknown_command(self, runner: CliRunner) -> None:
        """Test unknown command handling."""
        result = runner.invoke(cli, ["unknown-command"])

        assert result.exit_code != 0

    def test_invalid_option(self, runner: CliRunner) -> None:
        """Test invalid option handling."""
        result = runner.invoke(cli, ["serve", "--invalid-option"])

        assert result.exit_code != 0


class TestCLIOutputFormats:
    """Test CLI output formatting."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_info_output_formatting(self, runner: CliRunner) -> None:
        """Test info output is well-formatted."""
        result = runner.invoke(info)

        # Check for consistent formatting
        lines = result.output.split("\n")

        # Should have section headers
        assert any("Built-in Tools:" in line for line in lines)
        assert any("Built-in Prompts:" in line for line in lines)
        assert any("Built-in Resources:" in line for line in lines)

    def test_validate_output_formatting(self, runner: CliRunner) -> None:
        """Test validate output is well-formatted."""
        result = runner.invoke(validate)

        # Should have clear status
        assert "valid" in result.output.lower()

        # Should have indented details
        lines = result.output.split("\n")
        assert any(line.startswith("  ") for line in lines)
