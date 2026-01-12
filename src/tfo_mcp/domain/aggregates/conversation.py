"""Conversation aggregate root."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from tfo_mcp.domain.entities import Message
from tfo_mcp.domain.events import (
    ConversationCreatedEvent,
    DomainEvent,
    MessageAddedEvent,
)
from tfo_mcp.domain.valueobjects import ConversationID, Model, SystemPrompt


class ConversationStatus(str, Enum):
    """Conversation status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationSettings:
    """Conversation settings."""

    max_tokens: int = 4096
    temperature: float = 1.0
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.top_k is not None:
            result["top_k"] = self.top_k
        if self.stop_sequences:
            result["stop_sequences"] = self.stop_sequences
        return result


@dataclass
class Conversation:
    """Conversation aggregate root - manages a conversation with Claude."""

    id: ConversationID
    model: Model
    system_prompt: SystemPrompt
    messages: list[Message] = field(default_factory=list)
    status: ConversationStatus = ConversationStatus.ACTIVE
    settings: ConversationSettings = field(default_factory=ConversationSettings)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @classmethod
    def create(
        cls,
        model: Model | str = Model.CLAUDE_4_SONNET,
        system_prompt: str = "",
        settings: ConversationSettings | None = None,
    ) -> Conversation:
        """Create a new conversation."""
        if isinstance(model, str):
            model = Model.from_string(model)

        conversation = cls(
            id=ConversationID.generate(),
            model=model,
            system_prompt=SystemPrompt(value=system_prompt),
            settings=settings or ConversationSettings(),
        )
        conversation._add_event(
            ConversationCreatedEvent(
                conversation_id=str(conversation.id),
                model=model.value,
            )
        )
        return conversation

    def _add_event(self, event: DomainEvent) -> None:
        """Add a domain event."""
        self._events.append(event)

    def get_events(self) -> list[DomainEvent]:
        """Get and clear pending domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        with self._lock:
            self.messages.append(message)
            self.total_input_tokens += message.input_tokens
            self.total_output_tokens += message.output_tokens
            self.updated_at = datetime.now(UTC)

            self._add_event(
                MessageAddedEvent(
                    conversation_id=str(self.id),
                    message_id=str(message.id),
                    role=message.role.value,
                )
            )

    def get_messages_for_api(self) -> list[dict[str, Any]]:
        """Get messages formatted for Claude API."""
        with self._lock:
            return [msg.to_api_format() for msg in self.messages]

    def set_status(self, status: ConversationStatus) -> None:
        """Set the conversation status."""
        with self._lock:
            self.status = status
            self.updated_at = datetime.now(UTC)

    @property
    def message_count(self) -> int:
        """Get the number of messages."""
        with self._lock:
            return len(self.messages)

    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def last_message(self) -> Message | None:
        """Get the last message."""
        with self._lock:
            return self.messages[-1] if self.messages else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "model": self.model.value,
            "systemPrompt": str(self.system_prompt),
            "messageCount": self.message_count,
            "status": self.status.value,
            "settings": self.settings.to_dict(),
            "totalInputTokens": self.total_input_tokens,
            "totalOutputTokens": self.total_output_tokens,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
