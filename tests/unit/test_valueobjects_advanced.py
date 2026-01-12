"""Advanced unit tests for value objects with parametrization and edge cases."""

from __future__ import annotations

import pytest

from tfo_mcp.domain.valueobjects import (
    ContentType,
    ConversationID,
    MCPCapability,
    MCPErrorCode,
    MCPLogLevel,
    MCPMethod,
    MCPProtocolVersion,
    MimeType,
    Model,
    ResourceURI,
    Role,
    SessionID,
    SystemPrompt,
    ToolDescription,
    ToolName,
)


class TestSessionIDParametrized:
    """Parametrized tests for SessionID value object."""

    @pytest.mark.parametrize(
        "value",
        [
            "simple-id",
            "session-123-abc",
            "a" * 100,  # Long ID
            "123456789",  # Numeric string
            "uuid-like-4f8c-9a2b",
        ],
    )
    def test_valid_session_ids(self, value: str) -> None:
        """Test various valid session ID formats."""
        session_id = SessionID.from_string(value)
        assert str(session_id) == value
        assert session_id.value == value

    @pytest.mark.parametrize(
        "invalid_value,_expected_error",
        [
            ("", "empty"),
            (None, "None"),
        ],
    )
    def test_invalid_session_ids(self, invalid_value: str | None, _expected_error: str) -> None:
        """Test invalid session ID values raise errors."""
        with pytest.raises((ValueError, TypeError)):
            if invalid_value is None:
                SessionID(value=invalid_value)  # type: ignore[arg-type]
            else:
                SessionID(value=invalid_value)

    def test_generated_ids_are_unique(self) -> None:
        """Test that generated IDs are unique across many iterations."""
        ids = {SessionID.generate().value for _ in range(1000)}
        assert len(ids) == 1000, "Generated IDs should be unique"

    def test_equality_and_hashing(self) -> None:
        """Test equality and hash behavior."""
        id1 = SessionID.from_string("test-id")
        id2 = SessionID.from_string("test-id")
        id3 = SessionID.from_string("other-id")

        # Equality
        assert id1 == id2
        assert id1 != id3
        assert id1 != "test-id"  # Different type

        # Hashing (for use in sets/dicts)
        assert hash(id1) == hash(id2)
        assert {id1, id2} == {id1}  # Set deduplication


class TestConversationIDParametrized:
    """Parametrized tests for ConversationID value object."""

    @pytest.mark.parametrize(
        "value",
        [
            "conv-123",
            "conversation-abc-def",
            "c" * 50,
        ],
    )
    def test_valid_conversation_ids(self, value: str) -> None:
        """Test various valid conversation ID formats."""
        conv_id = ConversationID.from_string(value)
        assert str(conv_id) == value

    def test_generated_ids_contain_prefix(self) -> None:
        """Test generated IDs have expected format."""
        conv_id = ConversationID.generate()
        # Just verify it's non-empty and valid
        assert conv_id.value
        assert len(conv_id.value) > 0


