"""Conversation command and query handler."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import structlog

from tfo_mcp.domain.aggregates import Conversation, ConversationSettings
from tfo_mcp.domain.entities import Message, TextContent, ToolResultContent, ToolUseContent
from tfo_mcp.domain.valueobjects import Role

if TYPE_CHECKING:
    from tfo_mcp.application.commands import CreateConversationCommand, SendMessageCommand
    from tfo_mcp.application.queries import (
        GetConversationMessagesQuery,
        GetConversationQuery,
        ListConversationsQuery,
    )
    from tfo_mcp.domain.repositories import IConversationRepository
    from tfo_mcp.domain.services import IClaudeService


logger = structlog.get_logger(__name__)


class ConversationHandler:
    """Handler for conversation commands and queries."""

    def __init__(
        self,
        conversation_repository: IConversationRepository,
        claude_service: IClaudeService,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._claude_service = claude_service

    async def handle_create(
        self,
        command: CreateConversationCommand,
    ) -> Conversation:
        """Handle create conversation command."""
        logger.info(
            "Creating conversation",
            model=command.model.value,
        )

        settings = ConversationSettings(
            max_tokens=command.max_tokens,
            temperature=command.temperature,
        )

        conversation = Conversation.create(
            model=command.model,
            system_prompt=command.system_prompt,
            settings=settings,
        )

        await self._conversation_repository.save(conversation)

        logger.info(
            "Conversation created",
            conversation_id=str(conversation.id),
        )

        return conversation

    async def handle_send_message(
        self,
        command: SendMessageCommand,
    ) -> Message:
        """Handle send message command."""
        logger.info(
            "Sending message",
            conversation_id=command.conversation_id,
        )

        conversation = await self._conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {command.conversation_id}")

        # Add user message
        user_message = Message.user(command.message)
        conversation.add_message(user_message)

        # Call Claude API
        response = await self._claude_service.create_message(
            messages=conversation.messages,
            model=conversation.model,
            system_prompt=conversation.system_prompt if conversation.system_prompt else None,
            max_tokens=conversation.settings.max_tokens,
            temperature=conversation.settings.temperature,
            tools=command.tools if command.tools else None,
        )

        # Add assistant response
        conversation.add_message(response)
        await self._conversation_repository.save(conversation)

        logger.info(
            "Message sent",
            conversation_id=command.conversation_id,
            has_tool_use=response.has_tool_use,
        )

        return response

    async def handle_send_message_stream(
        self,
        command: SendMessageCommand,
    ) -> AsyncIterator[dict[str, Any]]:
        """Handle send message command with streaming."""
        logger.info(
            "Sending message (streaming)",
            conversation_id=command.conversation_id,
        )

        conversation = await self._conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {command.conversation_id}")

        # Add user message
        user_message = Message.user(command.message)
        conversation.add_message(user_message)

        # Stream from Claude API
        content_blocks: list[TextContent | ToolUseContent | ToolResultContent] = []
        current_text = ""

        async for event in self._claude_service.create_message_stream(
            messages=conversation.messages,
            model=conversation.model,
            system_prompt=conversation.system_prompt if conversation.system_prompt else None,
            max_tokens=conversation.settings.max_tokens,
            temperature=conversation.settings.temperature,
            tools=command.tools if command.tools else None,
        ):
            event_type = event.get("type")

            if event_type == "content_block_start":
                block = event.get("content_block", {})
                if block.get("type") == "text":
                    current_text = block.get("text", "")
                yield event

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    current_text += delta.get("text", "")
                yield event

            elif event_type == "content_block_stop":
                if current_text:
                    content_blocks.append(TextContent(text=current_text))
                    current_text = ""
                yield event

            elif event_type == "message_stop":
                # Create and add assistant message
                response = Message.create(role=Role.ASSISTANT, content=content_blocks)
                conversation.add_message(response)
                await self._conversation_repository.save(conversation)
                yield event

            else:
                yield event

    async def get_conversation(
        self,
        query: GetConversationQuery,
    ) -> Conversation | None:
        """Handle get conversation query."""
        return await self._conversation_repository.get_by_id(query.conversation_id)

    async def list_conversations(
        self,
        query: ListConversationsQuery,
    ) -> list[Conversation]:
        """Handle list conversations query."""
        if query.session_id:
            conversations = await self._conversation_repository.list_by_session(query.session_id)
        else:
            conversations = await self._conversation_repository.list_all()

        start = query.offset
        end = start + query.limit
        return conversations[start:end]

    async def get_messages(
        self,
        query: GetConversationMessagesQuery,
    ) -> list[Message]:
        """Handle get conversation messages query."""
        conversation = await self._conversation_repository.get_by_id(query.conversation_id)
        if not conversation:
            return []

        start = query.offset
        end = start + query.limit
        return conversation.messages[start:end]
