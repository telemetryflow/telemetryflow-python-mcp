"""MCP Server implementation with stdio transport."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Any, TextIO

import structlog

from tfo_mcp.application.handlers import ToolHandler
from tfo_mcp.domain.aggregates import Session, SessionCapabilities
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.valueobjects import MCPErrorCode, MCPLogLevel, MCPMethod
from tfo_mcp.infrastructure.config import Config
from tfo_mcp.infrastructure.telemetry import get_telemetry_client

logger = structlog.get_logger(__name__)


class MCPServer:
    """MCP Server implementation using JSON-RPC 2.0 over stdio."""

    JSONRPC_VERSION = "2.0"
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(
        self,
        config: Config,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
    ) -> None:
        self._config = config
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout
        self._session: Session | None = None
        self._tool_handler: ToolHandler | None = None
        self._running = False

    @property
    def session(self) -> Session | None:
        """Get the current session."""
        return self._session

    def _write_response(self, response: dict[str, Any]) -> None:
        """Write a JSON-RPC response to stdout."""
        try:
            output = json.dumps(response, ensure_ascii=False)
            self._stdout.write(output + "\n")
            self._stdout.flush()
        except Exception as e:
            logger.exception("Failed to write response", error=str(e))

    def _make_response(
        self,
        request_id: int | str | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a JSON-RPC response."""
        response: dict[str, Any] = {"jsonrpc": self.JSONRPC_VERSION}
        if request_id is not None:
            response["id"] = request_id
        if error:
            response["error"] = error
        else:
            response["result"] = result if result is not None else {}
        return response

    def _make_error(
        self,
        code: MCPErrorCode | int,
        message: str,
        data: Any = None,
    ) -> dict[str, Any]:
        """Create a JSON-RPC error object."""
        error: dict[str, Any] = {"code": int(code), "message": message}
        if data is not None:
            error["data"] = data
        return error

    async def _handle_initialize(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle initialize request."""
        if self._session is not None:
            raise ValueError("Session already initialized")

        protocol_version = params.get("protocolVersion", "2024-11-05")
        client_info = params.get("clientInfo", {})
        client_capabilities = params.get("capabilities", {})

        # Create session
        capabilities = SessionCapabilities(
            tools=self._config.mcp.enable_tools,
            resources=self._config.mcp.enable_resources,
            prompts=self._config.mcp.enable_prompts,
            logging=self._config.mcp.enable_logging,
            sampling=self._config.mcp.enable_sampling,
        )

        self._session = Session.create(
            server_name=self._config.server.name,
            server_version=self._config.server.version,
            capabilities=capabilities,
        )

        # Initialize session
        client = ClientInfo(
            name=client_info.get("name", "unknown"),
            version=client_info.get("version", "unknown"),
        )
        result = self._session.initialize(client, client_capabilities)

        # Create tool handler
        self._tool_handler = ToolHandler(self._session)

        logger.info(
            "Session initialized",
            session_id=str(self._session.id),
            client_name=client.name,
            client_version=client.version,
            protocol_version=protocol_version,
        )

        return result

    async def _handle_ping(self, _params: dict[str, Any]) -> dict[str, Any]:
        """Handle ping request."""
        return {}

    async def _handle_tools_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/list request."""
        if not self._session:
            raise ValueError("Session not initialized")

        tools = self._session.list_tools()
        return {"tools": [t.to_mcp_format() for t in tools]}

    async def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call request."""
        if not self._session or not self._tool_handler:
            raise ValueError("Session not initialized")

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Tool name is required")

        from tfo_mcp.application.commands import ExecuteToolCommand

        command = ExecuteToolCommand(tool_name=tool_name, arguments=arguments)
        result = await self._tool_handler.handle_execute(command)

        return result.to_dict()

    async def _handle_resources_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/list request."""
        if not self._session:
            raise ValueError("Session not initialized")

        resources = self._session.list_resources()
        return {"resources": [r.to_mcp_format() for r in resources if not r.is_template]}

    async def _handle_resources_templates_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/templates/list request."""
        if not self._session:
            raise ValueError("Session not initialized")

        resources = self._session.list_resources()
        templates = [r.to_template_format() for r in resources if r.is_template]
        return {"resourceTemplates": [t for t in templates if t]}

    async def _handle_resources_read(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/read request."""
        if not self._session:
            raise ValueError("Session not initialized")

        uri = params.get("uri")
        if not uri:
            raise ValueError("Resource URI is required")

        telemetry = get_telemetry_client()
        start_time = time.monotonic()
        success = True

        try:
            resource = self._session.get_resource(uri)
            if not resource:
                success = False
                raise ValueError(f"Resource not found: {uri}")

            content = await resource.read(params.get("params", {}))
            return {"contents": [content.to_dict()]}
        except Exception:
            success = False
            raise
        finally:
            duration_s = time.monotonic() - start_time
            if telemetry:
                telemetry.record_resource_read(
                    resource_uri=uri,
                    duration_seconds=duration_s,
                    success=success,
                )

    async def _handle_prompts_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        """Handle prompts/list request."""
        if not self._session:
            raise ValueError("Session not initialized")

        prompts = self._session.list_prompts()
        return {"prompts": [p.to_mcp_format() for p in prompts]}

    async def _handle_prompts_get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle prompts/get request."""
        if not self._session:
            raise ValueError("Session not initialized")

        name = params.get("name")
        arguments = params.get("arguments", {})

        if not name:
            raise ValueError("Prompt name is required")

        telemetry = get_telemetry_client()
        start_time = time.monotonic()
        success = True

        try:
            prompt = self._session.get_prompt(name)
            if not prompt:
                success = False
                raise ValueError(f"Prompt not found: {name}")

            messages = await prompt.get_messages(arguments)
            return {"messages": [m.to_dict() for m in messages]}
        except Exception:
            success = False
            raise
        finally:
            duration_s = time.monotonic() - start_time
            if telemetry:
                telemetry.record_prompt_get(
                    prompt_name=name,
                    duration_seconds=duration_s,
                    success=success,
                )

    async def _handle_logging_set_level(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle logging/setLevel request."""
        if not self._session:
            raise ValueError("Session not initialized")

        level = params.get("level", "info")
        mcp_level = MCPLogLevel.from_string(level)
        self._session.set_log_level(mcp_level)

        return {}

    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a single JSON-RPC request."""
        request_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        # Notifications don't require a response
        is_notification = request_id is None

        logger.debug("Handling request", method=method, request_id=request_id)

        try:
            # Route to handler
            if method == MCPMethod.INITIALIZE.value:
                result = await self._handle_initialize(params)
            elif method == MCPMethod.INITIALIZED.value:
                # Notification, no response needed
                return None
            elif method == MCPMethod.PING.value:
                result = await self._handle_ping(params)
            elif method == MCPMethod.TOOLS_LIST.value:
                result = await self._handle_tools_list(params)
            elif method == MCPMethod.TOOLS_CALL.value:
                result = await self._handle_tools_call(params)
            elif method == MCPMethod.RESOURCES_LIST.value:
                result = await self._handle_resources_list(params)
            elif method == MCPMethod.RESOURCES_TEMPLATES_LIST.value:
                result = await self._handle_resources_templates_list(params)
            elif method == MCPMethod.RESOURCES_READ.value:
                result = await self._handle_resources_read(params)
            elif method == MCPMethod.PROMPTS_LIST.value:
                result = await self._handle_prompts_list(params)
            elif method == MCPMethod.PROMPTS_GET.value:
                result = await self._handle_prompts_get(params)
            elif method == MCPMethod.LOGGING_SET_LEVEL.value:
                result = await self._handle_logging_set_level(params)
            elif method == MCPMethod.SHUTDOWN.value:
                self._running = False
                result = {}
            else:
                if is_notification:
                    return None
                return self._make_response(
                    request_id,
                    error=self._make_error(
                        MCPErrorCode.METHOD_NOT_FOUND,
                        f"Method not found: {method}",
                    ),
                )

            if is_notification:
                return None

            return self._make_response(request_id, result=result)

        except ValueError as e:
            logger.warning("Request validation error", method=method, error=str(e))
            if is_notification:
                return None
            return self._make_response(
                request_id,
                error=self._make_error(MCPErrorCode.INVALID_PARAMS, str(e)),
            )
        except Exception as e:
            logger.exception("Request handler error", method=method, error=str(e))
            if is_notification:
                return None
            return self._make_response(
                request_id,
                error=self._make_error(MCPErrorCode.INTERNAL_ERROR, str(e)),
            )

    async def _read_line(self) -> str | None:
        """Read a line from stdin asynchronously."""
        loop = asyncio.get_event_loop()
        try:
            line = await loop.run_in_executor(None, self._stdin.readline)
            return line.strip() if line else None
        except Exception:
            return None

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info(
            "Starting MCP server",
            name=self._config.server.name,
            version=self._config.server.version,
            transport=self._config.server.transport,
        )

        self._running = True

        while self._running:
            try:
                line = await self._read_line()
                if line is None:
                    # EOF
                    break

                if not line:
                    continue

                # Check message size
                if len(line) > self.MAX_MESSAGE_SIZE:
                    logger.warning("Message too large", size=len(line))
                    continue

                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON", error=str(e))
                    response = self._make_response(
                        None,
                        error=self._make_error(
                            MCPErrorCode.PARSE_ERROR,
                            f"Parse error: {e}",
                        ),
                    )
                    self._write_response(response)
                    continue

                # Validate JSON-RPC version
                if request.get("jsonrpc") != self.JSONRPC_VERSION:
                    response = self._make_response(
                        request.get("id"),
                        error=self._make_error(
                            MCPErrorCode.INVALID_REQUEST,
                            "Invalid JSON-RPC version",
                        ),
                    )
                    self._write_response(response)
                    continue

                # Handle request
                handler_response = await self._handle_request(request)
                if handler_response:
                    self._write_response(handler_response)

            except Exception as e:
                logger.exception("Error processing request", error=str(e))

        logger.info("MCP server stopped")

    def stop(self) -> None:
        """Stop the server."""
        self._running = False
        if self._session:
            self._session.close()