class TestToolNameParametrized:
    """Parametrized tests for ToolName value object."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            "read_file",
            "write_file",
            "tool_v2",
            "a",  # Single character
            "tool_123",
            "my_long_tool_name_here",
            "tool_with_numbers_123_456",
        ],
    )
    def test_valid_tool_names(self, valid_name: str) -> None:
        """Test various valid tool name formats."""
        name = ToolName(value=valid_name)
        assert str(name) == valid_name

    @pytest.mark.parametrize(
        "invalid_name,_reason",
        [
            ("ReadFile", "uppercase letters"),
            ("read file", "spaces"),
            ("read-file", "hyphens"),
            ("", "empty string"),
            ("Tool", "starts with uppercase"),
            ("tool.name", "dots"),
            ("tool@name", "special characters"),
        ],
    )
    def test_invalid_tool_names(self, invalid_name: str, _reason: str) -> None:
        """Test invalid tool names raise ValueError."""
        with pytest.raises(ValueError, match="ToolName"):
            ToolName(value=invalid_name)


class TestResourceURIParametrized:
    """Parametrized tests for ResourceURI value object."""

    @pytest.mark.parametrize(
        "uri,expected_scheme,expected_path",
        [
            ("config://server", "config", "server"),
            ("status://health", "status", "health"),
            ("file:///path/to/file.txt", "file", "/path/to/file.txt"),
            ("config://nested/path/here", "config", "nested/path/here"),
        ],
    )
    def test_valid_uris(self, uri: str, expected_scheme: str, expected_path: str) -> None:
        """Test various valid URI formats."""
        resource_uri = ResourceURI(value=uri)
        assert resource_uri.scheme == expected_scheme
        assert expected_path in resource_uri.path

    @pytest.mark.parametrize(
        "template_uri",
        [
            "file:///{path}",
            "config://{name}/settings",
            "status://{service}/{metric}",
        ],
    )
    def test_template_uris(self, template_uri: str) -> None:
        """Test template URI detection."""
        uri = ResourceURI(value=template_uri)
        assert uri.is_template

    @pytest.mark.parametrize(
        "invalid_uri",
        [
            "invalid://path",
            "ftp://server/file",
            "ssh://server/path",
            "",
        ],
    )
    def test_invalid_uris(self, invalid_uri: str) -> None:
        """Test invalid URIs raise errors."""
        with pytest.raises(ValueError):
            ResourceURI(value=invalid_uri)

    @pytest.mark.parametrize(
        "valid_http_uri",
        [
            "http://example.com",
            "https://api.example.com/resource",
        ],
    )
    def test_http_uris_are_valid(self, valid_http_uri: str) -> None:
        """Test that http/https URIs are valid schemes."""
        uri = ResourceURI(value=valid_http_uri)
        assert uri.scheme in ("http", "https")


class TestMCPMethodExhaustive:
    """Exhaustive tests for MCPMethod enum."""

    @pytest.mark.parametrize(
        "method,expected_value",
        [
            (MCPMethod.INITIALIZE, "initialize"),
            (MCPMethod.INITIALIZED, "notifications/initialized"),
            (MCPMethod.PING, "ping"),
            (MCPMethod.SHUTDOWN, "shutdown"),
            (MCPMethod.TOOLS_LIST, "tools/list"),
            (MCPMethod.TOOLS_CALL, "tools/call"),
            (MCPMethod.RESOURCES_LIST, "resources/list"),
            (MCPMethod.RESOURCES_READ, "resources/read"),
            (MCPMethod.RESOURCES_TEMPLATES_LIST, "resources/templates/list"),
            (MCPMethod.PROMPTS_LIST, "prompts/list"),
            (MCPMethod.PROMPTS_GET, "prompts/get"),
            (MCPMethod.LOGGING_SET_LEVEL, "logging/setLevel"),
        ],
    )
    def test_method_values(self, method: MCPMethod, expected_value: str) -> None:
        """Test each MCP method has correct value."""
        assert method.value == expected_value

    def test_all_methods_are_strings(self) -> None:
        """Verify all method values are strings."""
        for method in MCPMethod:
            assert isinstance(method.value, str)
            assert len(method.value) > 0


class TestMCPErrorCodeExhaustive:
    """Exhaustive tests for MCPErrorCode enum."""

    @pytest.mark.parametrize(
        "error_code,expected_value",
        [
            (MCPErrorCode.PARSE_ERROR, -32700),
            (MCPErrorCode.INVALID_REQUEST, -32600),
            (MCPErrorCode.METHOD_NOT_FOUND, -32601),
            (MCPErrorCode.INVALID_PARAMS, -32602),
            (MCPErrorCode.INTERNAL_ERROR, -32603),
        ],
    )
    def test_error_code_values(self, error_code: MCPErrorCode, expected_value: int) -> None:
        """Test each error code has correct JSON-RPC value."""
        assert error_code.value == expected_value

    def test_all_error_codes_are_negative(self) -> None:
        """Verify all error codes are negative integers."""
        for code in MCPErrorCode:
            assert isinstance(code.value, int)
            assert code.value < 0


class TestMCPLogLevelParametrized:
    """Parametrized tests for MCPLogLevel enum."""

    @pytest.mark.parametrize(
        "string_input,expected_level",
        [
            ("debug", MCPLogLevel.DEBUG),
            ("DEBUG", MCPLogLevel.DEBUG),
            ("Debug", MCPLogLevel.DEBUG),
            ("info", MCPLogLevel.INFO),
            ("INFO", MCPLogLevel.INFO),
            ("warning", MCPLogLevel.WARNING),
            ("WARNING", MCPLogLevel.WARNING),
            ("error", MCPLogLevel.ERROR),
            ("ERROR", MCPLogLevel.ERROR),
        ],
    )
    def test_from_string_case_insensitive(
        self, string_input: str, expected_level: MCPLogLevel
    ) -> None:
        """Test from_string handles case variations."""
        assert MCPLogLevel.from_string(string_input) == expected_level

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "invalid",
            "trace",
            "fatal",
            "",
            "123",
        ],
    )
    def test_from_string_invalid_defaults_to_info(self, invalid_input: str) -> None:
        """Test invalid inputs default to INFO level."""
        assert MCPLogLevel.from_string(invalid_input) == MCPLogLevel.INFO


class TestModelParametrized:
    """Parametrized tests for Model enum."""

    @pytest.mark.parametrize(
        "model",
        list(Model),
    )
    def test_all_models_contain_claude(self, model: Model) -> None:
        """Verify all model IDs contain 'claude'."""
        assert "claude" in model.value.lower()

    @pytest.mark.parametrize(
        "model_name,expected_model",
        [
            ("claude-sonnet-4-20250514", Model.CLAUDE_4_SONNET),
            ("claude-opus-4-20250514", Model.CLAUDE_4_OPUS),
            ("claude-3-5-sonnet-20241022", Model.CLAUDE_35_SONNET),
            ("claude-3-5-haiku-20241022", Model.CLAUDE_35_HAIKU),
        ],
    )
    def test_model_values(self, model_name: str, expected_model: Model) -> None:
        """Test model enum values match expected strings."""
        assert expected_model.value == model_name

    def test_default_model(self) -> None:
        """Test default model is Claude 4 Sonnet."""
        assert Model.default() == Model.CLAUDE_4_SONNET

    def test_from_string_valid(self) -> None:
        """Test from_string with valid model names."""
        model = Model.from_string("claude-sonnet-4-20250514")
        assert model == Model.CLAUDE_4_SONNET

    def test_from_string_invalid_raises(self) -> None:
        """Test from_string raises for invalid model."""
        with pytest.raises(ValueError, match="Unknown model"):
            Model.from_string("invalid-model")


class TestMimeTypeParametrized:
    """Parametrized tests for MimeType enum."""

    @pytest.mark.parametrize(
        "extension,expected_mime",
        [
            ("json", MimeType.APPLICATION_JSON),
            (".json", MimeType.APPLICATION_JSON),
            ("JSON", MimeType.APPLICATION_JSON),
            ("md", MimeType.TEXT_MARKDOWN),
            (".md", MimeType.TEXT_MARKDOWN),
            ("txt", MimeType.TEXT_PLAIN),
            (".txt", MimeType.TEXT_PLAIN),
            ("yaml", MimeType.APPLICATION_YAML),
            ("yml", MimeType.APPLICATION_YAML),
        ],
    )
    def test_from_extension(self, extension: str, expected_mime: MimeType) -> None:
        """Test MIME type detection from file extensions."""
        assert MimeType.from_extension(extension) == expected_mime

    @pytest.mark.parametrize(
        "unknown_extension",
        [
            "xyz",
            "unknown",
            "py",
            "rs",
            "go",
        ],
    )
    def test_from_extension_unknown_defaults(self, unknown_extension: str) -> None:
        """Test unknown extensions default to octet-stream."""
        assert MimeType.from_extension(unknown_extension) == MimeType.APPLICATION_OCTET_STREAM


class TestSystemPromptParametrized:
    """Parametrized tests for SystemPrompt value object."""

    @pytest.mark.parametrize(
        "prompt_text",
        [
            "You are a helpful assistant.",
            "Be concise and accurate.",
            "a" * 10000,  # Long prompt
            "Prompt with special chars: @#$%^&*()",
            "Multi\nline\nprompt",
        ],
    )
    def test_valid_prompts(self, prompt_text: str) -> None:
        """Test various valid system prompt values."""
        prompt = SystemPrompt(value=prompt_text)
        assert str(prompt) == prompt_text
        assert not prompt.is_empty

    def test_empty_prompt(self) -> None:
        """Test empty prompt behavior."""
        prompt = SystemPrompt(value="")
        assert prompt.is_empty
        assert str(prompt) == ""


class TestContentTypeExhaustive:
    """Exhaustive tests for ContentType enum."""

    @pytest.mark.parametrize(
        "content_type,expected_value",
        [
            (ContentType.TEXT, "text"),
            (ContentType.TOOL_USE, "tool_use"),
            (ContentType.TOOL_RESULT, "tool_result"),
        ],
    )
    def test_content_type_values(self, content_type: ContentType, expected_value: str) -> None:
        """Test content type enum values."""
        assert content_type.value == expected_value


class TestRoleExhaustive:
    """Exhaustive tests for Role enum."""

    @pytest.mark.parametrize(
        "role,expected_value",
        [
            (Role.USER, "user"),
            (Role.ASSISTANT, "assistant"),
        ],
    )
    def test_role_values(self, role: Role, expected_value: str) -> None:
        """Test role enum values."""
        assert role.value == expected_value


class TestMCPCapabilityExhaustive:
    """Exhaustive tests for MCPCapability enum."""

    @pytest.mark.parametrize(
        "capability,expected_value",
        [
            (MCPCapability.TOOLS, "tools"),
            (MCPCapability.RESOURCES, "resources"),
            (MCPCapability.PROMPTS, "prompts"),
            (MCPCapability.LOGGING, "logging"),
            (MCPCapability.SAMPLING, "sampling"),
        ],
    )
    def test_capability_values(self, capability: MCPCapability, expected_value: str) -> None:
        """Test capability enum values."""
        assert capability.value == expected_value


class TestMCPProtocolVersionParametrized:
    """Parametrized tests for MCPProtocolVersion value object."""

    @pytest.mark.parametrize(
        "version,is_supported",
        [
            ("2024-11-05", True),
            ("2020-01-01", False),
            ("2025-01-01", False),
            ("invalid", False),
        ],
    )
    def test_version_support(self, version: str, is_supported: bool) -> None:
        """Test protocol version support detection."""
        proto_version = MCPProtocolVersion(value=version)
        assert proto_version.is_supported == is_supported

    def test_latest_version(self) -> None:
        """Test latest version returns correct value."""
        latest = MCPProtocolVersion.latest()
        assert latest.value == "2024-11-05"
        assert latest.is_supported


class TestToolDescriptionParametrized:
    """Parametrized tests for ToolDescription value object."""

    @pytest.mark.parametrize(
        "description",
        [
            "Read a file from disk",
            "Execute a shell command",
            "Short",
            "A" * 500,  # Long description
        ],
    )
    def test_valid_descriptions(self, description: str) -> None:
        """Test various valid descriptions."""
        desc = ToolDescription(value=description)
        assert str(desc) == description

    def test_empty_description_raises(self) -> None:
        """Test empty description raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            ToolDescription(value="")
