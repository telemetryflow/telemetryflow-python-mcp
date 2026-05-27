"""Unit tests for domain events."""

from datetime import datetime

from tfo_mcp.domain.aggregates import Session
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.events import (
    ConversationCreatedEvent,
    MessageAddedEvent,
    SessionClosedEvent,
    SessionCreatedEvent,
    SessionInitializedEvent,
    ToolExecutedEvent,
    ToolRegisteredEvent,
)
from tfo_mcp.domain.valueobjects import ConversationID, SessionID


class TestSessionCreatedEvent:
    """Test SessionCreatedEvent."""

    def test_create_event(self):
        """Test creating session created event."""
        session_id = SessionID.generate()
        event = SessionCreatedEvent(session_id=str(session_id))

        assert event.event_type == "SessionCreatedEvent"
        assert event.session_id == str(session_id)
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_event_payload(self):
        """Test event payload."""
        session_id = SessionID.generate()
        event = SessionCreatedEvent(session_id=str(session_id))

        payload = event.to_dict()
        assert payload["eventType"] == "SessionCreatedEvent"
        assert payload["sessionId"] == str(session_id)
        assert "eventId" in payload
        assert "occurredAt" in payload


class TestSessionInitializedEvent:
    """Test SessionInitializedEvent."""

    def test_create_event(self):
        """Test creating session initialized event."""
        session_id = SessionID.generate()
        event = SessionInitializedEvent(
            session_id=str(session_id),
            client_name="test-client",
            client_version="1.0.0",
        )

        assert event.event_type == "SessionInitializedEvent"
        assert event.client_name == "test-client"

    def test_event_payload(self):
        """Test event payload includes client info."""
        event = SessionInitializedEvent(
            session_id="test-id",
            client_name="test-client",
            client_version="1.0.0",
        )

        payload = event.to_dict()
        assert payload["clientName"] == "test-client"
        assert payload["clientVersion"] == "1.0.0"


class TestSessionClosedEvent:
    """Test SessionClosedEvent."""

    def test_create_event(self):
        """Test creating session closed event."""
        event = SessionClosedEvent(
            session_id="test-id",
        )

        assert event.event_type == "SessionClosedEvent"
        assert event.session_id == "test-id"


class TestConversationCreatedEvent:
    """Test ConversationCreatedEvent."""

    def test_create_event(self):
        """Test creating conversation created event."""
        conv_id = ConversationID.generate()

        event = ConversationCreatedEvent(
            conversation_id=str(conv_id),
        )

        assert event.event_type == "ConversationCreatedEvent"
        assert event.conversation_id == str(conv_id)


class TestToolRegisteredEvent:
    """Test ToolRegisteredEvent."""

    def test_create_event(self):
        """Test creating tool registered event."""
        event = ToolRegisteredEvent(
            session_id="sess-123",
            tool_name="echo",
        )

        assert event.event_type == "ToolRegisteredEvent"
        assert event.tool_name == "echo"

    def test_event_payload(self):
        """Test event payload."""
        event = ToolRegisteredEvent(
            session_id="sess-123",
            tool_name="read_file",
            category="filesystem",
        )

        payload = event.to_dict()
        assert payload["toolName"] == "read_file"
        assert payload["category"] == "filesystem"


class TestToolExecutedEvent:
    """Test ToolExecutedEvent."""

    def test_create_success_event(self):
        """Test creating successful tool execution event."""
        event = ToolExecutedEvent(
            session_id="sess-123",
            tool_name="echo",
            duration_ms=50.5,
            success=True,
        )

        assert event.event_type == "ToolExecutedEvent"
        assert event.success is True
        assert event.duration_ms == 50.5

    def test_create_failure_event(self):
        """Test creating failed tool execution event."""
        event = ToolExecutedEvent(
            session_id="sess-123",
            tool_name="read_file",
            duration_ms=10.0,
            success=False,
            error_message="File not found",
        )

        assert event.success is False
        assert event.error_message == "File not found"


class TestMessageAddedEvent:
    """Test MessageAddedEvent."""

    def test_create_user_message_event(self):
        """Test creating user message event."""
        event = MessageAddedEvent(
            conversation_id="conv-123",
            message_id="msg-456",
            role="user",
        )

        assert event.event_type == "MessageAddedEvent"
        assert event.role == "user"

    def test_create_assistant_message_event(self):
        """Test creating assistant message event."""
        event = MessageAddedEvent(
            conversation_id="conv-123",
            message_id="msg-789",
            role="assistant",
        )

        assert event.role == "assistant"


class TestEventTimestamps:
    """Test event timestamp handling."""

    def test_event_has_timestamp(self):
        """Test that events have timestamps."""
        event = SessionCreatedEvent(session_id="test")
        assert event.occurred_at is not None
        assert isinstance(event.occurred_at, datetime)

    def test_event_has_unique_id(self):
        """Test that events have unique IDs."""
        event1 = SessionCreatedEvent(session_id="test")
        event2 = SessionCreatedEvent(session_id="test")
        assert event1.event_id != event2.event_id


class TestSessionEventIntegration:
    """Test events generated by Session aggregate."""

    def test_session_create_emits_event(self):
        """Test that creating a session emits event."""
        session = Session.create()
        events = session.get_events()

        assert len(events) >= 1
        assert any(isinstance(e, SessionCreatedEvent) for e in events)

    def test_session_initialize_emits_event(self):
        """Test that initializing a session emits event."""
        session = Session.create()
        # Consume the creation event
        session.get_events()

        client = ClientInfo(name="test", version="1.0")
        session.initialize(client)

        events = session.get_events()
        assert len(events) >= 1
        assert any(isinstance(e, SessionInitializedEvent) for e in events)

    def test_session_close_emits_event(self):
        """Test that closing a session emits event."""
        session = Session.create()
        client = ClientInfo(name="test", version="1.0")
        session.initialize(client)
        # Consume previous events
        session.get_events()

        session.close()

        events = session.get_events()
        assert len(events) >= 1
        assert any(isinstance(e, SessionClosedEvent) for e in events)

    def test_get_events_returns_list(self):
        """Test getting events returns a list."""
        session = Session.create()
        events = session.get_events()
        assert isinstance(events, list)
        assert len(events) > 0
