"""Mock objects for persistence layer."""

from typing import Any
from unittest.mock import AsyncMock

from tfo_mcp.domain.aggregates import Conversation, Session
from tfo_mcp.domain.entities import Prompt, Resource, Tool
from tfo_mcp.domain.valueobjects import ConversationID, ResourceURI, SessionID, ToolName


class NotFoundError(Exception):
    """Error raised when entity is not found."""

    pass


class MockSessionRepository:
    """Mock session repository for testing."""

    def __init__(self) -> None:
        """Initialize mock repository."""
        self._sessions: dict[str, Session] = {}
        self.save = AsyncMock(side_effect=self._save)
        self.find_by_id = AsyncMock(side_effect=self._find_by_id)
        self.delete = AsyncMock(side_effect=self._delete)
        self.list_all = AsyncMock(side_effect=self._list_all)

    def _save(self, session: Session) -> None:
        """Save a session."""
        self._sessions[str(session.id)] = session

    def _find_by_id(self, session_id: SessionID) -> Session | None:
        """Find a session by ID."""
        return self._sessions.get(str(session_id))

    def _delete(self, session_id: SessionID) -> bool:
        """Delete a session."""
        if str(session_id) in self._sessions:
            del self._sessions[str(session_id)]
            return True
        return False

    def _list_all(self) -> list[Session]:
        """List all sessions."""
        return list(self._sessions.values())

    def add_session(self, session: Session) -> None:
        """Add a session to the mock store."""
        self._sessions[str(session.id)] = session

    def clear(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()

    def reset(self) -> None:
        """Reset mock state."""
        self.clear()
        self.save.reset_mock()
        self.find_by_id.reset_mock()
        self.delete.reset_mock()
        self.list_all.reset_mock()


class MockConversationRepository:
    """Mock conversation repository for testing."""

    def __init__(self) -> None:
        """Initialize mock repository."""
        self._conversations: dict[str, Conversation] = {}
        self._by_session: dict[str, list[str]] = {}
        self.save = AsyncMock(side_effect=self._save)
        self.find_by_id = AsyncMock(side_effect=self._find_by_id)
        self.find_by_session = AsyncMock(side_effect=self._find_by_session)
        self.delete = AsyncMock(side_effect=self._delete)

    def _save(self, conversation: Conversation) -> None:
        """Save a conversation."""
        conv_id = str(conversation.id)
        session_id = str(conversation.session_id)
        self._conversations[conv_id] = conversation

        if session_id not in self._by_session:
            self._by_session[session_id] = []
        if conv_id not in self._by_session[session_id]:
            self._by_session[session_id].append(conv_id)

    def _find_by_id(self, conversation_id: ConversationID) -> Conversation | None:
        """Find a conversation by ID."""
        return self._conversations.get(str(conversation_id))

    def _find_by_session(self, session_id: SessionID) -> list[Conversation]:
        """Find conversations by session ID."""
        conv_ids = self._by_session.get(str(session_id), [])
        return [self._conversations[cid] for cid in conv_ids if cid in self._conversations]

    def _delete(self, conversation_id: ConversationID) -> bool:
        """Delete a conversation."""
        conv_id = str(conversation_id)
        if conv_id in self._conversations:
            conv = self._conversations[conv_id]
            session_id = str(conv.session_id)
            del self._conversations[conv_id]
            if session_id in self._by_session:
                self._by_session[session_id] = [
                    cid for cid in self._by_session[session_id] if cid != conv_id
                ]
            return True
        return False

    def add_conversation(self, conversation: Conversation) -> None:
        """Add a conversation to the mock store."""
        self._save(conversation)

    def clear(self) -> None:
        """Clear all conversations."""
        self._conversations.clear()
        self._by_session.clear()

    def reset(self) -> None:
        """Reset mock state."""
        self.clear()
        self.save.reset_mock()
        self.find_by_id.reset_mock()
        self.find_by_session.reset_mock()
        self.delete.reset_mock()


class MockToolRepository:
    """Mock tool repository for testing."""

    def __init__(self) -> None:
        """Initialize mock repository."""
        self._tools: dict[str, Tool] = {}
        self.save = AsyncMock(side_effect=self._save)
        self.find_by_name = AsyncMock(side_effect=self._find_by_name)
        self.find_all = AsyncMock(side_effect=self._find_all)
        self.delete = AsyncMock(side_effect=self._delete)

    def _save(self, tool: Tool) -> None:
        """Save a tool."""
        self._tools[str(tool.name)] = tool

    def _find_by_name(self, name: ToolName) -> Tool | None:
        """Find a tool by name."""
        return self._tools.get(str(name))

    def _find_all(self) -> list[Tool]:
        """Find all tools."""
        return list(self._tools.values())

    def _delete(self, name: ToolName) -> bool:
        """Delete a tool."""
        if str(name) in self._tools:
            del self._tools[str(name)]
            return True
        return False

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the mock store."""
        self._tools[str(tool.name)] = tool

    def clear(self) -> None:
        """Clear all tools."""
        self._tools.clear()

    def reset(self) -> None:
        """Reset mock state."""
        self.clear()
        self.save.reset_mock()
        self.find_by_name.reset_mock()
        self.find_all.reset_mock()
        self.delete.reset_mock()


class MockResourceRepository:
    """Mock resource repository for testing."""

    def __init__(self) -> None:
        """Initialize mock repository."""
        self._resources: dict[str, Resource] = {}
        self.save = AsyncMock(side_effect=self._save)
        self.find_by_uri = AsyncMock(side_effect=self._find_by_uri)
        self.find_all = AsyncMock(side_effect=self._find_all)
        self.delete = AsyncMock(side_effect=self._delete)

    def _save(self, resource: Resource) -> None:
        """Save a resource."""
        self._resources[str(resource.uri)] = resource

    def _find_by_uri(self, uri: ResourceURI) -> Resource | None:
        """Find a resource by URI."""
        return self._resources.get(str(uri))

    def _find_all(self) -> list[Resource]:
        """Find all resources."""
        return list(self._resources.values())

    def _delete(self, uri: ResourceURI) -> bool:
        """Delete a resource."""
        if str(uri) in self._resources:
            del self._resources[str(uri)]
            return True
        return False

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the mock store."""
        self._resources[str(resource.uri)] = resource

    def clear(self) -> None:
        """Clear all resources."""
        self._resources.clear()

    def reset(self) -> None:
        """Reset mock state."""
        self.clear()
        self.save.reset_mock()
        self.find_by_uri.reset_mock()
        self.find_all.reset_mock()
        self.delete.reset_mock()


class MockPromptRepository:
    """Mock prompt repository for testing."""

    def __init__(self) -> None:
        """Initialize mock repository."""
        self._prompts: dict[str, Prompt] = {}
        self.save = AsyncMock(side_effect=self._save)
        self.find_by_name = AsyncMock(side_effect=self._find_by_name)
        self.find_all = AsyncMock(side_effect=self._find_all)
        self.delete = AsyncMock(side_effect=self._delete)

    def _save(self, prompt: Prompt) -> None:
        """Save a prompt."""
        self._prompts[prompt.name] = prompt

    def _find_by_name(self, name: str) -> Prompt | None:
        """Find a prompt by name."""
        return self._prompts.get(name)

    def _find_all(self) -> list[Prompt]:
        """Find all prompts."""
        return list(self._prompts.values())

    def _delete(self, name: str) -> bool:
        """Delete a prompt."""
        if name in self._prompts:
            del self._prompts[name]
            return True
        return False

    def add_prompt(self, prompt: Prompt) -> None:
        """Add a prompt to the mock store."""
        self._prompts[prompt.name] = prompt

    def clear(self) -> None:
        """Clear all prompts."""
        self._prompts.clear()

    def reset(self) -> None:
        """Reset mock state."""
        self.clear()
        self.save.reset_mock()
        self.find_by_name.reset_mock()
        self.find_all.reset_mock()
        self.delete.reset_mock()


class MockAuditLogger:
    """Mock audit logger for testing."""

    def __init__(self) -> None:
        """Initialize mock audit logger."""
        self._events: list[dict[str, Any]] = []
        self.log = AsyncMock(side_effect=self._log)

    def _log(self, event_type: str, data: dict[str, Any]) -> None:
        """Log an audit event."""
        self._events.append({"type": event_type, "data": data})

    @property
    def events(self) -> list[dict[str, Any]]:
        """Get logged events."""
        return self._events.copy()

    def clear(self) -> None:
        """Clear logged events."""
        self._events.clear()

    def reset(self) -> None:
        """Reset mock state."""
        self.clear()
        self.log.reset_mock()
