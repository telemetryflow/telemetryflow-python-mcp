"""Unit tests for domain entities."""

import json
from datetime import datetime

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


class TestTextContent:
    """Test TextContent entity."""

    def test_create_text_content(self):
        """Test creating text content."""
        content = TextContent(text="Hello world")
        assert content.text == "Hello world"
        assert content.type == "text"

    def test_text_content_to_dict(self):
        """Test text content to dict conversion."""
        content = TextContent(text="Test")
        d = content.to_dict()
        assert d["type"] == "text"
        assert d["text"] == "Test"


class TestToolUseContent:
    """Test ToolUseContent entity."""

    def test_create_tool_use(self):
        """Test creating tool use content."""
        content = ToolUseContent(
            id="tool_123",
            name="echo",
            input={"message": "hello"},
        )
        assert content.id == "tool_123"
        assert content.name == "echo"
        assert content.input == {"message": "hello"}
        assert content.type == "tool_use"

    def test_tool_use_to_dict(self):
        """Test tool use content to dict."""
        content = ToolUseContent(
            id="tool_123",
            name="test",
            input={"key": "value"},
        )
        d = content.to_dict()
        assert d["type"] == "tool_use"
        assert d["id"] == "tool_123"
        assert d["name"] == "test"
        assert d["input"] == {"key": "value"}


class TestToolResultContent:
    """Test ToolResultContent entity."""

    def test_create_tool_result(self):
        """Test creating tool result content."""
        content = ToolResultContent(
            tool_use_id="tool_123",
            content="Result text",
        )
        assert content.tool_use_id == "tool_123"
        assert content.content == "Result text"
        assert content.is_error is False

    def test_tool_result_error(self):
        """Test tool result with error."""
        content = ToolResultContent(
            tool_use_id="tool_123",
            content="Error occurred",
            is_error=True,
        )
        assert content.is_error is True


class TestMessage:
    """Test Message entity."""

    def test_create_user_message(self):
        """Test creating user message."""
        msg = Message.user("Hello")
        assert msg.role == Role.USER
        assert msg.text == "Hello"
        assert msg.id is not None

    def test_create_assistant_message(self):
        """Test creating assistant message."""
        msg = Message.assistant("Hi there")
        assert msg.role == Role.ASSISTANT
        assert msg.text == "Hi there"

    def test_message_with_multiple_content(self):
        """Test message with multiple content blocks."""
        content = [
            TextContent(text="Here's the result:"),
            ToolUseContent(id="1", name="test", input={}),
        ]
        msg = Message.create(role=Role.ASSISTANT, content=content)
        assert len(msg.content) == 2
        assert msg.has_tool_use

    def test_message_timestamp(self):
        """Test message timestamp."""
        msg = Message.user("Test")
        assert msg.created_at is not None
        assert isinstance(msg.created_at, datetime)

    def test_message_tool_uses(self):
        """Test extracting tool uses from message."""
        content = [
            ToolUseContent(id="1", name="tool1", input={"a": 1}),
            TextContent(text="text"),
            ToolUseContent(id="2", name="tool2", input={"b": 2}),
        ]
        msg = Message.create(role=Role.ASSISTANT, content=content)
        tool_uses = msg.tool_uses
        assert len(tool_uses) == 2
        assert tool_uses[0].name == "tool1"
        assert tool_uses[1].name == "tool2"

    def test_message_to_api_format(self):
        """Test message to API format conversion."""
        msg = Message.user("Hello")
        api_format = msg.to_api_format()
        assert api_format["role"] == "user"
        # Content is returned as a list of content blocks
        assert isinstance(api_format["content"], list)
        assert api_format["content"][0]["type"] == "text"
        assert api_format["content"][0]["text"] == "Hello"


class TestTool:
    """Test Tool entity."""

    def test_create_tool(self):
        """Test creating a tool."""
        tool = Tool.create(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
        )
        assert str(tool.name) == "echo"
        # description is a value object, convert to string
        assert str(tool.description) == "Echo a message"
        assert tool.enabled

    def test_tool_with_handler(self):
        """Test tool with handler."""

        async def handler(_input_data):
            return ToolResult.text("result")

        tool = Tool.create(
            name="test",
            description="Test",
            input_schema={"type": "object"},
            handler=handler,
        )
        assert tool.handler is not None

    def test_tool_enabled_attribute(self):
        """Test tool enabled attribute."""
        tool = Tool.create(
            name="test",
            description="Test",
            input_schema={"type": "object"},
        )
        assert tool.enabled is True

    def test_tool_to_mcp_format(self):
        """Test tool MCP format conversion."""
        tool = Tool.create(
            name="echo",
            description="Echo a message",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
                "required": ["message"],
            },
        )
        mcp_format = tool.to_mcp_format()
        assert mcp_format["name"] == "echo"
        assert mcp_format["description"] == "Echo a message"
        assert "inputSchema" in mcp_format

    def test_tool_with_category_and_tags(self):
        """Test tool with category and tags."""
        tool = Tool.create(
            name="test",
            description="Test",
            input_schema={"type": "object"},
            category="utility",
            tags=["test", "mock"],
        )
        assert tool.category == "utility"
        assert "test" in tool.tags


