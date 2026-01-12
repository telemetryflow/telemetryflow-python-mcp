"""Prompt entity."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from tfo_mcp.domain.valueobjects import Role


@dataclass
class PromptArgument:
    """Prompt argument definition."""

    name: str
    description: str = ""
    required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP format."""
        result: dict[str, Any] = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.required:
            result["required"] = True
        return result


@dataclass
class PromptMessage:
    """Message in a prompt."""

    role: Role
    content: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP format."""
        return {
            "role": self.role.value,
            "content": {"type": "text", "text": self.content},
        }


# Type alias for prompt generator function
PromptGenerator = Callable[[dict[str, str]], Awaitable[list[PromptMessage]]]


@dataclass
class Prompt:
    """Prompt entity representing an MCP prompt."""

    name: str
    description: str = ""
    arguments: list[PromptArgument] = field(default_factory=list)
    generator: PromptGenerator | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        arguments: list[PromptArgument] | None = None,
        generator: PromptGenerator | None = None,
    ) -> Prompt:
        """Create a new prompt."""
        return cls(
            name=name,
            description=description,
            arguments=arguments or [],
            generator=generator,
        )

    async def get_messages(self, args: dict[str, str]) -> list[PromptMessage]:
        """Generate prompt messages with given arguments."""
        # Validate required arguments
        for arg in self.arguments:
            if arg.required and arg.name not in args:
                raise ValueError(f"Missing required argument: {arg.name}")

        if self.generator is None:
            return []
        return await self.generator(args)

    def to_mcp_format(self) -> dict[str, Any]:
        """Convert to MCP prompts/list format."""
        result: dict[str, Any] = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.arguments:
            result["arguments"] = [arg.to_dict() for arg in self.arguments]
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "arguments": [arg.to_dict() for arg in self.arguments],
        }
