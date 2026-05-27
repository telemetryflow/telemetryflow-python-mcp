from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from tfo_mcp.application.commands.commands import ExecuteToolCommand, RegisterToolCommand
from tfo_mcp.application.handlers.tool_handler import ToolHandler
from tfo_mcp.application.queries.queries import GetToolQuery, ListToolsQuery
from tfo_mcp.domain.aggregates import Session
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Tool, ToolResult


@pytest.fixture
def session():
    s = Session.create()
    s.initialize(ClientInfo(name="test", version="1.0.0"))
    return s


@pytest.fixture
def handler(session):
    return ToolHandler(session)


@pytest.fixture
def registered_tool(session):
    async def echo_handler(input_data):
        return ToolResult.text(f"echo: {input_data.get('msg', '')}")

    tool = Tool.create(
        name="echo",
        description="Echo tool",
        input_schema={"type": "object"},
        handler=echo_handler,
        category="utility",
    )
    session.register_tool(tool)
    return tool


class TestHandleRegister:
    async def test_registers_tool(self, handler, session):
        tool = Tool.create(
            name="new_tool",
            description="A new tool",
            input_schema={"type": "object"},
            category="test",
        )
        cmd = RegisterToolCommand(tool=tool)
        await handler.handle_register(cmd)

        assert session.get_tool("new_tool") is not None

    async def test_emits_event(self, handler, session):
        tool = Tool.create(
            name="tool_with_event",
            description="Tool",
            input_schema={"type": "object"},
            category="test",
        )
        cmd = RegisterToolCommand(tool=tool)
        await handler.handle_register(cmd)

        events = session.get_events()
        event_types = [type(e).__name__ for e in events]
        assert "ToolRegisteredEvent" in event_types