class TestToolResult:
    """Test ToolResult entity."""

    def test_text_result(self):
        """Test text result."""
        result = ToolResult.text("Hello")
        assert not result.is_error
        assert result.content[0]["type"] == "text"
        assert result.content[0]["text"] == "Hello"

    def test_error_result(self):
        """Test error result."""
        result = ToolResult.error("Something failed")
        assert result.is_error
        assert "Something failed" in result.content[0]["text"]

    def test_json_result(self):
        """Test JSON result."""
        data = {"key": "value", "number": 42}
        result = ToolResult.json(data)
        assert not result.is_error
        parsed = json.loads(result.content[0]["text"])
        assert parsed["key"] == "value"


class TestResource:
    """Test Resource entity."""

    def test_create_resource(self):
        """Test creating a resource."""
        resource = Resource.create(
            uri="config://server",
            name="Server Config",
            description="Server configuration",
            mime_type=MimeType.APPLICATION_JSON,
        )
        assert str(resource.uri) == "config://server"
        assert resource.name == "Server Config"

    def test_resource_with_reader(self):
        """Test resource with reader function."""

        async def reader(uri, _params):
            return ResourceContent(
                uri=uri,
                mime_type=MimeType.APPLICATION_JSON,
                text='{"key": "value"}',
            )

        # Use a valid URI scheme
        resource = Resource.create(
            uri="config://test-resource",
            name="Test",
            description="Test resource",
            mime_type=MimeType.APPLICATION_JSON,
            reader=reader,
        )
        assert resource.reader is not None

    def test_resource_to_mcp_format(self):
        """Test resource MCP format."""
        resource = Resource.create(
            uri="config://server",
            name="Config",
            description="Server configuration",
            mime_type=MimeType.APPLICATION_JSON,
        )
        mcp_format = resource.to_mcp_format()
        assert mcp_format["uri"] == "config://server"
        assert mcp_format["name"] == "Config"
        assert "mimeType" in mcp_format

    def test_template_resource(self):
        """Test template resource."""
        resource = Resource.template(
            uri_template="file:///{path}",
            name="File",
            description="Read file",
            mime_type=MimeType.TEXT_PLAIN,
        )
        assert resource.is_template


class TestResourceContent:
    """Test ResourceContent entity."""

    def test_create_resource_content(self):
        """Test creating resource content."""
        content = ResourceContent(
            uri="config://resource",
            mime_type=MimeType.TEXT_PLAIN,
            text="Hello world",
        )
        assert content.text == "Hello world"
        assert content.mime_type == MimeType.TEXT_PLAIN

    def test_resource_content_binary(self):
        """Test resource content with binary data."""
        content = ResourceContent(
            uri="config://binary",
            mime_type=MimeType.APPLICATION_OCTET_STREAM,
            blob=b"\x00\x01\x02\x03",
        )
        assert content.blob == b"\x00\x01\x02\x03"


class TestPrompt:
    """Test Prompt entity."""

    def test_create_prompt(self):
        """Test creating a prompt."""
        prompt = Prompt.create(
            name="code_review",
            description="Code review assistance",
            arguments=[
                PromptArgument(
                    name="code",
                    description="Code to review",
                    required=True,
                ),
            ],
        )
        assert str(prompt.name) == "code_review"
        assert len(prompt.arguments) == 1

    def test_prompt_with_generator(self):
        """Test prompt with generator."""

        async def generator(args):
            return [PromptMessage(role=Role.USER, content=args.get("topic", ""))]

        prompt = Prompt.create(
            name="test",
            description="Test prompt",
            arguments=[],
            generator=generator,
        )
        assert prompt.generator is not None

    def test_prompt_to_mcp_format(self):
        """Test prompt MCP format."""
        prompt = Prompt.create(
            name="explain",
            description="Explain code",
            arguments=[
                PromptArgument(
                    name="code",
                    description="Code to explain",
                    required=True,
                ),
                PromptArgument(
                    name="language",
                    description="Programming language",
                    required=False,
                ),
            ],
        )
        mcp_format = prompt.to_mcp_format()
        assert mcp_format["name"] == "explain"
        assert len(mcp_format["arguments"]) == 2


class TestPromptArgument:
    """Test PromptArgument entity."""

    def test_required_argument(self):
        """Test required argument."""
        arg = PromptArgument(
            name="code",
            description="Code input",
            required=True,
        )
        assert arg.required

    def test_optional_argument(self):
        """Test optional argument."""
        arg = PromptArgument(
            name="language",
            description="Language",
            required=False,
        )
        assert not arg.required


class TestPromptMessage:
    """Test PromptMessage entity."""

    def test_user_prompt_message(self):
        """Test user prompt message."""
        msg = PromptMessage(role=Role.USER, content="Please help")
        assert msg.role == Role.USER

    def test_assistant_prompt_message(self):
        """Test assistant prompt message."""
        msg = PromptMessage(role=Role.ASSISTANT, content="I'll help")
        assert msg.role == Role.ASSISTANT


class TestToolInputSchema:
    """Test ToolInputSchema value object."""

    def test_create_schema(self):
        """Test creating tool input schema."""
        schema = ToolInputSchema(
            properties={
                "message": {"type": "string"},
                "count": {"type": "integer"},
            },
            required=["message"],
        )
        assert "message" in schema.properties
        assert "message" in schema.required

    def test_schema_validation(self):
        """Test schema has expected structure."""
        schema = ToolInputSchema(
            properties={"path": {"type": "string"}},
            required=["path"],
        )
        schema_dict = schema.to_dict()
        assert schema_dict["type"] == "object"
        assert "properties" in schema_dict
