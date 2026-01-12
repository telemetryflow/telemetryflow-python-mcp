"""Tool command and query handler."""

from __future__ import annotations

import asyncio
import contextlib
import time
from typing import TYPE_CHECKING, Any

import structlog

from tfo_mcp.domain.entities import Tool, ToolResult
from tfo_mcp.domain.events import ToolExecutedEvent, ToolRegisteredEvent
from tfo_mcp.infrastructure.telemetry import get_telemetry_client

if TYPE_CHECKING:
    from tfo_mcp.application.commands import ExecuteToolCommand, RegisterToolCommand
    from tfo_mcp.application.queries import GetToolQuery, ListToolsQuery
    from tfo_mcp.domain.aggregates import Session


logger = structlog.get_logger(__name__)


class ToolHandler:
    """Handler for tool commands and queries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def handle_register(
        self,
        command: RegisterToolCommand,
    ) -> None:
        """Handle tool registration command."""
        logger.info(
            "Registering tool",
            tool_name=str(command.tool.name),
            category=command.tool.category,
        )

        self._session.register_tool(command.tool)

        # Emit event
        event = ToolRegisteredEvent(
            session_id=str(self._session.id),
            tool_name=str(command.tool.name),
            category=command.tool.category,
        )
        self._session._add_event(event)

        logger.info(
            "Tool registered",
            tool_name=str(command.tool.name),
        )

    async def handle_execute(
        self,
        command: ExecuteToolCommand,
    ) -> ToolResult:
        """Handle tool execution command."""
        logger.info(
            "Executing tool",
            tool_name=command.tool_name,
            arguments=command.arguments,
        )

        telemetry = get_telemetry_client()
        start_time = time.monotonic()
        success = True
        error_message: str | None = None
        error_type: str | None = None

        # Create telemetry span for tool execution
        span_context = (
            telemetry.span(
                f"tools.execute.{command.tool_name}",
                kind="server",
                attributes={
                    "tool.name": command.tool_name,
                    "session.id": str(self._session.id),
                },
            )
            if telemetry
            else None
        )

        try:
            if span_context:
                span_context.__enter__()

            tool = self._session.get_tool(command.tool_name)
            if tool is None:
                success = False
                error_message = f"Tool not found: {command.tool_name}"
                error_type = "NotFoundError"
                return ToolResult.error(error_message)

            if not tool.enabled:
                success = False
                error_message = f"Tool is disabled: {command.tool_name}"
                error_type = "DisabledError"
                return ToolResult.error(error_message)

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    tool.execute(command.arguments),
                    timeout=tool.timeout_seconds,
                )
                if result.is_error:
                    success = False
                    error_message = str(result.content[0].get("text", "Unknown error"))
                    error_type = "ExecutionError"
                return result
            except TimeoutError:
                success = False
                error_message = f"Tool execution timed out after {tool.timeout_seconds}s"
                error_type = "TimeoutError"
                return ToolResult.error(error_message)

        except Exception as e:
            success = False
            error_message = str(e)
            error_type = type(e).__name__
            logger.exception("Tool execution failed", tool_name=command.tool_name)
            return ToolResult.error(f"Tool execution failed: {e}")

        finally:
            duration_s = time.monotonic() - start_time
            duration_ms = duration_s * 1000

            # Exit span context
            if span_context:
                with contextlib.suppress(Exception):
                    span_context.__exit__(None, None, None)

            # Record telemetry metrics
            if telemetry:
                telemetry.record_tool_call(
                    tool_name=command.tool_name,
                    duration_seconds=duration_s,
                    success=success,
                    error_type=error_type,
                )

            # Emit domain event
            event = ToolExecutedEvent(
                session_id=str(self._session.id),
                tool_name=command.tool_name,
                success=success,
                duration_ms=duration_ms,
                error_message=error_message,
            )
            self._session._add_event(event)

            logger.info(
                "Tool execution completed",
                tool_name=command.tool_name,
                success=success,
                duration_ms=duration_ms,
            )

    async def get_tool(
        self,
        query: GetToolQuery,
    ) -> Tool | None:
        """Handle get tool query."""
        return self._session.get_tool(query.name)

    async def list_tools(
        self,
        query: ListToolsQuery,
    ) -> dict[str, Any]:
        """Handle list tools query."""
        tools = self._session.list_tools()

        # Filter by category if specified
        if query.category:
            tools = [t for t in tools if t.category == query.category]

        # Filter by enabled status
        if query.enabled_only:
            tools = [t for t in tools if t.enabled]

        return {
            "tools": [t.to_mcp_format() for t in tools],
        }
