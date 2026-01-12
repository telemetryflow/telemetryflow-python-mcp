"""Unit tests for built-in prompts."""

import pytest

from tfo_mcp.domain.aggregates import Session
from tfo_mcp.domain.entities import Prompt, PromptArgument, PromptMessage
from tfo_mcp.domain.valueobjects import Role
from tfo_mcp.presentation.prompts.builtin_prompts import (
    _code_review_generator,
    _debug_help_generator,
    _explain_code_generator,
    register_builtin_prompts,
)


class TestCodeReviewPrompt:
    """Test code_review prompt."""

    @pytest.mark.asyncio
    async def test_generate_code_review(self):
        """Test generating code review prompt."""
        args = {
            "code": "def hello():\n    print('world')",
            "language": "python",
        }

        messages = await _code_review_generator(args)

        assert len(messages) >= 1
        assert messages[0].role == Role.USER
        assert "code" in messages[0].content.lower() or args["code"] in messages[0].content

    @pytest.mark.asyncio
    async def test_code_review_with_focus(self):
        """Test code review with specific focus."""
        args = {
            "code": "def func(): pass",
            "language": "python",
            "focus": "security",
        }

        messages = await _code_review_generator(args)

        assert len(messages) >= 1
        # The generated prompt should mention security or the code
        content = messages[0].content.lower()
        assert "code" in content or "review" in content

    @pytest.mark.asyncio
    async def test_code_review_generates_message(self):
        """Test code review generates a valid message."""
        args = {
            "code": "print('hello')",
        }

        messages = await _code_review_generator(args)

        assert len(messages) >= 1
        assert isinstance(messages[0], PromptMessage)


class TestExplainCodePrompt:
    """Test explain_code prompt."""

    @pytest.mark.asyncio
    async def test_generate_explain_code(self):
        """Test generating explain code prompt."""
        args = {
            "code": "for i in range(10): print(i)",
            "language": "python",
        }

        messages = await _explain_code_generator(args)

        assert len(messages) >= 1
        assert messages[0].role == Role.USER

    @pytest.mark.asyncio
    async def test_explain_code_with_detail_level(self):
        """Test explain code with detail level."""
        args = {
            "code": "x = lambda y: y * 2",
            "language": "python",
            "detail_level": "detailed",
        }

        messages = await _explain_code_generator(args)

        assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_explain_code_default_language(self):
        """Test explain code with default language."""
        args = {
            "code": "console.log('hello')",
        }

        messages = await _explain_code_generator(args)

        assert len(messages) >= 1


class TestDebugHelpPrompt:
    """Test debug_help prompt."""

    @pytest.mark.asyncio
    async def test_generate_debug_help(self):
        """Test generating debug help prompt."""
        args = {
            "error": "TypeError: 'NoneType' object is not iterable",
            "code": "for item in data: print(item)",
            "language": "python",
        }

        messages = await _debug_help_generator(args)

        assert len(messages) >= 1
        assert messages[0].role == Role.USER

    @pytest.mark.asyncio
    async def test_debug_help_with_context(self):
        """Test debug help with additional context."""
        args = {
            "error": "IndexError: list index out of range",
            "code": "data[10]",
            "context": "The list has only 5 elements",
        }

        messages = await _debug_help_generator(args)

        assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_debug_help_generates_message(self):
        """Test debug help generates a valid message."""
        args = {
            "error": "SyntaxError: invalid syntax",
        }

        messages = await _debug_help_generator(args)

        assert len(messages) >= 1
        assert isinstance(messages[0], PromptMessage)


class TestPromptRegistration:
    """Test prompt registration."""

    @pytest.fixture
    def session(self):
        """Create test session."""
        return Session.create()

    def test_register_builtin_prompts(self, session):
        """Test registering built-in prompts."""
        register_builtin_prompts(session)

        # Check code_review prompt
        code_review = session.get_prompt("code_review")
        assert code_review is not None
        assert str(code_review.name) == "code_review"

        # Check explain_code prompt
        explain_code = session.get_prompt("explain_code")
        assert explain_code is not None

        # Check debug_help prompt
        debug_help = session.get_prompt("debug_help")
        assert debug_help is not None

    def test_prompt_count(self, session):
        """Test prompt count after registration."""
        initial_count = len(session.list_prompts())
        register_builtin_prompts(session)

        final_count = len(session.list_prompts())
        assert final_count >= initial_count + 3  # At least 3 prompts

    def test_prompt_arguments(self, session):
        """Test prompt arguments are configured."""
        register_builtin_prompts(session)

        code_review = session.get_prompt("code_review")
        assert len(code_review.arguments) >= 1

        # Code argument should be required
        code_arg = next(
            (arg for arg in code_review.arguments if arg.name == "code"),
            None,
        )
        assert code_arg is not None
        assert code_arg.required is True


class TestPromptEntity:
    """Test Prompt entity."""

    def test_create_prompt(self):
        """Test creating a prompt."""
        prompt = Prompt.create(
            name="test_prompt",
            description="A test prompt",
            arguments=[
                PromptArgument(
                    name="input",
                    description="The input",
                    required=True,
                ),
            ],
        )

        assert str(prompt.name) == "test_prompt"
        assert str(prompt.description) == "A test prompt"
        assert len(prompt.arguments) == 1

    def test_prompt_to_mcp_format(self):
        """Test prompt MCP format conversion."""
        prompt = Prompt.create(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(
                    name="arg1",
                    description="Argument 1",
                    required=True,
                ),
                PromptArgument(
                    name="arg2",
                    description="Argument 2",
                    required=False,
                ),
            ],
        )

        mcp_format = prompt.to_mcp_format()

        assert mcp_format["name"] == "test"
        assert mcp_format["description"] == "Test"
        assert len(mcp_format["arguments"]) == 2

    def test_prompt_with_generator(self):
        """Test prompt with generator function."""

        async def generator(args):
            return [PromptMessage(role=Role.USER, content=args.get("text", ""))]

        prompt = Prompt.create(
            name="custom",
            description="Custom prompt",
            arguments=[],
            generator=generator,
        )

        assert prompt.generator is not None


class TestPromptArgument:
    """Test PromptArgument entity."""

    def test_required_argument(self):
        """Test required argument."""
        arg = PromptArgument(
            name="code",
            description="The code to review",
            required=True,
        )

        assert arg.name == "code"
        assert arg.required is True

    def test_optional_argument(self):
        """Test optional argument."""
        arg = PromptArgument(
            name="language",
            description="Programming language",
            required=False,
        )

        assert arg.required is False

    def test_argument_to_dict(self):
        """Test argument to dict conversion."""
        arg = PromptArgument(
            name="test",
            description="Test argument",
            required=True,
        )

        d = arg.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "Test argument"
        assert d["required"] is True


class TestPromptMessage:
    """Test PromptMessage entity."""

    def test_user_message(self):
        """Test user prompt message."""
        msg = PromptMessage(role=Role.USER, content="Please help")

        assert msg.role == Role.USER
        assert msg.content == "Please help"

    def test_assistant_message(self):
        """Test assistant prompt message."""
        msg = PromptMessage(role=Role.ASSISTANT, content="I'll help")

        assert msg.role == Role.ASSISTANT

    def test_message_to_dict(self):
        """Test message to dict conversion."""
        msg = PromptMessage(role=Role.USER, content="Hello")

        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"]["type"] == "text"
        assert d["content"]["text"] == "Hello"
