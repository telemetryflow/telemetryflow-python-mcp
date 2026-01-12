"""CQRS Query definitions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Query:
    """Base class for queries."""

    pass


@dataclass
class GetSessionQuery(Query):
    """Query to get a session by ID."""

    session_id: str


@dataclass
class ListSessionsQuery(Query):
    """Query to list all sessions."""

    limit: int = 100
    offset: int = 0


@dataclass
class GetSessionStatsQuery(Query):
    """Query to get session statistics."""

    session_id: str


@dataclass
class GetConversationQuery(Query):
    """Query to get a conversation by ID."""

    conversation_id: str


@dataclass
class ListConversationsQuery(Query):
    """Query to list conversations."""

    session_id: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass
class GetConversationMessagesQuery(Query):
    """Query to get messages in a conversation."""

    conversation_id: str
    limit: int = 100
    offset: int = 0


@dataclass
class GetToolQuery(Query):
    """Query to get a tool by name."""

    name: str


@dataclass
class ListToolsQuery(Query):
    """Query to list tools."""

    category: str | None = None
    enabled_only: bool = True
    cursor: str | None = None


@dataclass
class ListResourcesQuery(Query):
    """Query to list resources."""

    cursor: str | None = None


@dataclass
class ReadResourceQuery(Query):
    """Query to read a resource."""

    uri: str
    params: dict[str, str] = field(default_factory=dict)


@dataclass
class ListPromptsQuery(Query):
    """Query to list prompts."""

    cursor: str | None = None


@dataclass
class GetPromptQuery(Query):
    """Query to get a prompt."""

    name: str
    arguments: dict[str, str] = field(default_factory=dict)
