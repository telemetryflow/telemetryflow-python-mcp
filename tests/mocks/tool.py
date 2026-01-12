"""Mock objects for tool testing."""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

from tfo_mcp.domain.entities import Tool, ToolResult


@dataclass
class MockToolCall:
    """Record of a tool call."""

    tool_name: str
    input_data: dict[str, Any]
    result: ToolResult | None = None
    error: Exception | None = None


class MockToolHandler:
    """Mock tool handler for testing."""

    def __init__(
        self,
        return_value: ToolResult | None = None,
        error: Exception | None = None,
    ) -> None:
        """Initialize mock handler."""
        self._return_value = return_value or ToolResult.text("Mock result")
        self._error = error
        self._calls: list[MockToolCall] = []
        self.handler = AsyncMock(side_effect=self._handle)

    async def _handle(self, input_data: dict[str, Any]) -> ToolResult:
        """Handle tool call."""
        call = MockToolCall(tool_name="mock", input_data=input_data)

        if self._error:
            call.error = self._error
            self._calls.append(call)
            raise self._error

        call.result = self._return_value
        self._calls.append(call)
        return self._return_value

    @property
    def calls(self) -> list[MockToolCall]:
        """Get recorded calls."""
        return self._calls.copy()

    @property
    def call_count(self) -> int:
        """Get number of calls."""
        return len(self._calls)

    @property
    def last_call(self) -> MockToolCall | None:
        """Get last call."""
        return self._calls[-1] if self._calls else None

    def set_return_value(self, result: ToolResult) -> None:
        """Set return value."""
        self._return_value = result
        self._error = None

    def set_error(self, error: Exception) -> None:
        """Set error to raise."""
        self._error = error

    def reset(self) -> None:
        """Reset mock state."""
        self._calls.clear()
        self.handler.reset_mock()


def mock_tool(
    name: str = "test_tool",
    description: str = "A test tool",
    category: str = "utility",
    tags: list[str] | None = None,
) -> Tool:
    """Create a mock tool."""
    return Tool.create(
        name=name,
        description=description,
        input_schema={"type": "object", "properties": {}},
        category=category,
        tags=tags or [],
    )


def mock_tool_with_schema(
    name: str = "test_tool",
    description: str = "A test tool",
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> Tool:
    """Create a mock tool with input schema."""
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": properties
        or {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "integer", "description": "Second parameter"},
        },
    }

    if required:
        input_schema["required"] = required

    return Tool.create(
        name=name,
        description=description,
        input_schema=input_schema,
    )


def mock_tool_with_error(
    name: str = "error_tool",
    error_message: str = "Tool execution failed",
) -> Tool:
    """Create a mock tool that returns an error."""

    async def error_handler(_input_data: dict[str, Any]) -> ToolResult:
        return ToolResult.error(error_message)

    return Tool.create(
        name=name,
        description="A tool that returns an error",
        input_schema={"type": "object"},
        handler=error_handler,
    )


def mock_tool_call(
    tool_name: str = "test_tool",
    input_data: dict[str, Any] | None = None,
) -> MockToolCall:
    """Create a mock tool call record."""
    return MockToolCall(
        tool_name=tool_name,
        input_data=input_data or {},
    )


def mock_tool_calls(count: int = 3) -> list[MockToolCall]:
    """Create multiple mock tool calls."""
    return [
        MockToolCall(
            tool_name=f"tool_{i}",
            input_data={"index": i},
        )
        for i in range(count)
    ]


def builtin_tools() -> list[str]:
    """Get list of built-in tool names."""
    return [
        "echo",
        "read_file",
        "write_file",
        "list_directory",
        "search_files",
        "execute_command",
        "system_info",
        "claude_conversation",
    ]


def mock_tool_input_schema() -> dict[str, Any]:
    """Create a standard mock tool input schema."""
    return {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message to process",
            },
            "options": {
                "type": "object",
                "description": "Additional options",
                "properties": {
                    "verbose": {"type": "boolean", "default": False},
                    "format": {"type": "string", "enum": ["json", "text"]},
                },
            },
        },
        "required": ["message"],
    }


async def success_handler(input_data: dict[str, Any]) -> ToolResult:
    """A handler that always succeeds."""
    return ToolResult.text(f"Success: {input_data}")


async def error_handler(_input_data: dict[str, Any]) -> ToolResult:
    """A handler that always errors."""
    return ToolResult.error("Handler error")


async def echo_handler(input_data: dict[str, Any]) -> ToolResult:
    """A handler that echoes input."""
    message = input_data.get("message", "")
    return ToolResult.text(f"Echo: {message}")
