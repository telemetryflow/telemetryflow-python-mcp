from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tfo_mcp.domain.entities import Message
from tfo_mcp.domain.valueobjects import Model, SystemPrompt
from tfo_mcp.infrastructure.claude.client import ClaudeClient
from tfo_mcp.infrastructure.config import ClaudeConfig


def _make_mock_response(
    text="Response", has_tool_use=False, tool_id="tool_123", tool_name="echo", tool_input=None
):
    from collections import namedtuple

    Usage = namedtuple("Usage", ["input_tokens", "output_tokens"])
    content = []
    if text:
        tb = MagicMock()
        tb.type = "text"
        tb.text = text
        content.append(tb)
    if has_tool_use:
        tb2 = MagicMock()
        tb2.type = "tool_use"
        tb2.id = tool_id
        tb2.name = tool_name
        tb2.input = tool_input or {}
        content.append(tb2)

    resp = MagicMock()
    resp.content = content
    resp.usage = Usage(input_tokens=10, output_tokens=20)
    resp.model = "claude-sonnet-4-20250514"
    resp.stop_reason = "end_turn" if not has_tool_use else "tool_use"
    return resp


@pytest.fixture
def config():
    return ClaudeConfig(
        api_key="test-key",
        default_model="claude-sonnet-4-20250514",
        max_tokens=4096,
        timeout=60.0,
    )


@pytest.fixture
def client(config):
    return ClaudeClient(config)


class TestClaudeClientInit:
    def test_init_creates_client(self, config):
        client = ClaudeClient(config)
        assert client._config == config
        assert client._client is not None

    def test_init_with_base_url(self):
        config = ClaudeConfig(api_key="key", base_url="http://custom:8080")
        client = ClaudeClient(config)
        assert client._config.base_url == "http://custom:8080"


class TestBuildTools:
    def test_none_tools(self, client):
        assert client._build_tools(None) is None
        assert client._build_tools([]) is None

    def test_builds_tool_list(self, client):
        from tfo_mcp.domain.entities import Tool

        tool = Tool.create(
            name="test_tool",
            description="A test",
            input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
        )
        result = client._build_tools([tool])
        assert len(result) == 1
        assert result[0]["name"] == "test_tool"
        assert "input_schema" in result[0]

    def test_builds_multiple_tools(self, client):
        from tfo_mcp.domain.entities import Tool

        tools = [
            Tool.create(name=f"tool_{i}", description=f"T{i}", input_schema={"type": "object"})
            for i in range(3)
        ]
        result = client._build_tools(tools)
        assert len(result) == 3


class TestBuildMessages:
    def test_builds_message_list(self, client):
        messages = [
            Message.user("Hello"),
            Message.assistant("Hi there"),
        ]
        result = client._build_messages(messages)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_empty_messages(self, client):
        result = client._build_messages([])
        assert result == []


class TestParseResponse:
    def test_parses_text_response(self, client):
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Hello world"

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "end_turn"

        result = client._parse_response(mock_response)
        assert result.role.value == "assistant"
        assert result.text == "Hello world"
        assert result.input_tokens == 10
        assert result.output_tokens == 20

    def test_parses_tool_use_response(self, client):
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Let me help"

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "tool_123"
        tool_block.name = "echo"
        tool_block.input = {"message": "hi"}

        mock_response = MagicMock()
        mock_response.content = [text_block, tool_block]
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 30
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "tool_use"

        result = client._parse_response(mock_response)
        assert result.has_tool_use
        assert len(result.tool_uses) == 1
        assert result.tool_uses[0].name == "echo"

    def test_parses_tool_use_with_none_input(self, client):
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "tool_456"
        tool_block.name = "test"
        tool_block.input = None

        mock_response = MagicMock()
        mock_response.content = [tool_block]
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 10
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.stop_reason = "tool_use"

        result = client._parse_response(mock_response)
        assert result.tool_uses[0].input == {}


class TestCreateMessage:
    async def test_creates_message(self, client):
        mock_response = _make_mock_response("Response")
        client._client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.create_message(
            messages=[Message.user("Hi")],
            model=Model.CLAUDE_SONNET_4,
        )
        assert result.text == "Response"

    async def test_with_system_prompt(self, client):
        mock_response = _make_mock_response("ok")
        client._client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.create_message(
            messages=[Message.user("Hi")],
            model=Model.CLAUDE_SONNET_4,
            system_prompt=SystemPrompt(value="Be helpful"),
        )
        assert result is not None
        call_kwargs = client._client.messages.create.call_args[1]
        assert call_kwargs["system"] == "Be helpful"

    async def test_with_empty_system_prompt(self, client):
        mock_response = _make_mock_response("ok")
        client._client.messages.create = AsyncMock(return_value=mock_response)

        await client.create_message(
            messages=[Message.user("Hi")],
            model=Model.CLAUDE_SONNET_4,
            system_prompt=SystemPrompt(value=""),
        )
        call_kwargs = client._client.messages.create.call_args[1]
        assert "system" not in call_kwargs

    async def test_with_tools(self, client):
        from tfo_mcp.domain.entities import Tool

        tool = Tool.create(name="test", description="T", input_schema={"type": "object"})
        mock_response = _make_mock_response("ok")
        client._client.messages.create = AsyncMock(return_value=mock_response)

        await client.create_message(
            messages=[Message.user("Hi")],
            model=Model.CLAUDE_SONNET_4,
            tools=[tool],
        )
        call_kwargs = client._client.messages.create.call_args[1]
        assert "tools" in call_kwargs


class TestCreateMessageStream:
    async def test_streams_events(self, client):
        mock_event1 = MagicMock()
        mock_event1.type = "message_start"
        mock_event2 = MagicMock()
        mock_event2.type = "content_block_delta"

        class MockStream:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def __aiter__(self):
                yield mock_event1
                yield mock_event2

        client._client.messages.stream = MagicMock(return_value=MockStream())

        events = []
        async for event in client.create_message_stream(
            messages=[Message.user("Hi")],
            model=Model.CLAUDE_SONNET_4,
        ):
            events.append(event)

        assert len(events) == 2
        assert events[0]["type"] == "message_start"

    async def test_skips_events_without_type(self, client):
        mock_event = MagicMock(spec=[])
        mock_event_with_type = MagicMock()
        mock_event_with_type.type = "message_start"

        class MockStream:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def __aiter__(self):
                yield mock_event
                yield mock_event_with_type

        client._client.messages.stream = MagicMock(return_value=MockStream())

        events = []
        async for event in client.create_message_stream(
            messages=[Message.user("Hi")],
            model=Model.CLAUDE_SONNET_4,
        ):
            events.append(event)

        assert len(events) == 1


class TestCountTokens:
    async def test_counts_tokens(self, client):
        mock_result = MagicMock()
        mock_result.input_tokens = 42

        client._client.messages.count_tokens = AsyncMock(return_value=mock_result)

        result = await client.count_tokens(
            messages=[Message.user("Hello")],
            model=Model.CLAUDE_SONNET_4,
        )
        assert result == 42

    async def test_with_system_prompt(self, client):
        mock_result = MagicMock()
        mock_result.input_tokens = 50

        client._client.messages.count_tokens = AsyncMock(return_value=mock_result)

        result = await client.count_tokens(
            messages=[Message.user("Hello")],
            model=Model.CLAUDE_SONNET_4,
            system_prompt=SystemPrompt(value="Be helpful"),
        )
        assert result == 50
        call_kwargs = client._client.messages.count_tokens.call_args[1]
        assert call_kwargs["system"] == "Be helpful"
