"""Advanced unit tests for domain entities with edge cases and serialization."""

from __future__ import annotations

from typing import Any

from tfo_mcp.domain.entities import (
    Message,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    ResourceContent,
    TextContent,
    Tool,
    ToolInputSchema,
    ToolResult,
    ToolResultContent,
    ToolUseContent,
)
from tfo_mcp.domain.valueobjects import MimeType, Role


class TestMessageBehavior:
    """Test Message entity behavior and integrity."""

    def test_message_equality_by_content(self) -> None:
        """Test message equality based on content."""
        msg1 = Message.user("Hello")
        msg2 = Message.user("Hello")
        msg3 = Message.user("Goodbye")
        msg4 = Message.assistant("Hello")

        # Same content and role should be logically equivalent
        assert msg1.text == msg2.text
        assert msg1.role == msg2.role

        # Different content
        assert msg1.text != msg3.text

        # Different role
        assert msg1.role != msg4.role

    def test_message_id_uniqueness(self) -> None:
        """Test that each message gets a unique ID."""
        messages = [Message.user(f"Message {i}") for i in range(100)]
        ids = {str(msg.id) for msg in messages}
        assert len(ids) == 100

    def test_message_has_content(self) -> None:
        """Test message has content blocks."""
        msg = Message.user("Test")
        assert len(msg.content) > 0
        assert msg.text == "Test"

    def test_message_roles(self) -> None:
        """Test different message roles."""
        user_msg = Message.user("User message")
        assistant_msg = Message.assistant("Assistant message")
        system_msg = Message.system("System message")

        assert user_msg.role == Role.USER
        assert assistant_msg.role == Role.ASSISTANT
        assert system_msg.role == Role.SYSTEM


class TestToolCreation:
    """Test Tool entity creation and behavior."""

    def test_tool_creation_basic(self) -> None:
        """Test basic tool creation."""
        tool = Tool.create(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
        )

        assert str(tool.name) == "test_tool"
        assert str(tool.description) == "A test tool"

    def test_tool_creation_with_all_parameters(self) -> None:
        """Test tool creation with all optional parameters."""

        async def handler(_data: dict[str, Any]) -> ToolResult:
            return ToolResult.text("OK")

        tool = Tool.create(
            name="full_tool",
            description="A fully configured tool",
            input_schema={
                "type": "object",
                "properties": {
                    "required_param": {"type": "string"},
                    "optional_param": {"type": "integer", "default": 0},
                },
                "required": ["required_param"],
            },
            handler=handler,
            category="testing",
            tags=["test", "example"],
            timeout_seconds=30.0,
        )

        assert str(tool.name) == "full_tool"
        assert tool.category == "testing"
        assert "test" in tool.tags
        assert tool.timeout_seconds == 30.0
        assert tool.handler is not None

    def test_tool_mcp_format(self) -> None:
        """Test tool MCP format serialization."""
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
        assert mcp_format["description"] == "Echo a message"
        assert "inputSchema" in mcp_format


class TestToolResultVariants:
    """Test ToolResult creation variants."""

    def test_text_result(self) -> None:
        """Test creating text result."""
        result = ToolResult.text("Hello, World!")
        result_dict = result.to_dict()

        assert "content" in result_dict
        assert result_dict["content"][0]["text"] == "Hello, World!"
        assert result_dict.get("isError", False) is False

    def test_error_result(self) -> None:
        """Test creating error result."""
        result = ToolResult.error("Something went wrong")
        result_dict = result.to_dict()

        assert "Something went wrong" in result_dict["content"][0]["text"]
        assert result_dict.get("isError") is True

    def test_json_result(self) -> None:
        """Test creating JSON result."""
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        result = ToolResult.json(data)
        result_dict = result.to_dict()

        assert "content" in result_dict
        content_text = result_dict["content"][0]["text"]
        assert "key" in content_text
        assert "value" in content_text

    def test_json_error_result(self) -> None:
        """Test creating JSON error result."""
        data = {"error": "details"}
        result = ToolResult.json(data, is_error=True)
        result_dict = result.to_dict()

        assert result_dict.get("isError") is True

    def test_result_to_dict_format(self) -> None:
        """Test result serialization to MCP format."""
        result = ToolResult.text("Test")
        result_dict = result.to_dict()

        assert "content" in result_dict
        assert isinstance(result_dict["content"], list)
        assert result_dict["content"][0]["type"] == "text"


