"""Built-in resources for the MCP server.

TelemetryFlow Python MCP Server - Community Enterprise Observability Platform
Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
Open Source Software built by Telemetri Data Indonesia.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

from tfo_mcp.domain.entities import ResourceContent
from tfo_mcp.domain.valueobjects import MimeType

if TYPE_CHECKING:
    from tfo_mcp.infrastructure.config import Config
    from tfo_mcp.presentation.server import MCPServer

ResourceReader = Callable[[str, dict[str, str]], Awaitable[ResourceContent]]


def _create_config_reader(config: Config) -> ResourceReader:
    async def reader(uri: str, _params: dict[str, str]) -> ResourceContent:
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


def _create_health_reader() -> ResourceReader:
    async def reader(uri: str, _params: dict[str, str]) -> ResourceContent:
        health_data = {
            "status": "healthy",
        }
        return ResourceContent(
            uri=uri,
            mime_type=MimeType.APPLICATION_JSON,
            text=json.dumps(health_data, indent=2),
        )

    return reader


async def _file_reader(uri: str, params: dict[str, str]) -> ResourceContent:
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
    server: MCPServer,
    config: Config,
) -> None:
    """Register all built-in resources with the MCP server."""
    server.register_resource(
        uri="config://server",
        name="Server Configuration",
        description="Current server configuration",
        mime_type=MimeType.APPLICATION_JSON.value,
        reader=_create_config_reader(config),
    )

    server.register_resource(
        uri="status://health",
        name="Health Status",
        description="Server health status",
        mime_type=MimeType.APPLICATION_JSON.value,
        reader=_create_health_reader(),
    )

    server.register_resource(
        uri="file:///{path}",
        name="File",
        description="Read a file from the filesystem",
        mime_type=MimeType.TEXT_PLAIN.value,
        reader=_file_reader,
    )
