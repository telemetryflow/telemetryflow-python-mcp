import pytest

from tfo_mcp.domain.entities.message import Message, ToolResultContent, ToolUseContent
from tfo_mcp.domain.entities.prompt import Prompt, PromptArgument
from tfo_mcp.domain.valueobjects import Role


class TestToolResultContentToDict:
    def test_with_is_error_true(self):
        trc = ToolResultContent(tool_use_id="tu-1", content="failed", is_error=True)
        d = trc.to_dict()
        assert d["is_error"] is True

    def test_with_is_error_false(self):
        trc = ToolResultContent(tool_use_id="tu-1", content="ok", is_error=False)
        d = trc.to_dict()
        assert "is_error" not in d


class TestMessageTotalTokens:
    def test_total_tokens(self):
        msg = Message.create(role=Role.USER, text="hi")
        msg.input_tokens = 100
        msg.output_tokens = 50
        assert msg.total_tokens == 150


class TestMessageToDict:
    def test_to_dict(self):
        msg = Message.user("hello")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert len(d["content"]) == 1
        assert d["content"][0]["type"] == "text"


class TestMessageToApiFormat:
    def test_text_only(self):
        msg = Message.user("hello")
        fmt = msg.to_api_format()
        assert fmt["role"] == "user"
        assert fmt["content"][0]["type"] == "text"

    def test_tool_use_content(self):
        tu = ToolUseContent(id="tu-1", name="my_tool", input={"a": 1})
        msg = Message.create(role=Role.ASSISTANT, content=[tu])
        fmt = msg.to_api_format()
        block = fmt["content"][0]
        assert block["type"] == "tool_use"
        assert block["id"] == "tu-1"
        assert block["name"] == "my_tool"
        assert block["input"] == {"a": 1}

    def test_tool_result_content(self):
        tr = ToolResultContent(tool_use_id="tu-1", content="result text", is_error=False)
        msg = Message.create(role=Role.USER, content=[tr])
        fmt = msg.to_api_format()
        block = fmt["content"][0]
        assert block["type"] == "tool_result"
        assert block["tool_use_id"] == "tu-1"
        assert block["content"] == "result text"
        assert block["is_error"] is False

    def test_tool_result_content_error(self):
        tr = ToolResultContent(tool_use_id="tu-2", content="oops", is_error=True)
        msg = Message.create(role=Role.USER, content=[tr])
        fmt = msg.to_api_format()
        block = fmt["content"][0]
        assert block["is_error"] is True


class TestPromptGetMessages:
    @pytest.mark.asyncio
    async def test_missing_required_argument(self):
        prompt = Prompt(
            name="test",
            arguments=[PromptArgument(name="code", required=True)],
        )
        with pytest.raises(ValueError, match="Missing required argument: code"):
            await prompt.get_messages({})

    @pytest.mark.asyncio
    async def test_no_generator_returns_empty(self):
        prompt = Prompt(
            name="test",
            arguments=[PromptArgument(name="code", required=True)],
        )
        result = await prompt.get_messages({"code": "print('hi')"})
        assert result == []

    @pytest.mark.asyncio
    async def test_with_generator(self):
        from tfo_mcp.domain.entities.prompt import PromptMessage

        async def gen(args):
            return [PromptMessage(role=Role.USER, content=args["q"])]

        prompt = Prompt(name="test", arguments=[], generator=gen)
        result = await prompt.get_messages({"q": "hello"})
        assert len(result) == 1
        assert result[0].content == "hello"


class TestPromptToDict:
    def test_to_dict(self):
        prompt = Prompt(
            name="review",
            description="Code review",
            arguments=[PromptArgument(name="code", description="Code", required=True)],
        )
        d = prompt.to_dict()
        assert d["name"] == "review"
        assert d["description"] == "Code review"
        assert len(d["arguments"]) == 1
        assert d["arguments"][0]["name"] == "code"