class TestResourceCreation:
    """Test Resource entity creation and behavior."""

    def test_static_resource_creation(self) -> None:
        """Test creating a static resource."""
        resource = Resource.create(
            uri="config://server",
            name="Server Config",
            description="Server configuration",
            mime_type=MimeType.APPLICATION_JSON,
        )

        assert str(resource.uri) == "config://server"
        assert resource.name == "Server Config"
        assert not resource.is_template

    def test_template_resource_creation(self) -> None:
        """Test creating a template resource."""
        resource = Resource.template(
            uri_template="file:///{path}",
            name="File Reader",
            description="Read files",
            mime_type=MimeType.TEXT_PLAIN,
        )

        assert resource.is_template
        assert "{path}" in str(resource.uri)

    def test_resource_to_mcp_format(self) -> None:
        """Test resource serialization to MCP format."""
        resource = Resource.create(
            uri="status://health",
            name="Health Status",
            description="System health",
            mime_type=MimeType.APPLICATION_JSON,
        )

        mcp_format = resource.to_mcp_format()

        assert "uri" in mcp_format
        assert "name" in mcp_format
        assert mcp_format["mimeType"] == "application/json"


class TestResourceContentVariants:
    """Test ResourceContent creation variants."""

    def test_text_content(self) -> None:
        """Test creating text content."""
        content = ResourceContent(
            uri="config://test",
            mime_type=MimeType.TEXT_PLAIN,
            text="Hello, World!",
        )

        assert content.text == "Hello, World!"
        assert content.blob is None

    def test_blob_content(self) -> None:
        """Test creating binary content."""
        binary_data = b"\x00\x01\x02\x03"
        content = ResourceContent(
            uri="file:///test.bin",
            mime_type=MimeType.APPLICATION_OCTET_STREAM,
            blob=binary_data,
        )

        assert content.blob == binary_data
        assert content.text is None

    def test_content_to_dict(self) -> None:
        """Test content serialization."""
        content = ResourceContent(
            uri="config://test",
            mime_type=MimeType.APPLICATION_JSON,
            text='{"key": "value"}',
        )

        content_dict = content.to_dict()

        assert content_dict["uri"] == "config://test"
        assert content_dict["mimeType"] == "application/json"
        assert "text" in content_dict


class TestPromptCreation:
    """Test Prompt entity creation and behavior."""

    def test_prompt_with_no_arguments(self) -> None:
        """Test creating prompt without arguments."""
        prompt = Prompt.create(
            name="simple_prompt",
            description="A simple prompt",
        )

        assert str(prompt.name) == "simple_prompt"
        assert len(prompt.arguments) == 0

    def test_prompt_with_required_arguments(self) -> None:
        """Test prompt with required arguments."""
        prompt = Prompt.create(
            name="greeting",
            description="Generate a greeting",
            arguments=[
                PromptArgument(name="name", description="Name to greet", required=True),
            ],
        )

        assert len(prompt.arguments) == 1
        assert prompt.arguments[0].required

    def test_prompt_with_mixed_arguments(self) -> None:
        """Test prompt with required and optional arguments."""
        prompt = Prompt.create(
            name="code_review",
            description="Review code",
            arguments=[
                PromptArgument(name="code", description="Code", required=True),
                PromptArgument(name="language", description="Language", required=False),
                PromptArgument(name="severity", description="Severity", required=False),
            ],
        )

        required = [arg for arg in prompt.arguments if arg.required]
        optional = [arg for arg in prompt.arguments if not arg.required]

        assert len(required) == 1
        assert len(optional) == 2

    def test_prompt_to_mcp_format(self) -> None:
        """Test prompt serialization to MCP format."""
        prompt = Prompt.create(
            name="test_prompt",
            description="Test prompt description",
            arguments=[
                PromptArgument(name="arg1", description="Arg 1", required=True),
            ],
        )

        mcp_format = prompt.to_mcp_format()

        assert "name" in mcp_format
        assert "description" in mcp_format
        assert "arguments" in mcp_format


class TestPromptMessageCreation:
    """Test PromptMessage entity creation."""

    def test_user_prompt_message(self) -> None:
        """Test creating user prompt message."""
        msg = PromptMessage(role=Role.USER, content="Hello")

        assert msg.role == Role.USER
        assert msg.content == "Hello"

    def test_assistant_prompt_message(self) -> None:
        """Test creating assistant prompt message."""
        msg = PromptMessage(role=Role.ASSISTANT, content="Hi there!")

        assert msg.role == Role.ASSISTANT

    def test_prompt_message_to_dict(self) -> None:
        """Test prompt message serialization."""
        msg = PromptMessage(role=Role.USER, content="Test content")
        msg_dict = msg.to_dict()

        assert msg_dict["role"] == "user"
        assert msg_dict["content"]["type"] == "text"
        assert msg_dict["content"]["text"] == "Test content"


