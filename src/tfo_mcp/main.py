"""TelemetryFlow Python MCP Server - Main entry point."""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path
from typing import Any

import click

from tfo_mcp import __version__


def setup_signal_handlers(server: Any) -> None:
    """Setup signal handlers for graceful shutdown."""

    def handle_signal(_signum: int, _frame: Any) -> None:
        server.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


async def run_server(
    config_path: str | None = None,
    debug: bool = False,
) -> None:
    """Run the MCP server."""
    from tfo_mcp.infrastructure.claude import ClaudeClient
    from tfo_mcp.infrastructure.config import load_config
    from tfo_mcp.infrastructure.logging import setup_logging
    from tfo_mcp.infrastructure.telemetry import (
        get_telemetry_client,
        initialize_telemetry,
        shutdown_telemetry,
    )
    from tfo_mcp.presentation.prompts import register_builtin_prompts
    from tfo_mcp.presentation.resources import register_builtin_resources
    from tfo_mcp.presentation.server import MCPServer
    from tfo_mcp.presentation.tools import register_builtin_tools

    # Load configuration
    config = load_config(config_path)

    # Override debug mode if specified
    if debug:
        config.server.debug = True
        config.logging.level = "debug"

    # Setup logging
    setup_logging(config.logging)

    import structlog

    logger = structlog.get_logger(__name__)

    # Initialize telemetry
    telemetry_client = initialize_telemetry(config.telemetry)
    if telemetry_client and telemetry_client.is_enabled:
        logger.info(
            "Telemetry enabled",
            service=config.telemetry.service_name,
            endpoint=config.telemetry.endpoint,
        )

    logger.info(
        "Starting TelemetryFlow Python MCP Server",
        version=__version__,
        name=config.server.name,
        transport=config.server.transport,
        debug=config.server.debug,
        telemetry=config.telemetry.enabled,
    )

    # Create Claude client if API key is available
    claude_client = None
    if config.claude.api_key:
        claude_client = ClaudeClient(config.claude)
        logger.info("Claude client initialized", model=config.claude.default_model)
    else:
        logger.warning("Claude API key not configured, claude_conversation tool disabled")

    # Create and configure server
    server = MCPServer(config)

    # Setup signal handlers
    setup_signal_handlers(server)

    # Register built-in components when session is initialized
    original_handle_initialize = server._handle_initialize

    async def handle_initialize_with_builtins(params: dict[str, Any]) -> dict[str, Any]:
        result = await original_handle_initialize(params)
        if server.session:
            register_builtin_tools(server.session, claude_client)
            register_builtin_resources(server.session, config)
            register_builtin_prompts(server.session)
            logger.info(
                "Built-in components registered",
                tools=len(server.session.tools),
                resources=len(server.session.resources),
                prompts=len(server.session.prompts),
            )

            # Record session initialization in telemetry
            telemetry = get_telemetry_client()
            if telemetry:
                telemetry.record_session_event(
                    "initialized",
                    session_id=str(server.session.id),
                    attributes={
                        "tools_count": len(server.session.tools),
                        "resources_count": len(server.session.resources),
                        "prompts_count": len(server.session.prompts),
                        "client_name": params.get("clientInfo", {}).get("name", "unknown"),
                    },
                )
                telemetry.increment_counter("server.sessions.active")

        return result

    server._handle_initialize = handle_initialize_with_builtins  # type: ignore[method-assign]

    # Run server
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.exception("Server error", error=str(e))
        # Record error in telemetry
        telemetry = get_telemetry_client()
        if telemetry:
            telemetry.log_error(
                "Server error",
                attributes={"error.type": type(e).__name__, "error.message": str(e)},
            )
            telemetry.increment_counter(
                "server.errors", attributes={"error.type": type(e).__name__}
            )
        raise
    finally:
        # Record session closure in telemetry
        telemetry = get_telemetry_client()
        if telemetry:
            if server.session:
                telemetry.record_session_event(
                    "closed",
                    session_id=str(server.session.id),
                )
            telemetry.increment_counter("server.shutdowns")

        server.stop()

        # Shutdown telemetry (flush remaining data)
        shutdown_telemetry(timeout=10.0)

        logger.info("Server stopped")


