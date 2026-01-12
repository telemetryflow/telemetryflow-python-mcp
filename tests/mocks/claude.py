"""Mock objects for Claude API client."""

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock


@dataclass
class MockClaudeMessage:
    """Mock Claude message response."""

    id: str = "msg_mock123"
    type: str = "message"
    role: str = "assistant"
    content: list[dict[str, Any]] = field(
        default_factory=lambda: [{"type": "text", "text": "Mock response"}]
    )
    model: str = "claude-sonnet-4-20250514"
    stop_reason: str = "end_turn"
    stop_sequence: str | None = None
    usage: dict[str, int] = field(default_factory=lambda: {"input_tokens": 10, "output_tokens": 20})


@dataclass
class MockClaudeToolUseContent:
    """Mock Claude tool use content."""

    type: str = "tool_use"
    id: str = "tool_use_123"
    name: str = "test_tool"
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class MockClaudeTextContent:
    """Mock Claude text content."""

    type: str = "text"
    text: str = "Mock response"


class MockClaudeService:
    """Mock Claude service for testing."""

    def __init__(self) -> None:
        """Initialize mock service."""
        self.messages: list[dict[str, Any]] = []
        self.send_message = AsyncMock(return_value=mock_claude_response())
        self.send_message_with_tools = AsyncMock(return_value=mock_claude_tool_use_response())

    def reset(self) -> None:
        """Reset mock state."""
        self.messages.clear()
        self.send_message.reset_mock()
        self.send_message_with_tools.reset_mock()

    def set_response(self, response: MockClaudeMessage) -> None:
        """Set the response for send_message."""
        self.send_message.return_value = response

    def set_tool_use_response(self, response: MockClaudeMessage) -> None:
        """Set the response for send_message_with_tools."""
        self.send_message_with_tools.return_value = response

    def set_error(self, error: Exception) -> None:
        """Set an error for send_message."""
        self.send_message.side_effect = error

    async def mock_send_message(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> MockClaudeMessage:
        """Mock send message implementation."""
        self.messages.extend(messages)
        return await self.send_message(messages, model, system, max_tokens)


def mock_claude_response(
    text: str = "Mock response",
    model: str = "claude-sonnet-4-20250514",
    input_tokens: int = 10,
    output_tokens: int = 20,
) -> MockClaudeMessage:
    """Create a mock Claude response."""
    return MockClaudeMessage(
        content=[{"type": "text", "text": text}],
        model=model,
        usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
    )


def mock_claude_tool_use_response(
    tool_name: str = "test_tool",
    tool_id: str = "tool_use_123",
    tool_input: dict[str, Any] | None = None,
    text_before: str | None = None,
) -> MockClaudeMessage:
    """Create a mock Claude tool use response."""
    content: list[dict[str, Any]] = []

    if text_before:
        content.append({"type": "text", "text": text_before})

    content.append(
        {
            "type": "tool_use",
            "id": tool_id,
            "name": tool_name,
            "input": tool_input or {},
        }
    )

    return MockClaudeMessage(
        content=content,
        stop_reason="tool_use",
    )


def mock_claude_request(
    user_message: str = "Hello",
    system_prompt: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """Create a mock Claude request."""
    request: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_message}],
    }

    if system_prompt:
        request["system"] = system_prompt

    return request


def mock_claude_request_with_system(
    user_message: str = "Hello",
    system_prompt: str = "You are a helpful assistant.",
) -> dict[str, Any]:
    """Create a mock Claude request with system prompt."""
    return mock_claude_request(user_message=user_message, system_prompt=system_prompt)


def mock_claude_request_with_tools(
    user_message: str = "Hello",
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a mock Claude request with tools."""
    request = mock_claude_request(user_message=user_message)
    request["tools"] = tools or [
        {
            "name": "test_tool",
            "description": "A test tool",
            "input_schema": {
                "type": "object",
                "properties": {"param": {"type": "string"}},
            },
        }
    ]
    return request


def mock_claude_stream_events() -> list[dict[str, Any]]:
    """Create mock Claude stream events."""
    return [
        {
            "type": "message_start",
            "message": {
                "id": "msg_mock123",
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": "claude-sonnet-4-20250514",
            },
        },
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "text", "text": ""},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": "Hello"},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": " world!"},
        },
        {
            "type": "content_block_stop",
            "index": 0,
        },
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn"},
            "usage": {"output_tokens": 5},
        },
        {
            "type": "message_stop",
        },
    ]
