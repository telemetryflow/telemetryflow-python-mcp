"""Repository interfaces for domain aggregates and entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tfo_mcp.domain.aggregates import Conversation, Session
    from tfo_mcp.domain.entities import Prompt, Resource, Tool
    from tfo_mcp.domain.valueobjects import ConversationID, SessionID


class ISessionRepository(ABC):
    """Repository interface for Session aggregate."""

    @abstractmethod
    async def save(self, session: Session) -> None:
        """Save a session."""
        ...

    @abstractmethod
    async def get(self, session_id: SessionID) -> Session | None:
        """Get a session by ID."""
        ...

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Session | None:
        """Get a session by string ID."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Session]:
        """List all sessions."""
        ...

    @abstractmethod
    async def delete(self, session_id: SessionID) -> bool:
        """Delete a session."""
        ...


class IConversationRepository(ABC):
    """Repository interface for Conversation aggregate."""

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """Save a conversation."""
        ...

    @abstractmethod
    async def get(self, conversation_id: ConversationID) -> Conversation | None:
        """Get a conversation by ID."""
        ...

    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by string ID."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Conversation]:
        """List all conversations."""
        ...

    @abstractmethod
    async def list_by_session(self, session_id: str) -> list[Conversation]:
        """List conversations by session ID."""
        ...

    @abstractmethod
    async def delete(self, conversation_id: ConversationID) -> bool:
        """Delete a conversation."""
        ...


class IToolRepository(ABC):
    """Repository interface for Tool entity."""

    @abstractmethod
    async def save(self, tool: Tool) -> None:
        """Save a tool."""
        ...

    @abstractmethod
    async def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Tool]:
        """List all tools."""
        ...

    @abstractmethod
    async def list_enabled(self) -> list[Tool]:
        """List only enabled tools."""
        ...

    @abstractmethod
    async def list_by_category(self, category: str) -> list[Tool]:
        """List tools by category."""
        ...

    @abstractmethod
    async def delete(self, name: str) -> bool:
        """Delete a tool."""
        ...


class IResourceRepository(ABC):
    """Repository interface for Resource entity."""

    @abstractmethod
    async def save(self, resource: Resource) -> None:
        """Save a resource."""
        ...

    @abstractmethod
    async def get(self, uri: str) -> Resource | None:
        """Get a resource by URI."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Resource]:
        """List all resources."""
        ...

    @abstractmethod
    async def list_templates(self) -> list[Resource]:
        """List template resources."""
        ...

    @abstractmethod
    async def delete(self, uri: str) -> bool:
        """Delete a resource."""
        ...


class IPromptRepository(ABC):
    """Repository interface for Prompt entity."""

    @abstractmethod
    async def save(self, prompt: Prompt) -> None:
        """Save a prompt."""
        ...

    @abstractmethod
    async def get(self, name: str) -> Prompt | None:
        """Get a prompt by name."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Prompt]:
        """List all prompts."""
        ...

    @abstractmethod
    async def delete(self, name: str) -> bool:
        """Delete a prompt."""
        ...
