"""Advanced unit tests for tool handler with mocking and error scenarios."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest import mock

import pytest

from tfo_mcp.application.commands import ExecuteToolCommand
from tfo_mcp.application.handlers import ToolHandler
from tfo_mcp.domain.aggregates import Session
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Tool, ToolResult


class TestToolHandlerExecution:
    """Test tool handler execution scenarios."""

    @pytest.fixture
    def session(self) -> Session:
        """Create initialized session with tools."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    @pytest.fixture
    def handler(self, session: Session) -> ToolHandler:
        """Create tool handler."""
        return ToolHandler(session)

    def test_execute_simple_tool(self, session: Session, handler: ToolHandler) -> None:
        """Test executing a simple tool."""

        async def echo_handler(input_data: dict[str, Any]) -> ToolResult:
            return ToolResult.text(f"Echo: {input_data.get('message', '')}")

        tool = Tool.create(
            name="echo",
            description="Echo tool",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            handler=echo_handler,
        )
        session.register_tool(tool)

        command = ExecuteToolCommand(tool_name="echo", arguments={"message": "Hello"})
        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))
        result_dict = result.to_dict()

        assert not result.is_error
        assert "Hello" in result_dict["content"][0]["text"]

    def test_execute_nonexistent_tool(self, handler: ToolHandler) -> None:
        """Test executing a nonexistent tool."""
        command = ExecuteToolCommand(tool_name="nonexistent", arguments={})
        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))
        result_dict = result.to_dict()

        assert result.is_error
        assert "not found" in result_dict["content"][0]["text"].lower()

    def test_execute_tool_with_error(self, session: Session, handler: ToolHandler) -> None:
        """Test executing a tool that raises an error."""

        async def error_handler(_input_data: dict[str, Any]) -> ToolResult:
            raise ValueError("Simulated error")

        tool = Tool.create(
            name="error_tool",
            description="Tool that errors",
            input_schema={"type": "object"},
            handler=error_handler,
        )
        session.register_tool(tool)

        command = ExecuteToolCommand(tool_name="error_tool", arguments={})
        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))
        result_dict = result.to_dict()

        assert result.is_error
        assert "error" in result_dict["content"][0]["text"].lower()


