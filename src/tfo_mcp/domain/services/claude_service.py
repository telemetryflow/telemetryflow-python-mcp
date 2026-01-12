"""Claude service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tfo_mcp.domain.entities import Message, Tool
    from tfo_mcp.domain.valueobjects import Model, SystemPrompt


class IClaudeService(ABC):
    """Interface for Claude API communication."""

    @abstractmethod
    async def create_message(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: list[Tool] | None = None,
    ) -> Message:
        """Create a message using Claude API."""
        ...

    @abstractmethod
    def create_message_stream(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: list[Tool] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Create a streaming message using Claude API.

        Returns an async generator that yields streaming events.
        """
        ...

    @abstractmethod
    async def count_tokens(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
    ) -> int:
        """Count tokens for messages."""
        ...
