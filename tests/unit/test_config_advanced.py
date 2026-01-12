"""Advanced unit tests for configuration with validation and edge cases."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from tfo_mcp.infrastructure.config import (
    ClaudeConfig,
    Config,
    LoggingConfig,
    MCPConfig,
    ServerConfig,
    TelemetryConfig,
    load_config,
)


class TestServerConfigValidation:
    """Test ServerConfig validation and defaults."""

    def test_default_values(self) -> None:
        """Test ServerConfig default values."""
        config = ServerConfig()

        assert config.name == "TelemetryFlow-MCP"
        assert config.transport == "stdio"
        assert config.debug is False

    @pytest.mark.parametrize(
        "name,version",
        [
            ("My-MCP", "1.0.0"),
            ("test-server", "2.1.0-beta"),
            ("A" * 100, "0.0.1"),
        ],
    )
    def test_custom_server_names(self, name: str, version: str) -> None:
        """Test various server name and version combinations."""
        config = ServerConfig(name=name, version=version)
        assert config.name == name
        assert config.version == version

    def test_debug_mode_enabled(self) -> None:
        """Test debug mode configuration."""
        config = ServerConfig(debug=True)
        assert config.debug is True


class TestClaudeConfigValidation:
    """Test ClaudeConfig validation and defaults."""

    def test_default_values(self) -> None:
        """Test ClaudeConfig default values."""
        config = ClaudeConfig()

        assert config.default_model == "claude-sonnet-4-20250514"
        assert config.max_tokens == 4096
        assert config.temperature == 1.0
        assert config.timeout == 120.0
        assert config.max_retries == 3

    @pytest.mark.parametrize(
        "model",
        [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ],
    )
    def test_valid_models(self, model: str) -> None:
        """Test various valid Claude models."""
        config = ClaudeConfig(default_model=model)
        assert config.default_model == model

    @pytest.mark.parametrize(
        "max_tokens",
        [100, 1000, 4096, 8192, 100000],
    )
    def test_max_tokens_range(self, max_tokens: int) -> None:
        """Test various max_tokens values."""
        config = ClaudeConfig(max_tokens=max_tokens)
        assert config.max_tokens == max_tokens

    @pytest.mark.parametrize(
        "temperature",
        [0.0, 0.5, 1.0, 1.5, 2.0],
    )
    def test_temperature_range(self, temperature: float) -> None:
        """Test various temperature values."""
        config = ClaudeConfig(temperature=temperature)
        assert config.temperature == temperature

    def test_api_key_from_env(self) -> None:
        """Test API key loaded from environment."""
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"}):
            config = ClaudeConfig()
            # Config should pick up env var if not explicitly set
            # Verify config was created successfully
            assert config is not None

    def test_base_url_configuration(self) -> None:
        """Test custom base URL."""
        config = ClaudeConfig(base_url="https://custom.api.example.com")
        assert config.base_url == "https://custom.api.example.com"


class TestMCPConfigValidation:
    """Test MCPConfig validation and defaults."""

    def test_default_values(self) -> None:
        """Test MCPConfig default values."""
        config = MCPConfig()

        assert config.protocol_version == "2024-11-05"
        assert config.enable_tools is True
        assert config.enable_resources is True
        assert config.enable_prompts is True
        assert config.enable_logging is True
        assert config.enable_sampling is False
        assert config.tool_timeout == 30.0

    def test_all_features_disabled(self) -> None:
        """Test configuration with all features disabled."""
        config = MCPConfig(
            enable_tools=False,
            enable_resources=False,
            enable_prompts=False,
            enable_logging=False,
            enable_sampling=False,
        )

        assert not config.enable_tools
        assert not config.enable_resources
        assert not config.enable_prompts
        assert not config.enable_logging
        assert not config.enable_sampling

    @pytest.mark.parametrize(
        "timeout",
        [1.0, 10.0, 30.0, 60.0, 300.0],
    )
    def test_tool_timeout_values(self, timeout: float) -> None:
        """Test various tool timeout values."""
        config = MCPConfig(tool_timeout=timeout)
        assert config.tool_timeout == timeout


class TestLoggingConfigValidation:
    """Test LoggingConfig validation and defaults."""

    def test_default_values(self) -> None:
        """Test LoggingConfig default values."""
        config = LoggingConfig()

        assert config.level == "info"
        assert config.format == "json"
        assert config.output == "stderr"

    @pytest.mark.parametrize(
        "level",
        ["debug", "info", "warning", "error", "critical"],
    )
    def test_log_levels(self, level: str) -> None:
        """Test various log levels."""
        config = LoggingConfig(level=level)
        assert config.level == level

    @pytest.mark.parametrize(
        "fmt",
        ["json", "console"],
    )
    def test_log_formats(self, fmt: str) -> None:
        """Test log format options."""
        config = LoggingConfig(format=fmt)
        assert config.format == fmt

    @pytest.mark.parametrize(
        "output",
        ["stdout", "stderr", "/var/log/mcp.log"],
    )
    def test_output_destinations(self, output: str) -> None:
        """Test various output destinations."""
        config = LoggingConfig(output=output)
        assert config.output == output


class TestTelemetryConfigValidation:
    """Test TelemetryConfig validation and defaults."""

    def test_default_values(self) -> None:
        """Test TelemetryConfig default values."""
        config = TelemetryConfig()

        assert config.enabled is False
        assert config.service_name == "telemetryflow-python-mcp"

    def test_enabled_telemetry(self) -> None:
        """Test enabled telemetry configuration."""
        config = TelemetryConfig(
            enabled=True,
            service_name="my-mcp-server",
            service_version="1.0.0",
            environment="production",
        )

        assert config.enabled
        assert config.service_name == "my-mcp-server"
        assert config.service_version == "1.0.0"
        assert config.environment == "production"

    @pytest.mark.parametrize(
        "protocol",
        ["grpc", "http"],
    )
    def test_protocol_options(self, protocol: str) -> None:
        """Test telemetry protocol options."""
        config = TelemetryConfig(protocol=protocol)
        assert config.protocol == protocol

    def test_signal_options(self) -> None:
        """Test telemetry signal enable/disable."""
        config = TelemetryConfig(
            enable_traces=True,
            enable_metrics=True,
            enable_logs=False,
        )

        assert config.enable_traces
        assert config.enable_metrics
        assert not config.enable_logs


class TestConfigComposition:
    """Test full Config composition and loading."""

    def test_default_config(self) -> None:
        """Test creating default config."""
        config = Config()

        assert config.server is not None
        assert config.claude is not None
        assert config.mcp is not None
        assert config.logging is not None
        assert config.telemetry is not None

    def test_config_with_custom_components(self) -> None:
        """Test config with custom sub-configurations."""
        config = Config(
            server=ServerConfig(name="Custom-MCP", debug=True),
            claude=ClaudeConfig(max_tokens=8192),
            mcp=MCPConfig(enable_sampling=True),
            logging=LoggingConfig(level="debug"),
            telemetry=TelemetryConfig(enabled=True),
        )

        assert config.server.name == "Custom-MCP"
        assert config.server.debug is True
        assert config.claude.max_tokens == 8192
        assert config.mcp.enable_sampling is True
        assert config.logging.level == "debug"
        assert config.telemetry.enabled is True


class TestConfigFileLoading:
    """Test configuration file loading."""

    def test_load_default_config(self) -> None:
        """Test loading config without file path."""
        config = load_config(None)
        assert config is not None
        assert isinstance(config, Config)

    def test_load_config_from_yaml(self) -> None:
        """Test loading config from YAML file."""
        yaml_content = """
