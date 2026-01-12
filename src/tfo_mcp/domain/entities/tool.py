"""Tool entity."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from tfo_mcp.domain.valueobjects import ToolDescription, ToolName


@dataclass
class ToolInputSchema:
    """JSON Schema for tool input validation."""

    type: str = "object"
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    additional_properties: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON Schema dictionary."""
        schema: dict[str, Any] = {
            "type": self.type,
            "properties": self.properties,
        }
        if self.required:
            schema["required"] = self.required
        if not self.additional_properties:
            schema["additionalProperties"] = False
        return schema

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolInputSchema:
        """Create from dictionary."""
        return cls(
            type=data.get("type", "object"),
            properties=data.get("properties", {}),
            required=data.get("required", []),
            additional_properties=data.get("additionalProperties", False),
        )


@dataclass
class ToolResult:
    """Result from tool execution."""

    content: list[dict[str, Any]]
    is_error: bool = False

    @classmethod
    def text(cls, text: str, is_error: bool = False) -> ToolResult:
        """Create a text result."""
        return cls(content=[{"type": "text", "text": text}], is_error=is_error)

    @classmethod
    def error(cls, message: str) -> ToolResult:
        """Create an error result."""
        return cls.text(message, is_error=True)

    @classmethod
    def json(cls, data: Any, is_error: bool = False) -> ToolResult:
        """Create a JSON result."""
        import json

        return cls.text(json.dumps(data, indent=2), is_error=is_error)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {"content": self.content}
        if self.is_error:
            result["isError"] = True
        return result


# Type alias for tool handler function
ToolHandler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


@dataclass
class Tool:
    """Tool entity representing an MCP tool."""

    name: ToolName
    description: ToolDescription
    input_schema: ToolInputSchema
    handler: ToolHandler | None = None
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    timeout_seconds: float = 30.0
    rate_limit: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        input_schema: dict[str, Any] | ToolInputSchema,
        handler: ToolHandler | None = None,
        category: str = "general",
        tags: list[str] | None = None,
        timeout_seconds: float = 30.0,
    ) -> Tool:
        """Create a new tool."""
        if isinstance(input_schema, dict):
            input_schema = ToolInputSchema.from_dict(input_schema)
        return cls(
            name=ToolName(value=name),
            description=ToolDescription(value=description),
            input_schema=input_schema,
            handler=handler,
            category=category,
            tags=tags or [],
            timeout_seconds=timeout_seconds,
        )

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the tool with given input."""
        if self.handler is None:
            return ToolResult.error(f"Tool '{self.name}' has no handler")
        if not self.enabled:
            return ToolResult.error(f"Tool '{self.name}' is disabled")
        return await self.handler(input_data)

    def to_mcp_format(self) -> dict[str, Any]:
        """Convert to MCP tools/list format."""
        return {
            "name": str(self.name),
            "description": str(self.description),
            "inputSchema": self.input_schema.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": str(self.name),
            "description": str(self.description),
            "inputSchema": self.input_schema.to_dict(),
            "category": self.category,
            "tags": self.tags,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
        }
