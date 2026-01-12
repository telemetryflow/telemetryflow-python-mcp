"""Integration tests for Claude client.

These tests require a valid ANTHROPIC_API_KEY environment variable.
They are skipped if the key is not set.
"""

import os

import pytest

from tfo_mcp.domain.valueobjects import Model
from tfo_mcp.infrastructure.claude import ClaudeClient
from tfo_mcp.infrastructure.config import ClaudeConfig


def skip_if_no_api_key():
    """Skip test if no API key is set."""
    return pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )


@skip_if_no_api_key()
class TestClaudeClientIntegration:
    """Integration tests for Claude client."""

    @pytest.fixture
    def config(self):
        """Create config with API key."""
        return ClaudeConfig(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            default_model="claude-3-5-haiku-20241022",  # Use fastest model for tests
            max_tokens=100,
            timeout=30.0,
        )

    @pytest.fixture
    def client(self, config):
        """Create Claude client."""
        return ClaudeClient(config)

    @pytest.mark.asyncio
    async def test_simple_message(self, client):
        """Test sending a simple message."""
        messages = [{"role": "user", "content": "Say hello in one word."}]

        response = await client.send_message(messages)

        assert response is not None
        assert len(response.content) > 0
        assert response.content[0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_message_with_system_prompt(self, client):
        """Test message with system prompt."""
        messages = [{"role": "user", "content": "What are you?"}]
        system = "You are a helpful coding assistant. Be brief."

        response = await client.send_message(messages, system=system)

        assert response is not None

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, client):
        """Test multi-turn conversation."""
        messages = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Nice to meet you, Alice!"},
            {"role": "user", "content": "What's my name? Answer in one word."},
        ]

        response = await client.send_message(messages)

        assert response is not None
        text = response.content[0]["text"].lower()
        assert "alice" in text

    @pytest.mark.asyncio
    async def test_tool_use(self, client):
        """Test tool use capability."""
        messages = [{"role": "user", "content": "What is 2+2? Use the calculator."}]
        tools = [
            {
                "name": "calculator",
                "description": "Perform arithmetic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                    },
                    "required": ["expression"],
                },
            }
        ]

        response = await client.send_message_with_tools(messages, tools)

        assert response is not None
        # Response might contain tool_use or text
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_token_usage(self, client):
        """Test token usage is reported."""
        messages = [{"role": "user", "content": "Hi"}]

        response = await client.send_message(messages)

        assert response.usage is not None
        assert response.usage["input_tokens"] > 0
        assert response.usage["output_tokens"] > 0


@skip_if_no_api_key()
class TestClaudeClientErrorHandling:
    """Test Claude client error handling."""

    @pytest.fixture
    def config(self):
        """Create config with API key."""
        return ClaudeConfig(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            default_model="claude-3-5-haiku-20241022",
            max_tokens=100,
            timeout=5.0,  # Short timeout for error tests
        )

    @pytest.fixture
    def client(self, config):
        """Create Claude client."""
        return ClaudeClient(config)

    @pytest.mark.asyncio
    async def test_empty_messages(self, client):
        """Test error on empty messages."""
        with pytest.raises((ValueError, TypeError, RuntimeError)):
            await client.send_message([])

    @pytest.mark.asyncio
    async def test_invalid_model(self):
        """Test error on invalid model."""
        config = ClaudeConfig(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            default_model="invalid-model-name",
            max_tokens=100,
        )
        client = ClaudeClient(config)

        with pytest.raises((ValueError, TypeError, RuntimeError)):
            await client.send_message([{"role": "user", "content": "Hi"}])


class TestClaudeClientMocked:
    """Test Claude client with mocks (no API key required)."""

    @pytest.fixture
    def config(self):
        """Create config without API key."""
        return ClaudeConfig(
            api_key="test-key",
            default_model="claude-sonnet-4-20250514",
            max_tokens=4096,
        )

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = ClaudeClient(config)

        assert client is not None
        assert client._config.default_model == "claude-sonnet-4-20250514"
        assert client._config.max_tokens == 4096

    def test_message_format_validation(self):
        """Test message format validation."""
        from tfo_mcp.domain.entities import Message

        # Valid message format
        msg = Message.user("Hello")
        api_format = msg.to_api_format()

        assert api_format["role"] == "user"
        # Content is a list of content blocks
        assert isinstance(api_format["content"], list)
        assert api_format["content"][0]["text"] == "Hello"

    def test_tool_format_validation(self):
        """Test tool format validation."""
        from tfo_mcp.domain.entities import Tool

        tool = Tool.create(
            name="echo",
            description="Echo a message",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        )

        mcp_format = tool.to_mcp_format()

        # Should have required fields for Claude API
        assert "name" in mcp_format
        assert "description" in mcp_format
        assert "inputSchema" in mcp_format


class TestClaudeModels:
    """Test Claude model selection."""

    def test_opus_model(self):
        """Test Opus model."""
        assert Model.CLAUDE_4_OPUS.value == "claude-opus-4-20250514"

    def test_sonnet_model(self):
        """Test Sonnet model."""
        assert Model.CLAUDE_4_SONNET.value == "claude-sonnet-4-20250514"

    def test_sonnet_35_model(self):
        """Test Sonnet 3.5 model."""
        assert Model.CLAUDE_35_SONNET.value == "claude-3-5-sonnet-20241022"

    def test_haiku_model(self):
        """Test Haiku model."""
        assert Model.CLAUDE_35_HAIKU.value == "claude-3-5-haiku-20241022"

    def test_default_is_sonnet(self):
        """Test default model is Sonnet."""
        assert Model.default() == Model.CLAUDE_4_SONNET