class TestToolInputSchemaValidation:
    """Test ToolInputSchema validation and behavior."""

    def test_from_dict(self) -> None:
        """Test creating schema from dict."""
        schema_dict = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }

        schema = ToolInputSchema.from_dict(schema_dict)
        result = schema.to_dict()

        assert result["type"] == "object"
        assert "name" in result["properties"]

    def test_empty_schema(self) -> None:
        """Test creating empty schema."""
        schema = ToolInputSchema.from_dict({"type": "object"})
        result = schema.to_dict()

        assert result["type"] == "object"

    def test_schema_with_complex_types(self) -> None:
        """Test schema with complex property types."""
        schema_dict = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        }

        schema = ToolInputSchema.from_dict(schema_dict)
        result = schema.to_dict()

        assert result["properties"]["items"]["type"] == "array"


class TestContentBlockTypes:
    """Test different content block types."""

    def test_text_content(self) -> None:
        """Test TextContent creation."""
        content = TextContent(text="Hello, World!")
        assert content.text == "Hello, World!"
        assert content.type.value == "text"

    def test_tool_use_content(self) -> None:
        """Test ToolUseContent creation."""
        content = ToolUseContent(
            id="tool_123",
            name="read_file",
            input={"path": "/tmp/test.txt"},
        )

        assert content.id == "tool_123"
        assert content.name == "read_file"
        assert content.input["path"] == "/tmp/test.txt"
        assert content.type.value == "tool_use"

    def test_tool_result_content(self) -> None:
        """Test ToolResultContent creation."""
        content = ToolResultContent(
            tool_use_id="tool_123",
            content="File contents here",
            is_error=False,
        )

        assert content.tool_use_id == "tool_123"
        assert content.content == "File contents here"
        assert not content.is_error
        assert content.type.value == "tool_result"

    def test_tool_result_content_error(self) -> None:
        """Test ToolResultContent with error."""
        content = ToolResultContent(
            tool_use_id="tool_456",
            content="File not found",
            is_error=True,
        )

        assert content.is_error


class TestMessageWithToolUse:
    """Test Message with tool use content."""

    def test_message_with_tool_use(self) -> None:
        """Test creating message with tool use."""
        tool_use = ToolUseContent(
            id="tool_123",
            name="read_file",
            input={"path": "/tmp/test.txt"},
        )

        msg = Message.create(role=Role.ASSISTANT, content=[tool_use])

        assert msg.has_tool_use
        assert len(msg.tool_uses) == 1

    def test_message_with_multiple_tool_uses(self) -> None:
        """Test message with multiple tool uses."""
        tool_uses: list[ToolUseContent] = [
            ToolUseContent(id=f"tool_{i}", name=f"tool_{i}", input={}) for i in range(3)
        ]

        msg = Message.create(role=Role.ASSISTANT, content=tool_uses)

        assert msg.has_tool_use
        assert len(msg.tool_uses) == 3

    def test_message_tool_result(self) -> None:
        """Test creating tool result message with ToolResultContent."""
        tool_result_content = ToolResultContent(
            tool_use_id="tool_123",
            content="Result content",
            is_error=False,
        )
        msg = Message.create(role=Role.USER, content=[tool_result_content])

        assert msg.role == Role.USER
        assert len(msg.content) == 1


class TestEntitySerializationRoundtrip:
    """Test entity serialization and deserialization."""

    def test_message_to_api_format(self) -> None:
        """Test message serialization to API format."""
        msg = Message.user("Hello, Claude!")
        api_format = msg.to_api_format()

        assert api_format["role"] == "user"
        assert isinstance(api_format["content"], list)
        assert api_format["content"][0]["type"] == "text"
        assert api_format["content"][0]["text"] == "Hello, Claude!"

    def test_tool_to_mcp_format(self) -> None:
        """Test tool serialization to MCP format."""
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
        assert mcp_format["description"] == "Echo a message"
        assert "inputSchema" in mcp_format

    def test_resource_to_mcp_format(self) -> None:
        """Test resource serialization to MCP format."""
        resource = Resource.create(
            uri="config://test",
            name="Test",
            description="Test resource",
            mime_type=MimeType.APPLICATION_JSON,
        )

        mcp_format = resource.to_mcp_format()

        assert "uri" in mcp_format
        assert "name" in mcp_format
        assert "mimeType" in mcp_format
