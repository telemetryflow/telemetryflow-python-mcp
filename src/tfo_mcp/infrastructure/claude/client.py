"""Claude API client implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import anthropic
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from tfo_mcp.domain.entities import Message, TextContent, ToolResultContent, ToolUseContent
from tfo_mcp.domain.services import IClaudeService
from tfo_mcp.domain.valueobjects import MessageID, Model, Role, SystemPrompt
from tfo_mcp.infrastructure.config import ClaudeConfig

logger = structlog.get_logger(__name__)


class ClaudeClient(IClaudeService):
    """Claude API client implementation."""

    def __init__(self, config: ClaudeConfig) -> None:
        self._config = config
        self._client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,  # We handle retries ourselves
        )

    def _build_tools(self, tools: list[Any] | None) -> list[dict[str, Any]] | None:
        """Build tools list for API call."""
        if not tools:
            return None
        return [
            {
                "name": str(tool.name),
                "description": str(tool.description),
                "input_schema": tool.input_schema.to_dict(),
            }
            for tool in tools
        ]

    def _build_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Build messages list for API call."""
        return [msg.to_api_format() for msg in messages]

    def _parse_response(self, response: anthropic.types.Message) -> Message:
        """Parse API response into Message entity."""
        content_blocks: list[TextContent | ToolUseContent | ToolResultContent] = []

        for block in response.content:
            if block.type == "text":
                content_blocks.append(TextContent(text=block.text))
            elif block.type == "tool_use":
                content_blocks.append(
                    ToolUseContent(
                        id=block.id,
                        name=block.name,
                        input=dict(block.input) if block.input else {},
                    )
                )

        message = Message(
            id=MessageID.generate(),
            role=Role.ASSISTANT,
            content=content_blocks,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            metadata={
                "model": response.model,
                "stop_reason": response.stop_reason,
            },
        )

        return message

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIConnectionError)),
        reraise=True,
    )
    async def create_message(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: list[Any] | None = None,
    ) -> Message:
        """Create a message using Claude API."""
        logger.debug(
            "Creating message",
            model=model.value,
            message_count=len(messages),
            has_tools=bool(tools),
        )

        kwargs: dict[str, Any] = {
            "model": model.value,
            "messages": self._build_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt and not system_prompt.is_empty:
            kwargs["system"] = str(system_prompt)

        if tools:
            kwargs["tools"] = self._build_tools(tools)

        response = await self._client.messages.create(**kwargs)

        message = self._parse_response(response)

        logger.debug(
            "Message created",
            input_tokens=message.input_tokens,
            output_tokens=message.output_tokens,
            has_tool_use=message.has_tool_use,
        )

        return message

    async def create_message_stream(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: list[Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Create a streaming message using Claude API."""
        logger.debug(
            "Creating streaming message",
            model=model.value,
            message_count=len(messages),
        )

        kwargs: dict[str, Any] = {
            "model": model.value,
            "messages": self._build_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt and not system_prompt.is_empty:
            kwargs["system"] = str(system_prompt)

        if tools:
            kwargs["tools"] = self._build_tools(tools)

        async with self._client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    yield {"type": event.type, "data": event}

    async def count_tokens(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
    ) -> int:
        """Count tokens for messages."""
        kwargs: dict[str, Any] = {
            "model": model.value,
            "messages": self._build_messages(messages),
        }

        if system_prompt and not system_prompt.is_empty:
            kwargs["system"] = str(system_prompt)

        result = await self._client.messages.count_tokens(**kwargs)
        return result.input_tokens
