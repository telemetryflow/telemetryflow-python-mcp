"""In-memory repository implementations for development and testing."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from tfo_mcp.domain.repositories import (
    IConversationRepository,
    IPromptRepository,
    IResourceRepository,
    ISessionRepository,
    IToolRepository,
)

if TYPE_CHECKING:
    from tfo_mcp.domain.aggregates import Conversation, Session
    from tfo_mcp.domain.entities import Prompt, Resource, Tool
    from tfo_mcp.domain.valueobjects import ConversationID, SessionID


class InMemorySessionRepository(ISessionRepository):
    """In-memory session repository."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.RLock()

    async def save(self, session: Session) -> None:
        """Save a session."""
        with self._lock:
            self._sessions[str(session.id)] = session

    async def get(self, session_id: SessionID) -> Session | None:
        """Get a session by ID."""
        with self._lock:
            return self._sessions.get(str(session_id))

    async def get_by_id(self, session_id: str) -> Session | None:
        """Get a session by string ID."""
        with self._lock:
            return self._sessions.get(session_id)

    async def list_all(self) -> list[Session]:
        """List all sessions."""
        with self._lock:
            return list(self._sessions.values())

    async def delete(self, session_id: SessionID) -> bool:
        """Delete a session."""
        with self._lock:
            if str(session_id) in self._sessions:
                del self._sessions[str(session_id)]
                return True
            return False


class InMemoryConversationRepository(IConversationRepository):
    """In-memory conversation repository."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._session_conversations: dict[str, list[str]] = {}
        self._lock = threading.RLock()

    async def save(self, conversation: Conversation) -> None:
        """Save a conversation."""
        with self._lock:
            self._conversations[str(conversation.id)] = conversation

    async def get(self, conversation_id: ConversationID) -> Conversation | None:
        """Get a conversation by ID."""
        with self._lock:
            return self._conversations.get(str(conversation_id))

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by string ID."""
        with self._lock:
            return self._conversations.get(conversation_id)

    async def list_all(self) -> list[Conversation]:
        """List all conversations."""
        with self._lock:
            return list(self._conversations.values())

    async def list_by_session(self, session_id: str) -> list[Conversation]:
        """List conversations by session ID."""
        with self._lock:
            conv_ids = self._session_conversations.get(session_id, [])
            return [self._conversations[cid] for cid in conv_ids if cid in self._conversations]

    async def delete(self, conversation_id: ConversationID) -> bool:
        """Delete a conversation."""
        with self._lock:
            if str(conversation_id) in self._conversations:
                del self._conversations[str(conversation_id)]
                return True
            return False


class InMemoryToolRepository(IToolRepository):
    """In-memory tool repository."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._lock = threading.RLock()

    async def save(self, tool: Tool) -> None:
        """Save a tool."""
        with self._lock:
            self._tools[str(tool.name)] = tool

    async def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        with self._lock:
            return self._tools.get(name)

    async def list_all(self) -> list[Tool]:
        """List all tools."""
        with self._lock:
            return list(self._tools.values())

    async def list_enabled(self) -> list[Tool]:
        """List only enabled tools."""
        with self._lock:
            return [t for t in self._tools.values() if t.enabled]

    async def list_by_category(self, category: str) -> list[Tool]:
        """List tools by category."""
        with self._lock:
            return [t for t in self._tools.values() if t.category == category]

    async def delete(self, name: str) -> bool:
        """Delete a tool."""
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                return True
            return False


class InMemoryResourceRepository(IResourceRepository):
    """In-memory resource repository."""

    def __init__(self) -> None:
        self._resources: dict[str, Resource] = {}
        self._lock = threading.RLock()

    async def save(self, resource: Resource) -> None:
        """Save a resource."""
        with self._lock:
            self._resources[str(resource.uri)] = resource

    async def get(self, uri: str) -> Resource | None:
        """Get a resource by URI."""
        with self._lock:
            # Direct match
            if uri in self._resources:
                return self._resources[uri]
            # Template match
            for resource in self._resources.values():
                if resource.matches_uri(uri):
                    return resource
            return None

    async def list_all(self) -> list[Resource]:
        """List all resources."""
        with self._lock:
            return list(self._resources.values())

    async def list_templates(self) -> list[Resource]:
        """List template resources."""
        with self._lock:
            return [r for r in self._resources.values() if r.is_template]

    async def delete(self, uri: str) -> bool:
        """Delete a resource."""
        with self._lock:
            if uri in self._resources:
                del self._resources[uri]
                return True
            return False


class InMemoryPromptRepository(IPromptRepository):
    """In-memory prompt repository."""

    def __init__(self) -> None:
        self._prompts: dict[str, Prompt] = {}
        self._lock = threading.RLock()

    async def save(self, prompt: Prompt) -> None:
        """Save a prompt."""
        with self._lock:
            self._prompts[prompt.name] = prompt

    async def get(self, name: str) -> Prompt | None:
        """Get a prompt by name."""
        with self._lock:
            return self._prompts.get(name)

    async def list_all(self) -> list[Prompt]:
        """List all prompts."""
        with self._lock:
            return list(self._prompts.values())

    async def delete(self, name: str) -> bool:
        """Delete a prompt."""
        with self._lock:
            if name in self._prompts:
                del self._prompts[name]
                return True
            return False
