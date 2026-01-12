"""Built-in resources for the MCP server."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

from tfo_mcp.domain.entities import Resource, ResourceContent
from tfo_mcp.domain.valueobjects import MimeType

if TYPE_CHECKING:
    from tfo_mcp.domain.aggregates import Session
    from tfo_mcp.infrastructure.config import Config

# Type alias for resource reader functions
ResourceReader = Callable[[str, dict[str, str]], Awaitable[ResourceContent]]


def _create_config_reader(config: Config) -> ResourceReader:
    """Create a config reader function."""

    async def reader(uri: str, _params: dict[str, str]) -> ResourceContent:
        """Read server configuration."""
        config_data = {
            "server": {
                "name": config.server.name,
                "version": config.server.version,
                "transport": config.server.transport,
            },
            "mcp": {
                "protocolVersion": config.mcp.protocol_version,
                "enableTools": config.mcp.enable_tools,
                "enableResources": config.mcp.enable_resources,
                "enablePrompts": config.mcp.enable_prompts,
            },
        }
        return ResourceContent(
            uri=uri,
            mime_type=MimeType.APPLICATION_JSON,
            text=json.dumps(config_data, indent=2),
        )

    return reader


def _create_health_reader(session: Session) -> ResourceReader:
    """Create a health status reader function."""

    async def reader(uri: str, _params: dict[str, str]) -> ResourceContent:
        """Read health status."""
        health_data = {
            "status": "healthy" if session.is_ready else "not_ready",
            "session": {
                "id": str(session.id),
                "state": session.state.value,
                "toolCount": len(session.tools),
                "resourceCount": len(session.resources),
                "promptCount": len(session.prompts),
            },
        }
        return ResourceContent(
            uri=uri,
            mime_type=MimeType.APPLICATION_JSON,
            text=json.dumps(health_data, indent=2),
        )

    return reader


async def _file_reader(uri: str, params: dict[str, str]) -> ResourceContent:
    """Read a file resource."""
    # Extract path from URI (file:///{path})
    path = uri[8:] if uri.startswith("file:///") else params.get("path", "")

    if not path:
        return ResourceContent(
            uri=uri,
            mime_type=MimeType.TEXT_PLAIN,
            text="Error: No file path specified",
        )

    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        return ResourceContent(
            uri=uri,
            mime_type=MimeType.TEXT_PLAIN,
            text=f"Error: File not found: {path}",
        )

    # Determine MIME type from extension
    mime_type = MimeType.from_extension(file_path.suffix)

    try:
        async with aiofiles.open(file_path, encoding="utf-8") as f:
            content = await f.read()
        return ResourceContent(
            uri=uri,
            mime_type=mime_type,
            text=content,
        )
    except UnicodeDecodeError:
        # Binary file - read as bytes
        async with aiofiles.open(file_path, "rb") as f:
            binary_content = await f.read()
        return ResourceContent(
            uri=uri,
            mime_type=MimeType.APPLICATION_OCTET_STREAM,
            blob=binary_content,
        )
    except Exception as e:
        return ResourceContent(
            uri=uri,
            mime_type=MimeType.TEXT_PLAIN,
            text=f"Error reading file: {e}",
        )


def register_builtin_resources(
    session: Session,
    config: Config,
) -> None:
    """Register all built-in resources with the session."""
    # Server configuration resource
    config_resource = Resource.create(
        uri="config://server",
        name="Server Configuration",
        description="Current server configuration",
        mime_type=MimeType.APPLICATION_JSON,
        reader=_create_config_reader(config),
    )
    session.register_resource(config_resource)

    # Health status resource
    health_resource = Resource.create(
        uri="status://health",
        name="Health Status",
        description="Server health status",
        mime_type=MimeType.APPLICATION_JSON,
        reader=_create_health_reader(session),
    )
    session.register_resource(health_resource)

    # File template resource
    file_resource = Resource.template(
        uri_template="file:///{path}",
        name="File",
        description="Read a file from the filesystem",
        mime_type=MimeType.TEXT_PLAIN,
        reader=_file_reader,
    )
    session.register_resource(file_resource)
