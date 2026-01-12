"""Domain entities."""

from tfo_mcp.domain.entities.message import (
    ContentBlock,
    Message,
    TextContent,
    ToolResultContent,
    ToolUseContent,
)
from tfo_mcp.domain.entities.prompt import Prompt, PromptArgument, PromptMessage
from tfo_mcp.domain.entities.resource import Resource, ResourceContent
from tfo_mcp.domain.entities.tool import Tool, ToolInputSchema, ToolResult

__all__ = [
    "Message",
    "ContentBlock",
    "TextContent",
    "ToolUseContent",
    "ToolResultContent",
    "Tool",
    "ToolResult",
    "ToolInputSchema",
    "Resource",
    "ResourceContent",
    "Prompt",
    "PromptArgument",
    "PromptMessage",
]
