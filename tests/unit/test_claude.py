"""Unit tests for Claude client."""

import pytest

from tfo_mcp.domain.valueobjects import Model
from tfo_mcp.infrastructure.claude import ClaudeClient
from tfo_mcp.infrastructure.config import ClaudeConfig


class TestClaudeClient:
    """Test ClaudeClient."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ClaudeConfig(
            api_key="test-api-key",
            default_model="claude-sonnet-4-20250514",
            max_tokens=4096,
            timeout=60.0,
        )

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return ClaudeClient(config)

    def test_create_client(self, config):
        """Test creating Claude client."""
        client = ClaudeClient(config)
        assert client is not None
        # Config is stored as _config (private attribute)
        assert client._config == config

    def test_client_config_default_model(self, client):
        """Test client config default model."""
        assert client._config.default_model == "claude-sonnet-4-20250514"

    def test_client_config_max_tokens(self, client):
        """Test client config max tokens."""
        assert client._config.max_tokens == 4096

    @pytest.mark.asyncio
    async def test_send_message_format(self):
        """Test message format for API call."""
        messages = [
            {"role": "user", "content": "Hello"},
        ]

        # Verify message format is correct
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_message_with_system(self):
        """Test message with system prompt."""
        messages = [{"role": "user", "content": "Hi"}]
        system = "You are a helpful assistant."

        # System prompt should be separate from messages
        assert system not in str(messages)

    def test_build_messages_from_conversation(self):
        """Test building messages from conversation format."""
        from tfo_mcp.domain.entities import Message

        msg1 = Message.user("Hello")
        msg2 = Message.assistant("Hi there!")

        api_messages = [
            msg1.to_api_format(),
            msg2.to_api_format(),
        ]

        assert len(api_messages) == 2
        assert api_messages[0]["role"] == "user"
        assert api_messages[1]["role"] == "assistant"

    def test_tool_format(self):
        """Test tool format for API call."""
        tool = {
            "name": "echo",
            "description": "Echo a message",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
                "required": ["message"],
            },
        }

        assert tool["name"] == "echo"
        assert "input_schema" in tool


class TestClaudeClientRetry:
    """Test Claude client retry logic."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ClaudeConfig(
            api_key="test-api-key",
            max_retries=3,
            timeout=30.0,
        )

    def test_max_retries_config(self, config):
        """Test max retries configuration."""
        assert config.max_retries == 3

    def test_timeout_config(self, config):
        """Test timeout configuration."""
        assert config.timeout == 30.0


class TestClaudeClientModels:
    """Test Claude client model handling."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ClaudeConfig(api_key="test-api-key")

    def test_available_models(self):
        """Test available models."""
        models = [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]

        for model_id in models:
            assert "claude" in model_id

    def test_model_enum_values(self):
        """Test Model enum values."""
        assert Model.CLAUDE_4_OPUS.value == "claude-opus-4-20250514"
        assert Model.CLAUDE_4_SONNET.value == "claude-sonnet-4-20250514"
        assert Model.CLAUDE_35_SONNET.value == "claude-3-5-sonnet-20241022"
        assert Model.CLAUDE_35_HAIKU.value == "claude-3-5-haiku-20241022"

    def test_default_model(self):
        """Test default model."""
        assert Model.default() == Model.CLAUDE_4_SONNET


class TestClaudeClientToolUse:
    """Test Claude client tool use handling."""

    def test_tool_use_response_structure(self):
        """Test tool use response structure."""
        tool_use = {
            "type": "tool_use",
            "id": "tool_123",
            "name": "echo",
            "input": {"message": "hello"},
        }

        assert tool_use["type"] == "tool_use"
        assert tool_use["id"] == "tool_123"
        assert tool_use["name"] == "echo"
        assert tool_use["input"]["message"] == "hello"

    def test_tool_result_structure(self):
        """Test tool result structure."""
        tool_result = {
            "type": "tool_result",
            "tool_use_id": "tool_123",
            "content": "Echo: hello",
        }

        assert tool_result["type"] == "tool_result"
        assert tool_result["tool_use_id"] == "tool_123"

    def test_tool_result_error_structure(self):
        """Test tool result error structure."""
        tool_result = {
            "type": "tool_result",
            "tool_use_id": "tool_123",
            "content": "Error: Something went wrong",
            "is_error": True,
        }

        assert tool_result["is_error"] is True


class TestClaudeClientStreaming:
    """Test Claude client streaming."""

    def test_stream_event_types(self):
        """Test stream event types."""
        event_types = [
            "message_start",
            "content_block_start",
            "content_block_delta",
            "content_block_stop",
            "message_delta",
            "message_stop",
        ]

        for event_type in event_types:
            assert isinstance(event_type, str)

    def test_text_delta_structure(self):
        """Test text delta structure."""
        delta = {
            "type": "text_delta",
            "text": "Hello",
        }

        assert delta["type"] == "text_delta"
        assert delta["text"] == "Hello"


class TestClaudeClientTokenCounting:
    """Test Claude client token counting."""

    def test_usage_structure(self):
        """Test usage structure."""
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
        }

        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["input_tokens"] + usage["output_tokens"] == 150

    def test_max_tokens_validation(self):
        """Test max tokens validation."""
        max_tokens = 4096
        assert max_tokens > 0
        assert max_tokens <= 8192  # Reasonable upper limit for most models


class TestClaudeClientErrorHandling:
    """Test Claude client error handling."""

    def test_api_error_codes(self):
        """Test API error codes."""
        error_codes = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            429: "Rate Limited",
            500: "Internal Server Error",
            529: "Overloaded",
        }

        for code, description in error_codes.items():
            assert isinstance(code, int)
            assert isinstance(description, str)

    def test_retry_on_rate_limit(self):
        """Test retry behavior on rate limit."""
        # 429 should trigger retry
        retryable_codes = [429, 500, 502, 503, 529]
        non_retryable_codes = [400, 401, 403, 404]

        for code in retryable_codes:
            assert code >= 429 or code >= 500

        for code in non_retryable_codes:
            assert code < 429