class TestToolHandlerWithMocks:
    """Test tool handler with mocked dependencies."""

    @pytest.fixture
    def mock_session(self) -> mock.MagicMock:
        """Create mock session."""
        session = mock.MagicMock()
        session.is_ready = True
        return session

    def test_tool_execution_calls_handler(self) -> None:
        """Test that tool execution calls the handler function."""
        mock_handler = mock.AsyncMock(return_value=ToolResult.text("Success"))

        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))

        tool = Tool.create(
            name="mock_tool",
            description="Mock tool",
            input_schema={"type": "object"},
            handler=mock_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        command = ExecuteToolCommand(tool_name="mock_tool", arguments={"key": "value"})

        asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))

        mock_handler.assert_called_once_with({"key": "value"})

    def test_tool_execution_with_telemetry(self) -> None:
        """Test tool execution records telemetry."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))

        async def simple_handler(_input: dict[str, Any]) -> ToolResult:
            return ToolResult.text("OK")

        tool = Tool.create(
            name="telemetry_tool",
            description="Tool for telemetry test",
            input_schema={"type": "object"},
            handler=simple_handler,
        )
        session.register_tool(tool)

        with mock.patch(
            "tfo_mcp.application.handlers.tool_handler.get_telemetry_client"
        ) as mock_get:
            mock_telemetry = mock.MagicMock()
            mock_telemetry.is_enabled = True
            # Mock the context manager for span
            mock_span = mock.MagicMock()
            mock_span.__enter__ = mock.MagicMock(return_value=mock_span)
            mock_span.__exit__ = mock.MagicMock(return_value=False)
            mock_telemetry.span.return_value = mock_span
            mock_get.return_value = mock_telemetry

            handler = ToolHandler(session)
            command = ExecuteToolCommand(tool_name="telemetry_tool", arguments={})

            asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))

            # Telemetry should have been recorded (record_tool_call is the actual method)
            mock_telemetry.record_tool_call.assert_called()


class TestToolHandlerEdgeCases:
    """Test tool handler edge cases."""

    @pytest.fixture
    def session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    def test_empty_arguments(self, session: Session) -> None:
        """Test executing tool with empty arguments."""

        async def no_args_handler(_input: dict[str, Any]) -> ToolResult:
            return ToolResult.text("No args needed")

        tool = Tool.create(
            name="no_args",
            description="No arguments",
            input_schema={"type": "object", "properties": {}},
            handler=no_args_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        command = ExecuteToolCommand(tool_name="no_args", arguments={})

        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))

        assert not result.is_error

    def test_large_arguments(self, session: Session) -> None:
        """Test executing tool with large argument data."""

        async def large_handler(input_data: dict[str, Any]) -> ToolResult:
            return ToolResult.text(f"Received {len(str(input_data))} chars")

        tool = Tool.create(
            name="large_args",
            description="Large arguments",
            input_schema={"type": "object"},
            handler=large_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        large_data = {"data": "x" * 100000}
        command = ExecuteToolCommand(tool_name="large_args", arguments=large_data)

        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))

        assert not result.is_error

    def test_special_characters_in_arguments(self, session: Session) -> None:
        """Test executing tool with special characters."""

        async def special_handler(input_data: dict[str, Any]) -> ToolResult:
            return ToolResult.text(input_data.get("text", ""))

        tool = Tool.create(
            name="special_chars",
            description="Special characters",
            input_schema={"type": "object"},
            handler=special_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        special_text = "Hello! @#$%^&*() 日本語 🎉"
        command = ExecuteToolCommand(tool_name="special_chars", arguments={"text": special_text})

        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))
        result_dict = result.to_dict()

        assert not result.is_error
        assert special_text in result_dict["content"][0]["text"]


class TestToolHandlerConcurrency:
    """Test tool handler concurrency scenarios."""

    @pytest.fixture
    def session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    @pytest.mark.asyncio
    async def test_concurrent_tool_executions(self, session: Session) -> None:
        """Test concurrent tool executions."""
        call_count = 0

        async def counting_handler(_input: dict[str, Any]) -> ToolResult:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return ToolResult.text(f"Call {call_count}")

        tool = Tool.create(
            name="concurrent_tool",
            description="Concurrent test",
            input_schema={"type": "object"},
            handler=counting_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)

        # Execute 10 concurrent calls
        commands = [
            ExecuteToolCommand(tool_name="concurrent_tool", arguments={"i": i}) for i in range(10)
        ]

        results = await asyncio.gather(*[handler.handle_execute(cmd) for cmd in commands])

        assert len(results) == 10
        assert all(not r.is_error for r in results)
        assert call_count == 10

    @pytest.mark.asyncio
    async def test_tool_execution_isolation(self, session: Session) -> None:
        """Test that tool executions are isolated."""
        shared_state: list[int] = []

        async def stateful_handler(input_data: dict[str, Any]) -> ToolResult:
            idx = input_data.get("idx", 0)
            shared_state.append(idx)
            await asyncio.sleep(0.01)
            return ToolResult.text(f"Added {idx}")

        tool = Tool.create(
            name="stateful_tool",
            description="Stateful test",
            input_schema={"type": "object"},
            handler=stateful_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)

        commands = [
            ExecuteToolCommand(tool_name="stateful_tool", arguments={"idx": i}) for i in range(5)
        ]

        await asyncio.gather(*[handler.handle_execute(cmd) for cmd in commands])

        # All indices should be recorded
        assert sorted(shared_state) == [0, 1, 2, 3, 4]


class TestToolHandlerResultFormats:
    """Test tool handler result format handling."""

    @pytest.fixture
    def session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    def test_text_result_format(self, session: Session) -> None:
        """Test text result format."""

        async def text_handler(_input: dict[str, Any]) -> ToolResult:
            return ToolResult.text("Plain text result")

        tool = Tool.create(
            name="text_tool",
            description="Text result",
            input_schema={"type": "object"},
            handler=text_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        command = ExecuteToolCommand(tool_name="text_tool", arguments={})

        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))
        result_dict = result.to_dict()

        assert "content" in result_dict
        assert result_dict["content"][0]["type"] == "text"

    def test_json_result_format(self, session: Session) -> None:
        """Test JSON result format."""

        async def json_handler(_input: dict[str, Any]) -> ToolResult:
            return ToolResult.json({"key": "value", "number": 42})

        tool = Tool.create(
            name="json_tool",
            description="JSON result",
            input_schema={"type": "object"},
            handler=json_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        command = ExecuteToolCommand(tool_name="json_tool", arguments={})

        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))
        result_dict = result.to_dict()

        assert not result.is_error
        assert "key" in result_dict["content"][0]["text"]

    def test_error_result_format(self, session: Session) -> None:
        """Test error result format."""

        async def error_handler(_input: dict[str, Any]) -> ToolResult:
            return ToolResult.error("Something went wrong")

        tool = Tool.create(
            name="error_tool",
            description="Error result",
            input_schema={"type": "object"},
            handler=error_handler,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        command = ExecuteToolCommand(tool_name="error_tool", arguments={})

        result = asyncio.get_event_loop().run_until_complete(handler.handle_execute(command))
        result_dict = result.to_dict()

        assert result_dict.get("isError") is True


class TestToolHandlerTimeout:
    """Test tool handler timeout behavior."""

    @pytest.fixture
    def session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    @pytest.mark.asyncio
    async def test_tool_with_custom_timeout(self, session: Session) -> None:
        """Test tool with custom timeout setting."""

        async def quick_handler(_input: dict[str, Any]) -> ToolResult:
            await asyncio.sleep(0.01)
            return ToolResult.text("Quick response")

        tool = Tool.create(
            name="quick_tool",
            description="Quick tool",
            input_schema={"type": "object"},
            handler=quick_handler,
            timeout_seconds=5.0,
        )
        session.register_tool(tool)

        handler = ToolHandler(session)
        command = ExecuteToolCommand(tool_name="quick_tool", arguments={})

        result = await handler.handle_execute(command)

        assert not result.is_error
