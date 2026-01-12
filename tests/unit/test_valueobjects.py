"""Unit tests for value objects."""

import pytest

from tfo_mcp.domain.valueobjects import (
    ContentType,
    ConversationID,
    MCPCapability,
    MCPErrorCode,
    MCPLogLevel,
    MCPMethod,
    MCPProtocolVersion,
    MessageID,
    MimeType,
    Model,
    ResourceURI,
    Role,
    SessionID,
    SystemPrompt,
    ToolDescription,
    ToolName,
)


class TestSessionID:
    """Test SessionID value object."""

    def test_generate(self):
        """Test generating a session ID."""
        session_id = SessionID.generate()
        assert session_id.value
        assert len(session_id.value) > 0

    def test_from_string(self):
        """Test creating from string."""
        session_id = SessionID.from_string("custom-id-123")
        assert session_id.value == "custom-id-123"

    def test_empty_raises(self):
        """Test empty value raises."""
        with pytest.raises(ValueError):
            SessionID(value="")

    def test_equality(self):
        """Test equality comparison."""
        id1 = SessionID.from_string("test-id")
        id2 = SessionID.from_string("test-id")
        id3 = SessionID.from_string("other-id")

        assert id1 == id2
        assert id1 != id3

    def test_str_representation(self):
        """Test string representation."""
        session_id = SessionID.from_string("test-123")
        assert str(session_id) == "test-123"

    def test_uniqueness(self):
        """Test generated IDs are unique."""
        ids = [SessionID.generate() for _ in range(100)]
        unique_ids = {str(id) for id in ids}
        assert len(unique_ids) == 100


class TestConversationID:
    """Test ConversationID value object."""

    def test_generate(self):
        """Test generating a conversation ID."""
        conv_id = ConversationID.generate()
        assert conv_id.value
        assert "conv-" in conv_id.value or len(conv_id.value) > 0

    def test_from_string(self):
        """Test creating from string."""
        conv_id = ConversationID.from_string("conv-123")
        assert conv_id.value == "conv-123"


class TestMessageID:
    """Test MessageID value object."""

    def test_generate(self):
        """Test generating a message ID."""
        msg_id = MessageID.generate()
        assert msg_id.value

    def test_from_string(self):
        """Test creating from string."""
        msg_id = MessageID.from_string("msg-456")
        assert msg_id.value == "msg-456"


class TestToolName:
    """Test ToolName value object."""

    def test_valid_name(self):
        """Test valid tool name."""
        name = ToolName(value="read_file")
        assert str(name) == "read_file"

    def test_valid_name_with_numbers(self):
        """Test valid name with numbers."""
        name = ToolName(value="tool_v2")
        assert str(name) == "tool_v2"

    def test_invalid_uppercase(self):
        """Test invalid uppercase name."""
        with pytest.raises(ValueError):
            ToolName(value="ReadFile")

    def test_invalid_spaces(self):
        """Test invalid name with spaces."""
        with pytest.raises(ValueError):
            ToolName(value="read file")

    def test_invalid_special_chars(self):
        """Test invalid special characters."""
        with pytest.raises(ValueError):
            ToolName(value="read-file")  # Hyphens not allowed


class TestToolDescription:
    """Test ToolDescription value object."""

    def test_valid_description(self):
        """Test valid description."""
        desc = ToolDescription(value="Read the contents of a file")
        assert "Read" in str(desc)

    def test_empty_raises(self):
        """Test empty description raises."""
        with pytest.raises(ValueError):
            ToolDescription(value="")


class TestResourceURI:
    """Test ResourceURI value object."""

    def test_config_uri(self):
        """Test config:// URI."""
        uri = ResourceURI(value="config://server")
        assert uri.scheme == "config"
        assert uri.path == "server"

    def test_status_uri(self):
        """Test status:// URI."""
        uri = ResourceURI(value="status://health")
        assert uri.scheme == "status"
        assert uri.path == "health"

    def test_file_uri(self):
        """Test file:// URI."""
        uri = ResourceURI(value="file:///path/to/file.txt")
        assert uri.scheme == "file"
        assert "/path/to/file.txt" in uri.path

    def test_template_uri(self):
        """Test template URI with placeholder."""
        uri = ResourceURI(value="file:///{path}")
        assert uri.is_template
        assert "{path}" in uri.path

    def test_invalid_scheme(self):
        """Test invalid scheme."""
        with pytest.raises(ValueError):
            ResourceURI(value="invalid://path")

    def test_str_representation(self):
        """Test string representation."""
        uri = ResourceURI(value="config://server")
        assert str(uri) == "config://server"


class TestMCPMethod:
    """Test MCPMethod enum."""

    def test_initialize(self):
        """Test initialize method."""
        assert MCPMethod.INITIALIZE.value == "initialize"

    def test_tools_list(self):
        """Test tools/list method."""
        assert MCPMethod.TOOLS_LIST.value == "tools/list"

    def test_tools_call(self):
        """Test tools/call method."""
        assert MCPMethod.TOOLS_CALL.value == "tools/call"

    def test_resources_list(self):
        """Test resources/list method."""
        assert MCPMethod.RESOURCES_LIST.value == "resources/list"

    def test_prompts_list(self):
        """Test prompts/list method."""
        assert MCPMethod.PROMPTS_LIST.value == "prompts/list"

    def test_method_values_are_strings(self):
        """Test all method values are strings."""
        for method in MCPMethod:
            assert isinstance(method.value, str)


