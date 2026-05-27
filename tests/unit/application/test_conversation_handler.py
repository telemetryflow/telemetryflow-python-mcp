from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tfo_mcp.application.commands.commands import CreateConversationCommand, SendMessageCommand
from tfo_mcp.application.handlers.conversation_handler import ConversationHandler
from tfo_mcp.application.queries.queries import (
    GetConversationMessagesQuery,
    GetConversationQuery,
    ListConversationsQuery,
)
from tfo_mcp.domain.aggregates.conversation import Conversation
from tfo_mcp.domain.entities import Message
from tfo_mcp.domain.valueobjects import Model
from tfo_mcp.infrastructure.persistence.memory_repositories import InMemoryConversationRepository


@pytest.fixture
def conversation_repo():
    return InMemoryConversationRepository()


@pytest.fixture
def claude_service():
    svc = MagicMock()
    svc.create_message = AsyncMock(return_value=Message.assistant("Hello back!"))
    return svc


@pytest.fixture
def handler(conversation_repo, claude_service):
    return ConversationHandler(conversation_repo, claude_service)


@pytest.fixture
def existing_conversation(conversation_repo):
    conv = Conversation.create(model=Model.CLAUDE_SONNET_4, system_prompt="test")
    conversation_repo._conversations[str(conv.id)] = conv
    return conv


class TestHandleCreate:
    async def test_creates_conversation(self, handler, conversation_repo):
        cmd = CreateConversationCommand(
            model=Model.CLAUDE_SONNET_4,
            system_prompt="You are helpful",
            max_tokens=2048,
            temperature=0.7,
        )
        result = await handler.handle_create(cmd)

        assert isinstance(result, Conversation)
        assert result.model == Model.CLAUDE_SONNET_4
        assert str(result.system_prompt) == "You are helpful"
        assert result.settings.max_tokens == 2048
        assert result.settings.temperature == 0.7
        saved = await conversation_repo.get_by_id(str(result.id))
        assert saved is not None

    async def test_creates_with_defaults(self, handler):
        cmd = CreateConversationCommand(model=Model.CLAUDE_SONNET_4)
        result = await handler.handle_create(cmd)

        assert result.settings.max_tokens == 4096
        assert result.settings.temperature == 1.0


class TestHandleSendMessage:
    async def test_sends_message(self, handler, existing_conversation, claude_service):
        cmd = SendMessageCommand(
            conversation_id=str(existing_conversation.id),
            message="Hello!",
        )
        result = await handler.handle_send_message(cmd)

        assert isinstance(result, Message)
        assert result.role.value == "assistant"
        claude_service.create_message.assert_called_once()

    async def test_raises_for_missing_conversation(self, handler):
        cmd = SendMessageCommand(
            conversation_id="nonexistent",
            message="Hello!",
        )
        with pytest.raises(ValueError, match="Conversation not found"):
            await handler.handle_send_message(cmd)

    async def test_passes_tools_to_claude(self, handler, existing_conversation, claude_service):
        from tfo_mcp.domain.entities import Tool

        tool = Tool.create(name="test_tool", description="A tool", input_schema={"type": "object"})
        cmd = SendMessageCommand(
            conversation_id=str(existing_conversation.id),
            message="Use tool",
            tools=[tool],
        )
        await handler.handle_send_message(cmd)

        call_kwargs = claude_service.create_message.call_args
        assert (
            call_kwargs.kwargs.get("tools") is not None
            or (call_kwargs[1] if len(call_kwargs) > 1 else {}).get("tools") is not None
        )

    async def test_saves_conversation_after_message(
        self, handler, existing_conversation, conversation_repo, claude_service  # noqa: ARG002
    ):
        cmd = SendMessageCommand(
            conversation_id=str(existing_conversation.id),
            message="Hello!",
        )
        await handler.handle_send_message(cmd)

        saved = await conversation_repo.get_by_id(str(existing_conversation.id))
        assert len(saved.messages) == 2
        assert saved.messages[0].role.value == "user"
        assert saved.messages[1].role.value == "assistant"


