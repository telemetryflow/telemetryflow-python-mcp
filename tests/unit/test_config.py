"""Unit tests for configuration."""

import os
import tempfile

from tfo_mcp.infrastructure.config import (
    ClaudeConfig,
    Config,
    LoggingConfig,
    MCPConfig,
    ServerConfig,
    TelemetryConfig,
)


class TestServerConfig:
    """Test ServerConfig."""

    def test_default_values(self):
        """Test default server config values."""
        config = ServerConfig()
        assert config.name == "TelemetryFlow-MCP"
        assert config.version == "1.1.2"
        assert config.host == "localhost"
        assert config.port == 8080
        assert config.transport == "stdio"
        assert config.debug is False

    def test_custom_values(self):
        """Test custom server config values."""
        config = ServerConfig(
            name="Custom-MCP",
            version="2.0.0",
            host="0.0.0.0",
            port=9090,
            debug=True,
        )
        assert config.name == "Custom-MCP"
        assert config.port == 9090
        assert config.debug is True

    def test_timeouts(self):
        """Test timeout configuration."""
        config = ServerConfig(
            read_timeout=600.0,
            write_timeout=120.0,
        )
        assert config.read_timeout == 600.0
        assert config.write_timeout == 120.0


class TestClaudeConfig:
    """Test ClaudeConfig."""

    def test_default_values(self):
        """Test default Claude config values."""
        config = ClaudeConfig()
        assert config.default_model == "claude-sonnet-4-20250514"
        assert config.max_tokens == 4096
        assert config.temperature == 1.0
        assert config.timeout == 120.0
        assert config.max_retries == 3

    def test_api_key_from_env(self, monkeypatch):
        """Test API key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        config = ClaudeConfig()
        assert config.api_key == "test-api-key"

    def test_custom_model(self):
        """Test custom model configuration."""
        config = ClaudeConfig(default_model="claude-opus-4-20250514")
        assert config.default_model == "claude-opus-4-20250514"

    def test_temperature_range(self):
        """Test temperature value."""
        config = ClaudeConfig(temperature=0.5)
        assert config.temperature == 0.5

    def test_base_url(self):
        """Test custom base URL."""
        config = ClaudeConfig(base_url="https://custom.api.com")
        assert config.base_url == "https://custom.api.com"


class TestMCPConfig:
    """Test MCPConfig."""

    def test_default_values(self):
        """Test default MCP config values."""
        config = MCPConfig()
        assert config.protocol_version == "2024-11-05"
        assert config.enable_tools is True
        assert config.enable_resources is True
        assert config.enable_prompts is True
        assert config.enable_logging is True
        assert config.enable_sampling is False

    def test_tool_timeout(self):
        """Test tool timeout configuration."""
        config = MCPConfig(tool_timeout=60.0)
        assert config.tool_timeout == 60.0

    def test_max_message_size(self):
        """Test max message size configuration."""
        config = MCPConfig(max_message_size=20971520)  # 20MB
        assert config.max_message_size == 20971520

    def test_disable_capabilities(self):
        """Test disabling capabilities."""
        config = MCPConfig(
            enable_tools=False,
            enable_resources=False,
            enable_prompts=False,
        )
        assert config.enable_tools is False
        assert config.enable_resources is False
        assert config.enable_prompts is False


class TestLoggingConfig:
    """Test LoggingConfig."""

    def test_default_values(self):
        """Test default logging config values."""
        config = LoggingConfig()
        assert config.level == "info"
        assert config.format == "json"
        assert config.output == "stderr"

    def test_debug_level(self):
        """Test debug log level."""
        config = LoggingConfig(level="debug")
        assert config.level == "debug"

    def test_text_format(self):
        """Test text log format."""
        config = LoggingConfig(format="text")
        assert config.format == "text"

    def test_file_output(self):
        """Test file output."""
        config = LoggingConfig(output="/var/log/tfo-mcp.log")
        assert config.output == "/var/log/tfo-mcp.log"


class TestTelemetryConfig:
    """Test TelemetryConfig."""

    def test_default_values(self):
        """Test default telemetry config values."""
        config = TelemetryConfig()
        assert config.enabled is False
        assert config.service_name == "telemetryflow-mcp"
        # endpoint is the actual attribute name (not otlp_endpoint)
        assert config.endpoint == "api.telemetryflow.id:4317"

    def test_enable_telemetry(self):
        """Test enabling telemetry."""
        config = TelemetryConfig(enabled=True)
        assert config.enabled is True

    def test_custom_endpoint(self):
        """Test custom OTLP endpoint."""
        config = TelemetryConfig(
            enabled=True,
            endpoint="otel-collector:4317",
        )
        assert config.endpoint == "otel-collector:4317"

    def test_rate_limit(self):
        """Test rate limit configuration."""
        config = TelemetryConfig(rate_limit=500)
        assert config.rate_limit == 500


class TestConfig:
    """Test main Config class."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.server is not None
        assert config.claude is not None
        assert config.mcp is not None
        assert config.logging is not None
        assert config.telemetry is not None

    def test_nested_config(self):
        """Test nested configuration access."""
        config = Config(
            server=ServerConfig(name="Test"),
            claude=ClaudeConfig(max_tokens=8192),
        )
        assert config.server.name == "Test"
        assert config.claude.max_tokens == 8192

    def test_from_yaml_file(self):
        """Test loading config from YAML file."""
        yaml_content = """
server:
  name: "Test-MCP"
  debug: true
claude:
  max_tokens: 8192
logging:
  level: "debug"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = Config.from_yaml(f.name)
                assert config.server.name == "Test-MCP"
                assert config.server.debug is True
                assert config.claude.max_tokens == 8192
                assert config.logging.level == "debug"
            finally:
                os.unlink(f.name)


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_log_level(self):
        """Test valid log level values."""
        for level in ["debug", "info", "warning", "error"]:
            config = LoggingConfig(level=level)
            assert config.level == level

    def test_valid_log_format(self):
        """Test valid log format values."""
        for fmt in ["json", "text"]:
            config = LoggingConfig(format=fmt)
            assert config.format == fmt

    def test_valid_transport(self):
        """Test valid transport values."""
        for transport in ["stdio", "sse", "websocket"]:
            config = ServerConfig(transport=transport)
            assert config.transport == transport

    def test_port_range(self):
        """Test port number validation."""
        config = ServerConfig(port=8080)
        assert config.port == 8080

        config = ServerConfig(port=443)
        assert config.port == 443

    def test_positive_timeout(self):
        """Test positive timeout values."""
        config = ServerConfig(read_timeout=1.0, write_timeout=1.0)
        assert config.read_timeout == 1.0

    def test_rate_limit_value(self):
        """Test rate limit values."""
        config = TelemetryConfig(rate_limit=100)
        assert config.rate_limit == 100

        config = TelemetryConfig(rate_limit=1000)
        assert config.rate_limit == 1000