@click.group()
@click.version_option(version=__version__, prog_name="tfo-mcp")
def cli() -> None:
    """TelemetryFlow Python MCP Server - AI Integration Layer for TelemetryFlow Platform."""
    pass


@cli.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode",
)
def serve(config: Path | None, debug: bool) -> None:
    """Start the MCP server."""
    config_path = str(config) if config else None
    asyncio.run(run_server(config_path, debug))


@cli.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
def validate(config: Path | None) -> None:
    """Validate the configuration file."""
    from tfo_mcp.infrastructure.config import load_config

    try:
        config_path = str(config) if config else None
        cfg = load_config(config_path)
        click.echo("Configuration is valid!")
        click.echo(f"  Server: {cfg.server.name} v{cfg.server.version}")
        click.echo(f"  Transport: {cfg.server.transport}")
        click.echo(f"  MCP Protocol: {cfg.mcp.protocol_version}")
        click.echo(f"  Tools: {'enabled' if cfg.mcp.enable_tools else 'disabled'}")
        click.echo(f"  Resources: {'enabled' if cfg.mcp.enable_resources else 'disabled'}")
        click.echo(f"  Prompts: {'enabled' if cfg.mcp.enable_prompts else 'disabled'}")
        click.echo(f"  Claude API: {'configured' if cfg.claude.api_key else 'not configured'}")
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


@cli.command()
def info() -> None:
    """Show server information."""
    click.echo(f"TelemetryFlow Python MCP Server v{__version__}")
    click.echo()
    click.echo("Built-in Tools:")
    from tfo_mcp.presentation.tools.builtin_tools import BUILTIN_TOOLS

    for tool in BUILTIN_TOOLS:
        click.echo(f"  - {tool['name']}: {tool['description']}")
    click.echo()
    click.echo("Built-in Prompts:")
    click.echo("  - code_review: Get a thorough code review")
    click.echo("  - explain_code: Get code explanation")
    click.echo("  - debug_help: Get debugging assistance")
    click.echo()
    click.echo("Built-in Resources:")
    click.echo("  - config://server: Server configuration")
    click.echo("  - status://health: Health status")
    click.echo("  - file:///{path}: File access (template)")


@cli.command()
def init_config() -> None:
    """Generate a default configuration file."""
    default_config = """# TelemetryFlow Python MCP Server Configuration

server:
  name: "TelemetryFlow-MCP"
  version: "1.1.2"
  transport: "stdio"
  debug: false

claude:
  # API key can also be set via ANTHROPIC_API_KEY environment variable
  api_key: ""
  default_model: "claude-sonnet-4-20250514"
  max_tokens: 4096
  temperature: 1.0
  timeout: 120.0
  max_retries: 3

mcp:
  protocol_version: "2024-11-05"
  enable_tools: true
  enable_resources: true
  enable_prompts: true
  enable_logging: true
  enable_sampling: false
  tool_timeout: 30.0

logging:
  level: "info"
  format: "json"
  output: "stderr"

telemetry:
  # Enable to send telemetry to TelemetryFlow platform
  enabled: false
  service_name: "telemetryflow-python-mcp"
  service_version: "1.1.2"
  service_namespace: "telemetryflow"
  environment: "production"

  # API credentials (or use TELEMETRYFLOW_API_KEY_ID/SECRET env vars)
  api_key_id: ""
  api_key_secret: ""

  # Connection settings
  endpoint: "api.telemetryflow.id:4317"
  protocol: "grpc"  # or "http"
  insecure: false
  timeout: 30.0
  compression: true

  # Signals
  enable_traces: true
  enable_metrics: true
  enable_logs: true
  enable_exemplars: true

  # Batch settings
  batch_timeout_ms: 5000
  batch_max_size: 512

  # Retry settings
  retry_enabled: true
  max_retries: 3
  retry_backoff_ms: 500

  # Rate limiting
  rate_limit: 1000
"""
    config_path = Path("tfo-mcp.yaml")
    if config_path.exists():
        click.echo(f"Configuration file already exists: {config_path}", err=True)
        sys.exit(1)

    config_path.write_text(default_config)
    click.echo(f"Created configuration file: {config_path}")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