class TestMCPCapability:
    """Test MCPCapability enum."""

    def test_tools_capability(self):
        """Test tools capability."""
        assert MCPCapability.TOOLS.value == "tools"

    def test_resources_capability(self):
        """Test resources capability."""
        assert MCPCapability.RESOURCES.value == "resources"


class TestMCPLogLevel:
    """Test MCPLogLevel enum."""

    def test_debug_level(self):
        """Test debug level."""
        assert MCPLogLevel.DEBUG.value == "debug"

    def test_info_level(self):
        """Test info level."""
        assert MCPLogLevel.INFO.value == "info"

    def test_from_string_case_insensitive(self):
        """Test from_string is case insensitive."""
        assert MCPLogLevel.from_string("DEBUG") == MCPLogLevel.DEBUG
        assert MCPLogLevel.from_string("debug") == MCPLogLevel.DEBUG
        assert MCPLogLevel.from_string("Debug") == MCPLogLevel.DEBUG

    def test_from_string_invalid(self):
        """Test from_string with invalid value defaults to INFO."""
        assert MCPLogLevel.from_string("invalid") == MCPLogLevel.INFO


class TestMCPErrorCode:
    """Test MCPErrorCode enum."""

    def test_parse_error(self):
        """Test parse error code."""
        assert MCPErrorCode.PARSE_ERROR.value == -32700

    def test_invalid_request(self):
        """Test invalid request code."""
        assert MCPErrorCode.INVALID_REQUEST.value == -32600

    def test_method_not_found(self):
        """Test method not found code."""
        assert MCPErrorCode.METHOD_NOT_FOUND.value == -32601

    def test_invalid_params(self):
        """Test invalid params code."""
        assert MCPErrorCode.INVALID_PARAMS.value == -32602

    def test_internal_error(self):
        """Test internal error code."""
        assert MCPErrorCode.INTERNAL_ERROR.value == -32603


class TestMCPProtocolVersion:
    """Test MCPProtocolVersion value object."""

    def test_latest_version(self):
        """Test latest version."""
        version = MCPProtocolVersion.latest()
        assert version.value == "2024-11-05"

    def test_is_supported(self):
        """Test is_supported property."""
        version = MCPProtocolVersion(value="2024-11-05")
        assert version.is_supported

    def test_unsupported_version(self):
        """Test unsupported version."""
        version = MCPProtocolVersion(value="2020-01-01")
        assert not version.is_supported

    def test_str_representation(self):
        """Test string representation."""
        version = MCPProtocolVersion.latest()
        assert str(version) == "2024-11-05"


class TestRole:
    """Test Role enum."""

    def test_user_role(self):
        """Test user role."""
        assert Role.USER.value == "user"

    def test_assistant_role(self):
        """Test assistant role."""
        assert Role.ASSISTANT.value == "assistant"


class TestModel:
    """Test Model enum."""

    def test_claude_4_opus(self):
        """Test Claude 4 Opus model."""
        assert "opus" in Model.CLAUDE_4_OPUS.value

    def test_claude_4_sonnet(self):
        """Test Claude 4 Sonnet model."""
        assert "sonnet" in Model.CLAUDE_4_SONNET.value

    def test_default_model(self):
        """Test default model."""
        default = Model.default()
        assert default == Model.CLAUDE_4_SONNET

    def test_model_ids(self):
        """Test model IDs are valid."""
        for model in Model:
            assert "claude" in model.value.lower()


class TestContentType:
    """Test ContentType enum."""

    def test_text_type(self):
        """Test text content type."""
        assert ContentType.TEXT.value == "text"

    def test_tool_use_type(self):
        """Test tool_use content type."""
        assert ContentType.TOOL_USE.value == "tool_use"

    def test_tool_result_type(self):
        """Test tool_result content type."""
        assert ContentType.TOOL_RESULT.value == "tool_result"


class TestMimeType:
    """Test MimeType enum."""

    def test_json_mime(self):
        """Test application/json mime type."""
        assert MimeType.APPLICATION_JSON.value == "application/json"

    def test_text_plain(self):
        """Test text/plain mime type."""
        assert MimeType.TEXT_PLAIN.value == "text/plain"

    def test_from_extension_json(self):
        """Test from_extension for json."""
        assert MimeType.from_extension("json") == MimeType.APPLICATION_JSON
        assert MimeType.from_extension(".json") == MimeType.APPLICATION_JSON

    def test_from_extension_markdown(self):
        """Test from_extension for markdown."""
        assert MimeType.from_extension("md") == MimeType.TEXT_MARKDOWN
        assert MimeType.from_extension(".md") == MimeType.TEXT_MARKDOWN

    def test_from_extension_unknown(self):
        """Test from_extension for unknown."""
        # Unknown extensions default to APPLICATION_OCTET_STREAM
        result = MimeType.from_extension("xyz")
        assert result == MimeType.APPLICATION_OCTET_STREAM
        # Python files are also not explicitly mapped
        result = MimeType.from_extension("py")
        assert result == MimeType.APPLICATION_OCTET_STREAM


class TestSystemPrompt:
    """Test SystemPrompt value object."""

    def test_create_prompt(self):
        """Test creating system prompt."""
        prompt = SystemPrompt(value="You are a helpful assistant.")
        assert "helpful" in str(prompt)

    def test_is_empty(self):
        """Test is_empty property."""
        prompt = SystemPrompt(value="")
        assert prompt.is_empty

        prompt2 = SystemPrompt(value="Hello")
        assert not prompt2.is_empty

    def test_str_representation(self):
        """Test string representation."""
        prompt = SystemPrompt(value="Test prompt")
        assert str(prompt) == "Test prompt"
