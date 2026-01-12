"""Unit tests for domain layer."""

import pytest

from tfo_mcp.domain.aggregates import Conversation, ConversationStatus, Session, SessionState
from tfo_mcp.domain.entities import Message, Tool, ToolResult, ToolUseContent
from tfo_mcp.domain.events import SessionCreatedEvent
from tfo_mcp.domain.valueobjects import (
    MCPLogLevel,
    MCPMethod,
    MCPProtocolVersion,
    MimeType,
    Model,
    ResourceURI,
    Role,
    SessionID,
    SystemPrompt,
    ToolName,
)


class TestIdentifiers:
    """Test identifier value objects."""

    def test_session_id_generate(self):
        """Test SessionID generation."""
        session_id = SessionID.generate()
        assert session_id.value
        assert str(session_id)

    def test_session_id_from_string(self):
        """Test SessionID from string."""
        session_id = SessionID.from_string("test-id")
        assert session_id.value == "test-id"

    def test_session_id_empty_raises(self):
        """Test SessionID empty value raises."""
        with pytest.raises(ValueError):
            SessionID(value="")

    def test_tool_name_valid(self):
        """Test valid ToolName."""
        name = ToolName(value="read_file")
        assert str(name) == "read_file"

    def test_tool_name_invalid_pattern(self):
        """Test invalid ToolName pattern."""
        with pytest.raises(ValueError):
            ToolName(value="ReadFile")  # Must be lowercase

    def test_resource_uri_valid(self):
        """Test valid ResourceURI."""
        uri = ResourceURI(value="file:///path/to/file")
        assert uri.scheme == "file"
        assert uri.path == "/path/to/file"

    def test_resource_uri_invalid_scheme(self):
        """Test invalid ResourceURI scheme."""
        with pytest.raises(ValueError):
            ResourceURI(value="invalid://path")


class TestMCPValueObjects:
    """Test MCP-related value objects."""

    def test_mcp_method_values(self):
        """Test MCPMethod enum values."""
        assert MCPMethod.INITIALIZE.value == "initialize"
        assert MCPMethod.TOOLS_LIST.value == "tools/list"

    def test_mcp_log_level_from_string(self):
        """Test MCPLogLevel.from_string."""
        assert MCPLogLevel.from_string("debug") == MCPLogLevel.DEBUG
        assert MCPLogLevel.from_string("INFO") == MCPLogLevel.INFO
        assert MCPLogLevel.from_string("unknown") == MCPLogLevel.INFO

    def test_mcp_protocol_version(self):
        """Test MCPProtocolVersion."""
        version = MCPProtocolVersion.latest()
        assert version.is_supported
        assert str(version) == "2024-11-05"


class TestContentValueObjects:
    """Test content-related value objects."""

    def test_role_values(self):
        """Test Role enum values."""
        assert Role.USER.value == "user"
        assert Role.ASSISTANT.value == "assistant"

    def test_model_default(self):
        """Test Model.default."""
        model = Model.default()
        assert model == Model.CLAUDE_4_SONNET

    def test_mime_type_from_extension(self):
        """Test MimeType.from_extension."""
        assert MimeType.from_extension("json") == MimeType.APPLICATION_JSON
        assert MimeType.from_extension(".py") == MimeType.APPLICATION_OCTET_STREAM

    def test_system_prompt(self):
        """Test SystemPrompt."""
        prompt = SystemPrompt(value="You are helpful.")
        assert not prompt.is_empty
        assert str(prompt) == "You are helpful."


class TestMessage:
    """Test Message entity."""

    def test_create_user_message(self):
        """Test creating user message."""
        msg = Message.user("Hello")
        assert msg.role == Role.USER
        assert msg.text == "Hello"

    def test_create_assistant_message(self):
        """Test creating assistant message."""
        msg = Message.assistant("Hi there")
        assert msg.role == Role.ASSISTANT
        assert msg.text == "Hi there"

    def test_message_with_tool_use(self):
        """Test message with tool use content."""
        tool_use = ToolUseContent(id="1", name="test", input={"key": "value"})
        msg = Message.create(role=Role.ASSISTANT, content=[tool_use])
        assert msg.has_tool_use
        assert len(msg.tool_uses) == 1


class TestTool:
    """Test Tool entity."""

    def test_create_tool(self):
        """Test creating tool."""
        tool = Tool.create(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
        )
        assert str(tool.name) == "test_tool"
        assert tool.enabled

    def test_tool_to_mcp_format(self):
        """Test tool MCP format conversion."""
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
        assert mcp_format["name"] == "echo"
        assert "inputSchema" in mcp_format


class TestToolResult:
    """Test ToolResult."""

    def test_text_result(self):
        """Test text result."""
        result = ToolResult.text("Hello")
        assert not result.is_error
        assert result.content[0]["text"] == "Hello"

    def test_error_result(self):
        """Test error result."""
        result = ToolResult.error("Something went wrong")
        assert result.is_error

    def test_json_result(self):
        """Test JSON result."""
        result = ToolResult.json({"key": "value"})
        assert "key" in result.content[0]["text"]


class TestSession:
    """Test Session aggregate."""

    def test_create_session(self):
        """Test creating session."""
        session = Session.create()
        assert session.state == SessionState.CREATED
        assert session.is_ready is False

    def test_initialize_session(self):
        """Test initializing session."""
        from tfo_mcp.domain.aggregates.session import ClientInfo

        session = Session.create()
        client = ClientInfo(name="test", version="1.0")
        result = session.initialize(client)

        assert session.state == SessionState.READY
        assert session.is_ready
        assert "protocolVersion" in result

    def test_session_events(self):
        """Test session domain events."""
        session = Session.create()
        events = session.get_events()
        assert len(events) == 1
        assert isinstance(events[0], SessionCreatedEvent)

    def test_register_tool(self):
        """Test registering tool."""
        session = Session.create()
        tool = Tool.create(
            name="test",
            description="Test",
            input_schema={"type": "object"},
        )
        session.register_tool(tool)
        assert session.get_tool("test") is not None


class TestConversation:
    """Test Conversation aggregate."""

    def test_create_conversation(self):
        """Test creating conversation."""
        conversation = Conversation.create()
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.message_count == 0

    def test_add_message(self):
        """Test adding message."""
        conversation = Conversation.create()
        msg = Message.user("Hello")
        conversation.add_message(msg)
        assert conversation.message_count == 1
        assert conversation.last_message == msg