class TestHandleSendMessageStream:
    async def test_streams_events(self, handler, existing_conversation, claude_service):
        events = [
            {"type": "content_block_start", "content_block": {"type": "text", "text": "Hi"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " there"}},
            {"type": "content_block_stop"},
            {"type": "message_stop"},
        ]

        async def mock_stream(**_kwargs):
            for event in events:
                yield event

        claude_service.create_message_stream = MagicMock(return_value=mock_stream())

        cmd = SendMessageCommand(
            conversation_id=str(existing_conversation.id),
            message="Hello!",
        )

        collected = []
        async for event in handler.handle_send_message_stream(cmd):
            collected.append(event)

        assert len(collected) == 4
        assert collected[0]["type"] == "content_block_start"
        assert collected[1]["type"] == "content_block_delta"
        assert collected[2]["type"] == "content_block_stop"
        assert collected[3]["type"] == "message_stop"

    async def test_stream_saves_on_message_stop(
        self, handler, existing_conversation, conversation_repo, claude_service
    ):
        events = [
            {"type": "content_block_start", "content_block": {"type": "text", "text": "Hi"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " there"}},
            {"type": "content_block_stop"},
            {"type": "message_stop"},
        ]

        async def mock_stream(**_kwargs):
            for event in events:
                yield event

        claude_service.create_message_stream = MagicMock(return_value=mock_stream())

        cmd = SendMessageCommand(
            conversation_id=str(existing_conversation.id),
            message="Hello!",
        )

        async for _ in handler.handle_send_message_stream(cmd):
            pass

        saved = await conversation_repo.get_by_id(str(existing_conversation.id))
        assert len(saved.messages) == 2

    async def test_stream_raises_for_missing_conversation(self, handler):
        cmd = SendMessageCommand(
            conversation_id="nonexistent",
            message="Hello!",
        )
        with pytest.raises(ValueError, match="Conversation not found"):
            async for _ in handler.handle_send_message_stream(cmd):
                pass

    async def test_stream_yields_other_events(self, handler, existing_conversation, claude_service):
        events = [
            {"type": "message_start"},
            {"type": "content_block_start", "content_block": {"type": "text", "text": ""}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "X"}},
            {"type": "content_block_stop"},
            {"type": "message_delta"},
            {"type": "message_stop"},
        ]

        async def mock_stream(**_kwargs):
            for event in events:
                yield event

        claude_service.create_message_stream = MagicMock(return_value=mock_stream())

        cmd = SendMessageCommand(
            conversation_id=str(existing_conversation.id),
            message="Hi",
        )

        collected = []
        async for event in handler.handle_send_message_stream(cmd):
            collected.append(event)

        assert len(collected) == 6
        assert collected[0]["type"] == "message_start"

    async def test_stream_handles_empty_text(
        self, handler, existing_conversation, claude_service, conversation_repo
    ):
        events = [
            {"type": "content_block_start", "content_block": {"type": "text", "text": ""}},
            {"type": "content_block_stop"},
            {"type": "message_stop"},
        ]

        async def mock_stream(**_kwargs):
            for event in events:
                yield event

        claude_service.create_message_stream = MagicMock(return_value=mock_stream())

        cmd = SendMessageCommand(
            conversation_id=str(existing_conversation.id),
            message="Hi",
        )

        async for _ in handler.handle_send_message_stream(cmd):
            pass

        saved = await conversation_repo.get_by_id(str(existing_conversation.id))
        assert len(saved.messages) == 2


class TestGetConversation:
    async def test_gets_existing(self, handler, existing_conversation):
        query = GetConversationQuery(conversation_id=str(existing_conversation.id))
        result = await handler.get_conversation(query)
        assert result is not None
        assert str(result.id) == str(existing_conversation.id)

    async def test_returns_none_for_missing(self, handler):
        query = GetConversationQuery(conversation_id="nonexistent")
        result = await handler.get_conversation(query)
        assert result is None


class TestListConversations:
    async def test_lists_all(self, handler, conversation_repo):
        for _i in range(5):
            conv = Conversation.create(model=Model.CLAUDE_SONNET_4)
            await conversation_repo.save(conv)

        query = ListConversationsQuery(limit=100, offset=0)
        result = await handler.list_conversations(query)
        assert len(result) == 5

    async def test_pagination(self, handler, conversation_repo):
        for _i in range(10):
            conv = Conversation.create(model=Model.CLAUDE_SONNET_4)
            await conversation_repo.save(conv)

        query = ListConversationsQuery(limit=3, offset=2)
        result = await handler.list_conversations(query)
        assert len(result) == 3

    async def test_by_session_id(self, handler, conversation_repo):
        conv = Conversation.create(model=Model.CLAUDE_SONNET_4)
        conversation_repo._session_conversations["session-1"] = [str(conv.id)]
        conversation_repo._conversations[str(conv.id)] = conv

        query = ListConversationsQuery(session_id="session-1", limit=100, offset=0)
        result = await handler.list_conversations(query)
        assert len(result) == 1


class TestGetMessages:
    async def test_gets_messages(self, handler, existing_conversation, conversation_repo):
        existing_conversation.add_message(Message.user("Hello"))
        existing_conversation.add_message(Message.assistant("Hi"))
        await conversation_repo.save(existing_conversation)

        query = GetConversationMessagesQuery(conversation_id=str(existing_conversation.id))
        result = await handler.get_messages(query)
        assert len(result) == 2

    async def test_pagination(self, handler, existing_conversation, conversation_repo):
        for i in range(5):
            existing_conversation.add_message(Message.user(f"msg-{i}"))
        await conversation_repo.save(existing_conversation)

        query = GetConversationMessagesQuery(
            conversation_id=str(existing_conversation.id),
            limit=2,
            offset=1,
        )
        result = await handler.get_messages(query)
        assert len(result) == 2

    async def test_returns_empty_for_missing(self, handler):
        query = GetConversationMessagesQuery(conversation_id="nonexistent")
        result = await handler.get_messages(query)
        assert result == []