class TestHandleExecute:
    @patch("tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=None)
    async def test_executes_tool(self, _mock_tel, handler, registered_tool):  # noqa: ARG002
        cmd = ExecuteToolCommand(tool_name="echo", arguments={"msg": "hello"})
        result = await handler.handle_execute(cmd)

        assert not result.is_error
        assert "echo: hello" in result.content[0]["text"]

    @patch("tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=None)
    async def test_tool_not_found(self, _mock_tel, handler):
        cmd = ExecuteToolCommand(tool_name="nonexistent", arguments={})
        result = await handler.handle_execute(cmd)

        assert result.is_error
        assert "Tool not found" in result.content[0]["text"]

    @patch("tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=None)
    async def test_tool_disabled(
        self, _mock_tel, handler, session, registered_tool  # noqa: ARG002
    ):
        registered_tool.enabled = False

        cmd = ExecuteToolCommand(tool_name="echo", arguments={})
        result = await handler.handle_execute(cmd)

        assert result.is_error
        assert "disabled" in result.content[0]["text"].lower()

    @patch("tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=None)
    async def test_tool_timeout(self, _mock_tel, handler, session):
        async def slow_handler(_input_data):
            await asyncio.sleep(10)
            return ToolResult.text("done")

        tool = Tool.create(
            name="slow_tool",
            description="Slow",
            input_schema={"type": "object"},
            handler=slow_handler,
            timeout_seconds=0.01,
        )
        session.register_tool(tool)

        cmd = ExecuteToolCommand(tool_name="slow_tool", arguments={})
        result = await handler.handle_execute(cmd)

        assert result.is_error
        assert "timed out" in result.content[0]["text"].lower()

    @patch("tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=None)
    async def test_tool_execution_error(self, _mock_tel, handler, session):
        async def error_handler(_input_data):
            raise RuntimeError("boom")

        tool = Tool.create(
            name="error_tool",
            description="Error",
            input_schema={"type": "object"},
            handler=error_handler,
        )
        session.register_tool(tool)

        cmd = ExecuteToolCommand(tool_name="error_tool", arguments={})
        result = await handler.handle_execute(cmd)

        assert result.is_error
        assert "boom" in result.content[0]["text"]

    @patch("tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=None)
    async def test_tool_returns_error_result(self, _mock_tel, handler, session):
        async def failing_handler(_input_data):
            return ToolResult.error("bad input")

        tool = Tool.create(
            name="failing_tool",
            description="Fails",
            input_schema={"type": "object"},
            handler=failing_handler,
        )
        session.register_tool(tool)

        cmd = ExecuteToolCommand(tool_name="failing_tool", arguments={})
        result = await handler.handle_execute(cmd)

        assert result.is_error

    async def test_with_telemetry(self, handler, registered_tool):  # noqa: ARG002
        mock_tel = MagicMock()
        mock_tel.span.return_value = MagicMock()
        mock_tel.span.return_value.__enter__ = MagicMock(return_value=None)
        mock_tel.span.return_value.__exit__ = MagicMock(return_value=None)

        with patch(
            "tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=mock_tel
        ):
            cmd = ExecuteToolCommand(tool_name="echo", arguments={"msg": "hi"})
            result = await handler.handle_execute(cmd)

            assert not result.is_error
            mock_tel.record_tool_call.assert_called_once()
            call_kwargs = mock_tel.record_tool_call.call_args[1]
            assert call_kwargs["success"] is True
            assert call_kwargs["tool_name"] == "echo"

    async def test_with_telemetry_failure(self, handler, session):
        async def error_handler(_input_data):
            raise RuntimeError("oops")

        tool = Tool.create(
            name="fail_tool",
            description="Fails",
            input_schema={"type": "object"},
            handler=error_handler,
        )
        session.register_tool(tool)

        mock_tel = MagicMock()
        mock_tel.span.return_value = MagicMock()
        mock_tel.span.return_value.__enter__ = MagicMock(return_value=None)
        mock_tel.span.return_value.__exit__ = MagicMock(return_value=None)

        with patch(
            "tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=mock_tel
        ):
            cmd = ExecuteToolCommand(tool_name="fail_tool", arguments={})
            result = await handler.handle_execute(cmd)

            assert result.is_error
            mock_tel.record_tool_call.assert_called_once()
            call_kwargs = mock_tel.record_tool_call.call_args[1]
            assert call_kwargs["success"] is False

    @patch("tfo_mcp.application.handlers.tool_handler.get_telemetry_client", return_value=None)
    async def test_emits_executed_event(
        self, _mock_tel, handler, session, registered_tool  # noqa: ARG002
    ):
        cmd = ExecuteToolCommand(tool_name="echo", arguments={"msg": "hi"})
        await handler.handle_execute(cmd)

        events = session.get_events()
        event_types = [type(e).__name__ for e in events]
        assert "ToolExecutedEvent" in event_types


class TestGetTool:
    async def test_gets_existing(self, handler, registered_tool):  # noqa: ARG002
        query = GetToolQuery(name="echo")
        result = await handler.get_tool(query)
        assert result is not None
        assert str(result.name) == "echo"

    async def test_returns_none_for_missing(self, handler):
        query = GetToolQuery(name="nonexistent")
        result = await handler.get_tool(query)
        assert result is None


class TestListTools:
    async def test_lists_all(self, handler, session, registered_tool):  # noqa: ARG002
        tool2 = Tool.create(
            name="tool2", description="T2", input_schema={"type": "object"}, category="system"
        )
        session.register_tool(tool2)

        query = ListToolsQuery(enabled_only=False)
        result = await handler.list_tools(query)
        assert len(result["tools"]) == 2

    async def test_filter_by_category(self, handler, session, registered_tool):  # noqa: ARG002
        tool2 = Tool.create(
            name="tool2", description="T2", input_schema={"type": "object"}, category="system"
        )
        session.register_tool(tool2)

        query = ListToolsQuery(category="utility", enabled_only=False)
        result = await handler.list_tools(query)
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "echo"

    async def test_filter_enabled_only(self, handler, session, registered_tool):  # noqa: ARG002
        tool2 = Tool.create(
            name="disabled_tool", description="Disabled", input_schema={"type": "object"}
        )
        tool2.enabled = False
        session.register_tool(tool2)

        query = ListToolsQuery(enabled_only=True)
        result = await handler.list_tools(query)
        names = [t["name"] for t in result["tools"]]
        assert "disabled_tool" not in names

    async def test_returns_mcp_format(self, handler, registered_tool):  # noqa: ARG002
        query = ListToolsQuery(enabled_only=True)
        result = await handler.list_tools(query)
        tool = result["tools"][0]
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
