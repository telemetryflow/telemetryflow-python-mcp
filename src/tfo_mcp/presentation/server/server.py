"""MCP Server implementation using official MCP Python SDK.

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

from typing import Any

import mcp.types as types
import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server

from tfo_mcp.infrastructure.config import Config

logger = structlog.get_logger(__name__)


class MCPServer:
    """MCP Server wrapping the official mcp.server.Server SDK."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._server = Server(
            name=config.server.name,
            version=config.server.version,
        )
        self._tool_handlers: dict[str, Any] = {}
        self._resource_readers: dict[str, Any] = {}
        self._prompt_generators: dict[str, Any] = {}
        self._prompt_definitions: dict[str, types.Prompt] = {}
        self._tool_definitions: dict[str, types.Tool] = {}
        self._resource_definitions: list[types.Resource] = []
        self._template_definitions: list[types.ResourceTemplate] = []
        self._session: Any = None
        self._running = False

    @property
    def session(self) -> Any:
        return self._session

    @property
    def server(self) -> Server:
        return self._server

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: Any,
    ) -> None:
        self._tool_definitions[name] = types.Tool(
            name=name,
            description=description,
            inputSchema=input_schema,
        )
        self._tool_handlers[name] = handler

    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str | None = None,
        reader: Any = None,
    ) -> None:
        if "{" in uri and "}" in uri:
            self._template_definitions.append(
                types.ResourceTemplate(
                    uriTemplate=uri,
                    name=name,
                    description=description or None,
                    mimeType=mime_type,
                )
            )
        else:
            self._resource_definitions.append(
                types.Resource(
                    uri=uri,
                    name=name,
                    description=description or None,
                    mimeType=mime_type,
                )
            )
        self._resource_readers[uri] = reader

    def register_prompt(
        self,
        name: str,
        description: str,
        arguments: list[types.PromptArgument] | None = None,
        generator: Any = None,
    ) -> None:
        self._prompt_definitions[name] = types.Prompt(
            name=name,
            description=description or None,
            arguments=arguments,
        )
        self._prompt_generators[name] = generator

    def _setup_handlers(self) -> None:
        @self._server.list_tools()  # type: ignore[misc, no-untyped-call, untyped-decorator]
        async def list_tools() -> list[types.Tool]:
            return list(self._tool_definitions.values())

        @self._server.call_tool()  # type: ignore[misc, no-untyped-call, untyped-decorator]
        async def call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.TextContent | types.ImageContent]:
            handler = self._tool_handlers.get(name)
            if handler is None:
                return [types.TextContent(type="text", text=f"Tool not found: {name}")]

            try:
                from tfo_mcp.domain.entities import ToolResult

                result = await handler(arguments)
                if isinstance(result, ToolResult):
                    content: list[types.TextContent | types.ImageContent] = []
                    for block in result.content:
                        content.append(types.TextContent(type="text", text=block.get("text", "")))
                    return content
                return [types.TextContent(type="text", text=str(result))]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error: {e}")]

        @self._server.list_resources()  # type: ignore[misc, no-untyped-call, untyped-decorator]
        async def list_resources() -> list[types.Resource]:
            return self._resource_definitions

        @self._server.list_resource_templates()  # type: ignore[misc, no-untyped-call, untyped-decorator]
        async def list_resource_templates() -> list[types.ResourceTemplate]:
            return self._template_definitions

        @self._server.read_resource()  # type: ignore[misc, no-untyped-call, untyped-decorator]
        async def read_resource(uri: Any) -> str | bytes:
            uri_str = str(uri)

            reader = self._resource_readers.get(uri_str)
            if reader is None:
                for template_uri, tmpl_reader in self._resource_readers.items():
                    if "{" in template_uri:
                        prefix = template_uri.split("{")[0]
                        if uri_str.startswith(prefix):
                            reader = tmpl_reader
                            break

            if reader is None:
                return f"Resource not found: {uri_str}"

            from tfo_mcp.domain.entities import ResourceContent

            result = await reader(uri_str, {})
            if isinstance(result, ResourceContent):
                if result.text is not None:
                    return result.text
                if result.blob is not None:
                    return result.blob
            return str(result)

        @self._server.list_prompts()  # type: ignore[misc, no-untyped-call, untyped-decorator]
        async def list_prompts() -> list[types.Prompt]:
            return list(self._prompt_definitions.values())

        @self._server.get_prompt()  # type: ignore[misc, no-untyped-call, untyped-decorator]
        async def get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
            generator = self._prompt_generators.get(name)
            if generator is None:
                raise ValueError(f"Prompt not found: {name}")

            messages = await generator(arguments or {})
            prompt_messages: list[types.PromptMessage] = []
            for msg in messages:
                prompt_messages.append(
                    types.PromptMessage(
                        role=msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                        content=types.TextContent(type="text", text=msg.content),
                    )
                )
            return types.GetPromptResult(messages=prompt_messages)

    async def run(self) -> None:
        """Run the MCP server using the official SDK stdio transport."""
        logger.info(
            "Starting MCP server",
            name=self._config.server.name,
            version=self._config.server.version,
            transport=self._config.server.transport,
        )

        self._setup_handlers()
        self._running = True

        async with stdio_server() as (read_stream, write_stream):
            init_options = self._server.create_initialization_options()
            await self._server.run(
                read_stream,
                write_stream,
                init_options,
                raise_exceptions=False,
            )

        self._running = False
        logger.info("MCP server stopped")

    def stop(self) -> None:
        self._running = False
