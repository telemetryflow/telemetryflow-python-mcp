"""Message entity and content blocks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from tfo_mcp.domain.valueobjects import ContentType, MessageID, Role


@dataclass
class TextContent:
    """Text content block."""

    type: ContentType = field(default=ContentType.TEXT, init=False)
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"type": self.type.value, "text": self.text}


@dataclass
class ToolUseContent:
    """Tool use content block."""

    type: ContentType = field(default=ContentType.TOOL_USE, init=False)
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "id": self.id,
            "name": self.name,
            "input": self.input,
        }


@dataclass
class ToolResultContent:
    """Tool result content block."""

    type: ContentType = field(default=ContentType.TOOL_RESULT, init=False)
    tool_use_id: str = ""
    content: str = ""
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "type": self.type.value,
            "tool_use_id": self.tool_use_id,
            "content": self.content,
        }
        if self.is_error:
            result["is_error"] = True
        return result


ContentBlock = TextContent | ToolUseContent | ToolResultContent


@dataclass
class Message:
    """Message entity representing a conversation message."""

    id: MessageID
    role: Role
    content: list[ContentBlock]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        role: Role,
        content: list[ContentBlock] | None = None,
        text: str | None = None,
    ) -> Message:
        """Create a new message."""
        if content is None:
            content = []
        if text is not None:
            content.append(TextContent(text=text))
        return cls(
            id=MessageID.generate(),
            role=role,
            content=content,
        )

    @classmethod
    def user(cls, text: str) -> Message:
        """Create a user message."""
        return cls.create(role=Role.USER, text=text)

    @classmethod
    def assistant(cls, text: str) -> Message:
        """Create an assistant message."""
        return cls.create(role=Role.ASSISTANT, text=text)

    @classmethod
    def system(cls, text: str) -> Message:
        """Create a system message."""
        return cls.create(role=Role.SYSTEM, text=text)

    @property
    def text(self) -> str:
        """Get concatenated text from all text content blocks."""
        texts = []
        for block in self.content:
            if isinstance(block, TextContent):
                texts.append(block.text)
        return "\n".join(texts)

    @property
    def tool_uses(self) -> list[ToolUseContent]:
        """Get all tool use content blocks."""
        return [block for block in self.content if isinstance(block, ToolUseContent)]

    @property
    def has_tool_use(self) -> bool:
        """Check if message contains tool use."""
        return any(isinstance(block, ToolUseContent) for block in self.content)

    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "role": self.role.value,
            "content": [block.to_dict() for block in self.content],
        }

    def to_api_format(self) -> dict[str, Any]:
        """Convert to Claude API format."""
        content_list: list[dict[str, Any]] = []
        for block in self.content:
            if isinstance(block, TextContent):
                content_list.append({"type": "text", "text": block.text})
            elif isinstance(block, ToolUseContent):
                content_list.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
            elif isinstance(block, ToolResultContent):
                content_list.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.tool_use_id,
                        "content": block.content,
                        "is_error": block.is_error,
                    }
                )
        return {"role": self.role.value, "content": content_list}