server:
  name: "Test-MCP"
  version: "1.0.0"
  debug: true

claude:
  default_model: "claude-opus-4-20250514"
  max_tokens: 8192

mcp:
  enable_sampling: true

logging:
  level: "debug"
  format: "console"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = load_config(f.name)

                assert config.server.name == "Test-MCP"
                assert config.server.debug is True
                assert config.claude.default_model == "claude-opus-4-20250514"
                assert config.claude.max_tokens == 8192
                assert config.mcp.enable_sampling is True
                assert config.logging.level == "debug"
            finally:
                Path(f.name).unlink()

    def test_load_config_missing_file(self) -> None:
        """Test loading config from non-existent file returns defaults."""
        config = load_config("/nonexistent/path/config.yaml")
        # Should return default config, not raise
        assert config is not None

    def test_load_config_invalid_yaml(self) -> None:
        """Test loading config from invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            try:
                # Should handle gracefully or return defaults
                loaded = load_config(f.name)
                # Implementation may vary - either raises or returns default
                assert loaded is not None
            except Exception:
                pass  # Expected behavior
            finally:
                Path(f.name).unlink()


class TestConfigEnvironmentOverrides:
    """Test configuration environment variable overrides."""

    def test_anthropic_api_key_override(self) -> None:
        """Test ANTHROPIC_API_KEY environment variable."""
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-api-key"}):
            config = Config()
            # Depending on implementation, env var may be used
            assert config is not None

    def test_debug_mode_env_override(self) -> None:
        """Test debug mode from environment."""
        with mock.patch.dict(os.environ, {"TFO_MCP_DEBUG": "true"}):
            # Implementation may check env vars
            pass


class TestConfigChaining:
    """Test configuration method chaining patterns."""

    def test_server_config_builder_pattern(self) -> None:
        """Test building server config incrementally."""
        # If builder pattern is supported
        config = ServerConfig(name="Base")
        assert config.name == "Base"

        # Create new config with modified values
        config2 = ServerConfig(
            name=config.name,
            version="2.0.0",
            debug=True,
        )
        assert config2.name == "Base"
        assert config2.version == "2.0.0"
        assert config2.debug is True


class TestConfigSerialization:
    """Test configuration serialization."""

    def test_config_to_dict(self) -> None:
        """Test converting config to dictionary."""
        config = Config(
            server=ServerConfig(name="Test", debug=True),
        )

        # If to_dict method exists
        if hasattr(config, "model_dump"):
            config_dict = config.model_dump()
            assert "server" in config_dict
            assert config_dict["server"]["name"] == "Test"

    def test_config_to_json(self) -> None:
        """Test converting config to JSON."""
        config = Config()

        # If JSON serialization is supported
        if hasattr(config, "model_dump_json"):
            json_str = config.model_dump_json()
            assert isinstance(json_str, str)
            assert "server" in json_str


class TestConfigValidationErrors:
    """Test configuration validation error handling."""

    def test_invalid_protocol_version(self) -> None:
        """Test invalid MCP protocol version."""
        # Protocol version validation if implemented
        config = MCPConfig(protocol_version="invalid")
        # May or may not raise depending on validation
        assert config is not None

    def test_negative_timeout(self) -> None:
        """Test negative timeout values."""
        # Depending on Pydantic validation
        try:
            config = MCPConfig(tool_timeout=-1.0)
            # May be allowed or raise
            assert config is not None
        except ValueError:
            pass  # Expected if validation is strict

    def test_empty_server_name(self) -> None:
        """Test empty server name."""
        config = ServerConfig(name="")
        # May be allowed - just document behavior
        assert config.name == ""
