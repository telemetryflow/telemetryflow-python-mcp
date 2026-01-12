"""Repository interfaces."""

from tfo_mcp.domain.repositories.repositories import (
    IConversationRepository,
    IPromptRepository,
    IResourceRepository,
    ISessionRepository,
    IToolRepository,
)

__all__ = [
    "ISessionRepository",
    "IConversationRepository",
    "IToolRepository",
    "IResourceRepository",
    "IPromptRepository",
]
