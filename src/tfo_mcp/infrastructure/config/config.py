"""Configuration management using Pydantic Settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TELEMETRYFLOW_MCP_SERVER_",
        extra="ignore",
    )

    name: str = Field(default="TelemetryFlow-MCP", description="Server name")
    version: str = Field(default="1.1.2", description="Server version")
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, description="Server port")
    transport: str = Field(default="stdio", description="Transport type (stdio, sse, websocket)")
    debug: bool = Field(default=False, description="Debug mode")
    read_timeout: float = Field(default=300.0, description="Read timeout in seconds")
    write_timeout: float = Field(default=60.0, description="Write timeout in seconds")


class ClaudeConfig(BaseSettings):
    """Claude API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TELEMETRYFLOW_MCP_CLAUDE_",
        extra="ignore",
    )

    api_key: str = Field(default="", description="Anthropic API key")
    default_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Default Claude model",
    )
    max_tokens: int = Field(default=4096, description="Maximum tokens per request")
    temperature: float = Field(default=1.0, ge=0.0, le=2.0, description="Temperature")
    timeout: float = Field(default=120.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    base_url: str | None = Field(default=None, description="Custom base URL")

    @field_validator("api_key", mode="before")
    @classmethod
    def get_api_key(cls, v: str) -> str:
        """Get API key from environment if not set."""
        if not v:
            return os.environ.get("ANTHROPIC_API_KEY", "")
        return v


class MCPConfig(BaseSettings):
    """MCP protocol configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TELEMETRYFLOW_MCP_MCP_",
        extra="ignore",
    )

    protocol_version: str = Field(default="2024-11-05", description="MCP protocol version")
    enable_tools: bool = Field(default=True, description="Enable tools capability")
    enable_resources: bool = Field(default=True, description="Enable resources capability")
    enable_prompts: bool = Field(default=True, description="Enable prompts capability")
    enable_logging: bool = Field(default=True, description="Enable logging capability")
    enable_sampling: bool = Field(default=False, description="Enable sampling capability")
    tool_timeout: float = Field(default=30.0, description="Tool execution timeout in seconds")
    max_message_size: int = Field(default=10 * 1024 * 1024, description="Max message size in bytes")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TELEMETRYFLOW_MCP_LOG_",
        extra="ignore",
    )

    level: str = Field(default="info", description="Log level")
    format: str = Field(default="json", description="Log format (json, text)")
    output: str = Field(default="stderr", description="Log output (stderr, stdout, file path)")


class TelemetryConfig(BaseSettings):
    """Telemetry configuration using TelemetryFlow Python SDK."""

    model_config = SettingsConfigDict(
        env_prefix="TELEMETRYFLOW_",
        extra="ignore",
    )

    enabled: bool = Field(default=False, description="Enable telemetry")
    service_name: str = Field(default="telemetryflow-mcp", description="Service name")
    service_version: str = Field(default="1.1.2", description="Service version")
    service_namespace: str = Field(default="telemetryflow", description="Service namespace")
    environment: str = Field(default="production", description="Deployment environment")

    # API credentials
    api_key_id: str = Field(default="", description="TelemetryFlow API key ID (tfk_*)")
    api_key_secret: str = Field(default="", description="TelemetryFlow API key secret (tfs_*)")

    # Connection settings
    endpoint: str = Field(default="api.telemetryflow.id:4317", description="OTLP endpoint")
    protocol: str = Field(default="grpc", description="Protocol (grpc, http)")
    insecure: bool = Field(default=False, description="Use insecure connection")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    compression: bool = Field(default=True, description="Enable compression")

    # Signal configuration
    enable_traces: bool = Field(default=True, description="Enable traces")
    enable_metrics: bool = Field(default=True, description="Enable metrics")
    enable_logs: bool = Field(default=True, description="Enable logs")
    enable_exemplars: bool = Field(default=True, description="Enable exemplars")

    # Batch settings
    batch_timeout_ms: int = Field(default=5000, description="Batch timeout in milliseconds")
    batch_max_size: int = Field(default=512, description="Maximum batch size")

    # Retry settings
    retry_enabled: bool = Field(default=True, description="Enable retry")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_backoff_ms: int = Field(default=500, description="Retry backoff in milliseconds")

    # Rate limiting
    rate_limit: int = Field(default=1000, description="Rate limit (requests/minute)")

    @field_validator("api_key_id", mode="before")
    @classmethod
    def get_api_key_id(cls, v: str) -> str:
        """Get API key ID from environment if not set."""
        if not v:
            return os.environ.get("TELEMETRYFLOW_API_KEY_ID", "")
        return v

    @field_validator("api_key_secret", mode="before")
    @classmethod
    def get_api_key_secret(cls, v: str) -> str:
        """Get API key secret from environment if not set."""
        if not v:
            return os.environ.get("TELEMETRYFLOW_API_KEY_SECRET", "")
        return v


class Config(BaseSettings):
    """Main configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TELEMETRYFLOW_MCP_",
        extra="ignore",
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> Config:
        """Create config from dictionary."""
        return cls(
            server=ServerConfig(**data.get("server", {})),
            claude=ClaudeConfig(**data.get("claude", {})),
            mcp=MCPConfig(**data.get("mcp", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            telemetry=TelemetryConfig(**data.get("telemetry", {})),
        )


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from file and environment.

    Priority (highest to lowest):
    1. Environment variables
    2. Config file
    3. Default values
    """
    # Default config paths to check
    default_paths = [
        Path("tfo-mcp.yaml"),
        Path("configs/tfo-mcp.yaml"),
        Path.home() / ".config" / "tfo-mcp" / "config.yaml",
        Path("/etc/tfo-mcp/config.yaml"),
    ]

    if config_path:
        config_file = Path(config_path)
    else:
        config_file = None
        for path in default_paths:
            if path.exists():
                config_file = path
                break

    if config_file and config_file.exists():
        return Config.from_yaml(config_file)

    return Config()
