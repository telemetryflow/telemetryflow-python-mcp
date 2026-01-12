"""Domain events for event sourcing and cross-aggregate communication."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class DomainEvent:
    """Base class for domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "occurredAt": self.occurred_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SessionCreatedEvent(DomainEvent):
    """Event emitted when a session is created."""

    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data["sessionId"] = self.session_id
        return data


@dataclass
class SessionInitializedEvent(DomainEvent):
    """Event emitted when a session is initialized."""

    session_id: str = ""
    client_name: str = ""
    client_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data["sessionId"] = self.session_id
        data["clientName"] = self.client_name
        data["clientVersion"] = self.client_version
        return data


@dataclass
class SessionClosedEvent(DomainEvent):
    """Event emitted when a session is closed."""

    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data["sessionId"] = self.session_id
        return data


@dataclass
class ConversationCreatedEvent(DomainEvent):
    """Event emitted when a conversation is created."""

    conversation_id: str = ""
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data["conversationId"] = self.conversation_id
        data["model"] = self.model
        return data


@dataclass
class MessageAddedEvent(DomainEvent):
    """Event emitted when a message is added to a conversation."""

    conversation_id: str = ""
    message_id: str = ""
    role: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data["conversationId"] = self.conversation_id
        data["messageId"] = self.message_id
        data["role"] = self.role
        return data


@dataclass
class ToolRegisteredEvent(DomainEvent):
    """Event emitted when a tool is registered."""

    session_id: str = ""
    tool_name: str = ""
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data["sessionId"] = self.session_id
        data["toolName"] = self.tool_name
        data["category"] = self.category
        return data


@dataclass
class ToolExecutedEvent(DomainEvent):
    """Event emitted when a tool is executed."""

    session_id: str = ""
    tool_name: str = ""
    success: bool = True
    duration_ms: float = 0.0
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data["sessionId"] = self.session_id
        data["toolName"] = self.tool_name
        data["success"] = self.success
        data["durationMs"] = self.duration_ms
        if self.error_message:
            data["errorMessage"] = self.error_message
        return data
